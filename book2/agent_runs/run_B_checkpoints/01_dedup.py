"""Step 1: load the three sources, normalise, deduplicate in passes. Checkpoint A."""
import sys, json, re, collections, difflib, itertools
sys.path.insert(0, '/tmp/agent_test_B/work')
import pandas as pd
from common import *

recs = []
for r in load('pubmed'):
    a = r.get('authors') or []
    recs.append(dict(src='pubmed', sid=r['pmid'], doi=norm_doi(r.get('doi')), pmid=norm_pmid(r['pmid']),
        pmcid=norm_pmcid(r.get('pmcid')), title=r.get('title'), year=year_int(r.get('year')),
        akey=akey_from_surname(a[0]['name']) if a else None, n_auth=len(a) or None,
        doctype='; '.join(r.get('pub_types') or [])))
for r in load('europepmc'):
    au = (r.get('authorString') or '').strip().rstrip('.')
    names = [x.strip() for x in au.split(',') if x.strip()]
    first = names[0] if names else None
    if first:
        t = first.split()
        # "Surname INITIALS": drop a trailing all-capitals initials token
        if len(t) > 1 and re.fullmatch(r"[A-Z\-']{1,4}", t[-1]): t = t[:-1]
        first = ' '.join(t)
    recs.append(dict(src='europepmc', sid=f"{r['source']}:{r['id']}", doi=norm_doi(r.get('doi')),
        pmid=norm_pmid(r.get('pmid')), pmcid=norm_pmcid(r.get('pmcid')), title=r.get('title'),
        year=year_int(r.get('pubYear')), akey=akey_from_surname(first), n_auth=len(names) or None,
        doctype=f"{r['source']}|{r.get('pubType') or ''}"))
for r in load('openalex'):
    a = r.get('authorships') or []
    recs.append(dict(src='openalex', sid=r['openalex_id'], doi=norm_doi(r.get('doi')), pmid=norm_pmid(r.get('pmid')),
        pmcid=None, title=r.get('title'), year=year_int(r.get('year')),
        akey=akey_from_surname(r.get('first_author')), n_auth=len(a) or None, doctype=r.get('type')))
R = pd.DataFrame(recs)
R['tn'] = R.title.map(norm_title)
R.loc[R.tn.isin(['not available', '']), 'tn'] = ''
N = len(R)
log = {'records_in': R.src.value_counts().to_dict(), 'records_total': N}
log['invalid_doi_dropped'] = {s: int(sum(1 for r in load(s) if r.get('doi') and not norm_doi(r.get('doi')))) for s in FILES}

# ---------- union-find with a guard: a cluster may never hold two different PMIDs
parent = list(range(N)); pmids = [({p} if p else set()) for p in R.pmid]
dois = [({d} if isinstance(d, str) else set()) for d in R.doi]
# preprint flag: a preprint and its journal version are one work (see QUESTIONS.md Q1)
isprep = [bool(re.search('preprint', str(d), re.I)) or str(d).startswith('PPR|') for d in R.doctype]
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
def union(i, j, relaxed=False):
    """strict: never join two different PMIDs.
    relaxed (title+year+author already agree): a PMID difference is accepted only if one side is a
    preprint (preprint + journal version) or both sides carry the same DOI (double-indexed record)."""
    a, b = find(i), find(j)
    if a == b: return 'same'
    if pmids[a] and pmids[b] and not (pmids[a] & pmids[b]):
        if not (relaxed and (isprep[a] or isprep[b] or (dois[a] & dois[b]))): return 'conflict'
    parent[b] = a; pmids[a] |= pmids[b]; dois[a] |= dois[b]; isprep[a] = isprep[a] and isprep[b]
    return 'merged'
def nclusters(): return len({find(i) for i in range(N)})
def sim(a, b): return difflib.SequenceMatcher(None, a, b).ratio()

steps = []; before = N
def close(name):
    global before
    n = nclusters(); steps.append({'pass': name, 'removed': before - n, 'unique_after': n}); before = n

