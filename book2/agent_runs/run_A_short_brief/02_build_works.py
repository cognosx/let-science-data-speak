"""Step 2: one row per unique work with year, type, relevance flags and first/last author countries.
Run after 01_dedup.py:  python3 -I work/02_build_works.py"""
import json, re, collections
import pandas as pd, pycountry
BASE='/tmp/agent_test_A/'; OUT=BASE+'work/out/'
df=pd.read_pickle(OUT+'records.pkl')

# ---------- World Bank reference tables
cl=pd.read_excel(BASE+'raw/CLASS.xlsx',sheet_name='List of economies')
cl=cl[cl.Region.notna()]                      # 218 economies; aggregates have no Region
assert len(cl)==218
REGION=dict(zip(cl.Code,cl.Region)); INC_NOW=dict(zip(cl.Code,cl['Income group'].where(cl['Income group'].notna(),'Unclassified')))
SSA={c for c,r in REGION.items() if r=='Sub-Saharan Africa'}; assert len(SSA)==48
h=pd.read_excel(BASE+'raw/OGHIST.xlsx',sheet_name='Country Analytical History',header=None)
datayears=[int(y) for y in h.iloc[5,2:]]; assert datayears[0]==1987 and datayears[-1]==2023
body=h.iloc[11:]; body=body[body[0].notna()&body[0].isin(REGION)]
LAB={'L':'Low income','LM':'Lower middle income','LM*':'Lower middle income','UM':'Upper middle income','H':'High income'}
INC_HIST={}
for _,r in body.iterrows():
    for y,v in zip(datayears,r.iloc[2:]): INC_HIST[(r[0],y)]=LAB.get(v,'Unclassified')
# check: OGHIST FY25 column must equal CLASS income group
mism=[c for c in REGION if INC_HIST.get((c,2023))!=INC_NOW[c]]
ref_checks={'class_economies':218,'ssa_economies':48,'class_vs_oghist_fy25_mismatches':mism,
            'oghist_parameters_sheet_says':'FY21 (stale; history table itself runs to FY25 and was used)'}
FR_DEPTS={'GF':'FRA','GP':'FRA','MQ':'FRA','RE':'FRA','YT':'FRA'}   # French overseas departments -> France
def iso3(a2):
    if a2 in FR_DEPTS: return FR_DEPTS[a2]
    if a2=='XK': return 'XKX'
    c=pycountry.countries.get(alpha_2=a2); return c.alpha_3 if c else None

# ---------- country parser for PubMed affiliation strings (fallback + validation only)
NAMES={}
for c in pycountry.countries:
    for n in {c.name,getattr(c,'common_name',None),getattr(c,'official_name',None)}:
        if n: NAMES[n.lower()]=c.alpha_3
for _,r in cl.iterrows(): NAMES.setdefault(r.Economy.lower(),r.Code)
NAMES.update({'usa':'USA','u.s.a':'USA','u.s.a.':'USA','us':'USA','united states of america':'USA','uk':'GBR','u.k':'GBR','u.k.':'GBR','england':'GBR','scotland':'GBR','wales':'GBR','northern ireland':'GBR',
 'the netherlands':'NLD','holland':'NLD','the gambia':'GMB','gambia':'GMB','west africa':None,'ivory coast':'CIV',"cote d'ivoire":'CIV',"côte d'ivoire":'CIV','côte d’ivoire':'CIV','tanzania':'TZA','republic of korea':'KOR','south korea':'KOR','korea':'KOR',
 'russia':'RUS','iran':'IRN','vietnam':'VNM','viet nam':'VNM','laos':'LAO','lao pdr':'LAO','democratic republic of congo':'COD','democratic republic of the congo':'COD','dr congo':'COD','drc':'COD','congo':'COG','republic of congo':'COG','republic of the congo':'COG','congo-brazzaville':'COG',
 'burkina faso':'BFA','papua new guinea':'PNG','new guinea':'PNG','taiwan':'TWN','republic of china':'TWN',"people's republic of china":'CHN','pr china':'CHN','p.r. china':'CHN','p. r. china':'CHN','brasil':'BRA','deutschland':'DEU','españa':'ESP','italia':'ITA','méxico':'MEX','czech republic':'CZE','turkey':'TUR','türkiye':'TUR','swaziland':'SWZ','eswatini':'SWZ','cape verde':'CPV','macau':'MAC','hong kong':'HKG','syria':'SYR','venezuela':'VEN','bolivia':'BOL','brunei':'BRN','moldova':'MDA','palestine':'PSE','zaire':'COD','upper volta':'BFA','ussr':'RUS','cameroun':'CMR','sénégal':'SEN','bénin':'BEN','belgique':'BEL','suisse':'CHE','schweiz':'CHE','georgia':None})
