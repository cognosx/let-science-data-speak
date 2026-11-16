"""Shared helpers. All paths are inside /tmp/agent_test_B."""
import json, re, html, unicodedata
BASE = '/tmp/agent_test_B'
RAW = BASE + '/raw'
OUT = BASE + '/work/out'
FILES = {'pubmed': 'pubmed_2026-11-10.jsonl', 'europepmc': 'europepmc_2026-11-10.jsonl',
         'openalex': 'openalex_2026-11-10.jsonl'}

def load(src):
    return [json.loads(l) for l in open(f'{RAW}/{FILES[src]}', encoding='utf-8')]

def fold(s):
    s = unicodedata.normalize('NFKD', str(s))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()

def norm_title(t):
    if t is None: return ''
    t = html.unescape(html.unescape(str(t)))
    t = re.sub(r'<[^>]{0,40}>', ' ', t)          # markup such as <i>..</i>
    t = fold(t)
    t = re.sub(r'[^a-z0-9]+', ' ', t).strip()
    return t

def norm_doi(d):
    if d is None: return None
    d = str(d).strip().lower()
    d = re.sub(r'^https?://(dx\.)?doi\.org/', '', d)
    return d if re.match(r'^10\.\d{4,9}/\S+$', d) else None

def norm_pmid(p):
    if p is None: return None
    p = str(p).strip()
    if p.endswith('.0'): p = p[:-2]
    return p if re.fullmatch(r'\d+', p) else None

def norm_pmcid(p):
    if p is None: return None
    p = str(p).strip().upper()
    return p if re.fullmatch(r'PMC\d+', p) else None

def year_int(y):
    try:
        y = int(float(y))
        return y if 1800 <= y <= 2026 else None
    except Exception:
        return None

def akey_from_surname(s):
    """last whitespace token of a surname, ascii-folded, letters only"""
    if not s: return None
    toks = [re.sub(r'[^a-z]', '', fold(x)) for x in str(s).split()]
    toks = [x for x in toks if x]
    return toks[-1] if toks else None
