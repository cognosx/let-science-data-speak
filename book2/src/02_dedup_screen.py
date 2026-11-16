# %% [markdown]
# # 02 — Removing duplicates and preparing screening (Book 2, Chapter 3)
#
# Merges the PubMed and Europe PMC exports (and OpenAlex, when available), removes duplicates in
# three passes, links preprints to published articles, and draws samples for double screening.

# %%
import re, unicodedata, json, glob, numpy as np, pandas as pd
from pathlib import Path
from rapidfuzz import fuzz, process

ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, INT, LOGS = ROOT / "data/raw", ROOT / "data/interim", ROOT / "logs"

def clean_doi(x):
    if not isinstance(x, str) or not x.strip(): return None
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", x.strip().lower())

def clean_title(x):
    if not isinstance(x, str): return ""
    x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()
    x = re.sub(r"<[^>]+>", " ", x.lower())
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    return re.sub(r"\s+", " ", x).strip()

def first_author_pubmed(authors):
    if isinstance(authors, list) and authors and authors[0].get("name"):
        return authors[0]["name"].split()[-1].lower()
    return ""

# %% [markdown]
# ## 1. Load and harmonise the sources

# %%
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})
pm = pd.DataFrame({
    "source": "PubMed", "pmid": pm["pmid"], "doi": pm["doi"].map(clean_doi), "title": pm["title"],
    "year": pm["year"], "first_author": pm["authors"].map(first_author_pubmed), "type": "article",
})
ep = pd.read_json(sorted(RAW.glob("europepmc_*.jsonl"))[-1], lines=True, dtype={"pmid": str, "id": str})
ep_type = ep["source"].map({"MED": "article", "PMC": "article", "PPR": "preprint", "PAT": "patent",
                            "ETH": "thesis", "AGR": "article", "CBA": "article", "CTX": "other"}).fillna("other")
ep = pd.DataFrame({
    "source": "Europe PMC (" + ep["source"] + ")", "pmid": ep.get("pmid"), "doi": ep.get("doi").map(clean_doi),
    "title": ep["title"], "year": pd.to_numeric(ep["pubYear"], errors="coerce"),
    "first_author": ep["authorString"].fillna("").str.split(",").str[0].str.split().str[0].str.lower(),
    "type": ep_type,
})
frames = [pm, ep]
oa_files = sorted(RAW.glob("openalex_*.jsonl"))
if oa_files:
    oa = pd.read_json(oa_files[-1], lines=True, dtype={"pmid": str})
    oa["type_simple"] = oa["type"].map({"article": "article", "review": "article", "letter": "article",
                                        "editorial": "article", "preprint": "preprint", "dissertation": "thesis"}).fillna("other")
    frames.append(pd.DataFrame({
        "source": "OpenAlex", "openalex_id": oa["openalex_id"], "pmid": oa["pmid"].astype("string"), "doi": oa["doi"].map(clean_doi),
        "title": oa["title"], "year": oa["year"], "first_author": oa["first_author"].fillna("").str.lower(),
        "type": oa["type_simple"]}))
df = pd.concat(frames, ignore_index=True)
df["pmid"] = df["pmid"].astype("string").replace({"<NA>": pd.NA, "nan": pd.NA, "": pd.NA})
df["title_c"] = df["title"].map(clean_title)
counts = {"records_in": len(df), "by_source": df["source"].value_counts().to_dict()}
print(counts)

# %% [markdown]
# Patents and theses are other productions (Book 1, Chapters 7 and 9). We set them aside here and
# keep articles and preprints for the publication corpus.

# %%
other = df[df["type"].isin(["patent", "thesis", "other"])]
other.to_csv(INT / "other_productions.csv", index=False)
df = df[df["type"].isin(["article", "preprint"])].reset_index(drop=True)
print("Set aside:", other["type"].value_counts().to_dict(), "| kept:", len(df))

# %% [markdown]
# ## 2. Three passes, from safe to careful
# We give every record a work ID; records judged to be the same work share the ID.

