# Do LLM papers get cited more? Compare with all other 2023 papers in the same journals.
import requests, pandas as pd, time
API="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
df=pd.read_csv('llm_papers_2023_2025.csv'); d23=df[df.pubYear==2023]
cand=d23.journalTitle.value_counts(); cand=cand[cand>=15].index.tolist()
def hits(q): return requests.get(API,params={"query":q,"format":"json","pageSize":1},timeout=60).json()["hitCount"]
rows=[]
for j in cand:
    q=f'JOURNAL:"{j}" AND PUB_YEAR:2023 AND SRC:MED'
    n=hits(q)
    if n>4000: print('skip',j,n); continue
    cur="*"
    while True:
        r=requests.get(API,params={"query":q,"format":"json","pageSize":1000,"cursorMark":cur,"resultType":"lite"},timeout=120).json()
        res=r["resultList"]["result"]
        rows+= [{"journal":j,"pmid":x.get("pmid"),"cites":x.get("citedByCount"),"pubType":x.get("pubType")} for x in res]
        if not res or not r.get("nextCursorMark") or r.get("nextCursorMark")==cur: break
        cur=r["nextCursorMark"]; time.sleep(0.2)
    print(j,n)
a=pd.DataFrame(rows).drop_duplicates('pmid')
llm=set(d23.pmid.dropna().astype(int).astype(str))
a['llm']=a.pmid.astype(str).isin(llm)
a['research']=~a.pubType.fillna('').str.lower().str.contains('editorial|comment|letter|news|review')
a.to_csv('within_journal_2023.csv',index=False)
r=a[a.research]
print('pooled: LLM median',r[r.llm].cites.median(),' others',r[~r.llm].cites.median(),' n',r.llm.sum(),(~r.llm).sum())
g=r.groupby(['journal','llm']).cites.median().unstack(); g['n_llm']=r.groupby('journal').llm.sum(); print(g)
ratio=(g[True]/g[False]).replace([float('inf')],float('nan'))
print('journals where LLM median > others:', (g[True]>g[False]).sum(),'of',len(g))
