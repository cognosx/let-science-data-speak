"""Book 2, Chapter 15: check a random sample of 50 apparent exits for a second OpenAlex profile with the same
display name and recent works (2023-2025). Names are used only for this check and are not saved."""
import os, json, re, unicodedata, numpy as np, pandas as pd, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data/checks"
X = Path(os.environ.get("RAW_DIR", ROOT / "data/raw")) / "oa_extra"
spec = importlib.util.spec_from_file_location("f", ROOT / "src/13_fetch_openalex.py"); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
C = pd.read_csv(X / "career_table.csv")
ex = C[C.exit].sample(50, random_state=15)
norm = lambda s: re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()).split()
res = []
for aid in ex.author:
    me = f.get(f"https://api.openalex.org/authors/{aid}", {"select": "id,display_name,display_name_alternatives"})
    name = me["display_name"]; key = norm(name)
    d = f.get("https://api.openalex.org/authors", {"search": name, "per_page": 25, "select": "id,display_name,counts_by_year,works_count"})
    other = []
    for a in d["results"]:
        if a["id"].endswith(aid): continue
        k = norm(a["display_name"])
        if k and key and k[-1] == key[-1] and k[0][:1] == key[0][:1]:
            rec = sum(x["works_count"] for x in a.get("counts_by_year") or [] if x["year"] in (2023, 2024, 2025))
            if rec > 0: other.append(rec)
    res.append({"case": len(res) + 1, "same_name_profiles_active": len(other)})  # no IDs saved: group results only
R = pd.DataFrame(res)
R.to_csv(OUT / "exit_check_sample.csv", index=False)
print("sample", len(R), "with an active same-name profile:", int((R.same_name_profiles_active > 0).sum()))