NAMES={k:v for k,v in NAMES.items() if v}
US_STATES="alabama alaska arizona arkansas california colorado connecticut delaware florida hawaii idaho illinois indiana iowa kansas kentucky louisiana maine maryland massachusetts michigan minnesota mississippi missouri montana nebraska nevada 'new hampshire' 'new jersey' 'new mexico' 'new york' 'north carolina' 'north dakota' ohio oklahoma oregon pennsylvania 'rhode island' 'south carolina' 'south dakota' tennessee texas utah vermont virginia washington 'west virginia' wisconsin wyoming 'district of columbia'"
import shlex
for s_ in shlex.split(US_STATES): NAMES.setdefault(s_,'USA')
for ab in "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split(): NAMES.setdefault('@'+ab,'USA')
CITY={'london':'GBR','oxford':'GBR','cambridge, uk':'GBR','edinburgh':'GBR','liverpool':'GBR','paris':'FRA','marseille':'FRA','lyon':'FRA','montpellier':'FRA','bethesda':'USA','atlanta':'USA','seattle':'USA','boston':'USA','baltimore':'USA','rockville':'USA','silver spring':'USA','melbourne':'AUS','sydney':'AUS','brisbane':'AUS','geneva':'CHE','basel':'CHE','tokyo':'JPN','osaka':'JPN','stockholm':'SWE','copenhagen':'DNK','nijmegen':'NLD','leiden':'NLD','amsterdam':'NLD','heidelberg':'DEU','tübingen':'DEU','hamburg':'DEU','berlin':'DEU','bangkok':'THA','new delhi':'IND','nairobi':'KEN','kilifi':'KEN','kisumu':'KEN','accra':'GHA','bamako':'MLI','ouagadougou':'BFA','dakar':'SEN','lambaréné':'GAB','ifakara':'TZA','dar es salaam':'TZA','kampala':'UGA','maputo':'MOZ','manhiça':'MOZ','banjul':'GMB','fajara':'GMB','ibadan':'NGA','lagos':'NGA','yaoundé':'CMR','blantyre':'MWI','bogotá':'COL','cali':'COL','barcelona':'ESP','madrid':'ESP','rome':'ITA','beijing':'CHN','shanghai':'CHN'}
def parse_aff(a):
    """Return set of ISO3 codes found in one affiliation string (last matching segment of each ';'-separated part)."""
    out=set()
    for part in re.split(r';',a):
        part=re.sub(r'\S+@\S+','',part); part=re.sub(r'electronic address:?','',part,flags=re.I)
        segs=[s.strip(' .') for s in part.split(',') if s.strip(' .')]
        found=None
        for s in reversed(segs[-3:]):
            s2=re.sub(r'[\d\-]{3,}','',s).strip(' .')          # drop postcodes
            k=s2.lower()
            if k in NAMES: found=NAMES[k]; break
            m=re.match(r'^([A-Z]{2})\b',s2)
            if m and '@'+m.group(1) in NAMES and len(s2)<=10: found='USA'; break
            # trailing country words: "... Maryland 20892 USA"
            toks=k.split()
            for n in (4,3,2,1):
                if len(toks)>=n and ' '.join(toks[-n:]) in NAMES: found=NAMES[' '.join(toks[-n:])]; break
            if found: break
        if not found:
            low=part.lower()
            for city,c in CITY.items():
                if re.search(r'\b'+re.escape(city)+r'\b',low): found=c; break
        if found: out.add(found)
    return out

