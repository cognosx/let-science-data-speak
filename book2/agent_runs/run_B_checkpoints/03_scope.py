"""Step 3: document-type filter ('paper'), keyword relevance flag, and the random sample for the manual
on-topic check of single-source works (checkpoint F)."""
import sys, re, json
sys.path.insert(0, '/tmp/agent_test_B/work')
import pandas as pd
from common import *
W = pd.read_pickle(OUT + '/works.pkl')
pm = {r['pmid']: r for r in load('pubmed')}

# ---- 'paper' = journal-type scholarly document (QUESTIONS.md Q2)
NOT_PAPER_OA = {'dissertation', 'dataset', 'paratext', 'erratum', 'peer-review', 'supplementary-materials', 'software',
                'study-registration', 'reference-entry', 'book', 'book-chapter', 'book-review', 'report', 'other'}
def is_paper(st):
    parts = dict(p.split('=', 1) for p in st.split(' || ') if '=' in p)   # one type per source (first seen)
    allp = [p.split('=', 1) for p in st.split(' || ') if '=' in p]
    if any(s == 'pubmed' for s, _ in allp):
        t = ' '.join(v for s, v in allp if s == 'pubmed')
        return not re.search(r'Published Erratum|Retraction of Publication|Expression of Concern', t)
    ep = [v for s, v in allp if s == 'europepmc']
    if ep:
        srcs = {v.split('|')[0] for v in ep}
        if srcs & {'MED', 'PMC', 'AGR', 'CBA', 'PPR'}: return True
        if srcs <= {'PAT', 'ETH', 'CTX'}: return False
    oa = [v for s, v in allp if s == 'openalex']
    return any(v not in NOT_PAPER_OA for v in oa)
W['paper'] = W.src_types.map(is_paper)
def strict(st):   # research articles and reviews only
    allp = [p.split('=', 1) for p in st.split(' || ') if '=' in p]
    t = ' '.join(v for s, v in allp if s == 'pubmed')
    if t: return bool(re.search(r'Journal Article|Review|Clinical Trial|Randomized', t)) and not re.search(r'Editorial|Letter|Comment|News|Erratum|Preprint|Biography|Interview', t)
    return any(v in ('article', 'review') for s, v in allp if s == 'openalex') or any(re.search(r'research-article|review', v) and not v.startswith(('PPR', 'PAT')) for s, v in allp if s == 'europepmc')
W['paper_strict'] = W.paper & W.src_types.map(strict)
W['preprint_only'] = W.src_types.map(lambda st: all(('preprint' in p.lower() or '=PPR|' in p) for p in st.split(' || ')))

# ---- keyword relevance flag (title in any source; PubMed abstract and MeSH where the work is in PubMed)
MAL = re.compile(r'malaria|plasmodi|paludisme|palud|falciparum|vivax|sporozoit|merozoit|rts,?\s?s|r21|pfspz|mosquirix|circumsporozoite|anophel', re.I)
VAC = re.compile(r'vaccin|immuni[sz]ation|immunogen|vakzin|impf|vacuna|疫苗', re.I)
R = pd.read_pickle(OUT + '/records2.pkl')
tt = R.groupby('cid').title.agg(lambda s: ' || '.join(str(x) for x in s if isinstance(x, str)))
W['all_titles'] = tt.reindex(W.index)
W['kw_title'] = W.all_titles.map(lambda t: bool(MAL.search(t) and VAC.search(t)))
def pm_flag(p):
    r = pm.get(p)
    if not r: return None
    if 'Malaria Vaccines' in (r.get('mesh') or []): return True
    txt = (r.get('title') or '') + ' ' + (r.get('abstract') or '')
    return bool(MAL.search(txt) and VAC.search(txt))
pmids = R[R.src == 'pubmed'].groupby('cid').sid.agg(list)
W['kw_pubmed'] = [any(pm_flag(p) for p in pmids[c]) if c in pmids.index else None for c in W.index]
W['kw_any'] = W.kw_title | (W.kw_pubmed == True)
W.to_pickle(OUT + '/works3.pkl')
print('paper', W.paper.sum(), 'strict', W.paper_strict.sum(), 'kw_title', W.kw_title.mean().round(3), 'kw_any', W.kw_any.mean().round(3))
print(W.groupby('sources')[['paper', 'kw_title', 'kw_any']].mean().round(3).assign(n=W.sources.value_counts()))

# ---- sample for manual check: 50 works per single-source group + 50 found by all three, seed 20261116
S = []
for grp in ['openalex', 'europepmc', 'pubmed', 'europepmc+openalex+pubmed']:
    d = W[W.sources == grp].sample(50, random_state=20261116)
    for cid, r in d.iterrows(): S.append(dict(cid=int(cid), group=grp, year=r.year, paper=bool(r.paper), kw_any=bool(r.kw_any), types=r.src_types[:60], title=str(r.title)[:230]))
pd.DataFrame(S).to_csv(OUT + '/scope_sample_to_rate.csv', index=False)
