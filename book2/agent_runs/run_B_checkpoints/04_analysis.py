"""Step 4: completeness (B), shares with 95% intervals (D), income groups, start-year tests (E),
scope (F), sensitivity analyses. Writes /tmp/agent_test_B/results.json."""
import sys, json, re, math, collections
sys.path.insert(0, '/tmp/agent_test_B/work')
import pandas as pd, numpy as np
from common import *
W = pd.read_pickle(OUT + '/works3.pkl')
REG = dict(zip(*[pd.read_excel(RAW + '/CLASS.xlsx')[c] for c in ['Code', 'Region']]))
SSA = {c for c, r in REG.items() if r == 'Sub-Saharan Africa'}
RES = {}
PERIODS = [('2000-2009', 2000, 2009), ('2010-2019', 2010, 2019), ('2020-2026', 2020, 2026)]
def period(y, P=PERIODS):
    if pd.isna(y): return None
    for n, a, b in P:
        if a <= y <= b: return n
    return None
def wilson(k, n, z=1.959964):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
def share(k, n):
    lo, hi = wilson(k, n)
    return {'k': int(k), 'n': int(n), 'pct': round(100 * k / n, 1) if n else None, 'ci95': [round(100 * lo, 1), round(100 * hi, 1)] if n else None}
def diff_ci(k1, n1, k2, n2):   # Newcombe interval for p2 - p1, in percentage points
    p1, p2 = k1 / n1, k2 / n2; l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2); d = p2 - p1
    return {'diff_pp': round(100 * d, 1), 'ci95': [round(100 * (d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)), 1), round(100 * (d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)), 1)]}
def trend_z(years, flags):     # Cochran-Armitage trend test, score = year
    d = pd.DataFrame({'y': years, 'f': flags}).dropna(); d['f'] = d.f.astype(float)
    n = len(d); p = d.f.mean(); ybar = d.y.mean()
    num = ((d.y - ybar) * d.f).sum(); den = math.sqrt(p * (1 - p) * ((d.y - ybar) ** 2).sum())
    z = num / den if den else float('nan')
    return {'z': round(z, 2), 'p_two_sided': float(f'{math.erfc(abs(z) / math.sqrt(2)):.2g}'), 'n': int(n), 'direction': 'up' if z > 0 else 'down'}

RES['unit'] = 'one scholarly work (a preprint and its journal version count once); shares are fractions of papers, whole counting, one first and one last author per paper'
RES['unique_works'] = int(len(W))
RES['dedup'] = json.load(open(OUT + '/dedup_log.json'))
RES['works_by_source_combination'] = W.sources.value_counts().to_dict()
RES['papers_all_years'] = int(W.paper.sum())
W['per'] = W.year.map(period)
P = W[W.paper & W.per.notna()].copy()
RES['papers_2000_2026'] = int(len(P)); RES['papers_by_period'] = P.per.value_counts().sort_index().to_dict()
RES['non_paper_works_excluded'] = int((~W.paper).sum())
RES['works_without_year'] = int(W.year.isna().sum())

# ================= B. completeness, BEFORE any share
B = {}
R = pd.read_pickle(OUT + '/records2.pkl')
R['yr'] = R.year
# (i) by source, on the source's own records (raw completeness of each download)
def rec_tab(src, col):
    d = R[(R.src == src)]
    if col == 'year': return d.assign(k=d.year.notna()).groupby(d.year.fillna(-1).astype(int)).k.agg(['size', 'mean'])
    known = d[col].notna()
    return d.assign(k=known)[d.year.between(2000, 2026)].groupby('year').k.agg(['size', 'mean'])
