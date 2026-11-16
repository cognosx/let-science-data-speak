# %% [markdown]
# # 03 — Enriching the corpus (Book 2, Chapter 4)
#
# Adds countries from author affiliations, World Bank region and income group in the year of
# publication, author positions, open access flags and funder names, and reports match rates.
# Countries are first extracted with a dictionary, then checked against the ROR affiliation
# matching service on a random sample.

# %%
import re, time, json, unicodedata, requests, numpy as np, pandas as pd, pycountry
from pathlib import Path

ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, INT, FIN, LOGS = ROOT / "data/raw", ROOT / "data/interim", ROOT / "data/final", ROOT / "logs"
works = pd.read_parquet(INT / "works.parquet")
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})
print(len(works), "works;", works["pmid"].notna().sum(), "with a PMID")

# %% [markdown]
# ## 1. A country dictionary
# ISO names plus common variants and the endings that appear in affiliations.

# %%
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s)

alias = {}
for c in pycountry.countries:
    for n in {c.name, getattr(c, "common_name", c.name), getattr(c, "official_name", c.name)}:
        alias[norm(n).strip()] = c.alpha_3
extra = {
    "usa": "USA", "u s a": "USA", "united states of america": "USA", "united states": "USA", "us": "USA",
    "uk": "GBR", "u k": "GBR", "england": "GBR", "scotland": "GBR", "wales": "GBR", "northern ireland": "GBR",
    "great britain": "GBR", "the gambia": "GMB", "gambia": "GMB", "tanzania": "TZA", "republic of tanzania": "TZA",
    "cote d ivoire": "CIV", "ivory coast": "CIV", "democratic republic of the congo": "COD", "dr congo": "COD",
    "drc": "COD", "republic of congo": "COG", "congo": "COG", "south korea": "KOR", "korea": "KOR",
    "republic of korea": "KOR", "vietnam": "VNM", "viet nam": "VNM", "russia": "RUS", "iran": "IRN",
    "laos": "LAO", "lao pdr": "LAO", "bolivia": "BOL", "venezuela": "VEN", "taiwan": "TWN", "the netherlands": "NLD",
    "holland": "NLD", "czech republic": "CZE", "burma": "MMR", "swaziland": "SWZ", "cape verde": "CPV",
    "p r china": "CHN", "pr china": "CHN", "people s republic of china": "CHN", "turkey": "TUR", "syria": "SYR",
    "moldova": "MDA", "macedonia": "MKD", "brasil": "BRA", "espana": "ESP", "deutschland": "DEU",
    "the philippines": "PHL", "papua new guinea": "PNG", "hong kong": "HKG",
}
alias.update(extra)
US_STATES = set("al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy dc".split())
US_NAMES = {norm(s.name).strip() for s in pycountry.subdivisions.get(country_code="US")}
names_sorted = sorted(alias, key=len, reverse=True)
pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in names_sorted if len(n) > 2) + r")\b")

def country_of(aff):
    if not isinstance(aff, str) or not aff.strip(): return None
    a = re.sub(r"\S+@\S+", " ", aff)                  # remove emails
    parts = [norm(p).strip() for p in a.split(",") if p.strip()]
    for p in reversed(parts[-3:]):                     # countries usually come last
        p2 = re.sub(r"\b\d+\b", " ", p).strip()
        p2 = re.sub(r"\s+", " ", p2)
        if p2 in alias: return alias[p2]
        toks = p2.split()
        if toks and (toks[0] in US_STATES and len(toks) <= 2 or p2 in US_NAMES): return "USA"
    m = pattern.findall(norm(a))
    return alias[m[-1]] if m else None

print(country_of("KEMRI-Wellcome Trust Research Programme, Kilifi, Kenya."))
print(country_of("Jenner Institute, University of Oxford, Oxford OX3 7DQ, UK. adrian.hill@ndm.ox.ac.uk"))
print(country_of("Walter Reed Army Institute of Research, Silver Spring, MD 20910"))

# %% [markdown]
# ## 2. One row per paper and author position

