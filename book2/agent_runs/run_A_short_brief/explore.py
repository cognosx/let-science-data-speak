import json, sys, collections
import pandas as pd
R='/tmp/agent_test_A/raw/'
for n in ['pubmed','europepmc','openalex']:
    rows=[json.loads(l) for l in open(R+n+'_2026-11-10.jsonl') if l.strip()]
    df=pd.DataFrame(rows)
    print('=====',n,len(df))
    print(df.dtypes)
    print(df.isna().mean().round(3))
    for c in df.columns:
        try:
            if df[c].nunique()<40: print(c, df[c].value_counts(dropna=False).to_dict())
        except TypeError: pass
    yc='year' if 'year' in df else 'pubYear'
    y=pd.to_numeric(df[yc],errors='coerce')
    print('year range',y.min(),y.max(), y.isna().sum())
    print((y//10*10).value_counts().sort_index().to_dict())
    for c in ['pmid','doi','openalex_id','id','pmcid']:
        if c in df: print(c,'dups',df[c].dropna().duplicated().sum(),'null',df[c].isna().sum())
