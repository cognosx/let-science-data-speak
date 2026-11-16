# this case's case (phage therapy): EP patent publications from EPO Linked Open Data (CC BY 4.0).
# Two routes: (A) by classification only (IPC A61K35/76: viruses and bacteriophages as active ingredients);
# (B) by classification AND title words (phage, bacteriophage). The difference is the lesson.
import requests, pandas as pd, time, datetime, json
EP = "https://data.epo.org/linked-data/query"
def q(sparql, tries=3):
    for i in range(tries):
        r = requests.post(EP, data={"query": sparql}, headers={"Accept": "application/sparql-results+json"}, timeout=180)
        if r.ok:
            b = r.json()["results"]["bindings"]
            return [{k: v["value"] for k, v in row.items()} for row in b]
        time.sleep(5 * (i + 1))
    raise RuntimeError(r.text[:300])
TMPL = """PREFIX pat: <http://data.epo.org/linked-data/def/patent/>
PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
SELECT ?pub ?date ?app ?title ?applicant WHERE {
  ?pub pat:classificationIPCInventive <http://data.epo.org/linked-data/def/ipc/%s> ;
       pat:publicationDate ?date ; pat:application ?app .
  OPTIONAL { ?pub pat:titleOfInvention ?title . FILTER(lang(?title) = "en") }
  OPTIONAL { ?pub pat:applicantVC ?vc . ?vc vcard:fn ?applicant }
} ORDER BY ?pub LIMIT 2000 OFFSET %d"""
rows = []
for ipc in ["A61K35-76", "C12N7-00", "C12N7-01"]:
    off = 0
    while True:
        part = q(TMPL % (ipc, off))
        for p in part: p["ipc"] = ipc
        rows += part; print(ipc, off, len(part)); 
        if len(part) < 2000: break
        off += 2000; time.sleep(2)
df = pd.DataFrame(rows)
df.to_csv("raw_epo_publications.csv", index=False)
json.dump({"source": "EPO Linked Open Data SPARQL endpoint", "licence": "CC BY 4.0", "date": datetime.date.today().isoformat(),
           "classes": ["A61K35/76", "C12N7/00", "C12N7/01"], "rows": len(df)}, open("log_epo.json", "w"), indent=1)
print(len(df), df.pub.nunique())
