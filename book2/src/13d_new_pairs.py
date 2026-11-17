"""Book 2, Chapter 13: novelty as first-time journal pairs (combinations of journals in a paper's references
never seen in earlier papers of the corpus), with two baselines: all earlier years, and the previous 10 years."""
import os, json, numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
src = {}
for l in open(X / "ref_meta.jsonl"):
    m = json.loads(l); s = ((m.get("primary_location") or {}).get("source") or {}).get("id")
    src[m["id"].split("/")[-1]] = s.split("/")[-1] if s else None
core = set(pd.read_parquet(ROOT / "data/final/openalex_enrich.parquet").openalex_id.dropna())
W = {}
for l in open(X / "corpus_refs_authors.jsonl"):
    w = json.loads(l); i = w["id"].split("/")[-1]
    if i in core and i not in W and w.get("publication_year"): W[i] = w
rows = []
for i, w in W.items():
    js = sorted({src.get(r.split("/")[-1]) for r in (w.get("referenced_works") or [])} - {None})
    pairs = {(a, b) for k, a in enumerate(js) for b in js[k + 1:]}
    rows.append((i, w["publication_year"], pairs, len(w.get("referenced_works") or [])))
rows.sort(key=lambda r: r[1])
first_seen = {}
for i, y, pairs, n in rows:
    for p in pairs:
        if p not in first_seen or y < first_seen[p]: first_seen[p] = y
out = []
for i, y, pairs, n in rows:
    if len(pairs) < 10: continue
    new_all = sum(first_seen[p] == y for p in pairs) / len(pairs)
    out.append({"id": i, "year": y, "n_refs": n, "n_pairs": len(pairs), "new_all": new_all})
D = pd.DataFrame(out)
# 10-year look-back: a pair is new if not seen in the previous 10 years
seen_years = defaultdict(set)
for i, y, pairs, n in rows:
    for p in pairs: seen_years[p].add(y)
nb = {}
for i, y, pairs, n in rows:
    if len(pairs) < 10: continue
    nb[i] = sum(not any(y - 10 <= t < y for t in seen_years[p]) for p in pairs) / len(pairs)
D["new_10y"] = D.id.map(nb)
papers_per_year = pd.Series([r[1] for r in rows]).value_counts().sort_index()
D["period"] = pd.cut(D.year, [1969, 1979, 1989, 1994, 1999, 2004, 2009, 2014, 2019, 2026],
                     labels=["1970s", "1980s", "1990-94", "1995-99", "2000-04", "2005-09", "2010-14", "2015-19", "2020-26"])
S = D.groupby("period", observed=True).agg(n=("id", "size"), new_pairs_all=("new_all", "mean"),
        new_pairs_10y=("new_10y", "mean"), any_new_all=("new_all", lambda s: (s > 0).mean()))
S.to_csv(OUT / "new_pairs_by_period.csv"); D.to_csv(OUT / "new_pairs_papers.csv", index=False)
print(S.round(3).to_string())
print("corpus papers per decade:", papers_per_year.groupby(papers_per_year.index // 10 * 10).sum().to_dict())
