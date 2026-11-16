"""Step 3: shares by period, sensitivity analyses, validation checks -> results.json
Run after 02_build_works.py:  python3 -I work/03_analyse.py"""
import json, math, collections
import pandas as pd
BASE='/tmp/agent_test_A/'; OUT=BASE+'work/out/'
W=pd.read_pickle(OUT+'works.pkl'); ref=json.load(open(OUT+'ref.json')); dd=json.load(open(OUT+'dedup_stats.json'))
SSA=set(ref['SSA']); INC_NOW=ref['INC_NOW']; INC_HIST={tuple(k.split('|')):v for k,v in ref['INC_HIST'].items()}
PERIODS=[('2000-2009',2000,2009),('2010-2019',2010,2019),('2020-2026',2020,2026)]
def period(y):
    if y is None or pd.isna(y): return None
    for n,a,b in PERIODS:
        if a<=y<=b: return n
    return None
W['period']=W.year.map(period)
ORDER=['Low income','Lower middle income','Upper middle income','High income','Unclassified']
def wilson(k,n,z=1.96):
    if n==0: return [None,None]
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [round(100*(c-h),1),round(100*(c+h),1)]
def pct(k,n): return round(100*k/n,1) if n else None
def ssa_any(c): return any(x in SSA for x in c)
def ssa_all(c): return bool(c) and all(x in SSA for x in c)

def ssa_table(P,first='first_c',last='last_c',rule=ssa_any,last_min_auth=2):
    out={}
    for n,_,_ in PERIODS+[('2000-2026 (all three periods)',0,0)]:
        S=P[P.period.notna()] if n.startswith('2000-2026') else P[P.period==n]
        F=S[S[first].map(len)>0]; kf=int(F[first].map(rule).sum())
        L0=S[(S.n_auth.fillna(0)>=last_min_auth)]; L=L0[L0[last].map(len)>0]; kl=int(L[last].map(rule).sum())
        out[n]=dict(papers=len(S),
            first_known=len(F),first_known_pct=pct(len(F),len(S)),first_ssa_n=kf,first_ssa_pct=pct(kf,len(F)),first_ssa_ci95=wilson(kf,len(F)),first_ssa_pct_of_all_papers_lower_bound=pct(kf,len(S)),
            last_eligible_papers=len(L0),last_known=len(L),last_known_pct=pct(len(L),len(L0)),last_ssa_n=kl,last_ssa_pct=pct(kl,len(L)),last_ssa_ci95=wilson(kl,len(L)))
    return out
def income_table(P,hist=False,col='first_c'):
    out={}
    for n,_,_ in PERIODS+[('2000-2026 (all three periods)',0,0)]:
        S=P[P.period.notna()] if n.startswith('2000-2026') else P[P.period==n]
        F=S[S[col].map(len)>0]; acc=collections.Counter()
        for cs,y in zip(F[col],F.year):
            for c in cs:   # fractional counting when the author lists several countries
                g=INC_HIST.get((c,str(min(int(y),2023))),'Unclassified') if hist else INC_NOW.get(c,'Unclassified')
                acc[g]+=1/len(cs)
        out[n]=dict(papers_with_known_country=len(F),**{g:dict(n=round(acc[g],1),pct=pct(acc[g],len(F))) for g in ORDER})
    return out

P_all=W[W.is_paper]; P=P_all[P_all.core]; P_broad=P_all[P_all.core|P_all.rel_abs]
res={}
res['meta']=dict(data_downloaded='2026-11-10',analysis_run='2026-11-16',note='2026 is a partial year (records to 10 Nov 2026)')
res['1_deduplication']=dict(records_loaded=dd['records_loaded'],records_total=dd['records_total'],unique_works=int(len(W)),
    works_by_source_combination=dd['works_by_source_combination'],
    steps=dict(after_pmid_match=dd['after_pmid'],after_doi_match=dd['after_doi'],after_title_year_match=dd['after_title']),
    invalid_doi_set_to_null=dd['invalid_doi_set_to_null'],openalex_pmids_dropped_as_contradicted=dd['openalex_pmids_dropped_as_contradicted'],
    duplicate_pmid_pairs_merged=dd['duplicate_pmid_pairs_merged'],blocked_title_merges=dd['blocked_merges'],
    unique_works_by_type=W.wtype.str.split(':').str[0].value_counts().to_dict(),
    works_without_year=int(W.year.isna().sum()))
