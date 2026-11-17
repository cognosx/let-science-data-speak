"""Book 2, Chapter 14: naive comparison, balance, and difference-in-differences (event study, -3..+3)
for SSA-based researchers on papers naming EDCTP or the Gates Foundation, against matched comparisons."""
import os, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
G = pd.read_csv(X / "funding_groups.csv")
Y = {json.loads(l)["author"]: {int(k): v for k, v in json.loads(l)["years"].items() if str(k).isdigit()} for l in open(X / "author_years.jsonl")}
A = pd.read_parquet(X / "authorships.parquet")
led = A[A.pos.isin(["first", "last"])].groupby(["author", "year"]).work.nunique()
rows = []
for r in G.itertuples():
    ys = Y.get(r.author, {}); tot = sum(ys.values())
    for e in range(-3, 4):
        yr = r.treat_year + e
        rows.append({"funder": r.funder, "match_id": r.match_id, "author": r.author, "role": r.role, "e": e,
                     "papers": ys.get(yr, 0), "led_corpus": led.get((r.author, yr), 0), "lifetime": tot,
                     "max_year": max(ys.values()) if ys else 0})
P = pd.DataFrame(rows)
P["flag"] = (P.lifetime < 3) | (P.max_year > 100)   # likely split (too few) or merged (too many) profiles
def did(D, y="papers", post=(1, 2, 3)):
    pre = D[D.e.isin([-3, -2, -1])].groupby(["match_id", "role"])[y].mean().unstack()
    po = D[D.e.isin(post)].groupby(["match_id", "role"])[y].mean().unstack()
    ch = (po - pre).dropna()
    return ch["supported"] - ch["comparison"], pre, po
rng = np.random.default_rng(14); res = []; ev = []
for f, D in P.groupby("funder"):
    # comparison = mean of its matched researchers
    D = D.groupby(["match_id", "role", "e"], as_index=False)[["papers", "led_corpus"]].mean().merge(
        P[P.funder == f].groupby(["match_id", "role"]).flag.mean().reset_index(), on=["match_id", "role"])
    for label, sub in (("all", D), ("no flagged", D[D.flag == 0])):
        keep = sub.groupby("match_id").role.nunique(); sub = sub[sub.match_id.isin(keep[keep == 2].index)]
        for y in ["papers", "led_corpus"]:
            d, pre, po = did(sub, y)
            b = [rng.choice(d.values, len(d)).mean() for _ in range(2000)]
            res.append({"funder": f, "sample": label, "outcome": y, "pairs": len(d),
                        "pre_supported": pre["supported"].mean(), "pre_comparison": pre["comparison"].mean(),
                        "post_supported": po["supported"].mean(), "post_comparison": po["comparison"].mean(),
                        "naive_post_ratio": po["supported"].mean() / po["comparison"].mean(),
                        "did": d.mean(), "lo": np.percentile(b, 2.5), "hi": np.percentile(b, 97.5)})
        if label == "all":
            m = sub.groupby(["e", "role"]).papers.mean().unstack()
            base = m.loc[-1]
            for e in range(-3, 4):
                diff = sub.pivot_table(index="match_id", columns=["role"], values="papers", aggfunc="mean").shape
                ev.append({"funder": f, "e": e, "supported": m.loc[e, "supported"], "comparison": m.loc[e, "comparison"],
                           "gap_vs_e-1": (m.loc[e, "supported"] - m.loc[e, "comparison"]) - (base["supported"] - base["comparison"])})
R = pd.DataFrame(res); E = pd.DataFrame(ev)
bal = P[P.e < 0].groupby(["funder", "role"]).agg(pre_papers=("papers", "mean"), flagged=("flag", "mean"), people=("author", "nunique"))
fy = G.groupby(["funder", "role"]).first_year.mean().rename("first_corpus_year")
bal = bal.join(fy)
R.to_csv(OUT / "funding_did.csv", index=False); E.to_csv(OUT / "funding_event_study.csv", index=False); bal.to_csv(OUT / "funding_balance.csv")
pd.set_option("display.width", 220)
print(bal.round(2)); print(R.round(2).to_string(index=False)); print(E.round(2).to_string(index=False))

# Sensitivity: supported researchers whose first funded paper had at most 20 authors (not one name among many)
nauth = A.groupby("work").author.nunique()
S2 = A[A.ssa]
sens = []
for f in ["EDCTP", "Gates"]:
    fp = S2[S2[f]].sort_values("year").groupby("author").first()
    small = set(fp.index[nauth.reindex(fp.work).values <= 20])
    D = P[(P.funder == f) & P.match_id.isin(small)]
    D = D.groupby(["match_id", "role", "e"], as_index=False).papers.mean()
    keep = D.groupby("match_id").role.nunique(); D = D[D.match_id.isin(keep[keep == 2].index)]
    d, pre, po = did(D, "papers")
    b = [rng.choice(d.values, len(d)).mean() for _ in range(2000)]
    sens.append({"funder": f, "start paper": "20 authors or fewer", "pairs": len(d), "did": d.mean(), "lo": np.percentile(b, 2.5), "hi": np.percentile(b, 97.5)})
pd.DataFrame(sens).to_csv(OUT / "funding_did_small_teams.csv", index=False)
print(pd.DataFrame(sens).round(2).to_string(index=False))
