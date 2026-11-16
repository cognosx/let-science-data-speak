# %% [markdown]
# # 10 — From landscape to review (Book 2, Chapter 10)

# %%
import numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, FIN, LOGS = ROOT/"data/raw", ROOT/"data/final", ROOT/"logs"
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})[["pmid","title","year","pub_types"]]
ent = pd.read_parquet(FIN/"entities.parquet").drop(columns="year")
d = pm.merge(ent, on="pmid").reset_index(drop=True)

# %% [markdown]
# ## 1. Randomised trials in the corpus (indexer-assigned publication type)
# %%
d["rct"] = d.pub_types.map(lambda p: "Randomized Controlled Trial" in p)
d["sr"] = d.pub_types.map(lambda p: "Systematic Review" in p or "Meta-Analysis" in p)
print("RCT reports:", d.rct.sum(), "| systematic reviews or meta-analyses:", d.sr.sum())
rct = d[d.rct]
print(rct.explode("candidates")["candidates"].value_counts().head(10).to_string())
rct[["pmid","year","title","candidates","phase","trial_ids"]].to_csv(LOGS/"rct_list_for_screening.csv", index=False)

# %% [markdown]
# ## 2. Evidence gap map: target stage × type of evidence
# %%
def ev(row):
    pt = row.pub_types
    if "Clinical Trial, Phase III" in pt or "3" in row.phase: return "4 Phase 3"
    if "Clinical Trial, Phase II" in pt or "2" in row.phase: return "3 Phase 2"
    if "Clinical Trial, Phase I" in pt or "1" in row.phase: return "2 Phase 1"
    if "Systematic Review" in pt or "Meta-Analysis" in pt: return "5 Review"
    return "1 Other (lab, animal, observational, commentary)"
d["evidence"] = d.apply(ev, axis=1)
gm = d.reset_index(drop=True).explode("stage").dropna(subset=["stage"])
gap = gm.groupby(["stage", "evidence"]).size().unstack(fill_value=0); gap.to_csv(LOGS/"gap_map_stage_evidence.csv"); gap

# %% [markdown]
# ## 3. Worked meta-analysis (teaching example: two estimates from the same R21 phase 3 trial)
# Vaccine efficacy (VE) = 1 − HR. Convert each 95% CI to a standard error on the log HR scale.
# %%
est = pd.DataFrame({"site": ["seasonal", "standard"], "ve": [75, 68], "lo": [71, 61], "hi": [79, 74]})
est["loghr"] = np.log(1 - est.ve/100)
est["se"] = (np.log(1 - est.lo/100) - np.log(1 - est.hi/100)) / (2*1.96)
w = 1/est.se**2; fe = (w*est.loghr).sum()/w.sum(); se_fe = np.sqrt(1/w.sum())
Q = (w*(est.loghr - fe)**2).sum(); dfree = len(est) - 1; I2 = max(0, (Q - dfree)/Q)
tau2 = max(0, (Q - dfree)/(w.sum() - (w**2).sum()/w.sum())); wr = 1/(est.se**2 + tau2)
re = (wr*est.loghr).sum()/wr.sum(); se_re = np.sqrt(1/wr.sum())
print(est.round(4).to_string(index=False))
print(f"Fixed effect: log HR {fe:.3f}, HR {np.exp(fe):.2f}, VE {100*(1-np.exp(fe)):.1f}% "
      f"(95% CI {100*(1-np.exp(fe+1.96*se_fe)):.1f}–{100*(1-np.exp(fe-1.96*se_fe)):.1f})")
print(f"Q = {Q:.2f}, df = {dfree}, p = {stats.chi2.sf(Q, dfree):.3f}, I² = {100*I2:.0f}%")
print(f"Random effects (DerSimonian–Laird): tau² = {tau2:.4f}, VE {100*(1-np.exp(re)):.1f}% "
      f"(95% CI {100*(1-np.exp(re+1.96*se_re)):.1f}–{100*(1-np.exp(re-1.96*se_re)):.1f})")
