# 图 4：单组参数三面板拐点诊断（内容与旧中文版一致，仅改期刊风）。
# (a) q_c 与首尾直线、q_inf 水平线；(b) q_c' 的极小值即拐点；(c) q_c'' 过零变号。
import os, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from inflection_analysis import solve, trajectory
rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],
  'mathtext.fontset':'stix','font.size':9,'axes.linewidth':0.7,'xtick.major.width':0.7,
  'ytick.major.width':0.7,'axes.spines.top':False,'axes.spines.right':False})
C_MAIN='#08519c'; C_QINF='#4292c6'; ACC='#b2182b'
HERE=os.path.dirname(os.path.abspath(__file__))
FIG=os.path.normpath(os.path.join(HERE,'..','figures'))
base=dict(beta=0.155,gamma=0.3504,c0=10.0,q0=0.01526,eta=0.05*763,N=763.0,S0=762.0,I0=1.0)

r=solve(**base); assert r['status']=='ok', r['status']
t,S,qc,qd,qdd=trajectory(r,3000)
ti,qinf=r['seg_high'],r['q_inf']
drop=qc[0]-r['q0']; chord=qc[0]-drop*t/r['dt']
dev=100*np.max(np.abs(qc-chord))/drop

fig,ax=plt.subplots(1,3,figsize=(7.4,2.5))
ax[0].plot(t,qc,color=C_MAIN,lw=1.6,label=r'$q_c$')
ax[0].plot([0,r['dt']],[qc[0],r['q0']],color='0.35',ls='--',lw=0.9,label='chord')
ax[0].axhline(qinf,color=C_QINF,ls=':',lw=1.2,label=r'$q_{\inf}$')
ax[0].set_ylabel(r'$q_c$',fontsize=9)
ax[0].legend(frameon=False,fontsize=7,handlelength=1.3,loc='upper right',ncol=1)

ax[1].plot(t,qd,color=C_MAIN,lw=1.6)
ax[1].set_ylabel(r"$q_c'$",fontsize=9)

ax[2].plot(t,qdd,color=C_MAIN,lw=1.6)
ax[2].axhline(0,color='0.35',lw=0.8)
ax[2].set_ylabel(r"$q_c''$",fontsize=9)

k=int(np.argmin(np.abs(t-ti)))
for i,y in enumerate((qc[k],qd[k],0.0)):
    ax[i].axvline(ti,color='0.55',ls=(0,(3,2)),lw=0.9)
    ax[i].plot(ti,y,'o',color=ACC,ms=4.5,mec='white',mew=0.6,zorder=5)
for i,lab in enumerate(('(a)','(b)','(c)')):
    ax[i].text(0.0,1.03,lab,transform=ax[i].transAxes,va='bottom',ha='left',fontsize=8.5)
    ax[i].set_xlabel('$t-t_1$ (days)',fontsize=8.5); ax[i].tick_params(labelsize=7.5)
fig.tight_layout(pad=0.5)
fig.savefig(os.path.join(FIG,'scenario1_inflection_diagnose.pdf'),bbox_inches='tight')
print(f"saved -> {os.path.join(FIG,'scenario1_inflection_diagnose.pdf')}  (chord dev={dev:.1f}%)")