# residual possible duplicates: same normalised title, different work
R=pd.read_pickle(OUT+'records.pkl')
t=R[R.nt.notna()&(R.nt.str.len()>=30)&~R.is_patent].groupby('nt').cluster.nunique()
res['1_deduplication']['possible_residual_duplicates_same_title_kept_separate']=int((t[t>1]-1).sum())
res['analysis_set']=dict(definition='journal papers (articles+reviews; no patents, preprints, theses, letters, editorials, news, errata, chapters) whose title names malaria AND vaccination, or that carry the MeSH heading "Malaria Vaccines"',
    papers_all_topics=len(P_all),papers_core_malaria_vaccine=len(P),papers_core_in_periods=int(P.period.notna().sum()),
    core_by_period=P.period.value_counts().sort_index().to_dict(),core_by_year_2018_2026=P[P.year>=2018].year.astype(int).value_counts().sort_index().to_dict(),
    core_outside_periods_or_no_year=int(P.period.isna().sum()))
res['2_ssa_first_last_author']=ssa_table(P)
res['3_income_group_first_author_FY25_classification']=income_table(P)
res['3b_income_group_first_author_classification_in_publication_year']=income_table(P,hist=True)
# country detail
def top(P,col,k=12):
    c=collections.Counter()
    for cs in P[col]:
        for x in cs: c[x]+=1/len(cs)
    return {a:round(b,1) for a,b in c.most_common(k)}
res['top_first_author_countries_by_period']={n:top(P[P.period==n],'first_c') for n,_,_ in PERIODS}
res['top_ssa_first_author_countries_by_period']={n:{a:b for a,b in top(P[P.period==n],'first_c',200).items() if a in SSA and b>=1} for n,_,_ in PERIODS}
for n in res['top_ssa_first_author_countries_by_period']: res['top_ssa_first_author_countries_by_period'][n]=dict(list(res['top_ssa_first_author_countries_by_period'][n].items())[:10])
# who leads the papers that involve Africa: papers with >=1 SSA-affiliated author (OpenAlex, all authors)
A=P[P.oa_any.map(lambda c:bool(c) and ssa_any(c))]
res['supplement_papers_with_any_ssa_based_author']={}
for n,_,_ in PERIODS:
    S=A[A.period==n]; allp=P[(P.period==n)&P.oa_any.map(lambda c:bool(c))]
    F=S[S.first_c.map(len)>0]; L=S[(S.n_auth.fillna(0)>=2)&(S.last_c.map(len)>0)]
    B=S[(S.n_auth.fillna(0)>=2)&(S.first_c.map(len)>0)&(S.last_c.map(len)>0)]
    res['supplement_papers_with_any_ssa_based_author'][n]=dict(papers_with_any_author_country=len(allp),papers_with_ssa_author=len(S),pct_of_papers_with_ssa_author=pct(len(S),len(allp)),
        first_ssa_pct=pct(int(F.first_c.map(ssa_any).sum()),len(F)),last_ssa_pct=pct(int(L.last_c.map(ssa_any).sum()),len(L)),
        both_first_and_last_ssa_pct=pct(int((B.first_c.map(ssa_any)&B.last_c.map(ssa_any)).sum()),len(B)),
        first_ssa_but_last_not_pct=pct(int((B.first_c.map(ssa_any)&~B.last_c.map(ssa_any)).sum()),len(B)))
