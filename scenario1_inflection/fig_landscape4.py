# 图 L：4 行 x 2 列拐点图谱（行 = q0, beta, c0, theta），期刊风、英文标签、蓝色渐变。
# 行序把 q0 放第一行：该行两图上方留白最多，图例（锚在第 0 行）不压数据。
import os, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.optimize import brentq
from inflection_analysis import solve
rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],
  'mathtext.fontset':'stix','font.size':9,'axes.linewidth':0.7,
  'axes.spines.top':False,'axes.spines.right':False})
C_QMAX='#08519c'; C_QINF='#4292c6'; C_Q0='#9ecae1'; FILL='#c6dbef'
C_HI='#2171b5'; C_LO='#9ecae1'
HERE=os.path.dirname(os.path.abspath(__file__))
FIG=os.path.normpath(os.path.join(HERE,'..','figures'))
base=dict(beta=0.155,gamma=0.3504,c0=10.0,q0=0.01526,eta=0.05*763,N=763.0,S0=762.0,I0=1.0)
def val(param,v):
    p=dict(base); p[param]=v*763 if param=='eta' else v; return solve(**p)
def edges(param,lo,hi):
    out=[]
    for f in [lambda v:(val(param,v)['q_inf']-val(param,v)['q_max']),
              lambda v:(val(param,v)['q_inf']-val(param,v)['q0'])]:
        vs=np.linspace(lo,hi,400)
        g=[f(v) if val(param,v)['status']=='ok' else np.nan for v in vs]
        for i in range(len(vs)-1):
            if not np.isnan(g[i]*g[i+1]) and g[i]*g[i+1]<0:
                try: out.append(brentq(f,vs[i],vs[i+1]))
                except Exception: pass
                break
    return out
# q0 行提到第一行：其左图 q_max 由 0.76 降到 0.52、右图 dt 由 6.1 降到 0.9，上方留白最多
specs=[('q0',0.0,0.39,r'$q_0$'),('beta',0.065,0.50,r'$\beta$'),
       ('c0',4.2,16,r'$c_0$'),('eta',0.0135,0.05,r'$\eta/N$')]
fig,axes=plt.subplots(4,2,figsize=(8.2,9.4))
for i,(param,lo,hi,plab) in enumerate(specs):
    aL,aR=axes[i,0],axes[i,1]
    vs=np.linspace(lo,hi,300); xs=[];qm=[];qi=[];q0v=[];hh=[];ll=[]
    for v in vs:
        r=val(param,v)
        if r['status']!='ok': continue
        xs.append(v);qm.append(r['q_max']);qi.append(r['q_inf']);q0v.append(r['q0'])
        hh.append(r['seg_high'] if r['has_inflection'] else np.nan)
        ll.append(r['seg_low'] if r['has_inflection'] else np.nan)
    xs=np.array(xs);qm=np.array(qm);qi=np.array(qi);q0v=np.array(q0v);hh=np.array(hh);ll=np.array(ll)
    inside=(qi>q0v)&(qi<qm)
    aL.fill_between(xs,q0v,qm,where=inside,color=FILL,alpha=0.6,lw=0)
    aL.plot(xs,qm,color=C_QMAX,lw=1.6); aL.plot(xs,qi,color=C_QINF,lw=1.7); aL.plot(xs,q0v,color=C_Q0,lw=1.5)
    for xv in edges(param,lo,hi): aL.axvline(xv,color='0.55',ls=(0,(2,2)),lw=0.9)
    aL.set_ylim(-0.03,1.05); aL.set_ylabel('quarantine rate',fontsize=8.5); aL.tick_params(labelsize=7.5); aL.set_xlabel(plab)
    aR.fill_between(xs,0,hh,color=C_HI,alpha=.9,lw=0)
    aR.fill_between(xs,hh,hh+ll,color=C_LO,alpha=.9,lw=0)
    aR.plot(xs,hh+ll,color='0.25',ls='--',lw=0.9)
    for xv in edges(param,lo,hi): aR.axvline(xv,color='0.55',ls=(0,(2,2)),lw=0.9)
    aR.set_ylabel('duration (days)',fontsize=8.5); aR.tick_params(labelsize=7.5); aR.set_xlabel(plab)
# 图例锚在第一行（q0 行）右上，竖排
axes[0,0].legend([plt.Line2D([],[],color=C_QMAX,lw=1.6),plt.Line2D([],[],color=C_QINF,lw=1.7),
    plt.Line2D([],[],color=C_Q0,lw=1.5)],[r'$q_{\max}$',r'$q_{\inf}$',r'$q_0$'],
    frameon=False,fontsize=7.5,loc='upper right',ncol=1,handlelength=1.3)
axes[0,1].legend([plt.Rectangle((0,0),1,1,fc=C_HI,alpha=.9),plt.Rectangle((0,0),1,1,fc=C_LO,alpha=.9),
    plt.Line2D([],[],color='0.25',ls='--',lw=.9)],[r'$t_{\rm inf}-t_1$',r'$t_2-t_{\rm inf}$',r'$\Delta t$'],
    frameon=False,fontsize=7,loc='upper right',ncol=1)
fig.tight_layout(pad=0.5)
fig.savefig(os.path.join(FIG,'scenario1_inflection_landscape.pdf'),bbox_inches='tight')
print('saved ->',os.path.join(FIG,'scenario1_inflection_landscape.pdf'))
