import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from math import log
import scan_fast as sf
from scan_fast import Cfg,S0
plt.rcParams['font.sans-serif']=['Noto Sans CJK JP','WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus']=False; plt.rcParams['font.size']=9

d=np.load('scan.npz'); ps,Ks=d['ps'],d['Ks']
reg,tau,M,G4b,sst=d['regime'],d['tau'],d['Marc'],d['G4b'],d['sstar']
sw=(reg==1)|(reg==2)
P,KK=np.meshgrid(ps,Ks); h=0.15/P; ipk=0.01+0.99-h+h*np.log(h/0.99); Kf=KK/ipk

def Dcurve(p,K,n=900):
    cf=Cfg(p,K); s1=sf.s1_of(cf)
    sb_=np.linspace(cf.h*(1+1e-9),s1,n//2,endpoint=False)
    sn_=np.linspace(s1,S0*(1-1e-9),n-n//2)
    s=np.concatenate([sb_,sn_]); iw=np.concatenate([np.full(sb_.size,cf.K),cf.inatv(sn_)])
    sbv,ok=sf.endpoint_v(cf,s,iw,n=60)
    D=cf.Th(sbv[ok],cf.av(sbv[ok]))-cf.Th(s[ok],iw[ok])
    rel=D/np.abs(cf.Th(s[ok],iw[ok]))
    return (s[ok]-cf.h)/(S0-cf.h), rel, (s1-cf.h)/(S0-cf.h), cf

fig,axs=plt.subplots(1,3,figsize=(15.5,4.5))

ax=axs[0]
cases=[(0.30,0.08),(0.50,0.15),(0.70,0.10),(0.85,0.30),(0.40,0.05),(0.60,0.25)]
for p,K in cases:
    x,y,xs1,cf=Dcurve(p,K)
    l,=ax.plot(x,y,lw=1.4,label=f'$p$={p}, $K$={K}')
    ax.plot(xs1,np.interp(xs1,x,y),'o',ms=4,color=l.get_color())
ax.axhline(0,color='k',lw=.8)
ax.set_xlabel('$(s-h)/(s_0-h)$  沿等待轨迹'); ax.set_ylabel('$D(s)/|\\Theta(s,i_{\\rm wait})|$')
ax.set_title('(a) 统一残差 $D$ 沿等待轨迹\n每条曲线恰穿零一次(由负转正)；圆点为 $s_1$')
ax.legend(fontsize=7.5); ax.grid(alpha=.3); ax.set_ylim(-1.2,1.2)

ax=axs[1]
m=sw&~np.isnan(tau)
sc=ax.scatter(Kf[m],tau[m],c=P[m],s=3,cmap='turbo')
ax.set_yscale('log'); ax.set_xlabel('$K/i_{\\rm pk}$'); ax.set_ylabel('$\\tau$')
ax.axhline(0.05,color='r',ls='--',lw=1); ax.text(0.05,0.055,'弱横截阈值 0.05',color='r',fontsize=7.5)
ax.set_title('(b) G3 横截性随容量紧度的变化\n仅在 $K\\to i_{\\rm pk}$ (控制窗口消失) 处退化')
plt.colorbar(sc,ax=ax,label='$p$'); ax.grid(alpha=.3)

ax=axs[2]
m2=sw&~np.isnan(M)
sc=ax.scatter(Kf[m2],np.maximum(M[m2],1e-9),c=P[m2],s=3,cmap='turbo')
ax.set_yscale('log'); ax.set_xlabel('$K/i_{\\rm pk}$'); ax.set_ylabel('$M$')
ax.axhline(1e-3,color='c',ls='--',lw=1)
ax.set_title('(c) G4a $q=1$ 弧裕度\n两端退化：$K\\to i_{\\rm pk}$ 与 $K\\to0$ (filling-the-box 极限)')
plt.colorbar(sc,ax=ax,label='$p$'); ax.grid(alpha=.3)

fig.tight_layout(); fig.savefig('/mnt/user-data/outputs/G3_G4_residual_slices.png',dpi=190)
print('fig2 ok')

# 最差点
print("\n=== 最差诊断点 ===")
for name,arr in [('tau',tau),('M',M),('G4b',G4b)]:
    a=np.where(sw,arr,np.nan); i=np.unravel_index(np.nanargmin(a),a.shape)
    print(f"  min {name}={a[i]:.3e} 于 p={ps[i[1]]:.3f}, K={Ks[i[0]]:.3f}, K/i_pk={Kf[i]:.4f}, "
          f"regime={'III' if reg[i]==1 else 'II'}")
print("\n=== G1 余量 ===")
g=d['G1gap'][sw]; g=g[~np.isnan(g)]
print(f"  切换点到 q=1 可达边界的相对余量: min={g.min():.4f}, 1%分位={np.percentile(g,1):.4f}, 中位={np.median(g):.3f}")
