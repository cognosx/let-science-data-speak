import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK="#141414"; GREY="#5c5c5c"; LIGHT="#f7f5f0"; MID="#e6e3dd"; ACC="#fbe9c7"; AMB="#9a5b00"
plt.rcParams.update({"font.family":"Inter","font.size":10})
def box(ax,x,y,w,h,t,s="",fc=LIGHT,ts=10.5,ss=8.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=MID,lw=1.2))
    if s:
        ax.text(x+w/2,y+h*0.66,t,ha="center",va="center",fontsize=ts,weight="bold",color=INK)
        ax.text(x+w/2,y+h*0.30,s,ha="center",va="center",fontsize=ss,color=GREY)
    else: ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=ts,weight="bold",color=INK)
def arrow(ax,a,b): ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=11,color=GREY,lw=1.1))
def title(ax,x,y,t,s): ax.text(x,y,t,fontsize=11,weight="bold",color=INK); ax.text(x,y-0.18,s,fontsize=9,color=GREY,va="top")
def save(fig,n): fig.savefig(n,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)

# Fig 1.1 portfolio map
fig,ax=plt.subplots(figsize=(10,6.0)); ax.set_xlim(0,13); ax.set_ylim(0,8.2); ax.axis("off")
title(ax,0.1,7.9,"Figure 1.1. One topic, many outputs","Every output draws on the same evidence pack. Chapter numbers show where each one is covered.")
box(ax,4.9,2.9,3.2,1.5,"Evidence pack","cleaned data, main tables,\nmethods, limitations",fc=ACC)
groups=[("Researchers",[("Research question","Ch 3"),("Article","Ch 4"),("Dataset and code","Ch 5")],0.1,4.4),
        ("Decision-makers and funders",[("Policy brief","Ch 6"),("Portfolio review","Ch 6"),("Foresight brief","Ch 7")],9.0,4.4),
        ("Industry",[("Landscape report","Ch 8"),("Watch bulletin","Ch 8")],9.0,0.45),
        ("The public and learners",[("Press summary","Ch 9"),("Course or workshop","Ch 10")],0.1,0.45)]
for g,items,x,y in groups:
    ax.text(x,y+len(items)*0.72+0.15,g,fontsize=9.5,weight="bold",color=AMB)
    for i,(t,c) in enumerate(items):
        yy=y+(len(items)-1-i)*0.72; box(ax,x,yy,3.9,0.6,f"{t}  ·  {c}",ts=9.2)
    cx=x+3.9 if x<5 else x; cy=y+len(items)*0.36
    arrow(ax,(6.5+(-1.6 if x<5 else 1.6),3.65+(0.5 if y>2 else -0.5)),(cx,cy))
save(fig,"fig1_1_portfolio.png")

# Fig 3.1 eight questions
q=["1. Search good\nenough?","2. Registered, not\nyet published?","3. In\npreprints?","4. In theses\nor reports?","5. Under another\nname?","6. In a recent\nreview?","7. Do experts\nagree?","8. Does it\nmatter?"]
fig,ax=plt.subplots(figsize=(10,4.3)); ax.set_xlim(0,13); ax.set_ylim(0,5.6); ax.axis("off")
title(ax,0.1,5.3,"Figure 3.1. From an empty cell to a gap you can claim","A candidate gap must survive all eight questions. Most do not, and that is the point of asking.")
box(ax,0.1,1.9,2.1,1.3,"Candidate gap","an empty cell\nin your map")
for i,t in enumerate(q):
    r,c=divmod(i,4); x=2.9+c*2.05; y=2.75-r*1.2
    box(ax,x,y,1.9,0.95,t,ts=8.6,fc=LIGHT)
arrow(ax,(2.2,2.55),(2.88,2.55))
box(ax,11.2,1.9,1.7,1.3,"Gap to claim","narrow and\ntestable",fc=ACC)
arrow(ax,(11.08,2.55),(11.2,2.55))
ax.text(7.0,0.15,"If any answer finds the work already done, go back to your map: the cell was not empty.",ha="center",fontsize=8.8,color=GREY,style="italic")
save(fig,"fig3_1_eight_questions.png")