# %%
parent = list(range(len(df)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
def union(i, j):
    a, b = find(i), find(j)
    if a != b: parent[max(a, b)] = min(a, b)

def merge_on(key):
    before = len({find(i) for i in range(len(df))})
    for _, idx in df[df[key].notna() & (df[key] != "")].groupby(key).groups.items():
        idx = list(idx)
        for j in idx[1:]: union(idx[0], j)
    after = len({find(i) for i in range(len(df))})
    return before - after

passes = {}
passes["Pass 1a: PMID"] = merge_on("pmid")
passes["Pass 1b: DOI"] = merge_on("doi")
df["key"] = df["title_c"] + "|" + df["year"].fillna(0).astype(int).astype(str) + "|" + df["first_author"].fillna("")
df.loc[df["title_c"].str.len() < 20, "key"] = None          # never match on very short titles
passes["Pass 2: title + year + first author"] = merge_on("key")

# Pass 3: near matches on title within ±1 year, reviewed by score
df["work"] = [find(i) for i in range(len(df))]
works = df.groupby("work").agg(title_c=("title_c", "first"), year=("year", "min")).reset_index()
cands = []
by_year = {y: g for y, g in works.groupby("year")}
for y, g in by_year.items():
    pool = pd.concat([by_year.get(y - 1, works.iloc[0:0]), g, by_year.get(y + 1, works.iloc[0:0])])
    titles = pool["title_c"].tolist(); ids = pool["work"].tolist()
    for w, t in zip(g["work"], g["title_c"]):
        if len(t) < 30: continue
        for match, score, k in process.extract(t, titles, scorer=fuzz.token_sort_ratio, limit=3, score_cutoff=93):
            if ids[k] != w: cands.append((min(w, ids[k]), max(w, ids[k]), score))
cands = pd.DataFrame(cands, columns=["a", "b", "score"]).drop_duplicates(["a", "b"])
cands.to_csv(LOGS / "dedup_pass3_candidates.csv", index=False)
n3 = 0
for a, b, s in cands.itertuples(index=False):
    if s >= 97 and find(a) != find(b): union(a, b); n3 += 1     # automatic only for very close titles
passes["Pass 3: near-identical titles (score ≥ 97)"] = n3
df["work"] = [find(i) for i in range(len(df))]
print(passes)
print("Pass 3 candidates for manual review (93–96):", int((cands["score"] < 97).sum()))

# %% [markdown]
# ## 3. Preprints and their published versions

# %%
g = df.groupby("work")
has_pre = g["type"].apply(lambda s: (s == "preprint").any())
has_art = g["type"].apply(lambda s: (s == "article").any())
linked = int((has_pre & has_art).sum()); pre_only = int((has_pre & ~has_art).sum())
print(f"Preprints matched to a published article: {linked}; preprints with no match: {pre_only}")

# %% [markdown]
# ## 4. One record per work, keeping the most complete

# %%
df["completeness"] = df["doi"].notna().astype(int) + df["pmid"].notna().astype(int) + (df["source"] == "PubMed").astype(int)
best = df.sort_values("completeness", ascending=False).drop_duplicates("work")
oa_id = df.dropna(subset=["openalex_id"]).groupby("work")["openalex_id"].first() if "openalex_id" in df else pd.Series(dtype=str)
best = best.assign(openalex_id=best["work"].map(oa_id),
                   sources=best["work"].map(g["source"].apply(lambda s: "; ".join(sorted(set(s))))),
                   is_preprint_only=best["work"].map(has_pre & ~has_art))
best.drop(columns=["key", "completeness"]).to_parquet(INT / "works.parquet", index=False)
summary = pd.DataFrame([("Records in (all sources)", counts["records_in"]),
                        ("Patents, theses and other set aside", len(other)),
                        ("Articles and preprints", len(df))] +
                       [(k, -v) for k, v in passes.items()] +
                       [("Unique works", len(best)), ("  of which preprints with no published match", pre_only)],
                       columns=["step", "records"])
summary.to_csv(LOGS / "dedup_summary.csv", index=False)
summary

# %% [markdown]
# ## 5. Which works did only one source find?

# %%
only = best["sources"].value_counts().head(8)
db = best["sources"].map(lambda s: frozenset(x.split(" (")[0] for x in s.split("; ")))
cover = db.map(lambda d: " + ".join(sorted(d))).value_counts()
print("Works by database combination:\n", cover.to_string())
only

# %% [markdown]
# ## 5b. Are records found by only one source relevant?
# A quick proxy before screening: does the title or abstract put a malaria word within a few words
# of a vaccine word (or name RTS,S, R21 or Mosquirix)? We compare 200 random OpenAlex-only works
# with 200 works found by PubMed and OpenAlex. This is not screening; it tells you where to look.

# %%
import os, requests
KEY = os.environ.get("OPENALEX_API_KEY", "")
NEAR = re.compile(r"(malaria|plasmodi\w*|falciparum|vivax)\W+(?:\w+\W+){0,8}?(vaccin\w*|immuni[sz]\w*)|(vaccin\w*|immuni[sz]\w*)\W+(?:\w+\W+){0,8}?(malaria|plasmodi\w*|falciparum|vivax)|RTS,?\s?S|mosquirix|R21", re.I)
def oa_text(ids):
    out = {}
    for i in range(0, len(ids), 50):
        r = requests.get("https://api.openalex.org/works", params={"filter": "openalex:" + "|".join(ids[i:i+50]), "per-page": 50,
                         "select": "id,title,abstract_inverted_index", "api_key": KEY}, timeout=60).json()
        for x in r["results"]:
            inv = x.get("abstract_inverted_index") or {}
            words = [t for _, t in sorted((p, t) for t, ps in inv.items() for p in ps)]
            out[x["id"].rsplit("/", 1)[-1]] = (x.get("title") or "") + " . " + " ".join(words)
    return out
if KEY and "openalex_id" in best:
    rows = []
    for label, sub in [("OpenAlex only", best[best.sources == "OpenAlex"]),
                       ("PubMed and OpenAlex", best[best.sources.str.contains("PubMed") & best.sources.str.contains("OpenAlex")])]:
        t = oa_text(sub.dropna(subset=["openalex_id"]).sample(200, random_state=11)["openalex_id"].tolist())
        rows.append((label, len(t), np.mean([len(v) > 200 for v in t.values()]).round(2), np.mean([bool(NEAR.search(v)) for v in t.values()]).round(2)))
    print(pd.DataFrame(rows, columns=["group", "n", "has abstract", "malaria near vaccine"]).to_string(index=False))

# %% [markdown]
# ## 6. Samples for double screening
# Two people screen the calibration sample independently with the criteria in Chapter 2,
# then compute agreement with `kappa()` below.

# %%
rng = np.random.default_rng(2026)
sample = best.sample(200, random_state=2026)[["work", "pmid", "doi", "title", "year", "sources"]]
sample.assign(screener_A="", screener_B="", reason="").to_csv(INT / "screening_calibration_sample.csv", index=False)

def kappa(a, b):
    a, b = pd.Series(a).astype(int), pd.Series(b).astype(int)
    po = (a == b).mean(); pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe)

print("Worked example from the book:", round(kappa([1]*10 + [0]*80 + [1]*5 + [0]*5, [1]*10 + [0]*80 + [0]*5 + [1]*5), 2))
