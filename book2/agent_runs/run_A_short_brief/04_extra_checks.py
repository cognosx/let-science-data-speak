"""Extra checks: recent-years composition, manual spot-check sample of the affiliation parser. Appends to results.json"""
import json, pandas as pd, random
BASE='/tmp/agent_test_A/'; W=pd.read_pickle(BASE+'work/out/works.pkl'); ref=json.load(open(BASE+'work/out/ref.json')); SSA=set(ref['SSA'])
R=pd.read_pickle(BASE+'work/out/records.pkl')
P=W[W.is_paper&W.core].copy(); P['fs']=P.first_c.map(lambda c:any(x in SSA for x in c)); P['known']=P.first_c.map(len)>0
out={}
for lab,S in [('pubmed_indexed',P[P.in_pubmed]),('not_in_pubmed',P[~P.in_pubmed])]:
    out[lab]={int(y):dict(papers=int(len(g)),first_ssa_pct=round(100*g[g.known].fs.mean(),1) if g.known.sum() else None) for y,g in S[S.year>=2019].groupby('year')}
out['core_2025_2026_mesh_indexed_pct']=round(100*P[(P.year>=2025)&P.in_pubmed].rel_mesh.mean(),1)
out['core_2015_2019_mesh_indexed_pct']=round(100*P[(P.year.between(2015,2019))&P.in_pubmed].rel_mesh.mean(),1)
print(json.dumps(out,indent=0))
# spot check: parser output vs raw string
pm=R[R.src=='pubmed'].set_index('cluster'); random.seed(7)
S=W[W.pm_first_hasaff].sample(25,random_state=7)
for _,r in S.iterrows():
    print(r.pm_first, r.oa_first, '|', ' ;; '.join(pm.loc[r.work_id].raw['authors'][0]['affiliations'])[:170])
U=W[W.pm_first_hasaff&~W.pm_first.map(bool)]
print('UNPARSED',len(U))
for _,r in U.sample(12,random_state=1).iterrows(): print('   ',' ;; '.join(pm.loc[r.work_id].raw['authors'][0]['affiliations'])[:170])
# disagreement sample OpenAlex SSA vs PubMed not
D=W[W.oa_first.map(bool)&W.pm_first.map(bool)]; D=D[D.oa_first.map(lambda c:any(x in SSA for x in c))!=D.pm_first.map(lambda c:any(x in SSA for x in c))]
for _,r in D.sample(10,random_state=2).iterrows(): print('DIS',r.year,r.oa_first,r.pm_first,'|',' ;; '.join(pm.loc[r.work_id].raw['authors'][0]['affiliations'])[:200])
res=json.load(open(BASE+'results.json')); res['checks']['recent_years_first_ssa_by_pubmed_indexing']=out; json.dump(res,open(BASE+'results.json','w'),indent=1)