B['year_known_by_source_records'] = {s: round(float(R[R.src == s].year.notna().mean()), 4) for s in FILES}
B['year_known_works'] = round(float(W.year.notna().mean()), 4)
rows = []
for y in range(2000, 2027):
    d = P[P.year == y]; r = {'year': y, 'papers': len(d)}
    for who, k in [('first', 'f'), ('last', 'l')]:
        for lab, m in [('pubmed', d.in_pm), ('openalex', d.in_oa), ('europepmc', d.in_ep)]:
            dd = d[m]
            col = {'pubmed': f'{k}_pm', 'openalex': f'{k}_oa'}.get(lab)
            r[f'{who}_{lab}'] = round(float(dd[col].notna().mean()), 3) if col and len(dd) else (0.0 if len(dd) else None)
        r[f'{who}_combined'] = round(float(d[f'{who}_iso3'].notna().mean()), 3)
    rows.append(r)
BY = pd.DataFrame(rows); BY.to_csv(OUT + '/completeness_by_year.csv', index=False)
B['by_year'] = rows
bp = {}
for n, a, b in PERIODS:
    d = P[P.per == n]; r = {'papers': int(len(d))}
    for who, k in [('first', 'f'), ('last', 'l')]:
        r[who] = {'pubmed_records (n=%d)' % d.in_pm.sum(): round(float(d[d.in_pm][f'{k}_pm'].notna().mean()), 3),
                  'openalex_records (n=%d)' % d.in_oa.sum(): round(float(d[d.in_oa][f'{k}_oa'].notna().mean()), 3),
                  'europepmc_records (n=%d)' % d.in_ep.sum(): 0.0,
                  'combined_all_papers': round(float(d[f'{who}_iso3'].notna().mean()), 3),
                  'filled_from': d[f'{who}_src'].value_counts().to_dict()}
    bp[n] = r
B['by_period'] = bp
B['years_below_half_combined'] = {who: [int(r['year']) for r in rows if r[f'{who}_combined'] < 0.5] for who in ['first', 'last']}
B['gate'] = {n: {who: ('PASS' if bp[n][who]['combined_all_papers'] >= 0.5 else 'FAIL - no share reported') for who in ['first', 'last']} for n, _, _ in PERIODS}
# is missingness related to things we can see?  (papers in PubMed vs not)
B['combined_known_by_in_pubmed'] = {str(k): {who: round(float(v[f'{who}_iso3'].notna().mean()), 3) for who in ['first', 'last']} for k, v in P.groupby('in_pm')}
RES['B_completeness'] = B

# ================= shares (only where the gate passes)
def ssa_table(D, col_first='first_ssa', col_last='last_ssa', P_=PERIODS, gate=True):
    out = {}
    for n, a, b in P_:
        d = D[(D.year >= a) & (D.year <= b)]; o = {'papers': int(len(d))}
        for who, col in [('first', col_first), ('last', col_last)]:
            kn = d[col].notna(); known = kn.mean() if len(d) else 0
            if gate and known < 0.5: o[who] = {'reported': False, 'known_share': round(float(known), 3), 'reason': 'country known for less than half of papers'}
            else:
                s = share(int((d[col][kn] == True).sum()), int(kn.sum())); s['known_share'] = round(float(known), 3)
                # bounds if every unknown were non-SSA / had the same share as OpenAlex-only-unknown is unknowable: give the floor
                s['floor_if_all_unknown_non_SSA_pct'] = round(100 * s['k'] / len(d), 1)
                o[who] = s
        out[n] = o
    return out
MAIN = ssa_table(P); RES['main_ssa_shares'] = MAIN
def change(tab, who, a='2000-2009', b='2020-2026'):
    x, y = tab[a][who], tab[b][who]
    if 'k' not in x or 'k' not in y: return None
    return diff_ci(x['k'], x['n'], y['k'], y['n'])
RES['main_change_2000s_to_2020s'] = {who: change(MAIN, who) for who in ['first', 'last']}
RES['main_change_2010s_to_2020s'] = {who: change(MAIN, who, '2010-2019') for who in ['first', 'last']}

