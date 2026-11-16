"""Step 1: load three sources, normalise identifiers, deduplicate into unique works.
Run: python3 -I work/01_dedup.py   (writes work/out/records.pkl, work/out/dedup_stats.json)"""
import json, re, html, unicodedata, collections
import pandas as pd
BASE='/tmp/agent_test_A/'; R=BASE+'raw/'; OUT=BASE+'work/out/'
def load(n): return [json.loads(l) for l in open(R+n+'_2026-11-10.jsonl',encoding='utf-8') if l.strip()]

def norm_doi(d):
    if not isinstance(d,str): return None
    d=d.strip().lower()
    d=re.sub(r'^(https?://)?(dx\.)?doi\.org/','',d)
    return d if re.match(r'^10\.\d{4,9}/\S+$',d) else None
def norm_pmid(p):
    if p is None or (isinstance(p,float) and pd.isna(p)): return None
    p=str(p).strip(); p=re.sub(r'\.0$','',p)
    return p if re.fullmatch(r'\d+',p) else None
def norm_title(t):
    if not isinstance(t,str): return None
    t=html.unescape(html.unescape(t)); t=re.sub(r'<[^>]+>','',t)
    t=unicodedata.normalize('NFKD',t); t=''.join(c for c in t if not unicodedata.combining(c))
    t=re.sub(r'[^a-z0-9]+','',t.lower())
    return t or None
def clean_title(t):
    if not isinstance(t,str): return None
    return re.sub(r'<[^>]+>','',html.unescape(html.unescape(t))).strip()
def yr(y):
    try:
        y=int(float(y)); return y
    except Exception: return None

recs=[]
for r in load('pubmed'):
    recs.append(dict(src='pubmed',sid=r['pmid'],pmid=norm_pmid(r['pmid']),doi=norm_doi(r.get('doi')),raw_doi=r.get('doi'),
        title=clean_title(r.get('title')),year=yr(r.get('year')),raw=r))
for r in load('europepmc'):
    recs.append(dict(src='europepmc',sid=r['source']+':'+r['id'],pmid=norm_pmid(r.get('pmid')),doi=norm_doi(r.get('doi')),raw_doi=r.get('doi'),
        title=clean_title(r.get('title')),year=yr(r.get('pubYear')),raw=r))
for r in load('openalex'):
    recs.append(dict(src='openalex',sid=r['openalex_id'],pmid=norm_pmid(r.get('pmid')),doi=norm_doi(r.get('doi')),raw_doi=r.get('doi'),
        title=clean_title(r.get('title')),year=yr(r.get('year')),raw=r))
df=pd.DataFrame(recs); df['nt']=df.title.map(norm_title)
# pandas turns None into NaN (which is truthy): force real None in every key column so `if x` tests are safe
for c in ['pmid','doi','nt','title','year','raw_doi']:
    df[c]=df[c].astype(object).where(df[c].notna(),None)
assert not any(isinstance(v,float) and v!=v for c in ['pmid','doi','nt','year'] for v in df[c])
stats={'records_loaded':df.src.value_counts().to_dict(),'records_total':len(df)}
stats['invalid_doi_set_to_null']=int((df.raw_doi.notna()&df.doi.isna()).sum())
# OpenAlex sometimes attaches the PMID of the *preprint* to the journal-article record.
# PubMed/Europe PMC are authoritative for DOI<->PMID: if they give this DOI a different PMID, drop the OpenAlex PMID.
auth=df[(df.src!='openalex')&df.doi.notna()&df.pmid.notna()].groupby('doi').pmid.agg(set).to_dict()
bad=[i for i in df.index[df.src=='openalex'] if df.pmid[i] and df.doi[i] in auth and df.pmid[i] not in auth[df.doi[i]]]
df['pmid_dropped']=None
df.loc[bad,'pmid_dropped']=df.loc[bad,'pmid']; df.loc[bad,'pmid']=None
stats['openalex_pmids_dropped_as_contradicted']=len(bad)
def surname(r):
    raw=r['raw']
    if r['src']=='pubmed':
        a=raw.get('authors') or []
        n=a[0]['name'] if a else ''
        return norm_title(n.split()[-1]) if n.split() else None
    if r['src']=='europepmc':
        n=(raw.get('authorString') or '').split(',')[0].strip().rstrip('.')
        return norm_title(' '.join(n.split()[:-1]) or n) if n else None
    return norm_title(raw.get('first_author')) if raw.get('first_author') else None
df['fa_sn']=df.apply(surname,axis=1)
df['is_patent']=[(r['src']=='europepmc' and r['raw'].get('source')=='PAT') for _,r in df.iterrows()]
stats['within_source_duplicate_ids']={s:int(g.sid.duplicated().sum()) for s,g in df.groupby('src')}

