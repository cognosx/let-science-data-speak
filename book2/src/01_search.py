# %% [markdown]
# # 01 — From question to corpus: PubMed and Europe PMC (Book 2, Chapter 2)
#
# This notebook runs the malaria vaccine search in PubMed, split by publication year to stay
# under the 10,000-record limit of the search API, fetches the full records, and runs the same
# concepts in Europe PMC. Every query, date and count goes into the search log.

# %%
import time, json, datetime, re, yaml, requests, pandas as pd
from pathlib import Path
from Bio import Entrez
from lxml import etree

ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
cfg = yaml.safe_load(open(ROOT / "config.yml"))
RAW, LOGS = ROOT / "data/raw", ROOT / "logs"
Entrez.email = cfg["email"]
TERM = " ".join(cfg["pubmed"]["term"].split())
TODAY = datetime.date.today().isoformat()
log = []

# %% [markdown]
# ## 1. Count each line of the search

# %%
lines = {
    "1 MeSH": '"Malaria Vaccines"[MeSH Terms]',
    "2 Text words": "(malaria[tiab] OR plasmodium[tiab]) AND (vaccine[tiab] OR vaccines[tiab] OR vaccination[tiab] OR immunization[tiab] OR immunisation[tiab])",
    "4 Product names NOT 1-2": '("RTS,S"[tiab] OR "R21/Matrix-M"[tiab] OR Mosquirix[tiab]) NOT ("Malaria Vaccines"[MeSH Terms] OR ((malaria[tiab] OR plasmodium[tiab]) AND (vaccine[tiab] OR vaccines[tiab] OR vaccination[tiab] OR immunization[tiab] OR immunisation[tiab])))',
    "5 Full search": TERM,
}
for name, q in lines.items():
    n = int(Entrez.read(Entrez.esearch(db="pubmed", term=q, retmax=0))["Count"])
    log.append({"database": "PubMed", "platform": "E-utilities", "date": TODAY, "line": name, "search": q, "results": n})
    print(f"{name:28s} {n:>7,}")
    time.sleep(0.4)

# %% [markdown]
# ## 2. Collect PMIDs year by year

# %%
# Slices by publication date [dp] overlap, because some records carry two publication dates
# (online and print). Slices by Entrez date [edat] do not overlap: each record has one entry date.
pmids_dp, pmids_edat, sum_dp = set(), set(), 0
for year in range(1940, cfg["pubmed"]["last_year"] + 1):
    r = Entrez.read(Entrez.esearch(db="pubmed", term=f"({TERM}) AND {year}[dp]", retmax=9999))
    sum_dp += len(r["IdList"]); pmids_dp.update(r["IdList"])
    r = Entrez.read(Entrez.esearch(db="pubmed", term=f"({TERM}) AND {year}[edat]", retmax=9999))
    pmids_edat.update(r["IdList"])
    time.sleep(0.35)
# Records outside the year range (very old or unusual dates) are caught with one more query
r = Entrez.read(Entrez.esearch(db="pubmed", term=f"({TERM}) NOT 1940:{cfg['pubmed']['last_year']}[dp]", retmax=9999))
leftover = set(r["IdList"])
pmids = pmids_dp | pmids_edat | leftover
print(f"Outside the year range: {len(leftover)}")
print(f"[dp] slices: sum {sum_dp:,}, unique {len(pmids_dp):,}")
print(f"[edat] slices: unique {len(pmids_edat):,}")
print(f"Union: {len(pmids):,} (full search count: {log[3]['results']:,})")
for line, n in [("Year slices [dp] (sum)", sum_dp), ("Year slices [dp] (unique)", len(pmids_dp)),
                ("Year slices [edat] (unique)", len(pmids_edat)), ("Outside year range", len(leftover)), ("Union of slices", len(pmids))]:
    log.append({"database": "PubMed", "platform": "E-utilities", "date": TODAY, "line": line,
                "search": f"({TERM}) AND YEAR[dp or edat]", "results": n})

# %% [markdown]
# ## 3. Fetch full records (XML) and parse them

# %%
def text(el):
    return "".join(el.itertext()).strip() if el is not None else None