# income group of first author's country
INC = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
def inc_table(D, col):
    out = {}
    for n, a, b in PERIODS + [('2000-2026', 2000, 2026)]:
        d = D[(D.year >= a) & (D.year <= b)]; kn = d[col].notna()
        o = {'papers': int(len(d)), 'known_share': round(float(kn.mean()), 3)}
        if kn.mean() >= 0.5:
            for g in INC: o[g] = share(int((d[col] == g).sum()), int(kn.sum()))
        else: o['reported'] = False
        out[n] = o
    return out
RES['income_first_author_at_publication_year'] = inc_table(P, 'first_income_pubyear')
RES['income_first_author_current_classification'] = inc_table(P, 'first_income_now')
# SSA first authors by income group (to see what drives it)
RES['top_first_author_countries_by_period'] = {n: P[(P.per == n)].first_iso3.value_counts().head(10).to_dict() for n, _, _ in PERIODS}
RES['top_ssa_first_author_countries_by_period'] = {n: P[(P.per == n) & (P.first_ssa == True)].first_iso3.value_counts().head(8).to_dict() for n, _, _ in PERIODS}
RES['top_ssa_last_author_countries_by_period'] = {n: P[(P.per == n) & (P.last_ssa == True)].last_iso3.value_counts().head(8).to_dict() for n, _, _ in PERIODS}

# ================= E. start year / period split
E = {'annual_trend_test': {}, 'period_splits': {}}
Wp = W[W.paper & W.year.notna()]
for who in ['first', 'last']:
    for start in [1990, 1995, 2000, 2005, 2010, 2015]:
        for end in [2026, 2025]:
            d = Wp[(Wp.year >= start) & (Wp.year <= end)]
            E['annual_trend_test'][f'{who}_{start}-{end}'] = trend_z(d.year, d[f'{who}_ssa'])
SPL = {'5-year': [('2000-2004', 2000, 2004), ('2005-2009', 2005, 2009), ('2010-2014', 2010, 2014), ('2015-2019', 2015, 2019), ('2020-2026', 2020, 2026)],
       'with_1990s': [('1990-1999', 1990, 1999)] + PERIODS,
       'shifted_2005': [('2005-2014', 2005, 2014), ('2015-2026', 2015, 2026)],
       'two_halves': [('2000-2012', 2000, 2012), ('2013-2026', 2013, 2026)],
       'drop_2026': [('2000-2009', 2000, 2009), ('2010-2019', 2010, 2019), ('2020-2025', 2020, 2025)]}
for name, pp in SPL.items(): E['period_splits'][name] = ssa_table(Wp, P_=pp)
E['annual_series'] = [{'year': int(y), 'papers': int(len(d)),
                       'first_ssa_pct': round(100 * (d.first_ssa == True).sum() / max(d.first_ssa.notna().sum(), 1), 1), 'first_known': round(float(d.first_ssa.notna().mean()), 2),
                       'last_ssa_pct': round(100 * (d.last_ssa == True).sum() / max(d.last_ssa.notna().sum(), 1), 1), 'last_known': round(float(d.last_ssa.notna().mean()), 2)}
                      for y, d in Wp[Wp.year >= 1990].groupby('year')]
RES['E_start_year'] = E

# ================= sensitivity analyses
S = {}
P['first_ssa_oafirst'] = P.first_iso3_oafirst.map(lambda c: (c in SSA) if isinstance(c, str) else None)
P['last_ssa_oafirst'] = P.last_iso3_oafirst.map(lambda c: (c in SSA) if isinstance(c, str) else None)
for src, k in [('oa', 'oa'), ('pm', 'pm')]:
    P[f'first_ssa_{src}'] = P[f'f_{k}'].map(lambda c: (c in SSA) if isinstance(c, str) else None)
    P[f'last_ssa_{src}'] = P[f'l_{k}'].map(lambda c: (c in SSA) if isinstance(c, str) else None)
