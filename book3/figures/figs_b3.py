import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK="#141414"; GREY="#5c5c5c"; LIGHT="#f7f5f0"; MID="#e6e3dd"; ACC="#fbe9c7"; AMB="#9a5b00"
plt.rcParams.update({"font.family":"Inter","font.size":10})
def box(ax,x,y,w,h,t,s,fc=LIGHT):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=MID,lw=1.2))
    ax.text(x+w/2,y+h*0.68,t,ha="center",va="center",fontsize=10.5,weight="bold",color=INK)
    ax.text(x+w/2,y+h*0.30,s,ha="center",va="center",fontsize=8.5,color=GREY)
def save(fig,n): fig.savefig(n,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)
# Fig 2.1 release pipeline
fig,ax=plt.subplots(figsize=(11,3.0)); ax.set_xlim(0,14.4); ax.set_ylim(0,3.9); ax.axis("off")
st=[("1. Evidence pack","verified findings,\nwith scope and caveat"),("2. AI draft","from a written brief:\n\"use only the pack\""),("3. Claim check","trace every number\nand claim to the pack"),("4. Disclosure","one line on\nhow AI was used"),("5. Release","version, date,\nlicence, link")]
w=2.45; gap=0.42
for i,(t,s) in enumerate(st):
    x=0.15+i*(w+gap); box(ax,x,0.3,w,1.9,t,s,fc=ACC if i==2 else LIGHT)
    if i<4: ax.add_patch(FancyArrowPatch((x+w,1.25),(x+w+gap,1.25),arrowstyle="-|>",mutation_scale=12,color=GREY,lw=1.2))
ax.text(0.15,3.45,"Figure 2.1. The release pipeline",fontsize=11,weight="bold",color=INK)
ax.text(0.15,3.0,"Every output goes through the same five steps. The claim check (step 3) is the one that matters most.",fontsize=9,color=GREY)
save(fig,"fig2_1_pipeline.png")
# Fig 2.2 claim check results
drafts=["Journal abstract","Policy brief","News story"]; probs=[3,6,10]
fig,ax=plt.subplots(figsize=(7.5,2.8))
ax.barh(drafts,probs,color=[MID,"#d9b98a",AMB]); 
for i,v in enumerate(probs): ax.text(v+0.2,i,f"{v}",va="center",fontsize=9.5,color=INK)
ax.set_xlim(0,12); ax.set_xlabel("Problems found by a person reading the draft")
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.grid(axis="x",color=MID); ax.set_axisbelow(True)
fig.text(0.01,1.08,"Figure 2.2. Every number was right; the words were not",fontsize=11,weight="bold",color=INK,ha="left")
fig.text(0.01,1.0,"Three AI drafts from the same verified evidence pack: 19 problems in all. The further from researchers, the more problems.",fontsize=9,color=GREY,ha="left")
save(fig,"fig2_2_claim_check.png")
print("ok")