MAL=re.compile(r'malari|plasmodi|paludi|falciparum|vivax|sporozo|merozo|rts,? ?s\b|\br21\b|mosquirix|pfspz',re.I)
VAC=re.compile(r'vaccin|immuni[sz]ation|immuni[sz]ed|immuni[sz]ing|rts,? ?s\b|\br21\b|mosquirix|pfspz|vacun|impf',re.I)
PM_NONPAPER={'News','Comment','Editorial','Letter','Published Erratum','Retraction of Publication','Preprint','Book chapter','Newspaper Article','Biography','Interview','Congress','Lecture','Portrait','Bibliography','Directory','Patient Education Handout','Autobiography','Expression of Concern','Retracted Publication','Introductory Journal Article','Personal Narrative','Legal Case','Address'}

rows=[]
for cid,g in df.groupby('cluster'):
    by={s:x for s,x in g.groupby('src')}
    pm=by['pubmed'].iloc[0] if 'pubmed' in by else None
    ep=by.get('europepmc'); oa=by.get('openalex')
    if oa is not None:  # prefer the OpenAlex record with most affiliation information
        oa=oa.assign(_n=oa.raw.map(lambda r:sum(1 for a in r['authorships'] if a['countries']))).sort_values('_n',ascending=False).iloc[0]
    epm=None
    if ep is not None:
        ep=ep.assign(_o=ep.raw.map(lambda r:{'MED':0,'PMC':1,'AGR':2,'CBA':3,'CTX':4,'PPR':5,'ETH':6,'PAT':7}.get(r['source'],9))).sort_values('_o').iloc[0]
    # year: PubMed > Europe PMC > OpenAlex
    year=None; ysrc=None
    for nm,r in (('pubmed',pm),('europepmc',ep),('openalex',oa)):
        if r is not None and r['year'] is not None: year=int(r['year']); ysrc=nm; break
    title=next((r['title'] for r in (pm,ep,oa) if r is not None and r['title']),None)
    # type
    epsrc=ep.raw['source'] if ep is not None else None
    any_preprint=bool((pm is not None and 'Preprint' in pm.raw['pub_types']) or (g.raw.map(lambda r:r.get('source')=='PPR').any()) or (oa is not None and oa.raw['type']=='preprint' and pm is None))
    if pm is not None:
        pt=set(pm.raw['pub_types'])
        is_paper=bool(pt&{'Journal Article','Review','Systematic Review','Meta-Analysis','Randomized Controlled Trial','Clinical Trial'}) and not (pt&PM_NONPAPER); tsrc='pubmed'
        wtype='paper' if is_paper else ('preprint' if 'Preprint' in pt else 'other:'+('/'.join(sorted(pt&PM_NONPAPER)) or 'unclassified'))
    elif oa is not None:
        t=oa.raw['type']; is_paper=t in ('article','review') and epsrc not in ('PPR','PAT','ETH'); tsrc='openalex'
        wtype='paper' if is_paper else ('preprint' if (t=='preprint' or epsrc=='PPR') else 'other:'+t)
    else:
        ptxt=(ep.raw.get('pubType') or '').lower()
        is_paper=epsrc in ('MED','PMC','AGR','CBA','CTX') and any(k in ptxt for k in ('journal article','research-article','review')) and not any(k in ptxt for k in ('letter','editorial','news','comment','erratum','preprint')); tsrc='europepmc'
        wtype='paper' if is_paper else {'PAT':'patent','PPR':'preprint','ETH':'other:thesis'}.get(epsrc,'other:'+(ptxt or 'unknown'))
    # relevance
    tm,tv=bool(MAL.search(title or '')),bool(VAC.search(title or ''))
    mesh_mv=bool(pm is not None and 'Malaria Vaccines' in pm.raw['mesh'])
    ta=((pm.raw.get('title') or '')+' '+(pm.raw.get('abstract') or '')) if pm is not None else ''
    abs_both=bool(MAL.search(ta) and VAC.search(ta))
    # authors: OpenAlex
    oa_first=oa_last=None; oa_n=None; oa_any=None
    if oa is not None and oa.raw['authorships']:
        A=oa.raw['authorships']; oa_n=len(A)
        f=next((a for a in A if a['pos']=='first'),A[0]); l=next((a for a in A if a['pos']=='last'),A[-1])
        oa_first=sorted({iso3(c) for c in f['countries']}-{None}); oa_last=sorted({iso3(c) for c in l['countries']}-{None})
        oa_any=sorted({iso3(c) for a in A for c in a['countries']}-{None})
    # authors: PubMed
    pm_first=pm_last=None; pm_n=None; pm_first_hasaff=pm_last_hasaff=False
    if pm is not None and pm.raw['authors']:
        A=pm.raw['authors']; pm_n=len(A)
        pm_first_hasaff=bool(A[0]['affiliations']); pm_last_hasaff=bool(A[-1]['affiliations'])
        pm_first=sorted(set().union(*[parse_aff(x) for x in A[0]['affiliations']])) if A[0]['affiliations'] else []
        pm_last=sorted(set().union(*[parse_aff(x) for x in A[-1]['affiliations']])) if A[-1]['affiliations'] else []
    n_auth=pm_n if pm_n else oa_n
    if n_auth is None and ep is not None and ep.raw.get('authorString'): n_auth=len(ep.raw['authorString'].split(','))
    rows.append(dict(work_id=int(cid),sources='+'.join(sorted(by)),pmid=next((p for p in g.pmid if p),None),doi=next((d for d in g.doi if d),None),title=title,year=year,year_src=ysrc,
        wtype=wtype,is_paper=bool(is_paper),type_src=tsrc,any_preprint=any_preprint,rel_title=tm and tv,rel_title_mal=tm,rel_mesh=mesh_mv,rel_abs=abs_both,in_pubmed=pm is not None,
        n_auth=n_auth,oa_first=oa_first,oa_last=oa_last,oa_any=oa_any,pm_first=pm_first,pm_last=pm_last,pm_first_hasaff=pm_first_hasaff,pm_last_hasaff=pm_last_hasaff,
        oa_first_sn=(oa.fa_sn if oa is not None else None),pm_first_sn=(pm.fa_sn if pm is not None else None),oa_year=(oa['year'] if oa is not None else None)))
W=pd.DataFrame(rows)
# final country assignment: OpenAlex first, PubMed-parsed affiliation as fallback
def pick(o,p): 
    if o: return o,'openalex'
    if p: return p,'pubmed'
    return [], None
W[['first_c','first_src']]=W.apply(lambda r:pd.Series(pick(r.oa_first,r.pm_first)),axis=1)
W[['last_c','last_src']]=W.apply(lambda r:pd.Series(pick(r.oa_last,r.pm_last)),axis=1)
W['core']=W.rel_title|W.rel_mesh
W.to_pickle(OUT+'works.pkl')
json.dump({'ref_checks':ref_checks,'SSA':sorted(SSA),'INC_NOW':INC_NOW,'INC_HIST':{f'{k[0]}|{k[1]}':v for k,v in INC_HIST.items()}},open(OUT+'ref.json','w'))
W.drop(columns=[]).to_csv(OUT+'works.csv',index=False)
print(len(W), W.wtype.str.split(':').str[0].value_counts().to_dict()); print(ref_checks)
print(W.is_paper.sum(), W[W.is_paper].core.sum())
