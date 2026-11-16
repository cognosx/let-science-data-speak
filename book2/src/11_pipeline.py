# %% [markdown]
# # 11 — Pipeline: run everything, then check it (Book 2, Chapter 11)
# Set RUN_ALL = True to re-execute notebooks 01–10 in order (downloads take ~30 minutes).
# The checks below run every time and stop the pipeline if something is wrong.

# %%
import os, subprocess, json, hashlib, platform, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
FIN, LOGS, NB = ROOT/"data/final", ROOT/"logs", ROOT/"notebooks"
RUN_ALL = False
ORDER = ["01_search","02_dedup_screen","03_enrich","04_entities","05_validate_ai","06_topics","07_networks","08_indicators","09_lab_to_patient","10_review_bridge"]
if RUN_ALL:
    for n in ORDER:
        subprocess.run(["jupyter","nbconvert","--to","notebook","--execute","--inplace","--ExecutePreprocessor.timeout=3000",f"{n}.ipynb"], cwd=NB, check=True)

# %%
checks = []
def check(name, ok, detail=""):
    checks.append((name, "PASS" if ok else "FAIL", detail))
works = pd.read_parquet(ROOT/"data/interim/works.parquet"); papers = pd.read_parquet(FIN/"papers.parquet")
pc = pd.read_parquet(FIN/"paper_country.parquet"); ent = pd.read_parquet(FIN/"entities.parquet")
log = pd.read_csv(LOGS/"search_log.csv")
check("PubMed records = search count", len(papers) == 12301, f"{len(papers):,}")
check("No duplicate PMIDs in papers", not papers.pmid.duplicated().any())
wsum = pc.groupby("pmid")["weight"].sum()
check("Fractional weights sum to 1 per paper", np.allclose(wsum, 1), f"min {wsum.min():.3f}, max {wsum.max():.3f}")
check("Years within range", papers.year.dropna().between(1900, 2026).all(), f"{papers.year.min():.0f}–{papers.year.max():.0f}")
check("Every entity row is a known paper", ent.pmid.isin(papers.pmid).all())
check("Income group only from 1988 (first data year 1987)", pc.loc[pc.income.notna(), "year"].min() >= 1988, f"first year with income: {pc.loc[pc.income.notna(),'year'].min():.0f}")
check("Unique works after dedup", len(works) > len(papers), f"{len(works):,}")
key = os.environ.get("OPENALEX_API_KEY", "")
leaks = [str(f) for f in ROOT.rglob("*") if key and f.is_file() and f.suffix in {".py", ".ipynb", ".csv", ".json", ".yml", ".md"} and key in f.read_text(errors="ignore")]
check("API key not written into any file", not leaks, "; ".join(leaks))
res = pd.DataFrame(checks, columns=["check","result","detail"]); print(res.to_string(index=False))
assert (res.result == "PASS").all(), "A check failed: stop and read before using any result."

# %% [markdown]
# ## Record the environment and file fingerprints
# %%
import importlib.metadata as md
env = {p: md.version(p) for p in ["pandas","numpy","biopython","rapidfuzz","sentence-transformers","bertopic","networkx","statsmodels"]}
env["python"] = platform.python_version()
fp = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:12] for f in sorted(FIN.glob("*")) if f.is_file()}
json.dump({"environment": env, "final_files_sha256_12": fp}, open(LOGS/"run_manifest.json","w"), indent=1)
print(json.dumps(env, indent=1)); print(len(fp), "final files fingerprinted")
