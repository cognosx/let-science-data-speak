import re, time, requests, pandas as pd
d=pd.read_csv('corpus_new_species.csv')
R={
 'temperature': r'(\d{1,2}(?:\.\d)?\s*(?:-|–|to)?\s*\d{0,2}\s*°\s*C)',
 'atmosphere': r'\b(strictly anaerob\w*|anaerob\w*|aerob\w*|facultative\w*|microaerophil\w*|capnophil\w*|5\s*% ?CO2|CO2)',
 'medium': r'(blood agar|sheep blood|horse blood|columbia|chocolate agar|brain heart infusion|BHI|trypticase soy|tryptic soy|TSA|YCFA|Schaedler|Wilkins|fastidious anaerobe agar|marine agar|R2A|nutrient agar|Middlebrook|L[oö]wenstein)',
 'specimen': r'(sputum|bronchoalveolar|BAL fluid|nasopharyn\w*|oropharyn\w*|cystic fibrosis|tracheal aspirate|pleural|lung)',
}
def extract(text):
    out={}
    for k,p in R.items():
        m=re.findall(p,text if isinstance(text,str) else '',flags=re.I)
        out[k]='; '.join(sorted({x.strip().lower() if isinstance(x,str) else x[0] for x in m}))[:200]
    return out
ab=pd.DataFrame([extract(a) for a in d.abstract]).add_prefix('abs_')
# open full texts from Europe PMC
ft=[]
for pmc in d.pmcid:
    txt=''
    if isinstance(pmc,str):
        r=requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML',timeout=60)
        if r.ok: txt=re.sub(r'<[^>]+>',' ',r.text)
        time.sleep(0.3)
    ft.append(extract(txt) if txt else {k:None for k in R}); 
ftd=pd.DataFrame(ft).add_prefix('full_')
out=pd.concat([d[['pmid','year','journal','title','pmcid']].reset_index(drop=True),ab,ftd],axis=1)
out['has_fulltext']=out.full_temperature.notna()
out.to_csv('growth_conditions_extracted.csv',index=False)
cov=lambda s:(s.fillna('')!='').mean()*100
print('papers',len(out),' with open full text',out.has_fulltext.sum())
for k in R: print(f"{k:12s} abstract {cov(out['abs_'+k]):5.1f}%   full text (open subset) {cov(out.loc[out.has_fulltext,'full_'+k]):5.1f}%   abstract on same subset {cov(out.loc[out.has_fulltext,'abs_'+k]):5.1f}%")