S['country_priority_openalex_first'] = ssa_table(P, 'first_ssa_oafirst', 'last_ssa_oafirst')
S['single_source_openalex_only (same method in all periods)'] = ssa_table(P, 'first_ssa_oa', 'last_ssa_oa')
S['single_source_pubmed_text_only (gate applies)'] = ssa_table(P[P.in_pm], 'first_ssa_pm', 'last_ssa_pm')
S['multi_country_authors_any_SSA'] = ssa_table(P, 'first_ssa_any', 'last_ssa_any')
S['multi_country_authors_only_SSA'] = ssa_table(P, 'first_ssa_only', 'last_ssa_only')
S['multi_author_papers_only'] = ssa_table(P[P.n_auth.fillna(0) >= 2])
S['research_articles_and_reviews_only'] = ssa_table(P[P.paper_strict])
S['excluding_preprint_only_works'] = ssa_table(P[~P.preprint_only])
S['works_found_by_all_three_sources'] = ssa_table(P[P.sources == 'europepmc+openalex+pubmed'])
P['strict_topic'] = P.kw_title | P.index.map(lambda c: False)
pm = {r['pmid']: r for r in load('pubmed')}
mesh_mv = R[R.src == 'pubmed'].assign(mv=lambda d: d.sid.map(lambda p: 'Malaria Vaccines' in (pm[p].get('mesh') or []))).groupby('cid').mv.any()
W['mesh_mv'] = mesh_mv.reindex(W.index).fillna(False).astype(bool); W['topic_screen'] = W.kw_title | W.mesh_mv
P['topic_screen'] = W.topic_screen.reindex(P.index)
S['keyword_screened_on_topic_subset'] = ssa_table(P[P.topic_screen])
S['not_passing_keyword_screen'] = ssa_table(P[~P.topic_screen])
P2 = P.copy(); P2['year'] = P2.year_min
S['year_definition_earliest_year_across_sources'] = ssa_table(P2)
S['all_work_types_incl_patents_theses_datasets'] = ssa_table(W[W.year.notna()])
RES['sensitivity'] = S
RES['sensitivity_change_2000s_to_2020s_pp'] = {k: {who: change(v, who) for who in ['first', 'last']} for k, v in S.items()}
RES['year_conflicts'] = {'works_with_different_years_across_sources': int(W.year_conflict.sum()),
                         'papers_changing_period_if_earliest_year_used': int((P.year.map(period) != P.year_min.map(period)).sum())}
RES['income_keyword_screened_subset_pubyear'] = inc_table(P[P.topic_screen], 'first_income_pubyear')

# supplementary: papers with at least one SSA-affiliated author (OpenAlex authorship countries) - who leads those?
import pycountry
I23 = {c.alpha_2: c.alpha_3 for c in pycountry.countries}
anyssa = {}
for r in load('openalex'):
    cs = {I23.get(c) for a in (r.get('authorships') or []) for c in (a.get('countries') or [])}
    anyssa[r['openalex_id']] = bool(cs & SSA)
a2 = R[R.src == 'openalex'].assign(a=lambda d: d.sid.map(anyssa)).groupby('cid').a.any()
P['any_author_ssa'] = a2.reindex(P.index).fillna(False).astype(bool) | (P.first_ssa == True) | (P.last_ssa == True)
S2 = ssa_table(P[P.any_author_ssa]); 
RES['supplementary_papers_with_any_SSA_author'] = {'note': 'denominator = papers with at least one author affiliated in SSA (OpenAlex authorship countries, or SSA first/last author)', 'table': S2,
    'share_of_all_papers_with_any_SSA_author': {n: share(int(P[P.per == n].any_author_ssa.sum()), int((P.per == n).sum())) for n, _, _ in PERIODS},
    'change_2000s_to_2020s': {who: change(S2, who) for who in ['first', 'last']}}