# %%
rows = []
for r in pm.itertuples():
    aus = r.authors if isinstance(r.authors, list) else []
    n = len(aus)
    for k, au in enumerate(aus):
        affs = au.get("affiliations") or []
        rows.append({"pmid": r.pmid, "year": r.year, "pos": k + 1, "n_authors": n,
                     "position": "first" if k == 0 else ("last" if k == n - 1 else "middle"),
                     "affiliation": affs[0] if affs else None,
                     "countries": sorted({c for c in map(country_of, affs) if c})})
pa = pd.DataFrame(rows)
pa["has_aff"] = pa["affiliation"].notna()
pa["has_country"] = pa["countries"].str.len() > 0
print(f"{len(pa):,} author positions; {pa['has_aff'].mean():.1%} with an affiliation; "
      f"{pa.loc[pa.has_aff, 'has_country'].mean():.1%} of those matched to a country")

# %% [markdown]
# ## 3. Check the dictionary against ROR on a random sample

# %%
sample = pa[pa.has_aff].drop_duplicates("affiliation").sample(150, random_state=2026)
checks = []
for aff, ours in zip(sample["affiliation"], sample["countries"]):
    try:
        r = requests.get("https://api.ror.org/v2/organizations", params={"affiliation": aff}, timeout=30).json()
        chosen = [i for i in r.get("items", []) if i.get("chosen")]
        ror_c = None
        if chosen:
            loc = chosen[0]["organization"].get("locations", [{}])[0].get("geonames_details", {})
            ror_c = loc.get("country_code")
    except Exception:
        ror_c = None
    ours2 = pycountry.countries.get(alpha_3=ours[0]).alpha_2 if ours else None
    checks.append({"affiliation": aff, "dictionary": ours2, "ror": ror_c})
    time.sleep(0.25)
chk = pd.DataFrame(checks)
both = chk.dropna()
agree = (both["dictionary"] == both["ror"]).mean()
chk.to_csv(LOGS / "country_validation_ror.csv", index=False)
print(f"ROR chose an organisation for {chk['ror'].notna().mean():.0%} of strings; "
      f"dictionary gave a country for {chk['dictionary'].notna().mean():.0%}; "
      f"agreement where both answered: {agree:.1%} (n={len(both)})")

# %% [markdown]
# ## 4. World Bank region and income group in the year of publication

# %%
cls = pd.read_excel(RAW / "CLASS.xlsx", sheet_name="List of economies")[["Code", "Region"]].dropna()
region = dict(zip(cls["Code"], cls["Region"]))
h = pd.read_excel(RAW / "OGHIST.xlsx", sheet_name="Country Analytical History", header=None)
data_years = h.iloc[5, 2:].tolist()   # row 6 in Excel: "Data for calendar year"
hist = h.iloc[11:, [0] + list(range(2, h.shape[1]))]
hist.columns = ["code"] + data_years
hist = hist.dropna(subset=["code"]).melt(id_vars="code", var_name="data_year", value_name="group")
hist = hist[pd.to_numeric(hist["data_year"], errors="coerce").notna()]
hist["data_year"] = hist["data_year"].astype(int)
hist["group"] = hist["group"].replace({"..": None, "LM*": "LM"})
first_year, last_year = hist["data_year"].min(), hist["data_year"].max()   # last year: latest release; reuse it for newer papers

def income(code, pub_year):
    if pub_year is None or pd.isna(pub_year): return None
    y = min(int(pub_year) - 1, last_year)            # before the first release (1987 data) there is no group            # classification released in July of the publication year
    g = hist[(hist.code == code) & (hist.data_year == y)]["group"]
    return g.iloc[0] if len(g) else None

inc_lookup = {(c, y): income(c, y) for c, y in
              pa.explode("countries").dropna(subset=["countries"])[["countries", "year"]].drop_duplicates().itertuples(index=False)}

# %% [markdown]
# ## 5. Paper-level and paper–country tables