def parse(article):
    mc = article.find("MedlineCitation"); a = mc.find("Article")
    pmid = mc.findtext("PMID")
    ids = {i.get("IdType"): i.text for i in article.findall("PubmedData/ArticleIdList/ArticleId")}
    year = (a.findtext("Journal/JournalIssue/PubDate/Year")
            or (a.findtext("Journal/JournalIssue/PubDate/MedlineDate") or "")[:4]
            or mc.findtext("DateCompleted/Year"))
    abstract = " ".join(text(t) for t in a.findall("Abstract/AbstractText")) or None
    authors, affs = [], []
    for au in a.findall("AuthorList/Author"):
        name = " ".join(x for x in [au.findtext("ForeName"), au.findtext("LastName")] if x) or au.findtext("CollectiveName")
        aff = [text(x) for x in au.findall("AffiliationInfo/Affiliation")]
        orcid = next((i.text for i in au.findall("Identifier") if i.get("Source") == "ORCID"), None)
        authors.append({"name": name, "affiliations": aff, "orcid": orcid})
    grants = [{"id": g.findtext("GrantID"), "agency": g.findtext("Agency"), "country": g.findtext("Country")}
              for g in a.findall("GrantList/Grant")]
    banks = {}
    for db in mc.findall("Article/DataBankList/DataBank"):
        banks[db.findtext("DataBankName")] = [x.text for x in db.findall("AccessionNumberList/AccessionNumber")]
    return {
        "pmid": pmid, "doi": (ids.get("doi") or "").lower() or None, "pmcid": ids.get("pmc"),
        "title": text(a.find("ArticleTitle")), "abstract": abstract,
        "year": int(year) if year and year.isdigit() else None,
        "journal": a.findtext("Journal/Title"), "language": a.findtext("Language"),
        "pub_types": [p.text for p in a.findall("PublicationTypeList/PublicationType")],
        "mesh": [m.findtext("DescriptorName") for m in mc.findall("MeshHeadingList/MeshHeading")],
        "authors": authors, "grants": grants, "databanks": banks,
    }

ids = sorted(pmids, key=int)
records = []
for i in range(0, len(ids), 200):
    chunk = ids[i:i + 200]
    f = RAW / f"pubmed_xml/batch_{i // 200:03d}.xml"
    if f.exists():                                   # re-runs on the same snapshot reuse saved XML
        xml = f.read_bytes()
    else:
        for attempt in range(3):
            try:
                xml = Entrez.efetch(db="pubmed", id=",".join(chunk), retmode="xml").read()
                break
            except Exception as e:
                time.sleep(3)
        (RAW / "pubmed_xml").mkdir(exist_ok=True)
        f.write_bytes(xml)
    root = etree.fromstring(xml)
    records += [parse(art) for art in root.findall("PubmedArticle")]
    for book in root.findall("PubmedBookArticle"):
        records.append({"pmid": book.findtext("BookDocument/PMID"), "title": text(book.find("BookDocument/ArticleTitle")),
                        "pub_types": ["Book chapter"], "authors": [], "grants": [], "databanks": {}, "mesh": []})
    time.sleep(0.35)
pubmed = pd.DataFrame(records)
pubmed.to_json(RAW / f"pubmed_{TODAY}.jsonl", orient="records", lines=True)
print(len(pubmed), "records fetched;", pubmed["abstract"].notna().mean().round(3), "with abstract")

# %% [markdown]
# ## 4. Europe PMC: the same concepts, cursor paging

# %%
q = " ".join(cfg["europepmc"]["query"].split())
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
params = {"query": q, "format": "json", "resultType": "lite", "pageSize": 1000, "cursorMark": "*"}
rows = []
cached = RAW / f"europepmc_{TODAY}.jsonl"
while not cached.exists():
    r = requests.get(url, params=params, timeout=120); r.raise_for_status(); d = r.json()
    rows += d["resultList"]["result"]
    nxt = d.get("nextCursorMark")
    if not nxt or nxt == params["cursorMark"] or not d["resultList"]["result"]:
        break
    params["cursorMark"] = nxt
    time.sleep(0.2)
if rows:
    epmc = pd.DataFrame(rows); epmc.to_json(cached, orient="records", lines=True); hits = int(d.get("hitCount", len(epmc)))
else:
    epmc = pd.read_json(cached, lines=True, dtype={"pmid": str, "id": str}); hits = len(epmc)