# ================= F. scope
rt = pd.read_csv(BASE + '/work/scope_ratings.csv')
F = {'sample_design': '50 works drawn at random (seed 20261116) from each group; rated by the agent from the title only',
     'works_per_group': W.sources.value_counts().to_dict(), 'sample': {}}
rt['screen'] = rt.cid.map(W.topic_screen)
for g, d in rt.groupby('group'):
    k = int((d.rating == 1).sum()); k2 = int((d.rating >= 0.5).sum())
    F['sample'][g] = {'n': len(d), 'on_topic_malaria_vaccine': share(k, len(d)), 'malaria_related_incl_on_topic': share(k2, len(d)),
                      'off_topic': share(int((d.rating == 0).sum()), len(d)), 'of_which_papers_in_sample': int(d.paper.sum()),
                      'on_topic_among_papers': share(int(((d.rating == 1) & d.paper).sum()), int(d.paper.sum()))}
tp = int(((rt.rating == 1) & rt.screen).sum())
F['keyword_screen_vs_manual_rating'] = {'screen_definition': 'title has a malaria term and a vaccine term, or PubMed MeSH "Malaria Vaccines"',
    'precision_on_sample': share(tp, int(rt.screen.sum())), 'recall_on_sample': share(tp, int((rt.rating == 1).sum())),
    'share_of_papers_2000_2026_passing': round(float(P.topic_screen.mean()), 3), 'papers_passing': int(P.topic_screen.sum())}
F['papers_2000_2026_by_source_combination'] = P.sources.value_counts().to_dict()
F['share_of_papers_2000_2026_found_by_one_source_only'] = round(float(P.sources.isin(['openalex', 'europepmc', 'pubmed']).mean()), 3)
F['first_ssa_by_source_combination_2000_2026'] = {g: share(int((d.first_ssa == True).sum()), int(d.first_ssa.notna().sum())) for g, d in P.groupby('sources')}
RES['F_scope'] = F
RES['C_checks'] = json.load(open(OUT + '/checks_C.json'))
P.drop(columns=[c for c in P.columns if c.endswith('_all')]).to_csv(OUT + '/papers_2000_2026.csv')
json.dump(RES, open(BASE + '/results.json', 'w'), indent=1, default=str)

# ------- console summary
pr = lambda t: {n: {w: (f"{v[w]['pct']} [{v[w]['ci95'][0]}-{v[w]['ci95'][1]}] n={v[w]['n']} known={v[w]['known_share']}" if 'pct' in v[w] else 'NOT REPORTED known=%s' % v[w]['known_share']) for w in ['first', 'last']} for n, v in t.items()}
print('PAPERS', RES['papers_by_period']); print('GATE', B['gate']); print('below half years', B['years_below_half_combined'])
for n in bp: print(n, bp[n])
print('MAIN'); [print(' ', k, v) for k, v in pr(MAIN).items()]
print('change', RES['main_change_2000s_to_2020s'], RES['main_change_2010s_to_2020s'])
for k, v in S.items():
    print(k); [print('   ', a, b) for a, b in pr(v).items()]
print('ANYSSA'); [print('   ', a, b) for a, b in pr(S2).items()]; print(RES['supplementary_papers_with_any_SSA_author']['share_of_all_papers_with_any_SSA_author'])
for k, v in E['period_splits'].items():
    print(k); [print('   ', a, b) for a, b in pr(v).items()]
for k, v in E['annual_trend_test'].items(): print(k, v)
for nm in ['income_first_author_at_publication_year', 'income_first_author_current_classification']:
    print(nm)
    for n, v in RES[nm].items(): print('  ', n, v['known_share'], {g: f"{v[g]['pct']} [{v[g]['ci95'][0]}-{v[g]['ci95'][1]}]" for g in INC})
print(json.dumps(F, indent=0)[:3000]); print(RES['year_conflicts']); print(RES['top_ssa_first_author_countries_by_period']); print(RES['top_first_author_countries_by_period'])