# ---- sensitivity analyses
def brief(tab): return {n:dict(papers=v['papers'],first_ssa_pct=v['first_ssa_pct'],last_ssa_pct=v['last_ssa_pct'],first_known=v['first_known'],last_known=v['last_known']) for n,v in tab.items() if not n.startswith('2000-2026')}
sens={}
sens['A_headline_core_set']=brief(ssa_table(P))
sens['B_broader_topic_core_or_pubmed_abstract_mentions_both']=brief(ssa_table(P_broad))
sens['C_all_papers_no_topic_filter']=brief(ssa_table(P_all))
sens['D_title_only_rule_same_for_all_sources']=brief(ssa_table(P_all[P_all.rel_title]))
sens['E_pubmed_indexed_core_only']=brief(ssa_table(P[P.in_pubmed]))
sens['F_strict_all_author_countries_in_ssa']=brief(ssa_table(P,rule=ssa_all))
sens['G_openalex_countries_only']=brief(ssa_table(P,first='oa_first',last='oa_last')) if False else None
Po=P.copy(); Po['oa_first']=Po.oa_first.map(lambda x:x or []); Po['oa_last']=Po.oa_last.map(lambda x:x or []); Po['pm_first']=Po.pm_first.map(lambda x:x or []); Po['pm_last']=Po.pm_last.map(lambda x:x or [])
sens['G_openalex_countries_only']=brief(ssa_table(Po,first='oa_first',last='oa_last'))
sens['H_pubmed_affiliation_strings_only']=brief(ssa_table(Po,first='pm_first',last='pm_last'))
sens['I_sole_author_counts_as_last_author']=brief(ssa_table(P,last_min_auth=1))
sens['J_excluding_2026_partial_year']=brief(ssa_table(P[P.year!=2026]))
sens['K_original_articles_only_openalex_type_not_review']=None
Wr=pd.read_pickle(OUT+'records.pkl'); oat=Wr[Wr.src=='openalex'].assign(t=lambda d:d.raw.map(lambda r:r['type'])).groupby('cluster').t.first()
P2=P.assign(oat=P.work_id.map(oat)); sens['K_original_articles_only_openalex_type_not_review']=brief(ssa_table(P2[P2.oat=='article']))
sens['L_year_from_openalex_instead_of_pubmed']=None
P3=P.copy(); P3['year']=P3.oa_year.where(P3.oa_year.notna(),P3.year); P3['period']=P3.year.map(period); sens['L_year_from_openalex_instead_of_pubmed']=brief(ssa_table(P3))
res['sensitivity_ssa_shares']=sens
res['sensitivity_income_all_papers_no_topic_filter_FY25']=income_table(P_all)
# annual series 2018-2026 for the recent trend
ann={}
for y in range(2015,2027):
    S=P[P.year==y]; F=S[S.first_c.map(len)>0]; L=S[(S.n_auth.fillna(0)>=2)&(S.last_c.map(len)>0)]
    ann[y]=dict(papers=len(S),first_ssa_pct=pct(int(F.first_c.map(ssa_any).sum()),len(F)),last_ssa_pct=pct(int(L.last_c.map(ssa_any).sum()),len(L)))
res['annual_core_2015_2026']=ann
# ---- validation checks
chk={}
chk['reference_tables']=ref['ref_checks']
# (a) OpenAlex vs PubMed-parsed first author country, where both exist
B=P_all[P_all.oa_first.map(bool)&P_all.pm_first.map(bool)]
chk['first_author_country_openalex_vs_pubmed']=dict(n_both=len(B),same_country_set_pct=pct(int((B.oa_first.map(set)==B.pm_first.map(set)).sum()),len(B)),overlap_pct=pct(int(B.apply(lambda r:bool(set(r.oa_first)&set(r.pm_first)),axis=1).sum()),len(B)),
    ssa_flag_agree_pct=pct(int((B.oa_first.map(ssa_any)==B.pm_first.map(ssa_any)).sum()),len(B)),
    openalex_ssa_pubmed_not=int((B.oa_first.map(ssa_any)&~B.pm_first.map(ssa_any)).sum()),pubmed_ssa_openalex_not=int((~B.oa_first.map(ssa_any)&B.pm_first.map(ssa_any)).sum()))
