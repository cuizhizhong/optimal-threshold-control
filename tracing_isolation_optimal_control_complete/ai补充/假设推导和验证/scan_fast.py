import numpy as np, math
from math import log, exp

C, GAM, S0, I0 = 2.0, 0.3, 0.99, 0.01

class Cfg:
    __slots__=('p','K','h','ell','r','A0')
    def __init__(self,p,K):
        self.p,self.K=p,K
        self.h=GAM/(p*C); self.ell=GAM/C; self.r=(1-p)*self.h
        self.A0=K+self.h-self.h*log(self.h)
    def a(self,s):    return self.A0-s+self.h*log(s)
    def av(self,s):   return self.A0-s+self.h*np.log(s)
    def inat(self,s): return I0+S0-s+self.h*log(s/S0)
    def inatv(self,s):return I0+S0-s+self.h*np.log(s/S0)
    def Th(self,s,i): return (s-self.h)/(i*(s-self.r))

# ---------- 标量端点映射 ----------
def endpoint(cf,s,i,n=64):
    h,ell=cf.h,cf.ell
    if s<=h or i<=cf.a(s): return None
    x0=s*exp(-i/ell)
    if x0>h and cf.a(x0)<0: return None          # G1: 特征线够不到安全集
    Psi=i-ell*log(s); lo,hi=h,s
    for _ in range(n):
        m=0.5*(lo+hi)
        if cf.a(m)-ell*log(m)-Psi>0: lo=m
        else: hi=m
    sb=0.5*(lo+hi)
    return sb if (cf.a(sb)>0 and h<sb<s) else None

# ---------- 向量端点映射(用于网格扫描) ----------
def endpoint_v(cf,s,i,n=56):
    h,ell=cf.h,cf.ell
    x0=s*np.exp(-i/ell)
    ok=(x0<=h)|(cf.av(np.maximum(x0,1e-12))>=0)
    ok&=(s>h)&(i>cf.av(s))
    Psi=i-ell*np.log(s); lo=np.full_like(s,h); hi=s.copy()
    for _ in range(n):
        m=0.5*(lo+hi)
        pos=cf.av(m)-ell*np.log(m)-Psi>0
        lo=np.where(pos,m,lo); hi=np.where(pos,hi,m)
    sb=0.5*(lo+hi)
    ok&=(cf.av(sb)>0)&(sb>h)&(sb<s)
    return sb,ok

def s1_of(cf):
    h=cf.h
    if S0<=h: return None
    if I0+S0-h+h*log(h/S0)<=cf.K: return None
    lo,hi=h,S0
    for _ in range(80):
        m=0.5*(lo+hi)
        if cf.inat(m)-cf.K>0: lo=m
        else: hi=m
    return 0.5*(lo+hi)

def iwait(cf,s1,s): return cf.K if s<=s1 else cf.inat(s)

def Dscal(cf,s1,s):
    i=iwait(cf,s1,s); sb=endpoint(cf,s,i)
    if sb is None: return None
    return cf.Th(sb,cf.a(sb))-cf.Th(s,i)

def CB(cf,hi,lo):
    p,K,r=cf.p,cf.K,cf.r
    return p/(K*(1-p))*(log(hi/lo)-p*log((hi-r)/(lo-r)))
