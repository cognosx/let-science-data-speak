import pandas as pd, re
app=pd.read_csv('epo_applications.csv')
t=app.title.fillna('').str.upper()
naive=t.str.contains('PHAGE')                       # the quick path: substring
word=t.str.contains(r'\b(?:BACTERIO)?PHAGES?\b|PHAGEMID|PROPHAGE|ENDOLYSIN')
app['naive_phage']=naive; app['phage']=word
tt=t.str.replace(r'BACTERIOPHAGES?','',regex=True)
cat=pd.Series('unclear from title',index=app.index)
tools=tt.str.contains(r'DISPLAY|PHAGEMID|LIBRAR|VECTOR|DETECT|ASSAY|SCREEN|DIAGNOS|SEQUENC|CLONING|EXPRESSION|PEPTIDE|ANTIBOD|CRISPR')
agri=tt.str.contains(r'FOOD|LIVESTOCK|CATTLE|DAIRY|POULTRY|SWINE|PIG|FISH|AQUACULT|ANIMAL|FEED|PLANT|CROP|AGRICUL|SANITAT|DISINFECT|DECONTAMIN|VETERIN')
ther=tt.str.contains(r'INFECTI|TREAT|THERAP|PHARMAC|PREVENT|WOUND|MEDICAL|PATIENT|DISEASE|ANTIBACTER|ANTIMICROB|ANTIBIOTIC|STAPHYLO|PSEUDOMONAS|KLEBSIELLA|ACINETOBACTER|MYCOBACTER|CLOSTRIDI|ENDOLYSIN|BIOFILM')
cat[ther]='therapy (human or unspecified)'; cat[agri]='food, agriculture, veterinary'; cat[tools]='tools, display, diagnostics'
app['use_from_title']=cat.where(word,'not phage')
app.to_csv('epo_applications_classified.csv',index=False)
ph=app[app.phage]
print('substring PHAGE',naive.sum(),' word-level',word.sum(),' false (macrophage etc.)',(naive&~word).sum())
print(ph.use_from_title.value_counts())
A=app.ipcs.str.contains('A61K35-76')
print('A61K35/76 apps',A.sum(),' phage share %.1f%%'%(100*(A&app.phage).sum()/A.sum()))
th=ph[ph.use_from_title.str.startswith('therapy')]
print('therapy apps',len(th),' outside A61K35/76',(~th.ipcs.str.contains('A61K35-76')).sum())
print(th.groupby(pd.cut(th.first_year,[1977,1999,2009,2014,2019,2026])).size())
# applicant normalisation trap
a=ph.applicants.fillna('').str.split('; ').explode()
raw=a.value_counts(); norm=a.str.lower().str.replace(r'[^a-z ]','',regex=True).str.replace(r'\s+',' ',regex=True).str.strip().value_counts()
print('distinct applicant strings',len(raw),' after normalising',len(norm)); print(norm.head(8))
# validation sample for the author
s=pd.concat([ph.sample(min(80,len(ph)),random_state=7), app[naive&~word].head(10)])
s[['app','title','applicants','first_year','use_from_title']].assign(your_label='',notes='').to_csv('validation_sample_TO_LABEL.csv',index=False)
