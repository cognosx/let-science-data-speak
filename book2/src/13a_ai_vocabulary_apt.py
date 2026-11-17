"""Book 2, Chapter 13 (part): excess style vocabulary in abstracts, and iCite APT.
Marker words and method from Kobak et al. 2025 (Sci Adv, doi:10.1126/sciadv.adt3813):
the 10-word 'common set'; expected frequency = linear extrapolation from 2021-2022."""
import os, json, re, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("RAW_DIR", ROOT / "data/raw"))
OUT = ROOT / "data/checks"
WORDS = ["across", "additionally", "comprehensive", "crucial", "enhancing",
         "exhibited", "insights", "notably", "particularly", "within"]
rows = []
for l in open(RAW / "pubmed_2026-11-10.jsonl"):
    d = json.loads(l)
    a = d.get("abstract") or ""
    if len(a) < 250 or not d.get("year"):
        continue
    toks = set(re.findall(r"[a-z]+", a.lower()))
    rows.append({"pmid": d["pmid"], "year": int(d["year"]), **{w: w in toks for w in WORDS}})
df = pd.DataFrame(rows)
df["any"] = df[WORDS].any(axis=1)
df = df[df.year.between(2010, 2026)]
n = df.groupby("year").size()
f = df.groupby("year")["any"].mean()
slope = max(f[2022] - f[2021], 0)
rng = np.random.default_rng(1)
res = []
for y in range(2010, 2027):
    exp = f[2022] + slope * (y - 2022) if y > 2022 else np.nan
    # bootstrap the gap: resample abstracts in 2021, 2022 and year y
    gaps = []
    if y > 2022:
        a21, a22, ay = (df.loc[df.year == k, "any"].values for k in (2021, 2022, y))
        for _ in range(2000):
            b21, b22, by = (rng.choice(v, len(v)).mean() for v in (a21, a22, ay))
            gaps.append(by - (b22 + max(b22 - b21, 0) * (y - 2022)))
    res.append({"year": y, "abstracts": int(n[y]), "observed": f[y], "expected": exp,
                "gap": f[y] - exp if y > 2022 else np.nan,
                "gap_lo": np.percentile(gaps, 2.5) if gaps else np.nan,
                "gap_hi": np.percentile(gaps, 97.5) if gaps else np.nan})
res = pd.DataFrame(res)
res.to_csv(OUT / "ai_vocabulary_by_year.csv", index=False)
print(res.round(3).to_string(index=False))
per_word = df.groupby("year")[WORDS].mean().loc[[2021, 2022, 2024, 2025, 2026]].T.round(3)
per_word.to_csv(OUT / "ai_vocabulary_per_word.csv")
print(per_word)

# iCite APT by decade and by first-author region
ic = pd.read_csv(OUT / "icite.csv", dtype={"pmid": str})
p = pd.read_parquet(ROOT / "data/final/papers.parquet")
p["pmid"] = p.pmid.astype(str)
m = p.merge(ic, on="pmid", how="inner")
m = m[m.is_research_article.astype(str).str.lower().isin(["true", "yes", "1"])]
m["decade"] = (m.year // 10 * 10).astype(int)
kf = m.known_first.fillna(False).astype(bool); sf = m.ssa_first.fillna(False).astype(bool)
m["first_ssa"] = np.where(~kf, "unknown", np.where(sf, "sub-Saharan Africa", "elsewhere"))
apt = m.groupby("decade")["apt"].agg(["count", "mean", "median"]).round(3)
apt2 = m[m.year >= 2010].groupby("first_ssa")["apt"].agg(["count", "mean", "median"]).round(3)
apt.to_csv(OUT / "apt_by_decade.csv"); apt2.to_csv(OUT / "apt_by_first_author_2010_2026.csv")
print(apt); print(apt2)