log.append({"database": "Europe PMC", "platform": "REST API", "date": TODAY, "line": "Full search",
            "search": q, "results": hits})
print(len(epmc), "Europe PMC records; sources:", epmc["source"].value_counts().to_dict())

# %% [markdown]
# ## 5. OpenAlex: title-and-abstract search, cursor paging
# OpenAlex needs a free API key (openalex.org/settings/api-key). Keep it out of files: set the
# environment variable OPENALEX_API_KEY. Note: the `search=` parameter also searches full text
# where OpenAlex has it, which returned 167,394 works on the run date, far too broad. We use the
# `title_and_abstract.search` filter instead, to match PubMed and Europe PMC.

# %%
import os
KEY = os.environ.get("OPENALEX_API_KEY", "")
OA = "https://api.openalex.org/works"
oa_lines = {"Concepts (title and abstract)": cfg["openalex"]["title_abstract"],
            "Product names (title and abstract)": cfg["openalex"]["products"]}
def oa_get(params):
    for attempt in range(5):
        r = requests.get(OA, params={**params, "api_key": KEY}, timeout=120)
        if r.status_code == 200: return r.json()
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()
def first_author(a):
    name = ((a[0].get("author") or {}).get("display_name") or "") if a else ""
    return name.split()[-1] if name.split() else None
def flat(w):
    a = w.get("authorships") or []
    return {"openalex_id": w["id"].rsplit("/", 1)[-1], "doi": w.get("doi"),
            "pmid": (w.get("ids") or {}).get("pmid", "").rsplit("/", 1)[-1] or None,
            "title": w.get("title"), "year": w.get("publication_year"), "type": w.get("type"),
            "language": w.get("language"), "first_author": first_author(a),
            "source_name": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "cited_by_count": w.get("cited_by_count"), "fwci": w.get("fwci"),
            "is_oa": (w.get("open_access") or {}).get("is_oa"), "oa_status": (w.get("open_access") or {}).get("oa_status"),
            "primary_topic": ((w.get("primary_topic") or {}).get("display_name")),
            "primary_subfield": (((w.get("primary_topic") or {}).get("subfield") or {}).get("display_name")),
            "primary_field": (((w.get("primary_topic") or {}).get("field") or {}).get("display_name")),
            "authorships": [{"pos": x.get("author_position"), "countries": x.get("countries", []),
                             "institutions": [{"id": (i.get("id") or "").rsplit("/", 1)[-1], "name": i.get("display_name"),
                                               "ror": i.get("ror"), "country": i.get("country_code"), "type": i.get("type")}
                                              for i in x.get("institutions", [])]} for x in a],
            "funders": sorted({(f.get("funder_display_name") or f.get("display_name") or "") for f in (w.get("grants") or w.get("funders") or [])} - {""})}
oa_file = RAW / f"openalex_{TODAY}.jsonl"
if KEY and not oa_file.exists():
    works = {}
    for line, q in oa_lines.items():
        q = " ".join(q.split()); cursor = "*"; n = None
        while cursor:
            d = oa_get({"filter": f"title_and_abstract.search:{q}", "per-page": 200, "cursor": cursor})
            n = n or d["meta"]["count"]
            for w in d["results"]: works.setdefault(w["id"], flat(w))
            cursor = d["meta"].get("next_cursor") if d["results"] else None
        log.append({"database": "OpenAlex", "platform": "API (title_and_abstract.search)", "date": TODAY,
                    "line": line, "search": q, "results": n})
    log.append({"database": "OpenAlex", "platform": "API", "date": TODAY, "line": "Union", "search": "both lines", "results": len(works)})
    oa_df = pd.DataFrame(works.values()); oa_df.to_json(oa_file, orient="records", lines=True)
if oa_file.exists():
    oa_df = pd.read_json(oa_file, lines=True, dtype={"pmid": str})
    print(len(oa_df), "OpenAlex works; types:", oa_df["type"].value_counts().head(8).to_dict())
else:
    print("No OpenAlex key set: skipping OpenAlex.")

# %% [markdown]
# ## 6. Search log

# %%
pd.DataFrame(log).to_csv(LOGS / "search_log.csv", index=False)
pd.DataFrame(log)[["database", "line", "results"]]
