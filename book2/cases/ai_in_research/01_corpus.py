# this case's case: papers about or using large language models, 2023-2025, from Europe PMC (with citation counts).
import requests, pandas as pd, json, datetime, time
API="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
Q=('(TITLE:"ChatGPT" OR TITLE:"large language model" OR TITLE:"large language models" OR TITLE:"GPT-4" OR TITLE:"LLM" OR TITLE:"LLMs" '
   'OR ABSTRACT:"ChatGPT" OR ABSTRACT:"large language model" OR ABSTRACT:"large language models") AND (PUB_YEAR:[2023 TO 2025]) AND SRC:MED')
def fetch(q, cap=None):
    rows=[]; cur="*"
    while True:
        r=requests.get(API,params={"query":q,"format":"json","pageSize":1000,"cursorMark":cur,"resultType":"lite"},timeout=120).json()
        res=r.get("resultList",{}).get("result",[])
        for x in res: rows.append({k:x.get(k) for k in ["id","pmid","doi","title","journalTitle","pubYear","citedByCount","pubType","isOpenAccess","authorString"]})
        nxt=r.get("nextCursorMark")
        if not res or nxt==cur or (cap and len(rows)>=cap): return rows, r.get("hitCount")
        cur=nxt; time.sleep(0.2)
rows,hits=fetch(Q)
df=pd.DataFrame(rows); df.to_csv("llm_papers_2023_2025.csv",index=False)
json.dump({"date":datetime.date.today().isoformat(),"query":Q,"hitCount":hits,"rows":len(df)},open("log_search.json","w"),indent=1)
print(hits,len(df)); print(df.pubYear.value_counts().sort_index().to_dict())
