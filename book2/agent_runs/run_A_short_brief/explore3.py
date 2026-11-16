import json, collections, re
import pandas as pd
pd.set_option('display.width',220); pd.set_option('display.max_colwidth',100)
try:
    import pycountry; print('pycountry yes')
except Exception as e: print('no pycountry',e)
R='/tmp/agent_test_A/raw/'
L=lambda n:[json.loads(l) for l in open(R+n+'_2026-11-10.jsonl') if l.strip()]
pm=pd.DataFrame(L('pubmed')); ep=pd.DataFrame(L('europepmc')); oa=pd.DataFrame(L('openalex'))
mal=re.compile(r'malari|plasmodi|paludi|falciparum|vivax|sporozo|merozo|RTS,? ?S|R21|mosquirix|anophel|PfSPZ|berghei|yoelii|knowlesi|chabaudi',re.I)
vac=re.compile(r'vaccin|immuni[sz]|immunogen|antigen|antibod|adjuvant|protecti|immunit|RTS,? ?S|R21|mosquirix|PfSPZ|vacun|impf',re.I)
def rel(t): 
    t=t if isinstance(t,str) else ''; return bool(mal.search(t)), bool(vac.search(t))
for n,d in [('pm',pm),('ep',ep),('oa',oa)]:
    r=d.title.map(rel); d['m']=r.str[0]; d['v']=r.str[1]
    print(n, pd.crosstab(d.m,d.v,normalize=True).round(3).to_dict())
pm['ta']=(pm.title.fillna('')+' '+pm.abstract.fillna('')).map(rel)
print('pm title+abs', pm.ta.value_counts(normalize=True).round(3).to_dict())
print('mesh Malaria Vaccines',pm.mesh.map(lambda m:'Malaria Vaccines' in m).mean(), 'any malaria mesh',pm.mesh.map(lambda m:any('alaria' in x or 'lasmodium' in x for x in m)).mean(),'no mesh',pm.mesh.map(len).eq(0).mean())
print(pm[~pm.ta.str[0]].title.sample(12,random_state=1).tolist())
pmids=set(pm.pmid)
oao=oa[~oa.pmid.isin(pmids)]
print('oa not in pm',len(oao), pd.crosstab(oao.m,oao.v).to_dict())
print(oao.type.value_counts().head(8).to_dict())
print('oa in pm',oa.pmid.isin(pmids).sum(),' oa pmid not in pm',(oa.pmid.notna()&~oa.pmid.isin(pmids)).sum())
print(oao[~oao.m].title.sample(15,random_state=1).tolist())
print(oao[oao.m&~oao.v].title.sample(10,random_state=1).tolist())
epo=ep[ep.pmid.notna()&~ep.pmid.isin(pmids)]; print('ep MED not in pm',len(epo), 'pm not in ep',len(pmids-set(ep.pmid.dropna())))
print(epo.title.sample(8,random_state=1).tolist())
# year agreement
m=pm[['pmid','year','doi','title']].merge(ep[['pmid','pubYear','doi','title']].dropna(subset=['pmid']),on='pmid',suffixes=('','_ep'))
m['d']=m.year-pd.to_numeric(m.pubYear); print('pm-ep year diff',m.d.value_counts().head(8).to_dict(), 'doi differ',(m.doi.notna()&m.doi_ep.notna()&(m.doi!=m.doi_ep)).sum(), 'doi only one', (m.doi.isna()!=m.doi_ep.isna()).sum())
m=pm[['pmid','year','doi','title']].merge(oa[['pmid','year','doi','title','type']].dropna(subset=['pmid']),on='pmid',suffixes=('','_oa'))
m['d']=m.year-m.year_oa; print('pm-oa year diff',m.d.value_counts().head(10).to_dict())
m['doi_oa']=m.doi_oa.str.replace('https://doi.org/','')
x=m[m.doi.notna()&m.doi_oa.notna()&(m.doi!=m.doi_oa)&(m.doi_oa!='')]; print('doi differ pm-oa',len(x)); print(x[['pmid','doi','doi_oa','title','title_oa']].head(8).to_string())
print(m[m.d.abs()>2][['pmid','year','year_oa','title','title_oa']].head(8).to_string())
print('types of oa in pm',m.type.value_counts().to_dict())
print('year nan',pm[pm.year.isna()].head(3).to_string())
print(oa[oa.year.isna()].head(3)[['openalex_id','doi','title','type']].to_string())
print('oa title dups', oa[oa.title.notna()].duplicated(['title','year'],keep=False).sum())
