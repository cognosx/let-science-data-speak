# %% [markdown]
# # 04 — Extracting entities (Book 2, Chapter 5)
#
# Dictionaries and rules extract parasite species, target stage, vaccine candidates, trial phase
# and trial registration numbers from titles and abstracts. Where PubMed indexers have assigned
# the same information (MeSH headings, publication types, databank links), we use it as a
# reference to measure precision and recall. An LLM step is provided but not run here.

# %%
import re, json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, FIN, LOGS = ROOT / "data/raw", ROOT / "data/final", ROOT / "logs"
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})
pm["text"] = pm["title"].fillna("") + " " + pm["abstract"].fillna("")
print(len(pm), "PubMed records;", (pm["abstract"].notna()).mean().round(3), "with abstract")

# %% [markdown]
# ## 1. Dictionaries and rules (versioned)

# %%
SPECIES = {"P. falciparum": [r"\bfalciparum\b"], "P. vivax": [r"\bvivax\b"], "P. malariae": [r"\bmalariae\b"],
           "P. ovale": [r"\bovale\b"], "P. knowlesi": [r"\bknowlesi\b"],
           "Rodent parasites": [r"\bberghei\b", r"\byoelii\b", r"\bchabaudi\b"]}
STAGE = {
    "pre-erythrocytic": [r"pre-?erythrocytic", r"\bsporozoites?\b", r"liver[- ]stage", r"circumsporozoite", r"\bCSP\b", r"\bRTS,S", r"\bR21\b", r"\bPfSPZ\b", r"\bTRAP\b"],
    "blood-stage": [r"blood[- ]stage", r"\bmerozoites?\b", r"asexual[- ]stage", r"\bAMA-?1\b", r"\bMSP-?\d", r"\bRH5\b", r"\bGMZ2\b", r"\bEBA-?175\b", r"\bDBP\b"],
    "transmission-blocking": [r"transmission[- ]blocking", r"sexual[- ]stage", r"\bgametocytes?\b", r"\bPfs?2[35]0?\b", r"\bPfs48/45\b", r"\bPvs25\b", r"\bookinetes?\b"],
}
CANDIDATES = {
    "RTS,S": [r"\bRTS,\s?S\b", r"\bmosquirix\b"], "R21": [r"\bR21\b(?!\s*(grant|award|mechanism))"],
    "PfSPZ": [r"\bPfSPZ\b"], "RH5": [r"\bRH5\b"], "Pfs230": [r"\bPfs230\b"], "Pfs25": [r"\bPfs25\b"],
    "Pfs48/45": [r"\bPfs48/45\b", r"\bR0\.?6C\b"], "AMA1": [r"\bAMA-?1\b"], "MSP1": [r"\bMSP-?1\b"],
    "MSP3": [r"\bMSP-?3\b"], "GMZ2": [r"\bGMZ2\b"], "ME-TRAP": [r"\bME-TRAP\b"], "SPf66": [r"\bSPf\s?66\b"],
    "PvDBP": [r"\bPvDBP\b"], "Pvs25": [r"\bPvs25\b"], "CelTOS": [r"\bCelTOS\b"], "FMP2.1": [r"\bFMP2\.1\b"],
}
PHASE = re.compile(r"\bphase\s*(?:-\s*)?(1|2|3|4|i{1,3}|iv)\s*([ab])?\b", re.I)
PHASE_MAP = {"1": "1", "i": "1", "2": "2", "ii": "2", "3": "3", "iii": "3", "4": "4", "iv": "4"}
TRIAL_ID = re.compile(r"\b(NCT\d{8}|PACTR\d{15}|ISRCTN\d{8}|CTRI/\d{4}/\d+/\d+)\b", re.I)

def tag(t, vocab):
    return sorted({k for k, pats in vocab.items() if any(re.search(p, t, re.I) for p in pats)})

pm["species"] = pm["text"].map(lambda t: tag(t, SPECIES))
pm["stage"] = pm["text"].map(lambda t: tag(t, STAGE))
pm["candidates"] = pm["text"].map(lambda t: tag(t, CANDIDATES))
pm["phase"] = pm["text"].map(lambda t: sorted({PHASE_MAP[m.group(1).lower()] for m in PHASE.finditer(t)}))
pm["trial_ids_text"] = pm["text"].map(lambda t: sorted({x.upper() for x in TRIAL_ID.findall(t)}))
pm["trial_ids_db"] = pm["databanks"].map(lambda d: sorted({x.upper() for k, v in (d or {}).items() for x in v
                                                             if re.match(r"(NCT|PACTR|ISRCTN)", str(x), re.I)}) if isinstance(d, dict) else [])
pm["trial_ids"] = [sorted(set(a) | set(b)) for a, b in zip(pm["trial_ids_text"], pm["trial_ids_db"])]

# %% [markdown]
# ## 2. Accuracy against PubMed indexing, used as a reference
# MeSH and publication types are assigned by trained indexers, so they are a useful (imperfect)
# reference. We compare document-level labels on records that have been indexed.