# ---- Pass 1a: same PMID
for _, idx in R[R.pmid.notna()].groupby('pmid').indices.items():
    ii = R.index[R.pmid.notna()][idx]
    for j in ii[1:]: union(ii[0], j)
close('1a identifier: PMID')
# ---- Pass 1b: same PMCID
conf = 0
sub = R[R.pmcid.notna()]
for _, g in sub.groupby('pmcid'):
    ii = list(g.index)
    for j in ii[1:]: conf += union(ii[0], j) == 'conflict'
close('1b identifier: PMCID'); log['pmcid_blocked_pmid_conflict'] = conf
# ---- Pass 1c: same DOI. Guards: no PMID conflict; titles must agree (>=0.60) unless a title is missing/translated
doi_conf = 0; doi_lowsim = []
sub = R[R.doi.notna()]
for d, g in sub.groupby('doi'):
    ii = list(g.index)
    for i, j in itertools.combinations(ii, 2):
        if find(i) == find(j): continue
        ti, tj = R.tn[i], R.tn[j]
        trans = str(R.title[i]).startswith('[') or str(R.title[j]).startswith('[')
        if ti and tj and not trans and sim(ti, tj) < 0.60:
            doi_lowsim.append((d, R.src[i], R.title[i], R.src[j], R.title[j])); continue
        doi_conf += union(i, j) == 'conflict'
close('1c identifier: DOI')
log['doi_pairs_blocked_pmid_conflict'] = doi_conf
log['doi_pairs_blocked_title_disagrees'] = len(doi_lowsim)
pd.DataFrame(doi_lowsim, columns=['doi', 'src1', 't1', 'src2', 't2']).to_csv(OUT + '/doi_shared_not_merged.csv', index=False)

# ---- cluster-level view helper
def cluster_view():
    R['cid'] = [find(i) for i in range(N)]
    d = collections.defaultdict(lambda: [set(), set(), set()])
    for cid, t, y, a in zip(R.cid, R.tn, R.year, R.akey):
        e = d[cid]
        if isinstance(t, str) and t: e[0].add(t)
        if pd.notna(y): e[1].add(int(y))
        if isinstance(a, str) and a: e[2].add(a)
    return pd.DataFrame({c: [sorted(v[0]), sorted(v[1]), sorted(v[2])] for c, v in d.items()},
                        index=['tns', 'years', 'akeys']).T
MIN_LEN = 25
# ---- Pass 2: exact normalised title + same year + same first-author key (title >= 25 chars)
C = cluster_view(); keymap = collections.defaultdict(list); short_pairs = 0
shortmap = collections.defaultdict(set)
for cid, row in C.iterrows():
    for t in row.tns:
        for y in row.years:
            for a in row.akeys:
                if len(t) >= MIN_LEN: keymap[(t, y, a)].append(cid)
                else: shortmap[(t, y, a)].add(cid)
p2_conf = 0
for k, cids in keymap.items():
    cids = list(dict.fromkeys(cids))
    for i, j in itertools.combinations(cids, 2): p2_conf += union(i, j, relaxed=True) == 'conflict'
close('2 exact title + year + first author')
log['pass2_blocked_pmid_conflict'] = p2_conf
log['pass2_short_title_groups_not_merged'] = sum(1 for v in shortmap.values() if len({find(c) for c in v}) > 1)

# ---- Pass 3: careful. Candidates = same first-author key, year within +-1.
#   3a exact title, year differs by 1 (online vs print year)  -> merge
#   3b title similarity >= 0.95 (same or adjacent year)        -> merge
#   uncertain band 0.85 <= sim < 0.95                          -> NOT merged, listed
C = cluster_view(); by_a = collections.defaultdict(list)
for cid, row in C.iterrows():
    for a in row.akeys: by_a[a].append(cid)
