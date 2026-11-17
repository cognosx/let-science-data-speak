"""Book 2, Chapter 15: cohort of researchers whose first corpus paper (2005-2015) had an institution in
sub-Saharan Africa; fetch their OpenAlex author profiles (affiliation years, counts by year, ORCID)."""
import os, sys, json, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
A = pd.read_parquet(X / "authorships.parquet").sort_values("year")
first = A.groupby("author").first()
coh = first[first.ssa & first.year.between(2005, 2015)].copy()
coh = coh.rename(columns={"year": "first_corpus_year", "country": "first_country"})[["first_corpus_year", "first_country"]]
coh["corpus_papers"] = A[A.author.isin(coh.index)].groupby("author").work.nunique()
coh.to_csv(X / "career_cohort.csv")
print("cohort", len(coh), coh.first_corpus_year.value_counts().sort_index().to_dict())
if len(sys.argv) > 1 and sys.argv[1] == "fetch":
    import importlib.util
    spec = importlib.util.spec_from_file_location("f", ROOT / "src/13_fetch_openalex.py"); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    out = X / "cohort_profiles.jsonl"
    done = {json.loads(l)["id"].split("/")[-1] for l in open(out)} if out.exists() else set()
    todo = [a for a in coh.index if a not in done]
    with open(out, "a") as fh:
        for k in range(0, len(todo), 100):
            d = f.get("https://api.openalex.org/authors", {"filter": "ids.openalex:" + "|".join(todo[k:k + 100]), "per_page": 100,
                     "select": "id,orcid,works_count,counts_by_year,affiliations,last_known_institutions"})
            for a in d["results"]: fh.write(json.dumps(a) + "\n")
    print("profiles", sum(1 for _ in open(out)))
