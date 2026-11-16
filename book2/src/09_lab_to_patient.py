# %% [markdown]
# # 09 — From lab to patient: trials and their publications (Book 2, Chapter 9)
# ClinicalTrials.gov API v2, linked to papers by registration number (in the text, in PubMed's
# databank field, or in the trial record's own reference list).

# %%
import re, json, time, requests, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, FIN, LOGS = ROOT/"data/raw", ROOT/"data/final", ROOT/"logs"
URL = "https://clinicaltrials.gov/api/v2/studies"
params = {"query.cond": "malaria", "query.intr": "vaccine", "pageSize": 100, "countTotal": "true"}
studies, tok = [], None
while True:
    if tok: params["pageToken"] = tok
    r = requests.get(URL, params=params, timeout=60).json(); studies += r["studies"]; tok = r.get("nextPageToken")
    if not tok: break
json.dump(studies, open(RAW/"ctgov_malaria_vaccine_2026-11-10.json", "w"))
print("records returned:", r.get("totalCount", len(studies)), "| downloaded:", len(studies))

# %%
def g(d, *ks, default=None):
    for k in ks:
        if not isinstance(d, dict) or k not in d: return default
        d = d[k]
    return d
rows = []
for s in studies:
    p = s["protocolSection"]
    ivs = g(p, "armsInterventionsModule", "interventions", default=[]) or []
    ivtext = " ".join((i.get("name","") + " " + i.get("description","")) for i in ivs)
    rows.append(dict(nct=g(p,"identificationModule","nctId"), title=g(p,"identificationModule","briefTitle"),
        phase="/".join(g(p,"designModule","phases",default=[]) or []), status=g(p,"statusModule","overallStatus"),
        start=g(p,"statusModule","startDateStruct","date"), primary_completion=g(p,"statusModule","primaryCompletionDateStruct","date"),
        has_results=s.get("hasResults", False), sponsor=g(p,"sponsorCollaboratorsModule","leadSponsor","name"),
        sponsor_class=g(p,"sponsorCollaboratorsModule","leadSponsor","class"),
        countries=sorted({l.get("country") for l in (g(p,"contactsLocationsModule","locations",default=[]) or []) if l.get("country")}),
        ref_pmids=[x.get("pmid") for x in (g(p,"referencesModule","references",default=[]) or []) if x.get("type") == "RESULT" and x.get("pmid")],
        interventions=ivtext))
tr = pd.DataFrame(rows)
# Keep trials where the intervention is a malaria vaccine (not, e.g., a drug trial with another vaccine)
VAX = r"RTS,?\s?S|R21|PfSPZ|Mosquirix|malaria vaccine|Pfs\d|Pvs\d|RH5|AMA-?1|MSP|CSP|circumsporozoite|ME-TRAP|GMZ2|FMP|PvDBP|sporozoite|ChAd63|MVA|Matrix-M|AS01|AS02|plasmodium|falciparum|vivax|PfCSP|Sanaria|merozoite|gametocyte|transmission.blocking"
tr["malaria_vaccine"] = tr["interventions"].str.contains(VAX, case=False, regex=True) | tr["title"].str.contains(r"malaria vaccine|RTS,S|R21|PfSPZ", case=False, regex=True)
print(tr["malaria_vaccine"].value_counts().to_string())
tr.loc[~tr.malaria_vaccine, ["nct","title"]].to_csv(LOGS/"ctgov_excluded_to_read.csv", index=False)
tr = tr[tr.malaria_vaccine].copy()
tr["phase"] = tr["phase"].replace("", "NA"); print(tr["phase"].value_counts().to_string()); print(tr["status"].value_counts().to_string())

# %% [markdown]
# ## Linking trials to papers

# %%
ent = pd.read_parquet(FIN/"entities.parquet")
pm_links = ent.explode("trial_ids").dropna(subset=["trial_ids"])[["pmid","year","trial_ids"]].rename(columns={"trial_ids":"nct"})
ref_links = tr.explode("ref_pmids").dropna(subset=["ref_pmids"])[["nct","ref_pmids"]].rename(columns={"ref_pmids":"pmid"})
ref_links = ref_links.merge(ent[["pmid","year"]], on="pmid", how="left")
links = pd.concat([pm_links.assign(route="PubMed side"), ref_links.assign(route="registry side")])
links = links[links.nct.isin(tr.nct)]
by_route = links.groupby("nct")["route"].agg(lambda s: "both" if s.nunique() == 2 else s.iloc[0])
print("trials with ≥1 linked paper, by route:\n", by_route.value_counts().to_string())
tr["linked"] = tr.nct.isin(links.nct)
tr["n_papers"] = tr.nct.map(links.groupby("nct")["pmid"].nunique()).fillna(0).astype(int)

# %% [markdown]
# ## Non-publication and time to publication
# Completed trials whose primary completion was at least 3 years ago (before Nov 2023).

# %%
tr["pc_date"] = pd.to_datetime(tr.primary_completion, errors="coerce", format="mixed")
done = tr[(tr.status == "COMPLETED") & (tr.pc_date < "2023-11-01")]
print(f"completed trials, primary completion before Nov 2023: {len(done)}")
print(f"  with a linked paper in our corpus: {done.linked.sum()} ({done.linked.mean():.0%})")
print(f"  with results posted on ClinicalTrials.gov: {done.has_results.sum()} ({done.has_results.mean():.0%})")
print(f"  with neither: {(~done.linked & ~done.has_results).sum()}")
print(done.groupby("phase").agg(trials=("nct","size"), published=("linked","mean")).round(2).to_string())
first_pub = links.dropna(subset=["year"]).groupby("nct")["year"].min()
d = done[done.linked].copy(); d["lag_years"] = d.nct.map(first_pub) - d.pc_date.dt.year
print("\nYears from primary completion to first linked paper (median, IQR):",
      d.lag_years.median(), d.lag_years.quantile([.25, .75]).tolist())
tr.drop(columns=["interventions"]).to_parquet(FIN/"trials.parquet", index=False); links.to_csv(FIN/"trial_paper_links.csv", index=False)

# %% [markdown]
# ## Where trials run, and who sponsors them
# %%
print(tr.explode("countries")["countries"].value_counts().head(12).to_string())
print(tr.sponsor_class.value_counts().to_string())