# ---- union-find with a guard: a cluster may never hold two different PMIDs
parent=list(range(len(df)))
def find(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]]; i=parent[i]
    return i
pm_of={i:({p} if p else set()) for i,p in enumerate(df.pmid)}
yr_of={i:([y] if y is not None else []) for i,y in enumerate(df.year)}
doi_of={i:({d} if d else set()) for i,d in enumerate(df.doi)}
blocked=collections.Counter(); forced=[]
def union(a,b,why,ytol=None,force=False,doiguard=False):
    a,b=find(a),find(b)
    if a==b: return False
    if doiguard and doi_of[a] and doi_of[b] and not (doi_of[a]&doi_of[b]): blocked[why+'_different_dois']+=1; return False
    if not force and len(pm_of[a]|pm_of[b])>1: blocked[why+'_pmid_conflict']+=1; return False
    if ytol is not None and yr_of[a] and yr_of[b]:
        if min(abs(x-y) for x in yr_of[a] for y in yr_of[b])>ytol: blocked[why+'_year_gap']+=1; return False
    parent[b]=a; pm_of[a]|=pm_of[b]; yr_of[a]+=yr_of[b]; doi_of[a]|=doi_of[b]; return True
def nclust(): return len({find(i) for i in range(len(df))})

# pass 1: PMID
for p,idx in df.groupby('pmid').indices.items():  # positions in full df (nulls dropped by groupby)
    idx=list(idx)
    for j in idx[1:]: union(idx[0],j,'pmid')
stats['after_pmid']=nclust()
# pass 2: DOI (guarded: DOIs shared by several PMIDs, e.g. Cochrane versions / letter series, are not merged)
for d,idx in df.groupby('doi').indices.items():
    idx=list(idx)
    npm=len({df.pmid.iat[i] for i in idx if df.pmid.iat[i]})
    if npm>1:
        # attach PMID-less records only to the PMID cluster with identical normalised title
        withp=[i for i in idx if df.pmid.iat[i]]; nop=[i for i in idx if not df.pmid.iat[i]]
        for x in range(len(withp)):
            for y in range(x):
                i,j=withp[x],withp[y]
                if df.src.iat[i]!='openalex' and df.src.iat[j]!='openalex' and df.pmid.iat[i]!=df.pmid.iat[j] and df.nt.iat[i] and df.nt.iat[i]==df.nt.iat[j] and df.year.iat[i]==df.year.iat[j] and df.fa_sn.iat[i] and df.fa_sn.iat[i]==df.fa_sn.iat[j]:
                    if union(i,j,'dup_pmid',force=True): forced.append((df.pmid.iat[i],df.pmid.iat[j],df.doi.iat[i]))
        for i in nop:
            c=[j for j in withp if df.nt.iat[j]==df.nt.iat[i] and df.year.iat[j]==df.year.iat[i]]
            if len({find(j) for j in c})==1: union(c[0],i,'doi_multi',force=True)
            else: blocked['doi_shared_by_multiple_pmids_left_separate']+=1
        continue
    for j in idx[1:]: union(idx[0],j,'doi')
stats['after_doi']=nclust()
# pass 3: normalised title (>=30 chars) and year within +/-1, never joining two PMIDs
MINLEN=30
t=df[df.nt.notna()&(df.nt.str.len()>=MINLEN)&~df.is_patent]
title_merges=[]
for k,idx in t.groupby('nt').indices.items():
    idx=sorted(t.index[list(idx)], key=lambda i:(df.pmid.iat[i] is None, df.year.iat[i] or 9999))
    if len({find(i) for i in idx})<2: continue
    for j in idx[1:]:
        for i in idx:
            if i==j: break
            if union(i,j,'title',ytol=1,doiguard=True): title_merges.append((i,j)); break
stats['after_title']=nclust()
stats['title_merges']=len(title_merges)
stats['blocked_merges']=dict(blocked)
stats['duplicate_pmid_pairs_merged']=forced
df['cluster']=[find(i) for i in range(len(df))]
stats['unique_works']=int(df.cluster.nunique())
# source combination per work
combo=df.groupby('cluster').src.agg(lambda s:'+'.join(sorted(set(s)))).value_counts().to_dict()
stats['works_by_source_combination']=combo
stats['cluster_size_distribution']=df.groupby('cluster').size().value_counts().sort_index().to_dict()
stats['clusters_with_same_source_twice']={s:int((g.groupby('cluster').size()>1).sum()) for s,g in df.groupby('src')}
df.to_pickle(OUT+'records.pkl')
json.dump(stats,open(OUT+'dedup_stats.json','w'),indent=1,default=str)
json.dump([[int(a),int(b)] for a,b in title_merges],open(OUT+'title_merges.json','w'))
print(json.dumps(stats,indent=1,default=str))
