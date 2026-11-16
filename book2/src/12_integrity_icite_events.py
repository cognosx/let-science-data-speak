"""Integrity check (Ch 3, T35), NIH iCite (Ch 8) and interrupted time series (Ch 8, T36).
Run from book2/: python src/12_integrity_icite_events.py
Needs: data/final/papers.parquet; internet access to api.labs.crossref.org and icite.od.nih.gov.
Results of the run of 16 November 2026 are in data/checks/.
"""
import json, os, time, urllib.request
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf

OUT = "data/checks"; os.makedirs(OUT, exist_ok=True)
MAILTO = os.environ.get("CROSSREF_MAILTO", "")  # your e-mail, from an environment variable
p = pd.read_parquet("data/final/papers.parquet")
p["pmid"] = p.pmid.astype(str).str.replace(r"\.0$", "", regex=True)

# 1. Integrity: Retraction Watch data (open via Crossref) + PubMed publication types
rw_file = f"{OUT}/retraction_watch.csv"
if not os.path.exists(rw_file):
    urllib.request.urlretrieve(f"https://api.labs.crossref.org/data/retractionwatch?mailto={MAILTO}", rw_file)
rw = pd.read_csv(rw_file, encoding="latin-1", low_memory=False,
                 usecols=["Record ID", "OriginalPaperDOI", "OriginalPaperPubMedID", "RetractionNature", "Reason", "RetractionDate"])
rw["od"] = rw.OriginalPaperDOI.astype(str).str.lower().str.strip()
rw["opm"] = pd.to_numeric(rw.OriginalPaperPubMedID, errors="coerce")
p["doi_l"] = p.doi.astype(str).str.lower().str.strip()
p["pmid_n"] = pd.to_numeric(p.pmid, errors="coerce")
m = pd.concat([p.merge(rw[rw.od.isin(set(p.doi_l[p.doi_l.str.startswith("10.")]))], left_on="doi_l", right_on="od"),
               p.merge(rw[rw.opm.isin(set(p.pmid_n.dropna())) & (rw.opm > 0)], left_on="pmid_n", right_on="opm")])
m = m.drop_duplicates(["pmid", "Record ID"])
m[["pmid", "year", "RetractionNature", "Reason", "RetractionDate"]].to_csv(f"{OUT}/corpus_retraction_matches.csv", index=False)
NOTICE = ["Published Erratum", "Expression of Concern", "Retracted Publication"]
flag = p.pub_types.apply(lambda x: any(k in list(x) for k in NOTICE))
print("Retraction Watch matches:", m.pmid.nunique(), "| notices and retracted by publication type:", int(flag.sum()))
for name, d in [("all records", p), ("without notices", p[~flag])]:
    s = d[(d.year >= 2020) & (d.year <= 2026) & d.known_first]
    print(f"2020-2026 share, {name}: {100 * s.ssa_first.mean():.1f}% of {len(s)}")
clean = p[~flag]

# 2. NIH iCite
ic_file = f"{OUT}/icite.csv"
ids = clean.pmid[clean.year >= 2000].tolist(); rows = []
for i in range(0, len(ids), 200):
    u = ("https://icite.od.nih.gov/api/pubs?pmids=" + ",".join(ids[i:i + 200]) +
         "&fl=pmid,relative_citation_ratio,apt,cited_by_clin,is_research_article,provisional")
    for _ in range(4):
        try:
            rows += json.load(urllib.request.urlopen(u, timeout=90))["data"]; break
        except Exception:
            time.sleep(4)
ic = pd.DataFrame(rows); ic["pmid"] = ic.pmid.astype(str); ic.to_csv(f"{OUT}/icite.csv", index=False)
d = clean.merge(ic, on="pmid")
d["cited_by_clinical"] = d.cited_by_clin.fillna("").astype(str).str.len() > 2
s = d[(d.year.between(2010, 2020)) & d.known_first & (d.is_research_article == True) & d.relative_citation_ratio.notna()]
print(s.groupby("ssa_first").agg(papers=("pmid", "size"), median_rcr=("relative_citation_ratio", "median"),
                                 cited_by_clinical=("cited_by_clinical", "mean")).round(3))

# 3. Interrupted time series with a comparison series (event: WHO recommendation, October 2021)
a = clean[clean.year.between(2010, 2025) & clean.known_first]  # 2026 left out: incomplete
a = a.assign(ssa_first=a.ssa_first.astype(int))
g = a.groupby("year").agg(n=("pmid", "size"), ssa=("ssa_first", "sum")).reset_index()
g["other"] = g.n - g.ssa
g["t"] = g.year - 2010; g["post"] = (g.year >= 2022).astype(int); g["tpost"] = np.where(g.post == 1, g.year - 2021, 0)
g.to_csv(f"{OUT}/annual_first_author_2010_2025.csv", index=False)
L = pd.concat([g.assign(cnt=g.ssa, ssa_g=1), g.assign(cnt=g.other, ssa_g=0)])
fit = smf.glm("cnt ~ t*ssa_g + post*ssa_g + tpost*ssa_g", L, family=sm.families.Poisson()).fit(scale="X2")
ci = np.exp(fit.conf_int())
print("Slope change, African-led vs other:", round(float(np.exp(fit.params["tpost:ssa_g"])), 2), ci.loc["tpost:ssa_g"].round(2).tolist())
pre, post = g[g.year <= 2021], g[g.year >= 2022]
for col in ["ssa", "other"]:
    trend = smf.glm(f"{col} ~ t", pre, family=sm.families.Poisson()).fit(scale="X2")
    print(col, "2022-2025 observed", int(post[col].sum()), "expected from trend", round(float(trend.predict(post).sum())))
# False-date test: repeat with the event in 2017 using 2010-2021 only
pg = g[g.year <= 2021].copy(); pg["post"] = (pg.year >= 2017).astype(int); pg["tpost"] = np.where(pg.post == 1, pg.year - 2016, 0)
PL = pd.concat([pg.assign(cnt=pg.ssa, ssa_g=1), pg.assign(cnt=pg.other, ssa_g=0)])
pf = smf.glm("cnt ~ t*ssa_g + post*ssa_g + tpost*ssa_g", PL, family=sm.families.Poisson()).fit(scale="X2")
print("False date 2017, slope change:", round(float(np.exp(pf.params["tpost:ssa_g"])), 2), np.exp(pf.conf_int()).loc["tpost:ssa_g"].round(2).tolist())