# %%
pc = pa.explode("countries").dropna(subset=["countries"]).rename(columns={"countries": "country"})
pc["region"] = pc["country"].map(region)
pc["income"] = [inc_lookup.get((c, y)) for c, y in zip(pc["country"], pc["year"])]
paper_country = pc.drop_duplicates(["pmid", "country"])[["pmid", "year", "country", "region", "income"]].copy()
paper_country["weight"] = 1 / paper_country.groupby("pmid")["country"].transform("count")
paper_country.to_parquet(FIN / "paper_country.parquet", index=False)

lead = pa[pa.position.isin(["first", "last"])].copy()
lead["ssa"] = lead["countries"].map(lambda cs: any(region.get(c) == "Sub-Saharan Africa" for c in cs))
lead["known"] = lead["has_country"]
first_last = lead.pivot_table(index="pmid", columns="position", values=["ssa", "known"], aggfunc="max")
first_last.columns = [f"{a}_{b}" for a, b in first_last.columns]
papers = pm[["pmid", "doi", "year", "journal", "language", "pub_types"]].merge(first_last.reset_index(), on="pmid", how="left")
papers["n_countries"] = papers["pmid"].map(paper_country.groupby("pmid").size()).fillna(0).astype(int)
papers["any_ssa"] = papers["pmid"].isin(paper_country.loc[paper_country.region == "Sub-Saharan Africa", "pmid"])
papers["international"] = papers["n_countries"] > 1
papers["grant_agencies"] = pm["grants"].map(lambda gs: sorted({g["agency"] for g in gs if g.get("agency")}) if isinstance(gs, list) else [])

# Open access flag from Europe PMC
ep = pd.read_json(sorted(RAW.glob("europepmc_*.jsonl"))[-1], lines=True, dtype={"pmid": str})
oa = ep.dropna(subset=["pmid"]).drop_duplicates("pmid").set_index("pmid")["isOpenAccess"].map({"Y": True, "N": False})
papers["open_access_epmc"] = papers["pmid"].map(oa)
papers.to_parquet(FIN / "papers.parquet", index=False)

# %% [markdown]
# ## 6. Match rates and provenance

