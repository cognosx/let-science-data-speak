"""Book 2, Chapter 14: researchers based in sub-Saharan Africa (SSA) on corpus papers, and those on papers
that name EDCTP or the Gates Foundation as funder. Uses data already downloaded (no API calls)."""
import os, json, numpy as np, pandas as pd, pycountry
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
RAW = Path(os.environ.get("RAW_DIR", ROOT / "data/raw"))
pc = pd.read_parquet(ROOT / "data/final/paper_country.parquet")
ssa3 = set(pc.loc[pc.region == "Sub-Saharan Africa", "country"])
SSA = {pycountry.countries.get(alpha_3=c).alpha_2 for c in ssa3 if pycountry.countries.get(alpha_3=c)}
FUND = {"EDCTP": "European and Developing Countries Clinical Trials Partnership", "Gates": "Bill and Melinda Gates Foundation"}
fund = {}
for l in open(RAW / "openalex_2026-11-10.jsonl"):
    d = json.loads(l)
    fund[d["openalex_id"]] = {(f.get("name") if isinstance(f, dict) else str(f)) for f in (d.get("funders") or [])}
core = set(pd.read_parquet(ROOT / "data/final/openalex_enrich.parquet").openalex_id.dropna())
rows = []; seen = set()
for l in open(RAW / "oa_extra/corpus_refs_authors.jsonl"):
    w = json.loads(l); i = w["id"].split("/")[-1]
    if i not in core or i in seen or not w.get("publication_year"): continue
    seen.add(i)
    for a in w.get("authorships") or []:
        aid = ((a.get("author") or {}).get("id") or "").split("/")[-1]
        cc = {x.get("country_code") for x in a.get("institutions") or []} | set(a.get("countries") or [])
        cc.discard(None)
        if not aid: continue
        rows.append({"work": i, "year": w["publication_year"], "author": aid, "pos": a.get("author_position"),
                     "ssa": bool(cc & SSA), "country": sorted(cc & SSA)[0] if cc & SSA else (sorted(cc)[0] if cc else None),
                     "EDCTP": FUND["EDCTP"] in fund.get(i, set()), "Gates": FUND["Gates"] in fund.get(i, set())})
A = pd.DataFrame(rows)
A.to_parquet(RAW / "oa_extra/authorships.parquet")
ssa_auth = A[A.ssa]
print("authorships", len(A), "SSA authorships", len(ssa_auth), "SSA authors", ssa_auth.author.nunique())
for f in FUND:
    t = ssa_auth[ssa_auth[f]].groupby("author").year.min()
    print(f, "SSA authors on funded papers", len(t), "first year by period:",
          pd.cut(t, [1990, 2004, 2008, 2012, 2016, 2020, 2026]).value_counts().sort_index().to_dict())
