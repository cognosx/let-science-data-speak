"""Step 5: extra checks added to results.json: bounds for unknown countries (B/D), topic split
(vaccine acceptance/implementation vs other), narrow windows and 2020-24 vs 2025-26 (E), file log (H)."""
import sys, json, math, hashlib, os, re, datetime
sys.path.insert(0, '/tmp/agent_test_B/work')
import pandas as pd
from common import *
RES = json.load(open(BASE + '/results.json'))
P = pd.read_csv(OUT + '/papers_2000_2026.csv', low_memory=False)
for c in ['first_ssa', 'last_ssa']: P[c] = P[c].map({True: True, False: False, 'True': True, 'False': False})
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * max(0, c - h), 1), round(100 * min(1, c + h), 1)]
def sh(d, col):
    kn = d[col].notna(); k = int((d[col] == True).sum()); n = int(kn.sum())
    return {'k': k, 'n': n, 'pct': round(100 * k / n, 1) if n else None, 'ci95': wilson(k, n) if n else None, 'known_share': round(float(kn.mean()), 3) if len(d) else None}
X = {}
# bounds: all unknown non-SSA (floor) and all unknown SSA (ceiling)
X['bounds_unknown_country'] = {}
for per, d in P.groupby('per'):
    X['bounds_unknown_country'][per] = {w: {'floor_pct': round(100 * (d[f'{w}_ssa'] == True).sum() / len(d), 1),
        'ceiling_pct': round(100 * ((d[f'{w}_ssa'] == True).sum() + d[f'{w}_ssa'].isna().sum()) / len(d), 1)} for w in ['first', 'last']}
# topic split by title words
ACC = re.compile(r'accept|uptake|hesitan|willing|knowledge|attitude|perception|readiness|roll-?out|introduc|implementation|coverage|caregiver|mothers|community', re.I)
P['acceptance_topic'] = P.title.fillna('').map(lambda t: bool(ACC.search(t)))
X['topic_split'] = {}
for per, d in P.groupby('per'):
    X['topic_split'][per] = {'share_of_papers_acceptance_implementation': round(float(d.acceptance_topic.mean()), 3),
        'acceptance_implementation': {w: sh(d[d.acceptance_topic], f'{w}_ssa') for w in ['first', 'last']},
        'other_topics': {w: sh(d[~d.acceptance_topic], f'{w}_ssa') for w in ['first', 'last']},
        'other_topics_keyword_screened': {w: sh(d[~d.acceptance_topic & d.topic_screen], f'{w}_ssa') for w in ['first', 'last']}}
# sub-periods inside 2020-2026 and narrow windows
X['subperiods'] = {}
for a, b in [(2020, 2022), (2023, 2024), (2025, 2026), (2020, 2024), (2008, 2016), (2008, 2012), (2013, 2016)]:
    d = P[(P.year >= a) & (P.year <= b)]
    X['subperiods'][f'{a}-{b}'] = {w: sh(d, f'{w}_ssa') for w in ['first', 'last']} | {'papers': int(len(d)), 'openalex_only_share': round(float((d.sources == 'openalex').mean()), 3)}
def trend(d, col):
    d = d[[ 'year', col]].dropna(); f = (d[col] == True).astype(float); y = d.year; p = f.mean()
    z = ((y - y.mean()) * f).sum() / math.sqrt(p * (1 - p) * ((y - y.mean()) ** 2).sum())
    return {'z': round(z, 2), 'p': float(f'{math.erfc(abs(z) / math.sqrt(2)):.2g}'), 'n': int(len(d))}
X['narrow_window_trends'] = {f'{w}_{a}-{b}': trend(P[(P.year >= a) & (P.year <= b)], f'{w}_ssa') for w in ['first', 'last'] for a, b in [(2008, 2016), (2005, 2015), (2010, 2019), (2010, 2022), (2000, 2019)]}
# file log
X['files'] = {}
for f in sorted(os.listdir(RAW)):
    p = RAW + '/' + f; h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    X['files'][f] = {'bytes': os.path.getsize(p), 'sha256': h, 'mtime_utc': datetime.datetime.utcfromtimestamp(os.path.getmtime(p)).isoformat(timespec='seconds'),
                     'lines': sum(1 for _ in open(p, 'rb')) if f.endswith('.jsonl') else None}
og = pd.read_excel(RAW + '/OGHIST.xlsx', sheet_name='Parameters', header=None)
X['oghist_parameters_sheet'] = dict(zip(og[0].astype(str), og[1].astype(str)))
RES['extra'] = X
json.dump(RES, open(BASE + '/results.json', 'w'), indent=1, default=str)
print(json.dumps(X, indent=0, default=str))