# %%
by_decade = papers.assign(decade=(papers.year // 10 * 10)).groupby("decade").agg(
    papers=("pmid", "size"), first_author_country=("known_first", "mean"), any_country=("n_countries", lambda s: (s > 0).mean()))
prov = pd.DataFrame([
    ("country (dictionary)", "PubMed affiliations + pycountry and aliases", "2026-11-10", "affiliation text",
     f"{pa.loc[pa.has_aff, 'has_country'].mean():.1%} of affiliations", f"{agree:.1%} agreement with ROR (n={len(both)})"),
    ("region", "World Bank CLASS.xlsx", "downloaded 2026-11-10", "ISO3", f"{paper_country.region.notna().mean():.1%}", "official"),
    ("income group", "World Bank OGHIST.xlsx (historical)", "downloaded 2026-11-10", "ISO3 + year",
     f"{paper_country.income.notna().mean():.1%}", "classification of the year before publication"),
    ("open access", "Europe PMC isOpenAccess", "2026-11-10", "PMID", f"{papers.open_access_epmc.notna().mean():.1%}", "Europe PMC definition"),
], columns=["column", "source", "version_or_date", "key", "match_rate", "accuracy_or_note"])
prov.to_csv(LOGS / "provenance.csv", index=False)
by_decade.round(3)

# %% [markdown]
# ## 7. OpenAlex: a second view of countries, plus institutions, funders, topics and FWCI
# OpenAlex records are joined to PubMed papers by PMID. OpenAlex builds its author data from
# publishers and other sources, not from MEDLINE alone, so it can fill gaps such as the missing
# non-first-author affiliations before 2014. We check that rather than assume it.

# %%
import pycountry
oa_files = sorted(RAW.glob("openalex_*.jsonl"))
if oa_files:
    oa = pd.read_json(oa_files[-1], lines=True, dtype={"pmid": str})
    oa = oa[oa.pmid.notna() & (oa.pmid != "")].drop_duplicates("pmid")
    iso3 = lambda c: (pycountry.countries.get(alpha_2=c).alpha_3 if c and pycountry.countries.get(alpha_2=c) else None)
    def pos_countries(auths, pos):
        rows = [a for a in (auths or []) if a.get("pos") == pos]
        return sorted({iso3(c) for a in rows for c in (a.get("countries") or [])} - {None})
    oa["oa_first"] = oa.authorships.map(lambda a: pos_countries(a, "first"))
    oa["oa_last"] = oa.authorships.map(lambda a: pos_countries(a, "last"))
    oa["oa_countries"] = oa.authorships.map(lambda a: sorted({iso3(c) for x in (a or []) for c in (x.get("countries") or [])} - {None}))
    oa["institutions"] = oa.authorships.map(lambda a: sorted({(i["id"], i["name"]) for x in (a or []) for i in x["institutions"] if i.get("id")}))
    m = papers[["pmid", "year", "known_first", "known_last", "ssa_first", "ssa_last"]].merge(
        oa[["pmid", "openalex_id", "oa_first", "oa_last", "oa_countries", "institutions", "funders", "is_oa", "oa_status",
            "primary_topic", "primary_subfield", "primary_field", "fwci", "cited_by_count"]], on="pmid", how="left")
    print(f"PubMed papers with an OpenAlex record (by PMID): {m.openalex_id.notna().mean():.1%}")
    m["period"] = pd.cut(m.year, [0, 1999, 2009, 2013, 2019, 2026], labels=["≤1999", "2000–09", "2010–13", "2014–19", "2020–26"])
    have = m[m.openalex_id.notna()]
    comp = have.groupby("period", observed=True).agg(
        papers=("pmid", "size"),
        last_known_pubmed=("known_last", lambda s: s.fillna(False).astype(bool).mean()),
        last_known_openalex=("oa_last", lambda s: s.map(bool).mean()),
        first_known_pubmed=("known_first", lambda s: s.fillna(False).astype(bool).mean()),
        first_known_openalex=("oa_first", lambda s: s.map(bool).mean())).round(3)
    print(comp.to_string())
    # Agreement on first-author country where both sources give one
    pm_first = pa[pa.position == "first"].set_index("pmid")["countries"]
    both = have[have.oa_first.map(bool)].copy(); both["pm_first"] = both.pmid.map(pm_first)
    both = both[both.pm_first.map(lambda x: isinstance(x, list) and len(x) > 0)]
    agree_fa = both.apply(lambda r: bool(set(r.oa_first) & set(r.pm_first)), axis=1).mean()
    print(f"First-author country agreement, OpenAlex vs PubMed dictionary: {agree_fa:.1%} (n={len(both):,})")
    recent = have[have.year >= 2015]
    print(f"Papers 2015+ with ≥1 funder: OpenAlex {recent.funders.map(len).gt(0).mean():.1%}; "
          f"PubMed grant field {papers.loc[papers.year >= 2015, 'grant_agencies'].map(len).gt(0).mean():.1%}")
    print("Top OpenAlex funders 2015+:\n", recent.explode("funders").funders.value_counts().head(10).to_string())
    print("Open access (OpenAlex is_oa) by period:\n", have.groupby("period", observed=True).is_oa.mean().round(3).to_string())
    print("OA status 2020–26:\n", have[have.year >= 2020].oa_status.value_counts(normalize=True).round(3).to_string())
    m.drop(columns="period").to_parquet(FIN / "openalex_enrich.parquet", index=False)
    # An OpenAlex-based paper–country table (all authors, all years), for Chapters 7 and 8
    pco = have[["pmid", "year", "oa_countries"]].explode("oa_countries").dropna(subset=["oa_countries"]).rename(columns={"oa_countries": "country"})
    pco["region"] = pco.country.map(region); pco["weight"] = 1 / pco.groupby("pmid").country.transform("count")
    pco.to_parquet(FIN / "paper_country_openalex.parquet", index=False)
