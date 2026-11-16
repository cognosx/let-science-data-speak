# %% [markdown]
# # 08 — Indicators with uncertainty (Book 2, Chapter 8)

# %%
import time, numpy as np, pandas as pd, yaml
from pathlib import Path
from Bio import Entrez
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
FIN, LOGS = ROOT/"data/final", ROOT/"logs"
cfg = yaml.safe_load(open(ROOT/"config.yml")); Entrez.email = cfg["email"]
pc = pd.read_parquet(FIN/"paper_country.parquet"); papers = pd.read_parquet(FIN/"papers.parquet")

# %% [markdown]
# ## Full and fractional counts, 2015–2024

# %%
w = pc[(pc.year >= 2015) & (pc.year <= 2024)]
cnt = pd.DataFrame({"full": w.groupby("country")["pmid"].nunique(), "fractional": w.groupby("country")["weight"].sum().round(1)})
cnt["rank_full"] = cnt.full.rank(ascending=False, method="min").astype(int)
cnt["rank_frac"] = cnt.fractional.rank(ascending=False, method="min").astype(int)
cnt = cnt.sort_values("fractional", ascending=False); print(cnt.head(15).to_string())

# %% [markdown]
# ## Activity index against all malaria research
# AI = (country's share of malaria-vaccine papers) / (country's share of all malaria papers).
# The baseline comes from PubMed affiliation searches, which are rough; the code logs the queries.

# %%
NAMES = {"USA":"USA OR United States","GBR":"United Kingdom OR UK OR England OR Scotland","AUS":"Australia","FRA":"France",
         "DEU":"Germany","KEN":"Kenya","MLI":"Mali","BFA":"Burkina Faso","GHA":"Ghana","TZA":"Tanzania","NLD":"Netherlands",
         "IND":"India","CHE":"Switzerland","DNK":"Denmark","BRA":"Brazil","THA":"Thailand","CHN":"China","GAB":"Gabon"}
def n_pub(q):
    for _ in range(3):
        try: return int(Entrez.read(Entrez.esearch(db="pubmed", term=q, retmax=0))["Count"])
        except Exception: time.sleep(2)
base, vac, log = {}, {}, []
for iso, nm in NAMES.items():
    aff = "(" + " OR ".join(f'"{x.strip()}"[ad]' for x in nm.split(" OR ")) + ")"
    base[iso] = n_pub(f"malaria[mh] AND {aff} AND 2015:2024[dp]")
    vac[iso] = n_pub(f"({cfg['pubmed']['term']}) AND {aff} AND 2015:2024[dp]"); time.sleep(0.4)
    log.append((iso, aff))
tot_base = n_pub("malaria[mh] AND 2015:2024[dp]"); tot_vac = n_pub(f"({cfg['pubmed']['term']}) AND 2015:2024[dp]")
ai = pd.DataFrame({"vaccine_papers": vac, "malaria_papers": base})
ai["AI"] = ((ai.vaccine_papers / tot_vac) / (ai.malaria_papers / tot_base)).round(2)
print("totals:", tot_vac, "vaccine;", tot_base, "malaria"); ai = ai.sort_values("AI", ascending=False); print(ai.to_string())
ai.to_csv(LOGS/"activity_index.csv")

# %% [markdown]
# ## Bootstrap interval for a share
# Share of papers (with a known first-author country) whose first author is in sub-Saharan Africa.

# %%
rng = np.random.default_rng(2026)
def boot_share(x, B=2000):
    x = np.asarray(x, float); est = x.mean()
    bs = rng.choice(x, (B, len(x)), replace=True).mean(1)
    return est, *np.percentile(bs, [2.5, 97.5])
rows = []
for lo, hi in [(2000, 2009), (2010, 2019), (2020, 2026)]:
    g = papers[(papers.year.between(lo, hi)) & papers.known_first]
    est, a, b = boot_share(g.ssa_first); rows.append((f"{lo}–{hi}", len(g), f"{est:.1%}", f"{a:.1%}–{b:.1%}"))
for y in (2024, 2025):
    g = papers[(papers.year == y) & papers.known_first & papers.any_ssa]
    est, a, b = boot_share(g.ssa_first); rows.append((f"{y}, papers with an SSA author", len(g), f"{est:.1%}", f"{a:.1%}–{b:.1%}"))
bs = pd.DataFrame(rows, columns=["period", "n", "SSA first author", "95% bootstrap interval"]); bs.to_csv(LOGS/"bootstrap_ssa_first.csv", index=False); bs

# %% [markdown]
# ## Counts per year (and the incomplete last year)
# %%
yr = papers.groupby("year").size(); print(yr.loc[2015:2026].to_string())

# %% [markdown]
# ## Citation impact: FWCI, with a warning about skew
# OpenAlex's field-weighted citation impact (FWCI) compares a paper's citations with similar papers
# (field, year, type). We use papers from 2015–2022 so that each has had time to be cited.

# %%
oe_file = FIN / "openalex_enrich.parquet"
if oe_file.exists():
    oe = pd.read_parquet(oe_file)[["pmid", "fwci"]].dropna()
    pco = pd.read_parquet(FIN / "paper_country_openalex.parquet")
    d = pco[pco.year.between(2015, 2022)].merge(oe, on="pmid")
    print(f"papers with FWCI 2015–2022: {d.pmid.nunique():,}; overall mean {oe.fwci.mean():.2f}, median {oe.fwci.median():.2f}")
    rows = []
    for c in ["USA", "GBR", "AUS", "DEU", "FRA", "IND", "CHN", "KEN", "MLI", "BFA", "GHA", "TZA"]:
        g = d[d.country == c].drop_duplicates("pmid")
        bs = rng.choice(g.fwci.to_numpy(), (2000, len(g))).mean(1)
        rows.append((c, len(g), round(g.fwci.mean(), 2), f"{np.percentile(bs, 2.5):.2f}–{np.percentile(bs, 97.5):.2f}", round(g.fwci.median(), 2)))
    fw = pd.DataFrame(rows, columns=["country", "papers", "mean FWCI", "95% bootstrap", "median FWCI"]).sort_values("mean FWCI", ascending=False)
    fw.to_csv(LOGS / "fwci_by_country.csv", index=False); print(fw.to_string(index=False))
    top = d.drop_duplicates("pmid").nlargest(5, "fwci")[["pmid", "fwci"]]
    print("Share of total FWCI from the top 1% of papers:",
          round(d.drop_duplicates("pmid").fwci.nlargest(int(0.01 * d.pmid.nunique())).sum() / d.drop_duplicates("pmid").fwci.sum(), 3))
