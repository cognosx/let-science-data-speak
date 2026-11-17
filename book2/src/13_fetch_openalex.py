"""Fetch OpenAlex data for Book 2, Chapters 13-15. Key from OPENALEX_API_KEY only (never written to a file)."""
import os, sys, json, time, requests
from pathlib import Path
KEY = os.environ["OPENALEX_API_KEY"]
RAW = Path(os.environ.get("RAW_DIR", Path(__file__).resolve().parents[1] / "data/raw")); X = RAW / "oa_extra"; X.mkdir(exist_ok=True)
S = requests.Session()
def get(url, params):
    params = {**params, "api_key": KEY}
    for t in range(8):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200: return r.json()
        except requests.RequestException:
            pass
        time.sleep(min(2 ** t, 60))
    raise SystemExit("OpenAlex request failed 8 times (address not printed, to keep the key out of logs)")

def works_by_ids(ids, select, out):
    done = set()
    if out.exists():
        for l in open(out): done.add(json.loads(l)["id"].split("/")[-1])
    todo = [i for i in ids if i not in done]
    with open(out, "a") as f:
        for k in range(0, len(todo), 100):
            chunk = todo[k:k + 100]
            d = get("https://api.openalex.org/works", {"filter": "ids.openalex:" + "|".join(chunk), "select": select, "per_page": 100})
            for w in d["results"]: f.write(json.dumps(w) + "\n")
    return out

if __name__ == "__main__" and sys.argv[1] == "corpus":
    ids = [json.loads(l)["openalex_id"] for l in open(RAW / "openalex_2026-11-10.jsonl")]
    ids = [i for i in ids if i]
    works_by_ids(ids, "id,publication_year,referenced_works,authorships,primary_location", X / "corpus_refs_authors.jsonl")
    print("corpus done", sum(1 for _ in open(X / "corpus_refs_authors.jsonl")))

def load_core():
    import pandas as pd
    core = set(pd.read_parquet(Path(__file__).resolve().parents[1] / "data/final/openalex_enrich.parquet").openalex_id.dropna())
    W = {}
    for l in open(X / "corpus_refs_authors.jsonl"):
        w = json.loads(l); i = w["id"].split("/")[-1]
        if i in core and i not in W: W[i] = w
    return W

def samples(W):
    import random
    random.seed(13)
    def ok(w): return 10 <= len(w.get("referenced_works") or []) <= 100
    dis, inter = [], []
    for lo in range(1990, 2021, 5):
        pool = sorted(i for i, w in W.items() if ok(w) and lo <= (w["publication_year"] or 0) <= min(lo + 4, 2020))
        dis += random.sample(pool, min(72, len(pool)))
    for lo in range(1990, 2026, 5):
        pool = sorted(i for i, w in W.items() if ok(w) and lo <= (w["publication_year"] or 0) <= lo + 4)
        rest = [i for i in pool if i not in dis]
        inter += random.sample(rest, min(220, len(rest)))
    inter = sorted(set(inter) | set(dis))
    json.dump({"disruption": dis, "diversity": inter}, open(X / "samples.json", "w"))
    return dis, inter

if __name__ == "__main__" and sys.argv[1] == "refmeta":
    W = load_core(); dis, inter = samples(W)
    refs = sorted({r.split("/")[-1] for i in inter for r in W[i]["referenced_works"]})
    print("samples", len(dis), len(inter), "refs to fetch", len(refs))
    works_by_ids(refs, "id,publication_year,primary_location,primary_topic", X / "ref_meta.jsonl")
    print("refmeta done", sum(1 for _ in open(X / "ref_meta.jsonl")))

def count(filt):
    return get("https://api.openalex.org/works", {"filter": filt, "per_page": 1, "select": "id"})["meta"]["count"]

def cd_counts(i, w, refyear, window=5):
    y = w["publication_year"]; yr = f"publication_year:{y}-{y + window}"
    refs = [r.split("/")[-1] for r in w["referenced_works"]]
    out = {"id": i, "year": y, "n_refs": len(refs)}
    out["A"] = count(f"cites:{i},{yr}")
    for tag, rs in (("all", refs), ("from1990", [r for r in refs if (refyear.get(r) or 0) >= 1990])):
        out[f"n_refs_{tag}"] = len(rs)
        if not rs:
            out[f"B_{tag}"] = out[f"C_{tag}"] = None; continue
        R = "|".join(rs)
        out[f"B_{tag}"] = count(f"cites:{i},cites:{R},{yr}")
        out[f"C_{tag}"] = count(f"cites:{R},{yr}")
    return out

if __name__ == "__main__" and sys.argv[1] == "cd":
    W = load_core(); s = json.load(open(X / "samples.json"))
    refyear = {}
    for l in open(X / "ref_meta.jsonl"):
        m = json.loads(l); refyear[m["id"].split("/")[-1]] = m.get("publication_year")
    out = X / "cd_counts.jsonl"
    done = {json.loads(l)["id"] for l in open(out)} if out.exists() else set()
    ids = s["disruption"][: int(sys.argv[2])] if len(sys.argv) > 2 else s["disruption"]
    with open(out, "a") as f:
        for i in ids:
            if i in done: continue
            f.write(json.dumps(cd_counts(i, W[i], refyear)) + "\n"); f.flush()
    print("cd done", sum(1 for _ in open(out)))

if __name__ == "__main__" and sys.argv[1] == "allrefs":
    W = load_core()
    refs = sorted({r.split("/")[-1] for w in W.values() for r in (w.get("referenced_works") or [])})
    print("all refs", len(refs))
    works_by_ids(refs, "id,publication_year,primary_location,primary_topic", X / "ref_meta.jsonl")
    print("refmeta done", sum(1 for _ in open(X / "ref_meta.jsonl")))
