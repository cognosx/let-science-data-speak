"""Book 2, Chapter 15 (part): ORCID coverage, and emerging-topic signals from the Chapter 6 topic map."""
import os, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
RAW = Path(os.environ.get("RAW_DIR", ROOT / "data/raw"))
p = pd.read_parquet(ROOT / "data/final/papers.parquet"); p["pmid"] = p.pmid.astype(str)
rows = []
for l in open(RAW / "pubmed_2026-11-10.jsonl"):
    d = json.loads(l)
    for i, a in enumerate(d["authors"]):
        rows.append({"pmid": str(d["pmid"]), "year": d["year"], "pos": "first" if i == 0 else ("last" if i == len(d["authors"]) - 1 else "middle"), "orcid": bool(a.get("orcid"))})
a = pd.DataFrame(rows)
print("author positions", len(a), "with ORCID", a.orcid.sum(), round(a.orcid.mean(), 3))
a["period"] = pd.cut(a.year, [0, 2009, 2014, 2019, 2022, 2026], labels=["to 2009", "2010-14", "2015-19", "2020-22", "2023-26"])
by_period = a.groupby("period", observed=True).orcid.agg(["size", "mean"]).round(3)
fa = a[a.pos == "first"].merge(p[["pmid", "known_first", "ssa_first"]], on="pmid")
fa = fa[fa.year >= 2015]
fa["region"] = np.where(~fa.known_first.fillna(False).astype(bool), "unknown",
                np.where(fa.ssa_first.fillna(False).astype(bool), "sub-Saharan Africa", "elsewhere"))
by_region = fa.groupby("region").orcid.agg(["size", "mean"]).round(3)
by_period.to_csv(OUT / "orcid_by_period.csv"); by_region.to_csv(OUT / "orcid_first_author_by_region_2015_2026.csv")
print(by_period); print(by_region)

t = pd.read_parquet(ROOT / "data/final/topics.parquet")
t = t[t.topic != -1] if (t.topic == -1).any() else t
tot = t.groupby("year").size()
early = t[t.year.between(2016, 2020)].groupby("topic_name").size()
late = t[t.year.between(2021, 2025)].groupby("topic_name").size()
e = pd.DataFrame({"n_2016_20": early, "n_2021_25": late}).fillna(0).astype(int)
e["share_2016_20"] = e.n_2016_20 / tot.loc[2016:2020].sum()
e["share_2021_25"] = e.n_2021_25 / tot.loc[2021:2025].sum()
e["ratio"] = (e.share_2021_25 / e.share_2016_20.replace(0, np.nan)).round(2)
e["n_2026_partial"] = t[t.year == 2026].groupby("topic_name").size().reindex(e.index).fillna(0).astype(int)
e = e.sort_values("ratio", ascending=False)
e.to_csv(OUT / "emerging_topics.csv")
print(e.head(10).round(3).to_string()); print(e.tail(5).round(3).to_string())
