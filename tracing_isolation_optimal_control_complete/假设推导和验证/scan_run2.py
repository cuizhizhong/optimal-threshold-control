import numpy as np, sys
from math import log
import scan_fast as sf
from scan_fast import Cfg, S0, I0

NP=NK=100
ps=np.linspace(0.16,0.95,NP); Ks=np.linspace(0.02,0.42,NK)
keys=['regime','nroot','sstar','tau','Marc','G4b','G1frac','G1gap',
      'cost','fillbox','s1','sexist','arclen']
F={k:np.full((NK,NP),np.nan) for k in keys}

for ip,p in enumerate(ps):
    for ik,K in enumerate(Ks):
        cf=Cfg(p,K); s1=sf.s1_of(cf)
        if s1 is None: F['regime'][ik,ip]=0; continue
        F['s1'][ik,ip]=s1
        n=500
        sb_=np.linspace(cf.h*(1+1e-9),s1,n//2,endpoint=False)
        sn_=np.linspace(s1,S0*(1-1e-9),n-n//2)
        s=np.concatenate([sb_,sn_])
        iw=np.concatenate([np.full(sb_.size,cf.K),cf.inatv(sn_)])
        sbv,ok=sf.endpoint_v(cf,s,iw)
        F['G1frac'][ik,ip]=ok.mean()
        if ok.sum()<20: F['regime'][ik,ip]=-1; continue
        ss,iws=s[ok],iw[ok]
        dd=cf.Th(sbv[ok],cf.av(sbv[ok]))-cf.Th(ss,iws)
        F['sexist'][ik,ip]=ss.max()
        cr=np.where(np.sign(dd[:-1])*np.sign(dd[1:])<0)[0]
        F['nroot'][ik,ip]=len(cr)
        if len(cr)==0:
            F['regime'][ik,ip]=3 if dd[-1]<0 else -2; continue
        k=cr[-1]; lo,hi=ss[k],ss[k+1]; slo=np.sign(dd[k])
        for _ in range(70):
            m=0.5*(lo+hi); dm=sf.Dscal(cf,s1,m)
            if dm is None or np.sign(dm)==slo: lo=m
            else: hi=m
        sst=0.5*(lo+hi); F['sstar'][ik,ip]=sst
        F['regime'][ik,ip]=2 if sst>s1 else 1
        eps=1e-5*max(sst-cf.h,1e-3)
        Dp,Dm=sf.Dscal(cf,s1,sst+eps),sf.Dscal(cf,s1,sst-eps)
        if Dp is not None and Dm is not None:
            F['tau'][ik,ip]=sst*((Dp-Dm)/(2*eps))/abs(cf.Th(sst,sf.iwait(cf,s1,sst)))
        iwst=sf.iwait(cf,s1,sst); sbst=sf.endpoint(cf,sst,iwst)
        if sbst is not None and sbst<sst:
            xs=np.linspace(sbst,sst,240); ii=cf.a(sbst)+cf.ell*np.log(xs/sbst)
            Te=cf.Th(sbst,cf.a(sbst))
            F['Marc'][ik,ip]=(cf.Th(xs,ii).max()-Te)/abs(Te)
            F['arclen'][ik,ip]=(sst-sbst)/(S0-cf.h)
            W=(1/cf.h)*log(iwst/cf.a(sbst))
            F['cost'][ik,ip]=(sf.CB(cf,s1,sst)+W) if sst<=s1 else W
        rel=np.abs(dd)/np.abs(cf.Th(ss,iws))
        far=np.abs(ss-sst)>0.06*(ss.max()-cf.h)
        if far.sum()>5: F['G4b'][ik,ip]=rel[far].min()
        F['G1gap'][ik,ip]=(ss.max()-sst)/(S0-cf.h)
        hf=cf.h*(1+1e-9); sbf=sf.endpoint(cf,hf,cf.K)
        if sbf is not None:
            F['fillbox'][ik,ip]=sf.CB(cf,s1,hf)+(1/cf.h)*log(cf.K/cf.a(sbf))
    sys.stderr.write(f"\r{ip+1}/{NP}")
np.savez('scan.npz',ps=ps,Ks=Ks,**F)
sys.stderr.write("\ndone\n")