B=P_all[P_all.oa_last.map(bool)&P_all.pm_last.map(bool)&(P_all.n_auth.fillna(0)>=2)]
chk['last_author_country_openalex_vs_pubmed']=dict(n_both=len(B),ssa_flag_agree_pct=pct(int((B.oa_last.map(ssa_any)==B.pm_last.map(ssa_any)).sum()),len(B)),
    openalex_ssa_pubmed_not=int((B.oa_last.map(ssa_any)&~B.pm_last.map(ssa_any)).sum()),pubmed_ssa_openalex_not=int((~B.oa_last.map(ssa_any)&B.pm_last.map(ssa_any)).sum()))
# (b) PubMed affiliation parser hit rate
chk['pubmed_affiliation_parser']=dict(first_author_strings=int(P_all.pm_first_hasaff.sum()),parsed_pct=pct(int((P_all.pm_first_hasaff&P_all.pm_first.map(bool)).sum()),int(P_all.pm_first_hasaff.sum())))
# (c) PubMed last-author affiliation availability by period (structural gap before ~2014)
chk['pubmed_has_last_author_affiliation_pct_by_period']={n:pct(int(P_all[(P_all.period==n)&P_all.in_pubmed&(P_all.n_auth.fillna(0)>=2)].pm_last_hasaff.sum()),len(P_all[(P_all.period==n)&P_all.in_pubmed&(P_all.n_auth.fillna(0)>=2)])) for n,_,_ in PERIODS}
# (d) same first author in OpenAlex and PubMed (surname)
B=P_all[P_all.oa_first_sn.notna()&P_all.pm_first_sn.notna()]
chk['first_author_surname_openalex_vs_pubmed_agree_pct']=dict(n=len(B),agree_pct=pct(int((B.oa_first_sn==B.pm_first_sn).sum()),len(B)))
# (e) where country came from
chk['core_first_author_country_source']={n:P[P.period==n].first_src.fillna('unknown').value_counts().to_dict() for n,_,_ in PERIODS}
chk['core_last_author_country_source']={n:P[(P.period==n)&(P.n_auth.fillna(0)>=2)].last_src.fillna('unknown').value_counts().to_dict() for n,_,_ in PERIODS}
# (f) internal consistency
t2=res['2_ssa_first_last_author']; t3=res['3_income_group_first_author_FY25_classification']
chk['periods_sum_to_total']=sum(t2[n]['papers'] for n,_,_ in PERIODS)==t2['2000-2026 (all three periods)']['papers']
chk['income_shares_sum_to_100']={n:round(sum(t3[n][g]['pct'] for g in ORDER),1) for n in t3}
chk['income_denominator_equals_first_known']=all(t3[n]['papers_with_known_country']==t2[n]['first_known'] for n in t3)
chk['year_source_core']=P.year_src.value_counts().to_dict()
chk['year_pubmed_vs_openalex_differs_pct_core']=pct(int((P[P.oa_year.notna()&(P.year_src=='pubmed')].pipe(lambda d:d.year!=d.oa_year)).sum()),int((P.oa_year.notna()&(P.year_src=='pubmed')).sum()))
chk['multi_country_first_authors_core_pct']=pct(int((P.first_c.map(len)>1).sum()),int((P.first_c.map(len)>0).sum()))
chk['single_author_core_papers_by_period']={n:int(((P.period==n)&(P.n_auth.fillna(0)<2)).sum()) for n,_,_ in PERIODS}
res['checks']=chk
json.dump(res,open(BASE+'results.json','w'),indent=1,default=str)
print(json.dumps({k:res[k] for k in res if k not in ('1_deduplication',)},indent=0,default=str))
