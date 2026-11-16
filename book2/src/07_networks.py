# %% [markdown]
# # 07 — Collaboration networks and leadership (Book 2, Chapter 7)

# %%
import itertools, numpy as np, pandas as pd, networkx as nx
from pathlib import Path
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
FIN, LOGS = ROOT/"data/final", ROOT/"logs"
pc = pd.read_parquet(FIN/"paper_country.parquet"); papers = pd.read_parquet(FIN/"papers.parquet")
# PubMed stored only the FIRST author's affiliation before late 2013 (all authors from 2014).
# Before 2014 the network would show only first-author countries, so we start in 2015.
pc = pc[pc["year"] >= 2015]
per = pc.groupby("pmid")["country"].apply(lambda s: sorted(set(s)))
multi = per[per.map(len) > 1]
print(f"papers 2015–2026 with a known country: {len(per):,}; with two or more countries: {len(multi):,} ({len(multi)/len(per):.1%})")

# %% [markdown]
# ## Fractional edge weights
# A paper with k countries contributes 1/(k−1) to each of its country pairs, so that a
# 30-country consortium paper does not outweigh 30 bilateral papers.

# %%
full, frac = {}, {}
for cs in multi:
    w = 1 / (len(cs) - 1)
    for a, b in itertools.combinations(cs, 2):
        full[(a, b)] = full.get((a, b), 0) + 1; frac[(a, b)] = frac.get((a, b), 0) + w
edges = pd.DataFrame([(a, b, full[(a, b)], round(frac[(a, b)], 1)) for a, b in full], columns=["a","b","papers","fractional"])
print("Top pairs by full count\n", edges.nlargest(10, "papers").to_string(index=False))
print("\nTop pairs by fractional weight\n", edges.nlargest(10, "fractional").to_string(index=False))
edges.to_csv(FIN/"country_edges_2015_2026.csv", index=False)

# %%
G = nx.Graph(); [G.add_edge(r.a, r.b, weight=r.fractional) for r in edges.itertuples()]
deg = pd.Series(dict(G.degree())); strength = pd.Series(dict(G.degree(weight="weight")))
btw = pd.Series(nx.betweenness_centrality(G, weight=None))
cent = pd.DataFrame({"partners": deg, "strength": strength.round(1), "betweenness": btw.round(3)}).sort_values("strength", ascending=False)
print("countries:", G.number_of_nodes(), "| links:", G.number_of_edges(), "| density:", round(nx.density(G), 3))
cent.head(12)

# %% [markdown]
# ## Leadership: who holds the first and last author positions?
# Among papers with at least one sub-Saharan African country, and a known country for that position.

# %%
p = papers[(papers["year"] >= 2015) & papers["any_ssa"].fillna(False).astype(bool)].copy()
p["period"] = pd.cut(p["year"], [2014, 2019, 2022, 2026], labels=["2015–19","2020–22","2023–26"])
lead = p.groupby("period", observed=True).apply(lambda g: pd.Series({
    "papers_with_SSA": len(g),
    "first_known": int(g.known_first.sum()), "SSA_first_%": round(100 * g.loc[g.known_first.fillna(False).astype(bool), "ssa_first"].astype(float).mean(), 1),
    "last_known": int(g.known_last.sum()), "SSA_last_%": round(100 * g.loc[g.known_last.fillna(False).astype(bool), "ssa_last"].astype(float).mean(), 1)}), include_groups=False)
lead.to_csv(LOGS/"leadership_ssa.csv"); lead

# %% [markdown]
# ## OpenAlex: leadership over a longer period, and institutions
# OpenAlex holds countries for all author positions in most older papers too (notebook 03), so it
# lets us look before 2014. We first check that it agrees with PubMed where both are complete.

# %%
oe_file = FIN / "openalex_enrich.parquet"
if oe_file.exists():
    oe = pd.read_parquet(oe_file); oe = oe[oe.openalex_id.notna()].copy()
    region = pd.read_parquet(FIN / "paper_country_openalex.parquet").drop_duplicates("country").set_index("country")["region"].to_dict()
    ssa = lambda cs: any(region.get(c) == "Sub-Saharan Africa" for c in cs)
    oe["any_ssa_oa"] = oe.oa_countries.map(lambda cs: ssa(list(cs)))
    oe = oe[oe.any_ssa_oa & (oe.year >= 2000)]
    oe["period"] = pd.cut(oe.year, [1999, 2009, 2014, 2019, 2022, 2026], labels=["2000–09", "2010–14", "2015–19", "2020–22", "2023–26"])
    lead_oa = oe.groupby("period", observed=True).apply(lambda g: pd.Series({
        "papers_with_SSA": len(g),
        "SSA_first_%": round(100 * g[g.oa_first.map(len) > 0].oa_first.map(lambda c: ssa(list(c))).mean(), 1),
        "SSA_last_%": round(100 * g[g.oa_last.map(len) > 0].oa_last.map(lambda c: ssa(list(c))).mean(), 1),
        "n_last_known": int((g.oa_last.map(len) > 0).sum())}), include_groups=False)
    lead_oa.to_csv(LOGS / "leadership_ssa_openalex.csv"); print(lead_oa.to_string())

    # Institution network, 2015–2026, fractional weights
    inst = oe_all = pd.read_parquet(oe_file)
    inst = inst[(inst.year >= 2015) & inst.institutions.map(lambda x: x is not None and len(x) > 0)]
    names, ifull, ifrac = {}, {}, {}
    for lst in inst.institutions:
        ids = sorted({i[0] for i in lst}); names.update({i[0]: i[1] for i in lst})
        if len(ids) < 2: continue
        w = 1 / (len(ids) - 1)
        for a, b in itertools.combinations(ids, 2):
            ifull[(a, b)] = ifull.get((a, b), 0) + 1; ifrac[(a, b)] = ifrac.get((a, b), 0) + w
    IG = nx.Graph(); [IG.add_edge(a, b, weight=ifrac[(a, b)]) for (a, b) in ifrac]
    npapers = inst.institutions.explode().dropna().map(lambda t: t[0]).value_counts()
    ib = pd.Series(nx.betweenness_centrality(IG, k=500, seed=2026))
    itab = pd.DataFrame({"institution": [names[i] for i in npapers.index[:15]], "papers": npapers.values[:15],
                         "partners": [IG.degree(i) if i in IG else 0 for i in npapers.index[:15]],
                         "betweenness": [round(ib.get(i, 0), 3) for i in npapers.index[:15]]})
    print("institutions:", IG.number_of_nodes(), "| links:", IG.number_of_edges()); print(itab.to_string(index=False))
    top_b = ib.sort_values(ascending=False).head(10)
    print("Highest betweenness:\n", pd.Series({names[i]: round(v, 3) for i, v in top_b.items()}).to_string())
