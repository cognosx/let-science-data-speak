# %% [markdown]
# # 05 — Validating automated extraction (Book 2, Chapter 1)
# Every metric gets a confidence interval. Here we validate the rule-based extractor from
# notebook 04 against PubMed indexing; the same code validates an LLM once its output exists.

# %%
import numpy as np, pandas as pd
from pathlib import Path
from statsmodels.stats.proportion import proportion_confint
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
FIN, LOGS, RAW = ROOT/"data/final", ROOT/"logs", ROOT/"data/raw"
ent = pd.read_parquet(FIN/"entities.parquet")
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})[["pmid","mesh","pub_types"]]
d = ent.merge(pm, on="pmid"); d = d[d["mesh"].map(len) > 0]

def metrics(pred, ref, label):
    pred, ref = np.asarray(pred, bool), np.asarray(ref, bool)
    tp, fp, fn = (pred&ref).sum(), (pred&~ref).sum(), (~pred&ref).sum()
    row = {"field": label, "TP": tp, "FP": fp, "FN": fn}
    for name, k, n in [("precision", tp, tp+fp), ("recall", tp, tp+fn)]:
        lo, hi = proportion_confint(k, n, method="wilson")
        row[name] = f"{k/n:.2f} ({lo:.2f}–{hi:.2f})"
    return row

rows = [metrics(d["species"].map(lambda s: "P. falciparum" in s), d["mesh"].map(lambda m: "Plasmodium falciparum" in m), "P. falciparum"),
        metrics(d["species"].map(lambda s: "P. vivax" in s), d["mesh"].map(lambda m: "Plasmodium vivax" in m), "P. vivax"),
        metrics(d["phase"].map(lambda s: "1" in s), d["pub_types"].map(lambda p: "Clinical Trial, Phase I" in p), "Phase 1 trial"),
        metrics(d["phase"].map(lambda s: "3" in s), d["pub_types"].map(lambda p: "Clinical Trial, Phase III" in p), "Phase 3 trial")]
tab = pd.DataFrame(rows); tab.to_csv(LOGS/"validation_wilson.csv", index=False); print(tab.to_string(index=False))

# %% [markdown]
# ## What a small validation sample would have told us
# Suppose we had read only 100 or 200 random records for phase 3. How wide would the interval be?

# %%
rng = np.random.default_rng(2026)
pred = d["phase"].map(lambda s: "3" in s).to_numpy(); ref = d["pub_types"].map(lambda p: "Clinical Trial, Phase III" in p).to_numpy()
for n in (100, 200, 400):
    idx = rng.choice(len(d), n, replace=False); tp=(pred[idx]&ref[idx]).sum(); pos=ref[idx].sum()
    print(f"random sample of {n}: reference positives = {pos}; true positives = {tp}")
print("Phase 3 prevalence among indexed records:", round(ref.mean(), 4))
# Stratified alternative: sample 50 predicted positives and 50 predicted negatives
pp, pn = np.where(pred)[0], np.where(~pred)[0]
s1, s0 = rng.choice(pp, 50, replace=False), rng.choice(pn, 50, replace=False)
print("Stratified: precision from 50 predicted positives =", ref[s1].mean().round(2),
      "| false negatives among 50 predicted negatives =", int(ref[s0].sum()))

# %% [markdown]
# ## LLM run (provided, not executed: needs a key)
# ```python
# import anthropic, json
# client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY
# def extract(title, abstract):
#     msg = client.messages.create(model="claude-haiku-4-5", max_tokens=600, temperature=0,
#             messages=[{"role": "user", "content": LLM_PROMPT.format(title=title, abstract=abstract)}])
#     return json.loads(msg.content[0].text)
# ```
# Log the model name, date, prompt version and temperature in logs/provenance.csv.