cand = set()
for a, cids in by_a.items():
    cids = list(dict.fromkeys(cids))
    if len(cids) < 2: continue
    for i, j in itertools.combinations(cids, 2):
        yi, yj = C.years[i], C.years[j]
        if not yi or not yj: continue
        if min(abs(x - y) for x in yi for y in yj) <= 1: cand.add((i, j))
m3a = m3b = 0; band = []; p3_conf = 0; fuzzy = []
MARK = re.compile(r'\b(additional file|supplement\w*|correction|corrigendum|erratum|errata|author response|reply|response|comment\w*|retract\w*|protocol|part|decision letter|review for|reviewer)\b')
for i, j in sorted(cand):
    if find(i) == find(j): continue
    best = 0; bt = None
    for t1 in C.tns[i]:
        for t2 in C.tns[j]:
            if min(len(t1), len(t2)) < MIN_LEN: continue
            if abs(len(t1) - len(t2)) > 0.3 * max(len(t1), len(t2)): continue
            s = 1.0 if t1 == t2 else sim(t1, t2)
            if s > best: best, bt = s, (t1, t2)
    if best >= 0.95:
        if best < 1.0 and (MARK.findall(bt[0]) != MARK.findall(bt[1]) or re.findall(r'\d+', bt[0]) != re.findall(r'\d+', bt[1])):
            band.append((i, j, round(best, 3), 'uncertain', *bt)); continue   # e.g. "correction to X", "part 2"
        r = union(i, j, relaxed=True)
        if r == 'conflict': p3_conf += 1; band.append((i, j, round(best, 3), 'pmid_conflict', *bt))
        elif r == 'merged':
            if best == 1.0: m3a += 1
            else: m3b += 1; fuzzy.append((round(best, 3), *bt))
    elif best >= 0.85:
        band.append((i, j, round(best, 3), 'uncertain', *bt))
close('3 near-identical titles (exact title/adjacent year, or similarity >= 0.95)')
steps[-1]['of_which_exact_title_adjacent_year'] = m3a; steps[-1]['of_which_fuzzy_ge_0.95'] = m3b
pd.DataFrame(fuzzy, columns=['sim', 't1', 't2']).to_csv(OUT + '/pass3_fuzzy_merged.csv', index=False)
B = pd.DataFrame(band, columns=['cid1', 'cid2', 'sim', 'kind', 't1', 't2'])
B = B[[find(a) != find(b) for a, b in zip(B.cid1, B.cid2)]]
B.to_csv(OUT + '/uncertain_band_pairs.csv', index=False)
log['uncertain_band_pairs_not_merged'] = int((B.kind == 'uncertain').sum())
log['near_identical_blocked_by_pmid_conflict'] = int((B.kind == 'pmid_conflict').sum())

# same title + year but first author missing on one side -> also uncertain, not merged
C = cluster_view(); tm = collections.defaultdict(set)
for cid, row in C.iterrows():
    for t in row.tns:
        if len(t) >= MIN_LEN:
            for y in row.years: tm[(t, y)].add(cid)
log['same_title_year_author_missing_or_different_not_merged_groups'] = sum(1 for v in tm.values() if len(v) > 1)
pd.DataFrame([(t, y, len(v)) for (t, y), v in tm.items() if len(v) > 1], columns=['tn', 'year', 'n_clusters']).to_csv(OUT + '/same_title_year_not_merged.csv', index=False)

R['cid'] = [find(i) for i in range(N)]
log['passes'] = steps; log['unique_works'] = int(R.cid.nunique())
log['works_with_more_than_one_pmid'] = int((R.groupby('cid').pmid.nunique() > 1).sum())
log['max_pmids_in_cluster'] = int(R.groupby('cid').pmid.nunique().max())
log['cluster_size_dist'] = {int(k): int(v) for k, v in R.groupby('cid').size().value_counts().sort_index().items()}
R.to_pickle(OUT + '/records.pkl')
json.dump(log, open(OUT + '/dedup_log.json', 'w'), indent=1)
print(json.dumps(log, indent=1))