# Fig 6.1 the one chart in the brief
per=["2000–2009","2010–2019","2020–2026"]; v=[8.1,10.1,20.0]; lo=[7.0,9.2,18.5]; hi=[9.2,11.1,21.4]; n=["2,423","3,704","3,060"]
fig,ax=plt.subplots(figsize=(7.5,3.4))
ax.bar(per,v,color=[MID,MID,AMB],width=0.55)
ax.errorbar(range(3),v,yerr=[[a-b for a,b in zip(v,lo)],[b-a for a,b in zip(v,hi)]],fmt="none",ecolor=INK,capsize=5,lw=1.1)
for i in range(3): ax.text(i,hi[i]+0.8,f"{v[i]:.1f}%",ha="center",fontsize=10,weight="bold",color=INK); ax.text(i,0.8,f"{n[i]} papers",ha="center",fontsize=8,color=INK if i<2 else "white")
ax.set_ylim(0,25); ax.set_ylabel("Share with a first author\nin sub-Saharan Africa (%)")
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.grid(axis="y",color=MID); ax.set_axisbelow(True)
fig.text(0.01,1.1,"Figure 6.1. One chart, one message: the field baseline",fontsize=11,weight="bold",color=INK,ha="left")
fig.text(0.01,1.02,"Malaria vaccine papers with a known first-author country. Lines show 95% intervals. Source: Book 2, Chapter 8.",fontsize=9,color=GREY,ha="left")
save(fig,"fig6_1_brief_chart.png")

# Fig 7.1 scenario matrix
fig,ax=plt.subplots(figsize=(9,6.4)); ax.set_xlim(0,12); ax.set_ylim(0,9.0); ax.axis("off")
title(ax,0.1,8.75,"Figure 7.1. Four futures for malaria vaccine research in Africa, 2035","Two drivers from Book 2, crossed. No quadrant is a prediction; the indicators show which one is taking shape.\nThe shaded future is written out in full in the text.")
sc=[("Led but stretched","African teams lead, but depend\non a few funders",1.6,4.0,ACC),("Shared lead","African-led work funded from\nmany sources",6.8,4.0,LIGHT),
    ("Stalled","few funders, leadership abroad,\nresearchers leave",1.6,0.9,LIGHT),("Funded from outside","money is plentiful, but studies\nare done in, not by, the region",6.8,0.9,LIGHT)]
for t,s,x,y,fc in sc: box(ax,x,y,4.9,2.8,t,s,fc=fc,ts=11.5,ss=9)
ax.text(0.55,3.6,"African-led research capacity",rotation=90,ha="center",va="center",fontsize=9.5,weight="bold",color=AMB)
ax.text(1.0,5.4,"strong",rotation=90,ha="center",va="center",fontsize=8.5,color=GREY); ax.text(1.0,2.3,"weak",rotation=90,ha="center",va="center",fontsize=8.5,color=GREY)
ax.text(6.75,0.45,"Funding outlook",ha="center",fontsize=9.5,weight="bold",color=AMB)
ax.text(4.05,0.45,"narrow",ha="center",fontsize=8.5,color=GREY); ax.text(9.25,0.45,"broad",ha="center",fontsize=8.5,color=GREY)
ax.text(1.6,7.45,"Baselines to watch: first-author share 20.0% (2020–2026) · five main funders 49% of funded papers (2021–2025)\n· cohort based only abroad 10% (2023–2025)",fontsize=8.3,color=INK,va="top")
save(fig,"fig7_1_scenarios.png")

# Fig 8.1 bulletin cycle
st=[("1. Fix the searches","patents, trials, papers,\neach with its date"),("2. Compare","with last month:\nonly what changed"),("3. Sort","by what matters\nto the reader"),
    ("4. Draft with AI","from the list only,\nsource and date per line"),("5. Claim check","a filing is not a product;\nremove \"breakthrough\""),("6. Send","on a fixed day, even\nwhen nothing changed")]
fig,ax=plt.subplots(figsize=(10.5,4.4)); ax.set_xlim(0,13.6); ax.set_ylim(0,5.7); ax.axis("off")
title(ax,0.1,5.4,"Figure 8.1. The monthly technology watch bulletin","The landscape's searches, rerun every month. Only the changes are reported.")
w=3.9;h=1.5
pos=[(0.2,2.6),(4.85,2.6),(9.5,2.6),(9.5,0.4),(4.85,0.4),(0.2,0.4)]
for i,((t,s),(x,y)) in enumerate(zip(st,pos)): box(ax,x,y,w,h,t,s,fc=ACC if i==4 else LIGHT)
arrow(ax,(4.1,3.35),(4.85,3.35)); arrow(ax,(8.75,3.35),(9.5,3.35)); arrow(ax,(11.45,2.6),(11.45,1.9))
arrow(ax,(9.5,1.15),(8.75,1.15)); arrow(ax,(4.85,1.15),(4.1,1.15)); arrow(ax,(2.15,1.9),(2.15,2.6))
ax.text(0.35,2.15,"next month",fontsize=8,color=GREY,style="italic")
save(fig,"fig8_1_bulletin.png")
print("ok")
