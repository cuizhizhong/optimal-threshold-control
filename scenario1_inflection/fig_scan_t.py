# 图 S：2x2，横轴为真实时间 t（天），每面板一个参数取低/中/高三条 q_c(t)。
# 曲线水平跨度 = 控制时长 dt；左右位置差来自启动时刻 t1 不同（疫情越快 t1 越早）。
import os, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.integrate import solve_ivp
from inflection_analysis import solve, trajectory
rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],'font.size':9,'axes.linewidth':0.7,'xtick.major.width':0.7,
  'ytick.major.width':0.7,'mathtext.fontset':'stix','axes.spines.top':False,'axes.spines.right':False})
def blues(n): return plt.cm.Blues(np.linspace(0.4,0.9,n))
ACC='#b2182b'
HERE=os.path.dirname(os.path.abspath(__file__))
FIG=os.path.normpath(os.path.join(HERE,'..','figures'))
base=dict(beta=0.155,gamma=0.3504,c0=10.0,q0=0.01526,eta=0.05*763,N=763.0,S0=762.0,I0=1.0)
def t1_of(p):
    b,g,c0,q0,N,S0,I0,eta=(p[k] for k in ['beta','gamma','c0','q0','N','S0','I0','eta'])
    H=b+(1-b)*q0; rhs=lambda t,y:[-(c0*H/N)*y[0]*y[1],(b*c0*(1-q0)/N)*y[0]*y[1]-g*y[1]]
    ev=lambda t,y:y[1]-eta; ev.terminal=True; ev.direction=1
    s=solve_ivp(rhs,[0,3000],[S0,I0],events=ev,rtol=1e-9,atol=1e-9,max_step=0.05)
    return s.t_events[0][0] if len(s.t_events[0]) else np.nan

# 低中高代表值
sweeps=[('beta',[0.10,0.155,0.25],r'$\beta$'),('q0',[0.02,0.15,0.30],r'$q_0$'),
        ('c0',[5,10,15],r'$c_0$'),('eta',[0.02,0.035,0.05],r'$\eta/N$')]
fig,axes=plt.subplots(2,2,figsize=(7.2,5.2))
for ax,(param,vals,plab) in zip(axes.ravel(),sweeps):
    cols=blues(len(vals))
    for v,c in zip(vals,cols):
        p=dict(base); p[param]=v*763 if param=='eta' else v
        r=solve(**p)
        if r['status']!='ok': continue
        t1=t1_of(p); t,S,qc,qd,qdd=trajectory(r,1500); tt=t+t1
        ax.plot(tt,qc,color=c,lw=1.5,label=f"{plab}$={v:g}$")
        ax.plot(tt[-1],r['q0'],'|',color=c,ms=6,mew=1.2)
        if r['has_inflection']:
            k=int(np.argmin(abs(t-r['seg_high'])))
            ax.plot(tt[k],qc[k],'o',color=ACC,ms=4.5,mec='white',mew=0.6,zorder=5)
    ax.set_ylim(0,1); ax.tick_params(labelsize=8)
    ax.legend(frameon=False,fontsize=7.5,handlelength=1.1,loc='upper right',ncol=1)
    ax.set_xlabel('$t$ (days)',fontsize=8.5); ax.set_ylabel('$q_c$',fontsize=8.5)
fig.tight_layout(pad=0.6)
fig.savefig(os.path.join(FIG,'scenario1_inflection_scan_t.pdf'),bbox_inches='tight')
print('saved ->',os.path.join(FIG,'scenario1_inflection_scan_t.pdf'))
