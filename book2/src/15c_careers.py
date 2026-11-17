"""Book 2, Chapter 15: career paths, mobility and exits for 1,127 researchers whose first corpus paper
(2005-2015) had an institution in sub-Saharan Africa. Group results only; no individual is named."""
import os, sys, json, numpy as np, pandas as pd, pycountry
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
pc = pd.read_parquet(ROOT / "data/final/paper_country.parquet")
SSA = {pycountry.countries.get(alpha_3=c).alpha_2 for c in set(pc.loc[pc.region == "Sub-Saharan Africa", "country"]) if pycountry.countries.get(alpha_3=c)}
coh = pd.read_csv(X / "career_cohort.csv", index_col=0)
P = {json.loads(l)["id"].split("/")[-1]: json.loads(l) for l in open(X / "cohort_profiles.jsonl")}
rows = []
for aid, c in coh.iterrows():
    p = P.get(aid)
    if not p: continue
    cby = {d["year"]: d["works_count"] for d in p.get("counts_by_year") or []}
    yrs = sorted(y for y, n in cby.items() if n > 0)
    ssa_y, out_y = set(), set()
    for af in p.get("affiliations") or []:
        cc = (af.get("institution") or {}).get("country_code")
        for y in af.get("years") or []:
            (ssa_y if cc in SSA else out_y).add(y)
    after = lambda s: {y for y in s if y > c.first_corpus_year}
    only_out = sorted(after(out_y) - ssa_y); both = after(out_y) & ssa_y
    returned = any(any(z > y for z in ssa_y) for y in only_out)
    recent = sum(cby.get(y, 0) for y in (2023, 2024, 2025))
    rows.append({"author": aid, "first_corpus_year": c.first_corpus_year, "country": c.first_country, "orcid": p.get("orcid"),
                 "works": p.get("works_count", 0), "first_work_year": yrs[0] if yrs else None, "last_work_year": yrs[-1] if yrs else None,
                 "recent_2023_25": recent, "any_abroad_after": bool(after(out_y)), "dual_years": len(both),
                 "only_abroad_after": bool(only_out), "returned": returned,
                 "recent_only_abroad": bool({2023, 2024, 2025} & out_y) and not bool({2023, 2024, 2025} & ssa_y)})
C = pd.DataFrame(rows)
C["exit"] = C.recent_2023_25 == 0
C["flag_small"] = C.works < 3
C["cohort"] = np.where(C.first_corpus_year <= 2009, "2005-09", "2010-15")
C.to_csv(X / "career_table.csv", index=False)
summary = C.groupby("cohort").agg(people=("author", "size"), with_orcid=("orcid", lambda s: s.notna().mean()),
        median_works=("works", "median"), exit_share=("exit", "mean"),
        exit_share_without_small=("exit", lambda s: s[~C.loc[s.index, "flag_small"]].mean()),
        any_abroad=("any_abroad_after", "mean"), only_abroad=("only_abroad_after", "mean"),
        returned=("returned", "mean"), recent_only_abroad=("recent_only_abroad", "mean"))
summary.loc["all"] = [len(C), C.orcid.notna().mean(), C.works.median(), C.exit.mean(), C.loc[~C.flag_small, "exit"].mean(),
                      C.any_abroad_after.mean(), C.only_abroad_after.mean(), C.returned.mean(), C.recent_only_abroad.mean()]
summary.to_csv(OUT / "careers_summary.csv")
pd.set_option("display.width", 220); print(summary.round(3).to_string())
print("exits:", int(C.exit.sum()), "of which small profiles:", int((C.exit & C.flag_small).sum()), "with ORCID:", int((C.exit & C.orcid.notna()).sum()))
print("dual-affiliation years among those ever abroad:", round((C.loc[C.any_abroad_after, "dual_years"] > 0).mean(), 3))
# who moved where (group level)

# career paths: papers per year by career age (years since first work), and corpus leadership by years since first corpus paper
rows = []
for aid, p in P.items():
    if aid not in set(C.author): continue
    cby = {d["year"]: d["works_count"] for d in p.get("counts_by_year") or []}
    y0 = min((y for y, n in cby.items() if n > 0), default=None)
    if y0 is None: continue
    for age in range(0, 21):
        y = y0 + age
        if y > 2025: break
        rows.append({"author": aid, "age": age, "papers": cby.get(y, 0)})
K = pd.DataFrame(rows)
curve = K.groupby("age").papers.agg(["size", "median", "mean"]).round(2)
A = pd.read_parquet(X / "authorships.parquet")
A = A[A.author.isin(C.author)].merge(C[["author", "first_corpus_year"]], on="author")
A["since"] = A.year - A.first_corpus_year
A["led"] = A.pos.isin(["first", "last"])
lead = A[A.since.between(0, 15)].assign(band=lambda d: pd.cut(d.since, [-1, 2, 5, 10, 15], labels=["0-2", "3-5", "6-10", "11-15"])).groupby("band", observed=True).agg(authorships=("led", "size"), led_share=("led", "mean"), in_region=("ssa", "mean")).round(3)
curve.to_csv(OUT / "careers_output_by_age.csv"); lead.to_csv(OUT / "careers_leadership_by_years.csv")
print(curve.loc[[0, 2, 5, 10, 15, 20]].to_string()); print(lead.to_string())
