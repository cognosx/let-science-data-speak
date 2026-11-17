"""Book 2, Chapter 13: within-field novelty (journal pairs vs a shuffled baseline, after Uzzi et al. 2013)
and Rao-Stirling diversity of referenced subfields (Stirling 2007), on a stratified sample of papers."""
import os, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
s = json.load(open(X / "samples.json"))["diversity"]
meta = {}
for l in open(X / "ref_meta.jsonl"):
    m = json.loads(l); i = m["id"].split("/")[-1]
    src = ((m.get("primary_location") or {}).get("source") or {}).get("id")
    sub = ((m.get("primary_topic") or {}).get("subfield") or {}).get("display_name")
    meta[i] = (src.split("/")[-1] if src else None, sub, m.get("publication_year"))
core = {}
for l in open(X / "corpus_refs_authors.jsonl"):
    w = json.loads(l); i = w["id"].split("/")[-1]
    if i in s and i not in core: core[i] = w
papers = []
for i in s:
    refs = [r.split("/")[-1] for r in core[i]["referenced_works"]]
    rm = [meta.get(r) for r in refs]
    papers.append({"id": i, "year": core[i]["publication_year"], "n_refs": len(refs),
                   "n_found": sum(x is not None for x in rm),
                   "srcs": [x[0] for x in rm if x and x[0]], "srcyears": [x[2] for x in rm if x and x[0]],
                   "subs": [x[1] for x in rm if x and x[1]]})
P = pd.DataFrame(papers)
# ---- novelty
srcs = sorted({x for l in P.srcs for x in l}); sid = {x: k for k, x in enumerate(srcs)}; S = len(srcs)
def pair_keys(lists):
    out = []
    for l in lists:
        a = np.asarray(l, dtype=np.int64)
        if len(a) < 2: out.append(np.array([], dtype=np.int64)); continue
        ii, jj = np.triu_indices(len(a), 1)
        x, y = np.minimum(a[ii], a[jj]), np.maximum(a[ii], a[jj])
        keep = x != y
        out.append(x[keep] * S + y[keep])
    return out
obs_lists = [np.array([sid[x] for x in l]) for l in P.srcs]
obs_keys = pair_keys(obs_lists)
allk = np.concatenate(obs_keys); uk, oc = np.unique(allk, return_counts=True)
# null: shuffle sources among all reference slots with the same reference publication year
slots = pd.DataFrame({"p": np.repeat(np.arange(len(P)), [len(l) for l in obs_lists]),
                      "src": np.concatenate(obs_lists), "yr": np.nan_to_num(np.concatenate([np.array(y, dtype=float) for y in P.srcyears]), nan=-1)})
rng = np.random.default_rng(13); R = 20; null = np.zeros((R, len(uk)))
for r in range(R):
    sh = slots.copy()
    sh["src"] = sh.groupby("yr")["src"].transform(lambda v: rng.permutation(v.values))
    lists = [g.values for _, g in sh.groupby("p")["src"]]
    k = np.concatenate(pair_keys(lists)); u, c = np.unique(k, return_counts=True)
    pos = np.searchsorted(uk, u); ok = (pos < len(uk)) & (uk[np.minimum(pos, len(uk) - 1)] == u)
    null[r, pos[ok]] = c[ok]
z = (oc - null.mean(0)) / np.maximum(null.std(0), 1)
zmap = dict(zip(uk, z))
P["z10"] = [np.percentile([zmap[k] for k in np.unique(ks)], 10) if len(ks) else np.nan for ks in obs_keys]
P["zmed"] = [np.median([zmap[k] for k in np.unique(ks)]) if len(ks) else np.nan for ks in obs_keys]
P["novel_tail"] = P.z10 < 0  # kept to show trap T39: a within-sample baseline makes almost every paper "novel"
# ---- Rao-Stirling diversity
subs = sorted({x for l in P.subs for x in l}); xid = {x: k for k, x in enumerate(subs)}
M = np.zeros((len(P), len(subs)))
for k, l in enumerate(P.subs):
    for x in l: M[k, xid[x]] += 1
C = M.T @ M; nrm = np.sqrt(np.diag(C)); sim = C / np.outer(nrm, nrm).clip(1e-9); dist = 1 - sim
pr = M / M.sum(1, keepdims=True).clip(1)
P["rao_stirling"] = [p @ dist @ p for p in pr]
P["variety"] = (M > 0).sum(1)
oe = pd.read_parquet(ROOT / "data/final/openalex_enrich.parquet")[["openalex_id", "known_first", "ssa_first"]]
P = P.merge(oe.drop_duplicates("openalex_id"), left_on="id", right_on="openalex_id", how="left")
kf = P.known_first.fillna(False).astype(bool); sf = P.ssa_first.fillna(False).astype(bool)
P["first_region"] = np.where(~kf, "unknown", np.where(sf, "sub-Saharan Africa", "elsewhere"))
P["period"] = pd.cut(P.year, [1989, 1994, 1999, 2004, 2009, 2014, 2019, 2026], labels=["1990-94", "1995-99", "2000-04", "2005-09", "2010-14", "2015-19", "2020-26"])
P["share_refs_found"] = P.n_found / P.n_refs
summ = P.groupby("period", observed=True).agg(n=("id", "size"), refs_found=("share_refs_found", "mean"),
        novel_tail=("novel_tail", "mean"), z_median=("zmed", "median"), rao_stirling=("rao_stirling", "mean"), variety=("variety", "mean"))
reg = P[P.year >= 2010].groupby("first_region").agg(n=("id", "size"), novel_tail=("novel_tail", "mean"), rao_stirling=("rao_stirling", "mean"))
summ.to_csv(OUT / "novelty_diversity_by_period.csv"); reg.to_csv(OUT / "novelty_diversity_by_region_2010_2026.csv")
P.drop(columns=["srcs", "srcyears", "subs"]).to_csv(OUT / "novelty_diversity_sample.csv", index=False)
print("sources", S, "pairs", len(uk), "subfields", len(subs))
print(summ.round(3).to_string()); print(reg.round(3).to_string())
