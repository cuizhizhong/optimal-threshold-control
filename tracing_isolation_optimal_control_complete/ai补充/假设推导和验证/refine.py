import numpy as np, sys
from math import log
import scan_fast as sf
from scan_fast import Cfg, S0
d=dict(np.load('scan.npz')); ps,Ks=d['ps'],d['Ks']
reg,sst,s1a=d['regime'],d['sstar'],d['s1']
G4b=np.full_like(sst,np.nan); nr2=np.full_like(sst,np.nan); Dmin2=np.full_like(sst,np.nan)
for ip,p in enumerate(ps):
    for ik,K in enumerate(Ks):
        if reg[ik,ip] not in (1,2): continue
        cf=Cfg(p,K); s1=s1a[ik,ip]; st=sst[ik,ip]
        n=2400
        sb_=np.linspace(cf.h*(1+1e-9),s1,n//2,endpoint=False)
        sn_=np.linspace(s1,S0*(1-1e-9),n-n//2)
        s=np.concatenate([sb_,sn_])
        iw=np.concatenate([np.full(sb_.size,cf.K),cf.inatv(sn_)])
        sbv,ok=sf.endpoint_v(cf,s,iw,n=60)
        ss,iws=s[ok],iw[ok]
        dd=cf.Th(sbv[ok],cf.av(sbv[ok]))-cf.Th(ss,iws)
        # 加密后的零点计数(排除 s->h 的平凡零点)
        keep=ss>cf.h+0.02*(S0-cf.h)
        nr2[ik,ip]=int((np.sign(dd[keep][:-1])*np.sign(dd[keep][1:])<0).sum())
        rel=np.abs(dd)/np.abs(cf.Th(ss,iws))
        far=keep&(np.abs(ss-st)>0.06*(ss.max()-cf.h))
        if far.sum()>5:
            G4b[ik,ip]=rel[far].min(); Dmin2[ik,ip]=np.abs(dd[far]).min()
    sys.stderr.write(f"\r{ip+1}/{len(ps)}")
d['G4b']=G4b; d['nroot_fine']=nr2
np.savez('scan.npz',**d)
sw=(reg==1)|(reg==2)
g=G4b[sw]; g=g[~np.isnan(g)]
print("\n=== 修正后 G4b (排除 s->h 平凡零点, 网格加密到 2400) ===")
print(f"  min={g.min():.3e}  0.5%分位={np.percentile(g,0.5):.3e}  1%={np.percentile(g,1):.3e}  中位={np.median(g):.4f}")
print(f"  G4b<1e-3 的点: {(g<1e-3).sum()} ({100*(g<1e-3).mean():.2f}%)")
print("\n=== 加密后零点计数 ===")
v,c=np.unique(nr2[sw][~np.isnan(nr2[sw])],return_counts=True)
for a,b in zip(v,c): print(f"  零点数={int(a)}: {b} 点 ({100*b/c.sum():.2f}%)")