# %%
def prf(pred, ref):
    pred, ref = pd.Series(pred, dtype=bool), pd.Series(ref, dtype=bool)
    tp = (pred & ref).sum(); fp = (pred & ~ref).sum(); fn = (~pred & ref).sum()
    p = tp / (tp + fp) if tp + fp else np.nan; r = tp / (tp + fn) if tp + fn else np.nan
    return dict(n=len(pred), ref_positive=int(ref.sum()), precision=round(p, 3), recall=round(r, 3),
                f1=round(2 * p * r / (p + r), 3) if p and r else np.nan)

indexed = pm[pm["mesh"].map(len) > 0]
mesh_has = lambda term: indexed["mesh"].map(lambda m: term in m)
res = {
    "P. falciparum vs MeSH 'Plasmodium falciparum'": prf(indexed["species"].map(lambda s: "P. falciparum" in s), mesh_has("Plasmodium falciparum")),
    "P. vivax vs MeSH 'Plasmodium vivax'": prf(indexed["species"].map(lambda s: "P. vivax" in s), mesh_has("Plasmodium vivax")),
    "Phase 3 (text) vs publication type 'Clinical Trial, Phase III'": prf(indexed["phase"].map(lambda s: "3" in s), indexed["pub_types"].map(lambda p: "Clinical Trial, Phase III" in p)),
    "Phase 1 (text) vs publication type 'Clinical Trial, Phase I'": prf(indexed["phase"].map(lambda s: "1" in s), indexed["pub_types"].map(lambda p: "Clinical Trial, Phase I" in p)),
    "Trial ID in text vs PubMed databank link": prf(pm["trial_ids_text"].map(bool), pm["trial_ids_db"].map(bool)),
}
acc = pd.DataFrame(res).T
acc.to_csv(LOGS / "entity_accuracy_vs_indexing.csv")
acc

# %% [markdown]
# Reading the errors matters more than the numbers. Mismatches with MeSH are often not extraction
# errors: a paper may study *P. falciparum* without the indexer assigning that heading, or mention
# a phase 3 trial it did not run. The notebook saves 50 random disagreements for each comparison
# so that a person can read them.

# %%
dis = []
for name, pred, ref in [("vivax", indexed["species"].map(lambda s: "P. vivax" in s), mesh_has("Plasmodium vivax")),
                        ("phase3", indexed["phase"].map(lambda s: "3" in s), indexed["pub_types"].map(lambda p: "Clinical Trial, Phase III" in p))]:
    d = indexed[pred != ref].sample(min(50, int((pred != ref).sum())), random_state=1)
    dis.append(d.assign(comparison=name, extracted=pred[d.index], reference=ref[d.index])[["comparison", "pmid", "title", "extracted", "reference"]])
pd.concat(dis).to_csv(LOGS / "entity_disagreements_to_read.csv", index=False)

# %% [markdown]
# ## 3. What the field has been testing

# %%
pm["period"] = pd.cut(pm["year"], [0, 1989, 1999, 2009, 2014, 2019, 2026],
                      labels=["≤1989", "1990–99", "2000–09", "2010–14", "2015–19", "2020–26"])
stage_tab = (pm.explode("stage").dropna(subset=["stage"]).groupby(["period", "stage"], observed=False).size()
             .unstack(fill_value=0))
stage_share = stage_tab.div(pm.groupby("period", observed=False).size(), axis=0).round(3)
species_share = (pm.explode("species").dropna(subset=["species"]).groupby(["period", "species"], observed=False).size()
                 .unstack(fill_value=0).div(pm.groupby("period", observed=False).size(), axis=0).round(3))
cand = pm.explode("candidates").dropna(subset=["candidates"])["candidates"].value_counts()
print("Share of papers mentioning each stage, by period\n", stage_share, "\n")
print("Share of papers mentioning each species, by period\n", species_share[["P. falciparum", "P. vivax"]], "\n")
print("Papers mentioning each candidate\n", cand.head(12))

# %%
out = pm[["pmid", "year", "species", "stage", "candidates", "phase", "trial_ids"]]
out.to_parquet(FIN / "entities.parquet", index=False)
pd.DataFrame({"version": ["1.0"], "date": ["2026-11-10"], "species": [json.dumps(SPECIES)],
              "stage": [json.dumps(STAGE)], "candidates": [json.dumps(CANDIDATES)]}).to_csv(LOGS / "dictionary_v1.csv", index=False)
print(f"Records with at least one trial ID: {out['trial_ids'].map(bool).sum():,}; "
      f"distinct trial IDs: {out.explode('trial_ids')['trial_ids'].nunique():,}")

# %% [markdown]
# ## 4. LLM extraction (provided, not run)
# Set an API key for your provider and run on the validation sample first (Chapter 5). The prompt
# asks for evidence quotes so that invented values can be detected.

# %%
LLM_PROMPT = """Read the title and abstract below. Return a JSON object with: vaccine_candidates (list),
parasite_species (list from P. falciparum, P. vivax, P. malariae, P. ovale, P. knowlesi, other, not reported),
target_stage (list from pre-erythrocytic, blood-stage, transmission-blocking, multi-stage, not reported),
study_type (one of in vitro, animal, phase 1, phase 2, phase 3, phase 4, observational, review, modelling, other),
population (short text or "not reported"), evidence (for each field, the exact supporting words).
Use only information in the text. If unsure, write "not reported".
Title: {title}
Abstract: {abstract}"""
