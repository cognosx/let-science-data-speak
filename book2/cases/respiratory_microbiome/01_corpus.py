# this case's case: bacterial species newly described from human respiratory samples (PubMed),
# then growth conditions extracted from abstracts and, where open, from full texts (Europe PMC).
import json, datetime, time, pandas as pd
from Bio import Entrez
from lxml import etree
Entrez.email="you@example.org"
TERM=("nov[ti] AND (sputum[tiab] OR respiratory[tiab] OR bronchoalveolar[tiab] OR nasopharyn*[tiab] "
      "OR oropharyn*[tiab] OR \"cystic fibrosis\"[tiab] OR bronchiectasis[tiab] OR \"lower respiratory\"[tiab]) "
      "AND (human[tiab] OR patient*[tiab])")
ids=Entrez.read(Entrez.esearch(db="pubmed",term=TERM,retmax=5000))["IdList"]
recs=[]
for i in range(0,len(ids),100):
    for k in range(4):
        try:
            x=etree.fromstring(Entrez.efetch(db="pubmed",id=",".join(ids[i:i+100]),retmode="xml").read()); break
        except Exception as e:
            time.sleep(3*(k+1))
    for a in x.findall(".//PubmedArticle"):
        pmid=a.findtext(".//PMID"); title="".join(a.find(".//ArticleTitle").itertext()) if a.find(".//ArticleTitle") is not None else ""
        ab=" ".join("".join(t.itertext()) for t in a.findall(".//AbstractText"))
        yr=a.findtext(".//PubDate/Year") or (a.findtext(".//PubDate/MedlineDate") or "")[:4]
        pmc=next((i.text for i in a.findall(".//ArticleId") if i.get("IdType")=="pmc"),None)
        j=a.findtext(".//Journal/ISOAbbreviation")
        recs.append({"pmid":pmid,"year":yr,"journal":j,"title":title,"abstract":ab,"pmcid":pmc})
    time.sleep(0.4)
df=pd.DataFrame(recs); df.to_csv("pubmed_new_species_respiratory.csv",index=False)
json.dump({"date":datetime.date.today().isoformat(),"term":TERM,"n":len(df)},open("log_search.json","w"),indent=1)
print(len(df), df.pmcid.notna().sum()); print(df.journal.value_counts().head(8))
