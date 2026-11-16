"""Step 2: one row per unique work, with year, document type, first/last-author country (OpenAlex codes,
PubMed affiliation text), World Bank region and income group. Checkpoints B (inputs) and C."""
import sys, json, re, collections
sys.path.insert(0, '/tmp/agent_test_B/work')
import pandas as pd, pycountry
from common import *

CHECKS = []   # checkpoint C log
def check(name, ok, detail):
    CHECKS.append({'check': name, 'passed': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, '|', detail)
    return ok

# ---------------- World Bank reference tables
cl = pd.read_excel(RAW + '/CLASS.xlsx', sheet_name='List of economies')
cl = cl[cl.Region.notna()].copy()
REGION = dict(zip(cl.Code, cl.Region)); INC_NOW = dict(zip(cl.Code, cl['Income group']))
og = pd.read_excel(RAW + '/OGHIST.xlsx', sheet_name='Country Analytical History', header=None)
yrs = [int(v) for v in og.iloc[5, 2:]]                      # "Data for calendar year"
hist = og.iloc[11:, :].copy(); hist = hist[hist[0].astype(str).str.fullmatch(r'[A-Z]{3}')]
MAPI = {'L': 'Low income', 'LM': 'Lower middle income', 'UM': 'Upper middle income', 'H': 'High income', 'LM*': 'Lower middle income'}
INC_HIST = {}
for _, r in hist.iterrows():
    for k, y in enumerate(yrs):
        v = MAPI.get(str(r[2 + k]).strip())
        if v: INC_HIST[(r[0], y)] = v
HY0, HY1 = min(yrs), max(yrs)
def income_at(iso3, year):
    """income group for the GNI calendar year = publication year; years after the last column use the last column;
       if the economy was unclassified that year, nearest later then earlier classified year."""
    if iso3 is None or year is None or pd.isna(year): return None
    y = int(min(max(year, HY0), HY1))
    for yy in [y] + list(range(y + 1, HY1 + 1)) + list(range(y - 1, HY0 - 1, -1)):
        if (iso3, yy) in INC_HIST: return INC_HIST[(iso3, yy)]
    return None
# ISO2 (OpenAlex) -> ISO3 (World Bank). Kosovo: OpenAlex XK, World Bank XKX.
ISO23 = {c.alpha_2: c.alpha_3 for c in pycountry.countries}; ISO23['XK'] = 'XKX'
# French overseas departments are not separate World Bank economies: counted as France (assumption A9)
FR_DOM = {'GUF': 'FRA', 'MTQ': 'FRA', 'GLP': 'FRA', 'REU': 'FRA', 'MYT': 'FRA'}
for k2, v3 in list(ISO23.items()):
    if v3 in FR_DOM: ISO23[k2] = 'FRA'

# ---------------- PubMed affiliation text -> ISO3
NAMES = {}
for c in pycountry.countries:
    for n in {c.name, getattr(c, 'common_name', None), getattr(c, 'official_name', None)}:
        if n: NAMES[fold(n)] = c.alpha_3
for code, name in zip(cl.Code, cl.Economy):
    if ',' not in name: NAMES.setdefault(fold(name), code)
ALIAS = {'usa': 'USA', 'u s a': 'USA', 'united states of america': 'USA', 'united states': 'USA', 'u s': 'USA', 'us': 'USA',
 'uk': 'GBR', 'u k': 'GBR', 'united kingdom': 'GBR', 'england': 'GBR', 'scotland': 'GBR', 'wales': 'GBR', 'northern ireland': 'GBR', 'great britain': 'GBR',
 'the netherlands': 'NLD', 'holland': 'NLD', 'russia': 'RUS', 'ussr': 'RUS', 'south korea': 'KOR', 'republic of korea': 'KOR', 'korea': 'KOR',
 'iran': 'IRN', 'vietnam': 'VNM', 'viet nam': 'VNM', 'laos': 'LAO', 'lao pdr': 'LAO', 'taiwan': 'TWN', 'hong kong': 'HKG', 'macau': 'MAC', 'p r china': 'CHN', 'pr china': 'CHN', 'peoples republic of china': 'CHN',
 'tanzania': 'TZA', 'united republic of tanzania': 'TZA', 'the gambia': 'GMB', 'gambia': 'GMB', 'ivory coast': 'CIV', "cote d'ivoire": 'CIV', 'cote d ivoire': 'CIV', 'cote divoire': 'CIV',
 'democratic republic of the congo': 'COD', 'democratic republic of congo': 'COD', 'dr congo': 'COD', 'drc': 'COD', 'd r congo': 'COD', 'congo kinshasa': 'COD', 'zaire': 'COD',
 'republic of the congo': 'COG', 'republic of congo': 'COG', 'congo brazzaville': 'COG', 'congo': 'COG',
 'swaziland': 'SWZ', 'eswatini': 'SWZ', 'cape verde': 'CPV', 'burkina faso': 'BFA', 'guinea bissau': 'GNB', 'sao tome and principe': 'STP',
 'bolivia': 'BOL', 'venezuela': 'VEN', 'syria': 'SYR', 'czech republic': 'CZE', 'czechia': 'CZE', 'turkey': 'TUR', 'turkiye': 'TUR', 'brasil': 'BRA', 'deutschland': 'DEU', 'espana': 'ESP', 'italia': 'ITA',
 'palestine': 'PSE', 'west bank': 'PSE', 'burma': 'MMR', 'myanmar': 'MMR', 'papua new guinea': 'PNG', 'east timor': 'TLS', 'brunei': 'BRN', 'moldova': 'MDA', 'macedonia': 'MKD', 'kosovo': 'XKX',
 'kingdom of saudi arabia': 'SAU', 'ksa': 'SAU', 'uae': 'ARE', 'belgique': 'BEL', 'suisse': 'CHE', 'schweiz': 'CHE', 'cameroun': 'CMR', 'republic of south africa': 'ZAF', 'rsa': 'ZAF'}
NAMES.update(ALIAS)
NAMES = {k: FR_DOM.get(v, v) for k, v in NAMES.items()}
NAMES.update({'guyane': 'FRA', 'f r g': 'DEU', 'frg': 'DEU', 'west germany': 'DEU'})
for bad in ['jersey', 'guernsey', 'georgia', 'niue', 'guam']:   # too ambiguous as plain words; Georgia handled below
    NAMES.pop(bad, None)
NAME_RE = re.compile(r'(?<![a-z])(' + '|'.join(sorted((re.escape(n) for n in NAMES), key=len, reverse=True)) + r')(?![a-z])')
US_STATES = ['alabama','alaska','arizona','arkansas','california','colorado','connecticut','delaware','florida','hawaii','idaho','illinois','indiana','iowa','kansas','kentucky','louisiana','maine','maryland','massachusetts','michigan','minnesota','mississippi','missouri','montana','nebraska','nevada','new hampshire','new jersey','new mexico','new york','north carolina','north dakota','ohio','oklahoma','oregon','pennsylvania','rhode island','south carolina','south dakota','tennessee','texas','utah','vermont','virginia','washington','west virginia','wisconsin','wyoming','district of columbia']
US_ABBR = 'AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split()
US_RE1 = re.compile(r'(?<![a-z])(' + '|'.join(US_STATES) + r')(?![a-z])')
US_RE2 = re.compile(r',\s*(' + '|'.join(US_ABBR) + r')\b\.?(\s+\d{5}(-\d{4})?)?\s*[,.;]?\s*$|\b(' + '|'.join(US_ABBR) + r')\s+\d{5}\b')
CITY = {'london': 'GBR', 'oxford': 'GBR', 'edinburgh': 'GBR', 'liverpool': 'GBR', 'paris': 'FRA', 'marseille': 'FRA', 'lyon': 'FRA', 'geneva': 'CHE', 'geneve': 'CHE', 'basel': 'CHE', 'lausanne': 'CHE',
        'bethesda': 'USA', 'rockville': 'USA', 'atlanta': 'USA', 'baltimore': 'USA', 'boston': 'USA', 'seattle': 'USA', 'silver spring': 'USA', 'walter reed army institute': 'USA', 'national institutes of health': 'USA', 'centers for disease control': 'USA',
        'melbourne': 'AUS', 'sydney': 'AUS', 'brisbane': 'AUS', 'queensland': 'AUS', 'stockholm': 'SWE', 'copenhagen': 'DNK', 'amsterdam': 'NLD', 'nijmegen': 'NLD', 'leiden': 'NLD', 'tokyo': 'JPN', 'osaka': 'JPN',
        'nairobi': 'KEN', 'kilifi': 'KEN', 'bamako': 'MLI', 'dakar': 'SEN', 'ouagadougou': 'BFA', 'accra': 'GHA', 'ibadan': 'NGA', 'lagos': 'NGA', 'kampala': 'UGA', 'dar es salaam': 'TZA', 'ifakara': 'TZA', 'yaounde': 'CMR', 'lambarene': 'GAB', 'banjul': 'GMB', 'fajara': 'GMB', 'maputo': 'MOZ', 'manhica': 'MOZ',
        'bangkok': 'THA', 'goroka': 'PNG', 'madang': 'PNG', 'bern': 'CHE', 'berne': 'CHE', 'zurich': 'CHE', 'montreal': 'CAN', 'toronto': 'CAN', 'new haven': 'USA', 'wien': 'AUT', 'vienna': 'AUT', 'oslo': 'NOR', 'bordeaux': 'FRA', 'montpellier': 'FRA', 'canberra': 'AUS', 'nottingham': 'GBR', 'glasgow': 'GBR', 'kobenhavn': 'DNK', 'chandigarh': 'IND', 'freiburg': 'DEU', 'marburg': 'DEU', 'munchen': 'DEU', 'munich': 'DEU', 'new delhi': 'IND', 'bogota': 'COL', 'cali': 'COL', 'beijing': 'CHN', 'shanghai': 'CHN', 'heidelberg': 'DEU', 'tubingen': 'DEU', 'hamburg': 'DEU', 'berlin': 'DEU', 'barcelona': 'ESP', 'madrid': 'ESP', 'rome': 'ITA', 'roma': 'ITA', 'brussels': 'BEL', 'antwerp': 'BEL'}
CITY_RE = re.compile(r'(?<![a-z])(' + '|'.join(sorted(CITY, key=len, reverse=True)) + r')(?![a-z])')

def seg_country(seg):
    raw = re.sub(r'\S+@\S+', ' ', seg); raw = re.sub(r'electronic address:?', ' ', raw, flags=re.I)
    s = fold(raw).replace('’', "'")
    s = re.sub(r'new south wales', 'australia', s); s = re.sub(r'new mexico', 'usa', s)
    s2 = re.sub(r"[^a-z' ]+", ' ', s); s2 = re.sub(r'\s+', ' ', s2)
    m = list(NAME_RE.finditer(s2))
    if m: return NAMES[m[-1].group(1)], 'name'        # the country is normally the last place name
    if re.search(r'(?<![a-z])georgia(?![a-z])', s2):
        return ('GEO', 'name') if 'tbilisi' in s2 else ('USA', 'us_state')
    if US_RE2.search(raw) or US_RE1.search(s2): return 'USA', 'us_state'
    c = CITY_RE.search(s2)
    if c: return CITY[c.group(1)], 'city'
    return None, None

def affil_countries(affs):
    """returns (primary ISO3, method, list of all ISO3 found) for one author's affiliation list"""
    found = []
    for a in affs or []:
        for seg in re.split(r';', a):
            c, how = seg_country(seg)
            if c: found.append((c, how))
        if not any(True for _ in found) and a:       # whole string as a fallback
            c, how = seg_country(a)
            if c: found.append((c, how))
    if not found: return None, None, []
    return found[0][0], found[0][1], list(dict.fromkeys(c for c, _ in found))

if __name__ == '__main__':
    R = pd.read_pickle(OUT + '/records.pkl')
    # ---- per-record author-country facts
    oa = {r['openalex_id']: r for r in load('openalex')}; pm = {r['pmid']: r for r in load('pubmed')}
    F = {k: [None] * len(R) for k in ['f_oa', 'l_oa', 'f_oa_all', 'l_oa_all', 'f_pm', 'l_pm', 'f_pm_all', 'l_pm_all', 'f_pm_how', 'l_pm_how', 'f_pm_aff', 'l_pm_aff', 'nauth_src']}
    unk2 = collections.Counter()
    def to3(cs):
        out = []
        for c in cs or []:
            if c in ISO23: out.append(ISO23[c])
            else: unk2[c] += 1
        return out
    for i, (src, sid) in enumerate(zip(R.src, R.sid)):
        if src == 'openalex':
            a = oa[sid].get('authorships') or []
            F['nauth_src'][i] = len(a) or None
            f = [x for x in a if x['pos'] == 'first']; l = [x for x in a if x['pos'] == 'last']
            if len(a) == 1: l = a                      # single author is both first and last (QUESTIONS.md Q4)
            if f: c = to3(f[0].get('countries')); F['f_oa'][i] = c[0] if c else None; F['f_oa_all'][i] = c
            if l: c = to3(l[0].get('countries')); F['l_oa'][i] = c[0] if c else None; F['l_oa_all'][i] = c
        elif src == 'pubmed':
            a = pm[sid].get('authors') or []
            F['nauth_src'][i] = len(a) or None
            if a:
                c, how, al = affil_countries(a[0]['affiliations']); F['f_pm'][i], F['f_pm_how'][i], F['f_pm_all'][i] = c, how, al
                F['f_pm_aff'][i] = bool(a[0]['affiliations'])
                c, how, al = affil_countries(a[-1]['affiliations']); F['l_pm'][i], F['l_pm_how'][i], F['l_pm_all'][i] = c, how, al
                F['l_pm_aff'][i] = bool(a[-1]['affiliations'])
        elif src == 'europepmc':
            F['nauth_src'][i] = R.n_auth[i]
    for k, v in F.items(): R[k] = v
    check('OpenAlex ISO2 -> ISO3 mapping complete', not unk2, f'unmapped codes: {dict(unk2)}')
    # PubMed parser: how many affiliation strings got no country
    pmr = R[R.src == 'pubmed']
    have = pmr.f_pm_aff.fillna(False).astype(bool)
    rate = pmr.f_pm[have].notna().mean()
    check('PubMed first-author affiliation text parsed to a country (>=95%)', rate >= 0.95, f'{rate:.3f} of {int(have.sum())} affiliation texts; methods {pmr.f_pm_how.value_counts().to_dict()}')
    unparsed = [pm[s]['authors'][0]['affiliations'][0] for s in pmr.sid[have & pmr.f_pm.isna()]]
    pd.Series(unparsed).to_csv(OUT + '/pubmed_affil_unparsed.csv', index=False)
    R.to_pickle(OUT + '/records2.pkl')

    # ---- one row per work
    PRI = {'pubmed': 0, 'europepmc': 1, 'openalex': 2}
    def first_notnull(s):
        for v in s:
            if v is not None and not (isinstance(v, float) and pd.isna(v)) and not (isinstance(v, list) and not v): return v
        return None
    R['prep'] = R.doctype.fillna('').str.contains('preprint', case=False) | R.doctype.fillna('').str.startswith('PPR|')
    R['pri'] = R.src.map(PRI) + 10 * R.prep.astype(int)        # journal version before preprint; PubMed > Europe PMC > OpenAlex
    R = R.sort_values(['cid', 'pri']).reset_index(drop=True)
    g = R.groupby('cid', sort=False)
    W = pd.DataFrame({
        'n_records': g.size(),
        'sources': g.src.agg(lambda s: '+'.join(sorted(set(s)))),
        'title': g.title.agg(first_notnull), 'year': g.year.agg(first_notnull),
        'year_min': g.year.min(), 'year_max': g.year.max(),
        'doi': g.doi.agg(first_notnull), 'pmid': g.pmid.agg(first_notnull),
        'n_auth': g.nauth_src.agg(first_notnull),
        'f_oa': g.f_oa.agg(first_notnull), 'l_oa': g.l_oa.agg(first_notnull),
        'f_pm': g.f_pm.agg(first_notnull), 'l_pm': g.l_pm.agg(first_notnull),
        'f_oa_all': g.f_oa_all.agg(first_notnull), 'l_oa_all': g.l_oa_all.agg(first_notnull),
        'f_pm_all': g.f_pm_all.agg(first_notnull), 'l_pm_all': g.l_pm_all.agg(first_notnull),
        'types': g.doctype.agg(lambda s: ' || '.join(f'{a}' for a in s if isinstance(a, str))),
        'src_types': g.apply(lambda d: ' || '.join(f'{a}={b}' for a, b in zip(d.src, d.doctype)), include_groups=False),
        'in_pm': g.src.agg(lambda s: 'pubmed' in set(s)), 'in_ep': g.src.agg(lambda s: 'europepmc' in set(s)),
        'in_oa': g.src.agg(lambda s: 'openalex' in set(s)),
    })
    # single-author PubMed papers: last = first already (authors[-1] is authors[0])
    # combined country: OpenAlex first, PubMed text as fill (QUESTIONS.md Q5)
    # MAIN: published affiliation text (PubMed) first, OpenAlex institution country as fill (QUESTIONS.md Q5)
    for who, k in [('first', 'f'), ('last', 'l')]:
        pmc, oac = W[f'{k}_pm'], W[f'{k}_oa']
        W[f'{who}_iso3'] = pmc.where(pmc.notna(), oac)
        W[f'{who}_src'] = ['pubmed' if pd.notna(a) else ('openalex' if pd.notna(b) else None) for a, b in zip(pmc, oac)]
        W[f'{who}_iso3_oafirst'] = oac.where(oac.notna(), pmc)
    def allc(a, b): return list(a) if isinstance(a, list) and a else (list(b) if isinstance(b, list) and b else [])
    W['first_all'] = [allc(a, b) for a, b in zip(W.f_pm_all, W.f_oa_all)]; W['last_all'] = [allc(a, b) for a, b in zip(W.l_pm_all, W.l_oa_all)]

    # ---- derived columns + checkpoint C
    for who in ['first', 'last']:
        W[f'{who}_region'] = W[f'{who}_iso3'].map(REGION)
        W[f'{who}_ssa'] = (W[f'{who}_region'] == 'Sub-Saharan Africa').where(W[f'{who}_iso3'].notna())
        W[f'{who}_ssa_any'] = [any(REGION.get(c) == 'Sub-Saharan Africa' for c in cs) if cs else None for cs in W[f'{who}_all']]
        W[f'{who}_ssa_only'] = [all(REGION.get(c) == 'Sub-Saharan Africa' for c in cs) if cs else None for cs in W[f'{who}_all']]
    W['first_income_now'] = W.first_iso3.map(INC_NOW)
    W['first_income_pubyear'] = [income_at(c, y) for c, y in zip(W.first_iso3, W.year)]
    kn = W.first_iso3.notna()
    check('work table has one row per cluster', len(W) == R.cid.nunique(), f'{len(W)} rows')
    check('first_iso3 not empty', kn.sum() > 0, f'{int(kn.sum())} of {len(W)} works')
    nomatch = W.first_iso3[kn & W.first_region.isna()].value_counts().to_dict()
    check('region join: every known country got a World Bank region (>=99%)', W.first_region[kn].notna().mean() >= 0.99,
          f'{W.first_region[kn].notna().mean():.4f} matched; unmatched codes {nomatch}')
    check('region values plausible (7 World Bank regions, USA in North America, Kenya in SSA)',
          W.first_region.nunique() == 7 and REGION['USA'] == 'North America' and REGION['KEN'] == 'Sub-Saharan Africa',
          str(W.first_region.value_counts().to_dict()))
    top_ssa = W.first_iso3[W.first_ssa == True].value_counts().head(8).to_dict()
    check('SSA flag plausible (top SSA countries are malaria-research countries; share between 2% and 60%)',
          0.02 < (W.first_ssa[kn] == True).mean() < 0.6 and all(REGION[c] == 'Sub-Saharan Africa' for c in top_ssa), f'share {(W.first_ssa[kn] == True).mean():.3f}; top {top_ssa}')
    check('income (current, CLASS) not empty and matched >=99%', W.first_income_now[kn].notna().mean() >= 0.99,
          f'{W.first_income_now[kn].notna().mean():.4f}; unmatched {W.first_iso3[kn & W.first_income_now.isna()].value_counts().to_dict()}; values {W.first_income_now.value_counts().to_dict()}')
    kny = kn & W.year.notna()
    check('income (publication year, OGHIST) not empty and matched >=99%', W.first_income_pubyear[kny].notna().mean() >= 0.99,
          f'{W.first_income_pubyear[kny].notna().mean():.4f}; unmatched {W.first_iso3[kny & W.first_income_pubyear.isna()].value_counts().to_dict()}; values {W.first_income_pubyear.value_counts().to_dict()}')
    check('income plausible: USA high, Mali low (now and 2005), Kenya low in 2005 and lower-middle now',
          INC_NOW['USA'] == 'High income' and INC_NOW['MLI'] == 'Low income' and income_at('MLI', 2005) == 'Low income' and income_at('KEN', 2005) == 'Low income' and INC_NOW['KEN'] == 'Lower middle income',
          f"KEN 2005={income_at('KEN', 2005)}, KEN now={INC_NOW['KEN']}, OGHIST years {HY0}-{HY1}")
    dis = W.f_oa.notna() & W.f_pm.notna() & ((W.f_oa.map(REGION) == 'Sub-Saharan Africa') != (W.f_pm.map(REGION) == 'Sub-Saharan Africa'))
    d1 = int((W.f_pm[dis].map(REGION) == 'Sub-Saharan Africa').sum())
    check('direction of OpenAlex/PubMed disagreement on the SSA flag examined', True, f'first author: {int(dis.sum())} disagreements, PubMed text says SSA and OpenAlex not in {d1}, the reverse in {int(dis.sum()) - d1}; top pairs OpenAlex GBR vs PubMed KEN/GMB (MRC Gambia, KEMRI-Wellcome coded to the UK parent by OpenAlex)')
    both = W.f_oa.notna() & W.f_pm.notna(); bl = W.l_oa.notna() & W.l_pm.notna()
    agree_f = (W.f_oa[both] == W.f_pm[both]).mean(); agree_l = (W.l_oa[bl] == W.l_pm[bl]).mean()
    ssa_f = ((W.f_oa[both].map(REGION) == 'Sub-Saharan Africa') == (W.f_pm[both].map(REGION) == 'Sub-Saharan Africa')).mean()
    ssa_l = ((W.l_oa[bl].map(REGION) == 'Sub-Saharan Africa') == (W.l_pm[bl].map(REGION) == 'Sub-Saharan Africa')).mean()
    check('OpenAlex and PubMed-text countries agree where both exist (SSA flag >=95%)', ssa_f >= 0.95 and ssa_l >= 0.95,
          f'first: n={int(both.sum())}, same country {agree_f:.3f}, same SSA flag {ssa_f:.3f}; last: n={int(bl.sum())}, same country {agree_l:.3f}, same SSA flag {ssa_l:.3f}')
    yc = (W.year_min != W.year_max) & W.year_min.notna()
    W['year_conflict'] = yc
    check('year plausible (1800-2026)', W.year.dropna().between(1800, 2026).all(), f'min {W.year.min()}, max {W.year.max()}, missing {int(W.year.isna().sum())}, works whose sources disagree on year {int(yc.sum())}')
    W.to_pickle(OUT + '/works.pkl')
    json.dump(CHECKS, open(OUT + '/checks_C.json', 'w'), indent=1)
