import requests, pandas as pd, json, datetime, time
from Bio import Entrez
Entrez.email="you@example.org"
rows=[]; tok=None
while True:
    p={"query.intr":"bacteriophage OR phage OR phages","pageSize":200,"format":"json"}
    if tok: p["pageToken"]=tok
    r=requests.get("https://clinicaltrials.gov/api/v2/studies",params=p,timeout=60).json()
    for s in r.get("studies",[]):
        ps=s["protocolSection"]; idm=ps["identificationModule"]; st=ps.get("statusModule",{}); de=ps.get("designModule",{})
        arms=ps.get("armsInterventionsModule",{}).get("interventions",[])
        rows.append({"nct":idm["nctId"],"title":idm.get("briefTitle"),"status":st.get("overallStatus"),
            "start":st.get("startDateStruct",{}).get("date"),"phases":"|".join(de.get("phases",[]) or []),
            "type":de.get("studyType"),"interventions":"; ".join(i.get("name","") for i in arms),
            "conditions":"; ".join(ps.get("conditionsModule",{}).get("conditions",[])),
            "sponsor":ps.get("sponsorCollaboratorsModule",{}).get("leadSponsor",{}).get("name"),
            "countries":"; ".join(sorted({l.get("country","") for l in ps.get("contactsLocationsModule",{}).get("locations",[])})),
            "has_results":s.get("hasResults")})
    tok=r.get("nextPageToken")
    if not tok: break
t=pd.DataFrame(rows); t.to_csv("raw_ctgov.csv",index=False)
txt=(t.title.fillna('')+' '+t.interventions.fillna('')).str.lower()
t['phage_word']=txt.str.contains(r'\b(?:bacterio)?phages?\b|phage therapy|phage cocktail|lysin')
t['display_or_other']=txt.str.contains(r'macrophage|phage display')
print('trials returned',len(t),' with phage as a word',t.phage_word.sum())
print(t[t.phage_word].status.value_counts().head(8)); print(t[t.phage_word].phases.value_counts().head(8))
# papers
term='("Phage Therapy"[Mesh] OR "phage therapy"[tiab] OR "bacteriophage therapy"[tiab] OR "phage therapeutic*"[tiab])'
n=int(Entrez.read(Entrez.esearch(db="pubmed",term=term,retmax=0))["Count"])
byyear={y:int(Entrez.read(Entrez.esearch(db="pubmed",term=f"{term} AND {y}[dp]",retmax=0))["Count"]) for y in range(2000,2026)}
json.dump({"date":datetime.date.today().isoformat(),"ctgov_query":"query.intr=bacteriophage OR phage OR phages","ctgov_returned":len(t),
  "pubmed_term":term,"pubmed_total":n,"pubmed_by_year":byyear},open("log_trials_papers.json","w"),indent=1)
print('PubMed phage therapy',n); print({k:v for k,v in byyear.items() if k%5==0 or k>=2020})
t.to_csv("ctgov_trials.csv",index=False)
