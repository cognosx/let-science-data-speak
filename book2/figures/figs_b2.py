import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
INK="#141414"; GREY="#5c5c5c"; MID="#e6e3dd"; AMB="#9a5b00"; BLUE="#2F64B5"; NEU="#9a9890"
plt.rcParams.update({"font.family":"Inter","font.size":10,"axes.edgecolor":GREY,"axes.labelcolor":INK,"xtick.color":GREY,"ytick.color":GREY,
 "axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":MID,"grid.linewidth":0.8,"axes.axisbelow":True})
def head(fig,t,s):
    fig.text(0.01,1.04,t,fontsize=11,weight="bold",color=INK,ha="left"); fig.text(0.01,0.985,s,fontsize=9,color=GREY,ha="left")
def save(fig,n): fig.savefig(n,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)

# Fig 3.1 deduplication
steps=[("Records from three databases",47817),("Non-articles set aside",-4610),("Pass 1a: same PMID",-22867),("Pass 1b: same DOI",-379),
       ("Pass 2: same title, year, author",-271),("Pass 3: near-identical title",-268),("Unique works",19422)]
fig,ax=plt.subplots(figsize=(8,3.8)); run=0
for i,(lab,v) in enumerate(steps):
    y=len(steps)-1-i
    if i==0: ax.barh(y,v,color=NEU); run=v; txt=f"{v:,}"
    elif i==len(steps)-1: ax.barh(y,v,color=AMB); txt=f"{v:,}"
    else: ax.barh(y,v,left=run+v,color="#c9c6bf"); run+=v; txt=f"−{-v:,}"
    ax.text((run if i not in (0,len(steps)-1) else v)+400, y, txt, va="center", fontsize=9, color=INK)
ax.set_yticks(range(len(steps))); ax.set_yticklabels([s[0] for s in steps][::-1]); ax.set_xlim(0,54000)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x,_:f"{int(x):,}")); ax.grid(axis="y",visible=False)
head(fig,"Figure 3.1. From 47,817 records to 19,422 works","PubMed, Europe PMC and OpenAlex exports of 10 November 2026; each bar is what one step removed.")
save(fig,"fig3_1_dedup.png")

# Fig 7.1 start year
per=["2000–09","2010–14","2015–19","2020–22","2023–26"]; fa=[62,57,52,57,62]; la=[45,47,39,47,53]
fig,ax=plt.subplots(figsize=(8,3.6))
ax.axvspan(1.5,4.5,color="#fbe9c7",alpha=0.6,lw=0); ax.text(3,69,"What a 2015 start shows",ha="center",fontsize=8.5,color=AMB)
ax.plot(per,fa,marker="o",color=AMB,lw=2,label="First author in the region"); ax.plot(per,la,marker="o",color=BLUE,lw=2,label="Last author in the region")
for x,y in zip(per,fa): ax.text(x,y+1.6,f"{y}%",ha="center",fontsize=8.5,color=AMB)
for x,y in zip(per,la): ax.text(x,y-3.6,f"{y}%",ha="center",fontsize=8.5,color=BLUE)
ax.set_ylim(30,72); ax.set_ylabel("Share of papers (%)"); ax.legend(frameon=False,loc="lower left",fontsize=8.5)
head(fig,"Figure 7.1. The start year changes the story","Papers with at least one author in sub-Saharan Africa (OpenAlex countries). From 2015: a rise. From 2000: a dip and a recovery.")
save(fig,"fig7_1_start_year.png")

# Fig 8.1 shares with intervals
P=["2000–2009","2010–2019","2020–2026"]; s=[8.1,10.1,20.0]; lo=[7.0,9.2,18.5]; hi=[9.2,11.1,21.4]; n=[2423,3704,3060]
fig,ax=plt.subplots(figsize=(7,3.4))
ax.errorbar(P,s,yerr=[np.array(s)-lo,np.array(hi)-s],fmt="o",color=AMB,ecolor=AMB,elinewidth=2,capsize=6,markersize=7)
for i,(v,l,h,k) in enumerate(zip(s,lo,hi,n)): ax.annotate(f"{v}%  ({l}–{h})\n{k:,} papers",(i,v),xytext=(12,0),textcoords="offset points",ha="left",va="center",fontsize=8.5,color=INK)
ax.set_xlim(-0.4,2.7)
ax.set_ylim(0,28); ax.set_ylabel("First author in sub-Saharan Africa (%)")
head(fig,"Figure 8.1. The doubling is larger than its uncertainty","All PubMed papers with a known first-author country; 95% bootstrap intervals that do not overlap.")
save(fig,"fig8_1_share_intervals.png")

# Fig 8.2 interrupted time series
g=pd.read_csv("/home/claude/book/repo/book2/data/checks/annual_first_author_2010_2025.csv")
pre=g[g.year<=2021]
fig,axs=plt.subplots(1,2,figsize=(9,3.5),sharex=True)
for ax,col,c,t in [(axs[0],"ssa",AMB,"Led from sub-Saharan Africa"),(axs[1],"other",NEU,"Led from elsewhere")]:
    m=smf.glm(f"{col}~t",pre,family=sm.families.Poisson()).fit()
    ax.plot(g.year,g[col],"o",color=c,ms=5,label="Papers per year")
    ax.plot(pre.year,m.predict(pre),"-",color=GREY,lw=1.2,label="Trend 2010–2021")
    ax.plot(g.year[g.year>=2021],m.predict(g[g.year>=2021]),"--",color=GREY,lw=1.2,label="Same trend, extended")
    ax.set_xticks([2010,2013,2016,2019,2022,2025])
    ax.axvline(2021.75,color=INK,lw=0.8); ax.set_title(t,fontsize=10,color=INK,loc="left")
    ax.set_ylim(0,None)
for ax in axs: ax.text(2021.6,8,"WHO recommendation,\nOctober 2021",fontsize=7.5,ha="right",va="bottom",color=INK)
axs[0].set_ylabel("Papers per year"); axs[0].legend(frameon=False,fontsize=7.5,loc="upper left")
head(fig,"Figure 8.2. African-led output grew faster than its earlier trend after 2021","2022–2025: 364 African-led papers against about 278 expected; other papers 4% below their trend. A fit, not proof of cause (T36).")
save(fig,"fig8_2_its.png")

# Fig 12.1 agent runs
runs=["Reference (Chapter 8)","Run A, short brief","Run B, with checkpoints"]; vals=[[8.1,10.1,20.0],[9.3,10.7,25.5],[7.7,10.2,22.1]]; cols=[INK,"#c9c6bf",AMB]
x=np.arange(3); w=0.26
fig,ax=plt.subplots(figsize=(8,3.5))
for i,(r,v,c) in enumerate(zip(runs,vals,cols)):
    b=ax.bar(x+(i-1)*w,v,w,color=c,label=r)
    for xi,vi in zip(x+(i-1)*w,v): ax.text(xi,vi+0.4,f"{vi}",ha="center",fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(["2000–09","2010–19","2020–26"]); ax.set_ylabel("First author in sub-Saharan Africa (%)")
ax.legend(frameon=False,fontsize=8.5,loc="upper left"); ax.grid(axis="x",visible=False)
head(fig,"Figure 12.1. Both agents got the direction right; the short brief overshot","Share of papers with a first author in sub-Saharan Africa, from the same raw data of 10 November 2026.")
save(fig,"fig12_1_agents.png")
print("ok")
