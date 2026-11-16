import json, collections, re
import pandas as pd
pd.set_option('display.width',220); pd.set_option('display.max_colwidth',90)
R='/tmp/agent_test_A/raw/'
L=lambda n:[json.loads(l) for l in open(R+n+'_2026-11-10.jsonl') if l.strip()]
pm=pd.DataFrame(L('pubmed')); ep=pd.DataFrame(L('europepmc')); oa=pd.DataFrame(L('openalex'))
# id formats
for n,d in [('pm',pm),('ep',ep),('oa',oa)]:
    print(n,'doi samples',d.doi.dropna().sample(5,random_state=1).tolist())
    print(n,'doi not starting 10.',d.doi.dropna()[~d.doi.dropna().str.lower().str.replace('https://doi.org/','').str.strip().str.startswith('10.')].head(10).tolist())
    print(n,'doi with upper', d.doi.dropna().str.contains('[A-Z]').sum(), 'ws', (d.doi.dropna()!=d.doi.dropna().str.strip()).sum())
    print(n,'pmid samples',d.pmid.dropna().sample(5,random_state=1).tolist(), 'nondigit', (~d.pmid.dropna().str.fullmatch(r'\d+')).sum())
    dd=d[d.doi.notna()&d.doi.str.lower().duplicated(keep=False)].sort_values('doi')
    print(dd[[c for c in ['doi','pmid','id','source','openalex_id','type','title','year','pubYear'] if c in d]].head(12).to_string())
print(oa[~oa.pmid.dropna().str.fullmatch(r'\d+').reindex(oa.index,fill_value=True)].pmid.head())
# pubmed authors
pm['na']=pm.authors.map(len)
print('pm n authors==0',(pm.na==0).sum())
pm['fa']=pm.authors.map(lambda a: len(a[0]['affiliations'])>0 if a else False)
pm['la']=pm.authors.map(lambda a: len(a[-1]['affiliations'])>0 if a else False)
pm['dec']=(pm.year//5*5)
print(pm.groupby('dec')[['fa','la']].mean().round(2).tail(8), pm.groupby('dec').size().tail(8))
print('multi aff first', pm.authors.map(lambda a: len(a[0]['affiliations']) if a else 0).value_counts().head(6).to_dict())
import random; random.seed(2)
for a in random.sample([x for x in pm.authors if x and x[0]['affiliations']],12): print(a[0]['affiliations'])
print(pm.authors.iloc[9000])
print('pub_types',collections.Counter(t for x in pm.pub_types for t in x).most_common(40))
# europe pmc
print(ep.pubType.value_counts().head(25))
print(ep[ep.source=='PPR'][['id','doi','title','pubYear']].head(3)); print(ep[ep.source=='PAT'][['id','doi','title','pubYear']].head(3))
print(ep.groupby('source').pmid.apply(lambda s:s.notna().mean()))
# openalex
print('oa nauth',oa.authorships.map(len).describe())
print('pos first count',oa.authorships.map(lambda a:[x['pos'] for x in a].count('first')).value_counts().to_dict())
print('pos last count',oa.authorships.map(lambda a:[x['pos'] for x in a].count('last')).value_counts().to_dict())
print('first is idx0',oa.authorships.map(lambda a: a[0]['pos']=='first' if a else None).value_counts(dropna=False).to_dict())
print('last is idx-1',oa.authorships.map(lambda a: a[-1]['pos'] if a else None).value_counts(dropna=False).to_dict())
print('first ncountries',oa.authorships.map(lambda a: len(a[0]['countries']) if a else -1).value_counts().to_dict())
print('keys',collections.Counter(k for a in oa.authorships for x in a for k in x).most_common())
print('inst country vs countries mismatch', sum(1 for a in oa.authorships for x in a if set(i['country'] for i in x['institutions'] if i.get('country'))!=set(x['countries'])))
print(oa.funders.iloc[5000], oa.authorships.iloc[5000][:2])
oa['dec']=oa.year//10*10
oa['fc']=oa.authorships.map(lambda a: len(a[0]['countries'])>0 if a else False)
print(oa.groupby('dec').fc.mean().round(2).tail(6)); print(oa.groupby('type').fc.mean().round(2))
print(oa[oa.authorships.map(len)==1].shape)
print(oa.sample(15,random_state=3)[['title','year','type','primary_field']].to_string())
