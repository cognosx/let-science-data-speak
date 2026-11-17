"""Book 2, Chapter 13: CD index (5-year window) on a stratified sample of 504 papers, with robustness tests."""
import os, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
d = pd.DataFrame([json.loads(l) for l in open(X / "cd_counts.jsonl")])
def cd(A, B, C):
    ni, nj, nk = A - B, B, np.maximum(C - B - 1, 0)
    return (ni - nj) / (ni + nj + nk).replace(0, np.nan), (ni - nj) / (ni + nj).replace(0, np.nan)
d["cd_all"], d["cdnok_all"] = cd(d.A, d.B_all, d.C_all)
m = d.B_from1990.notna()
d.loc[m, "cd_1990"], d.loc[m, "cdnok_1990"] = cd(d.A[m], d.B_from1990[m].astype(float), d.C_from1990[m].astype(float))
d["period"] = pd.cut(d.year, [1989, 1994, 1999, 2004, 2009, 2014, 2020], labels=["1990-94", "1995-99", "2000-04", "2005-09", "2010-14", "2015-20"])
d["share_refs_pre1990"] = 1 - d.n_refs_from1990 / d.n_refs_all
rng = np.random.default_rng(13)
def ci(x):
    x = x.dropna().values
    if len(x) < 5: return (np.nan, np.nan)
    b = [rng.choice(x, len(x)).mean() for _ in range(2000)]
    return np.percentile(b, [2.5, 97.5])
rows = []
for p, g in d.groupby("period", observed=True):
    r = {"period": p, "n": len(g), "uncited_in_window": int((g.A == 0).sum()), "share_refs_pre1990": g.share_refs_pre1990.mean()}
    for col in ["cd_all", "cd_1990", "cdnok_all", "cdnok_1990"]:
        lo, hi = ci(g[col]); r[col] = g[col].mean(); r[col + "_lo"], r[col + "_hi"] = lo, hi
    g5 = g[g.A >= 5]
    r["n_cited5"] = len(g5); r["cdnok_all_cited5"] = g5.cdnok_all.mean()
    rows.append(r)
res = pd.DataFrame(rows)
res.to_csv(OUT / "disruption_by_period.csv", index=False)
d.to_csv(OUT / "disruption_sample.csv", index=False)
pd.set_option("display.width", 200)
print(res.round(4).to_string(index=False))
# trend tests: slope of mean per year
for col in ["cd_all", "cd_1990", "cdnok_all", "cdnok_1990"]:
    g = d.dropna(subset=[col]); s = np.polyfit(g.year, g[col], 1)[0]
    print(col, "slope per decade", round(s * 10, 4), "n", len(g))
