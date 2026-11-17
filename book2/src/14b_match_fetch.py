"""Book 2, Chapter 14: build supported and comparison groups, then fetch papers per year (all fields)
for every researcher from OpenAlex (one group_by request each). Key from OPENALEX_API_KEY only."""
import os, sys, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")); X = RAW / "oa_extra"
A = pd.read_parquet(X / "authorships.parquet")
S = A[A.ssa]
prof = S.groupby("author").agg(first_year=("year", "min"), country=("country", lambda c: c.mode().iat[0]))
rng = np.random.default_rng(14); groups = []
for f in ["EDCTP", "Gates"]:
    t = S[S[f]].groupby("author").year.min().rename("treat_year")
    t = t[t.between(2010, 2022)]
    ever = set(A.loc[A[f], "author"])
    pool = prof[~prof.index.isin(ever)].copy()
    for aid, ty in t.items():
        p = prof.loc[aid]
        n_before = (S[(S.author == aid) & (S.year < ty)].work.nunique())
        cand = pool[(pool.country == p.country) & (pool.first_year.between(p.first_year - 2, p.first_year + 2)) & (pool.first_year < ty)]
        if len(cand) < 3:
            cand = pool[(pool.first_year.between(p.first_year - 2, p.first_year + 2)) & (pool.first_year < ty)]
        # prefer similar corpus output before the treatment year
        nb = S[S.author.isin(cand.index) & (S.year < ty)].groupby("author").work.nunique().reindex(cand.index).fillna(0)
        order = (nb - n_before).abs().sort_values(kind="stable")
        best = order[order <= order.iloc[min(2, len(order) - 1)]].index.tolist() if len(order) else []
        ctrl = list(rng.choice(best, min(3, len(best)), replace=False)) if best else []
        groups.append({"funder": f, "author": aid, "role": "supported", "treat_year": int(ty), "country": p.country, "first_year": int(p.first_year), "match_id": aid})
        for c in ctrl:
            groups.append({"funder": f, "author": c, "role": "comparison", "treat_year": int(ty), "country": prof.loc[c, "country"], "first_year": int(prof.loc[c, "first_year"]), "match_id": aid})
G = pd.DataFrame(groups); G.to_csv(X / "funding_groups.csv", index=False)
print(G.groupby(["funder", "role"]).size().to_dict(), "unique authors", G.author.nunique())

if len(sys.argv) > 1 and sys.argv[1] == "fetch":
    sys.path.insert(0, str(ROOT / "src"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("f", ROOT / "src/13_fetch_openalex.py"); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    out = X / "author_years.jsonl"
    done = {json.loads(l)["author"] for l in open(out)} if out.exists() else set()
    with open(out, "a") as fh:
        for aid in sorted(set(G.author) - done):
            d = f.get("https://api.openalex.org/works", {"filter": f"author.id:{aid}", "group_by": "publication_year"})
            fh.write(json.dumps({"author": aid, "years": {g["key"]: g["count"] for g in d["group_by"]}}) + "\n"); fh.flush()
    print("fetched", sum(1 for _ in open(out)))
