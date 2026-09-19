#!/usr/bin/env python3
"""Independent computational checks for the unified constant-rate manuscript.

Python >= 3.10; dependencies: numpy, scipy, sympy.
Run from any directory:
  python verify_revision.py --output results.json

This script does not import the repository's analytical solver. It checks exact
algebra and finitely many numerical states. It is NOT a proof of global
optimality, uniqueness, infinite-horizon transversality, or numerical convergence.
The analytical proofs and their quantifiers are in latex/main.tex.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import sys
from typing import Any
import numpy as np
import scipy
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq
import sympy as sp

@dataclass(frozen=True)
class Evaluation:
    region: str
    value: float
    gradient: tuple[float, float]
    wait_endpoint: tuple[float, float] | None = None

@dataclass(frozen=True)
class Model:
    p: float = 0.5
    c: float = 2.0
    gamma: float = 0.3
    K: float = 0.15

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in (self.p, self.c, self.gamma, self.K)):
            raise ValueError('All parameters must be finite.')
        if not (0 < self.p < 1 and self.c > 0 and self.gamma > 0 and 0 < self.K < 1):
            raise ValueError('Require 0<p<1, c>0, gamma>0, 0<K<1.')

    @property
    def h(self) -> float: return self.gamma / (self.p * self.c)
    @property
    def ell(self) -> float: return self.gamma / self.c
    @property
    def r(self) -> float: return (1-self.p) * self.h
    @property
    def phiA(self) -> float: return self.K + self.h - self.h*math.log(self.h)
    def phi(self, s: float, i: float) -> float: return i+s-self.h*math.log(s)
    def a(self, s: float) -> float: return self.K+self.h-s+self.h*math.log(s/self.h)
    def g(self, s: float) -> float: return (s-self.h)*(s-self.r)/s
    def theta(self, s: float, i: float) -> float: return (s-self.h)/(i*(s-self.r))
    def root(self, fun, left: float, right: float) -> float:
        return float(brentq(fun, left, right, xtol=5e-15, rtol=2e-14, maxiter=200))

    @cached_property
    def sK(self) -> float:
        hi=2*self.h+self.K+1
        while self.a(hi)>0: hi*=2
        return self.root(self.a, self.h, hi)

    @cached_property
    def e(self) -> float:
        return self.root(lambda z:self.a(z)-self.g(z), self.h, self.sK)

    def endpoint(self, s: float, i: float) -> tuple[float, float]:
        if not (s>self.h and 0<i<=self.K+1e-12 and i>self.a(s)):
            raise ValueError(f'Unsafe positive state with i<=K required: {(s,i)}')
        if math.log(s)-i/self.ell >= math.log(self.sK):
            raise ValueError('Immediate full control has no finite positive safe endpoint.')
        z=self.root(lambda z:self.a(z)-i+self.ell*math.log(s/z),
                    self.h, min(s,self.sK))
        j=self.a(z)
        if j<=0: raise ArithmeticError('Endpoint infection lost positivity at numerical precision.')
        return z,j

    def W(self, s: float, i: float) -> float:
        _,j=self.endpoint(s,i)
        return math.log(i/j)/self.h

    def gradW(self, s: float, i: float) -> tuple[float,float]:
        z,j=self.endpoint(s,i); theta=self.theta(z,j)
        return self.p*theta/s, (1/i-theta)/self.h

    def D(self, s: float, i: float) -> float:
        z,j=self.endpoint(s,i)
        return self.theta(z,j)-self.theta(s,i)

    @cached_property
    def sB(self) -> float:
        lo=self.e; hi=lo*1.2
        limit_log=math.log(self.sK)+self.K/self.ell
        for _ in range(100):
            if math.log(hi)>=limit_log:
                hi=math.exp(limit_log-1e-7)
            if self.D(hi,self.K)>0:
                return self.root(lambda s:self.D(s,self.K),lo,hi)
            hi*=1.5
        raise ArithmeticError('Could not bracket the capacity switching root.')

    @cached_property
    def zB(self) -> float: return self.endpoint(self.sB,self.K)[0]
    @cached_property
    def phiB(self) -> float: return self.phi(self.sB,self.K)

    def gamma_point(self, z: float) -> tuple[float,float]:
        """Positive switching root with the trivial root analytically removed.

        With y=log(s/z), equality of Theta reduces, after division by y, to
        a(z)*z*(1-exp(-y))/y = (z-h)*(z-r*exp(-y)).
        This avoids selecting the trivial root s=z.
        """
        if abs(z-self.e)<=2e-15: return self.e,self.a(self.e)
        if not (self.h<z<self.e): raise ValueError('Require h<z<e.')
        az=self.a(z)
        def residual(y: float) -> float:
            if y==0: return z*(az-self.g(z))
            return az*z*(-math.expm1(-y))/y-(z-self.h)*(z-self.r*math.exp(-y))
        hi=max(0.1,2*az/(z-self.h))
        while residual(hi)>0: hi*=2
        y=self.root(residual,0,hi)
        if y>700: raise OverflowError('Auxiliary switching point exceeds float range.')
        s=z*math.exp(y)
        return s,az+self.ell*y

    def gamma_hit(self, phi: float) -> tuple[float,float]:
        if not (self.phiA<phi<=self.phiB+1e-13):
            raise ValueError('This routine computes only the capacity-truncated branch.')
        if abs(phi-self.phiB)<1e-14: return self.sB,self.K
        def residual(z):
            s,i=self.gamma_point(z)
            return self.phi(s,i)-phi
        z=self.root(residual,self.zB,self.e)
        return self.gamma_point(z)

    def cap_hit(self, s: float, i: float) -> float:
        if abs(i-self.K)<1e-14: return s
        return self.root(lambda eta:i+s-eta+self.h*math.log(eta/s)-self.K,self.h,s)

    def CB(self, sa: float, sb: float) -> float:
        if sa<sb-1e-12 or sb<self.h-1e-12: raise ValueError('Require sa>=sb>=h.')
        return self.p/(self.K*(1-self.p))*(math.log(sa/sb)-self.p*math.log((sa-self.r)/(sb-self.r)))

    def evaluate(self, s: float, i: float) -> Evaluation:
        if not (s>0 and 0<i<=self.K+1e-12): raise ValueError('Outside positive capacity strip.')
        phi=self.phi(s,i)
        if s<=self.h or phi<=self.phiA:
            return Evaluation('safe',0.0,(0.0,0.0))
        if phi<=self.phiB:
            eta,j=self.gamma_hit(phi)
            if s<=eta:
                return Evaluation('tracking',self.W(s,i),self.gradW(s,i))
            grad=(self.p*(s-self.h)/(s*j*(eta-self.r)),self.p/(j*(eta-self.r)))
            return Evaluation('wait_gamma',self.W(eta,j),grad,(eta,j))
        eta=self.cap_hit(s,i); j=self.K
        grad=(self.p*(s-self.h)/(s*j*(eta-self.r)),self.p/(j*(eta-self.r)))
        reg='capacity' if abs(i-self.K)<1e-13 else 'wait_capacity'
        return Evaluation(reg,self.CB(eta,self.sB)+self.W(self.sB,self.K),grad,(eta,j))

    def fields(self,s:float,i:float):
        return np.array([-self.p*self.c*s*i,self.p*self.c*(s-self.h)*i]),np.array([-self.c*s*i,-self.gamma*i])


def exact_algebra() -> dict[str,bool]:
    s,i,p,c,h,K,eta,j,B=sp.symbols('s i p c h K eta j B',positive=True)
    r=(1-p)*h; ell=p*h
    f0=sp.Matrix([-p*c*s*i,p*c*(s-h)*i]); f1=sp.Matrix([-c*s*i,-p*c*h*i])
    Phi=i+s-h*sp.log(s); Psi=i-ell*sp.log(s)
    grad=lambda z:sp.Matrix([sp.diff(z,s),sp.diff(z,i)])
    qB=1-h/s; fb=f0+qB*(f1-f0)
    g=(s-h)*(s-r)/s; theta=(s-h)/(i*(s-r))
    w=sp.Matrix([p*B/s,(1/i-B)/h])
    wait=sp.Matrix([p*(s-h)/(s*j*(eta-r)),p/(j*(eta-r))])
    cap=wait.subs({eta:s,j:K})
    identities={
      'Phi_f0':grad(Phi).dot(f0),
      'Phi_control_direction':grad(Phi).dot(f1-f0)+c*i*(s-r),
      'Psi_f1':grad(Psi).dot(f1),
      'Psi_f0':grad(Psi).dot(f0)-p*c*i*(s-r),
      'capacity_i':fb[1],
      'capacity_s':(fb[0]+c*i*(s-r)),
      'W_H1':w.dot(f1)+p*c,
      'W_H0':w.dot(f0)-p*c*i*(s-r)*(theta-B)/h,
      'waiting_H0':wait.dot(f0),
      'waiting_Sigma':p*c+wait.dot(f1-f0)-p*c*(1-i*(s-r)/(j*(eta-r))),
      'capacity_Sigma':(p*c+cap.dot(f1-f0)).subs(i,K),
      'Lambda_natural':sp.diff(i*(s-r),s)+sp.diff(i*(s-r),i)*(h-s)/s-(i-g),
      'theta_log_q1':sp.diff(sp.log(theta),s)+sp.diff(sp.log(theta),i)*ell/s-ell*(1/((s-h)*(s-r))-1/(s*i)),
      'g_minus_I_q1':sp.diff(g,s)-ell/s-(s-h)*(s+r)/s**2,
      'gradient_match_s':w[0].subs(B,theta)-p*(s-h)/(s*i*(s-r)),
      'gradient_match_i':w[1].subs(B,theta)-p/(i*(s-r)),
      'capacity_cost_primitive':sp.diff(p/(K*(1-p))*(sp.log(s)-p*sp.log(s-r)),s)-p*(s-h)/(K*s*(s-r))
    }
    return {name:sp.simplify(expr)==0 for name,expr in identities.items()}


def candidate_integration(m:Model,s0:float,i0:float) -> dict[str,float|str]:
    ev=m.evaluate(s0,i0); state=np.array([s0,i0,0.0]); max_i=i0
    def integrate(qfun,T):
        nonlocal state,max_i
        def rhs(t,x):
            s,i,_=x;q=qfun(s)
            return [-m.c*(m.p+(1-m.p)*q)*s*i,(m.p*m.c*(1-q)*s-m.gamma)*i,m.p*m.c*q]
        sol=solve_ivp(rhs,(0,T),state,rtol=2e-11,atol=2e-13,max_step=max(1e-4,min(.05,T/30)))
        if not sol.success: raise RuntimeError(sol.message)
        state=sol.y[:,-1];max_i=max(max_i,float(sol.y[1].max()))
    if ev.region=='safe': return {'region':ev.region,'cost_error':0.0,'capacity_excess':0.0,'terminal_residual':0.0}
    if ev.region.startswith('wait_'):
        eta,j=ev.wait_endpoint
        nat=lambda s:i0+s0-s+m.h*math.log(s/s0)
        T=quad(lambda s:1/(m.p*m.c*s*nat(s)),eta,s0,epsabs=1e-11,epsrel=1e-11)[0]
        integrate(lambda s:0,T)
    if ev.region in ('wait_capacity','capacity'):
        T=math.log((state[0]-m.r)/(m.sB-m.r))/(m.c*m.K)
        integrate(lambda s:1-m.h/s,T)
    # A very small integrator capacity error is allowed for endpoint evaluation.
    z,j=m.endpoint(float(state[0]),min(float(state[1]),m.K))
    T=math.log(state[1]/j)/m.gamma
    integrate(lambda s:1,T)
    return {'region':ev.region,'cost_error':abs(float(state[2])-ev.value),
            'capacity_excess':max(0.,max_i-m.K),
            'terminal_residual':abs(m.phi(float(state[0]),float(state[1]))-m.phiA)}


def source_checks(tex:Path) -> dict[str,Any]:
    raw=tex.read_text(encoding='utf-8')
    text='\n'.join(re.sub(r'(?<!\\)%.*','',line) for line in raw.splitlines())
    labs=re.findall(r'\\label\{([^}]+)\}',text)
    refs=re.findall(r'\\(?:eqref|ref|pageref)\{([^}]+)\}',text)
    bib=(tex.parent/'references.bib').read_text(encoding='utf-8')
    keys=set(re.findall(r'@\w+\s*\{\s*([^,]+),',bib))
    cites=[]
    for match in re.findall(r'\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}',text): cites+=match.split(',')
    figs=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',text)
    return {'sha256':hashlib.sha256(raw.encode()).hexdigest(),'line_count':len(raw.splitlines()),
      'labels':len(labs),'duplicate_labels':[k for k,v in Counter(labs).items() if v>1],
      'undefined_references':sorted(set(refs)-set(labs)-{'LastPage'}),
      'missing_bibliography_keys':sorted(set(cites)-keys),
      'figure_dependencies':figs,
      'missing_local_figures':[f for f in figs if not (tex.parent.parent/'figures'/f).exists()],
      'old_geometry_assumption_reference_present':r'\ref{ass:geometry}' in text,
      'note':'Missing original figures are reported as dependencies, not replaced or fabricated.'}


def checks() -> dict[str,Any]:
    rng=np.random.default_rng(20260918)
    settings=[(.5,.3,.15),(.25,.2,.08),(.75,.2,.3),(.8,.65,.03),(.2,.08,.4),(.9,.15,.01),(.5,1.2,.15),(.4,.8,.35)]
    counts=Counter(); fd_errors=[]; Hmins=[]; negative_residuals=[]; geometry=[]; branch_signs=[]
    per_model=[]; evaluated=0
    for p,h,K in settings:
        m=Model(p=p,c=2.,gamma=p*2*h,K=K)
        local=Counter()
        for _ in range(80):
            s=float(rng.uniform(.025,.98)); imax=min(K,1-s)
            i=float(rng.uniform(max(1e-7,0.01*imax),imax))
            ev=m.evaluate(s,i);counts[ev.region]+=1;local[ev.region]+=1;evaluated+=1
            f0,f1=m.fields(s,i);grad=np.array(ev.gradient)
            H0=float(grad@f0);H1=float(grad@f1)+p*m.c
            Hmins.append(abs(min(H0,H1)))
            negative_residuals.append(max(0.,-min(H0,H1)))
            if ev.region.startswith('wait_'):branch_signs.append(H1-H0>0)
            if ev.region=='tracking':branch_signs.append(H0>0)
            eps=min(1e-6,.05*i,.05*s,.05*(K-i),.05*(1-s-i))
            if eps>2e-8:
                around=[m.evaluate(s+eps,i),m.evaluate(s-eps,i),m.evaluate(s,i+eps),m.evaluate(s,i-eps)]
                if all(a.region==ev.region for a in around):
                    num=np.array([(around[0].value-around[1].value)/(2*eps),(around[2].value-around[3].value)/(2*eps)])
                    fd_errors.append(float(np.max(abs(num-grad)/(1+abs(grad)))))
        # Boundary and full physical-mass states are additional finite samples.
        for frac in (.15,.4,.7,.95):
            s=(1-K)*frac
            for i in (K,min(K,1-s)):
                ev=m.evaluate(s,i);f0,f1=m.fields(s,i);g=np.array(ev.gradient)
                q0=max(0.,1-h/s)
                hs=[float(g@((1-q)*f0+q*f1)+p*m.c*q) for q in (q0,1.)]
                negative_residuals.append(max(0.,-min(hs)))
            s=float(rng.uniform(.05,.98));i=1-s
            if i<=K:m.evaluate(s,i)
        # Check real, capacity-truncated nontrivial switching geometry.
        for z in np.linspace(m.zB+(m.e-m.zB)*.03,m.e-(m.e-m.zB)*.03,16):
            s,i=m.gamma_point(float(z));az=m.a(float(z))
            ls=m.ell*(1/((s-m.h)*(s-m.r))-1/(s*i))
            lz=m.ell*(1/((z-m.h)*(z-m.r))-1/(z*az))
            psi_prime=(m.r-z)/z
            Fpsi=1/az-1/i-lz/psi_prime
            sigma_prime=(-Fpsi/ls)*psi_prime
            jprime=psi_prime+(m.ell/s)*sigma_prime
            slope=jprime/sigma_prime
            geometry.append(sigma_prime<0 and jprime<0 and slope>m.ell/s and i<m.g(s))
        per_model.append({'p':p,'h':h,'K':K,'sK':m.sK,'e':m.e,'sB':m.sB,'counts':dict(local)})
    m=Model();s0,i0=.99,.01;s1=m.cap_hit(s0,i0);sR,iR=m.endpoint(m.sB,m.K)
    nat=lambda s:i0+s0-s+m.h*math.log(s/s0)
    benchmark={'sK':m.sK,'e':m.e,'s1':s1,'sB':m.sB,'sR':sR,'iR':iR,
      'tau1':quad(lambda s:1/(m.p*m.c*s*nat(s)),s1,s0,epsabs=1e-12,epsrel=1e-12)[0],
      'TB':math.log((s1-m.r)/(m.sB-m.r))/(m.c*m.K),'T1':math.log(m.K/iR)/m.gamma,
      'Jstar':m.CB(s1,m.sB)+m.W(m.sB,m.K),'Jfilling':m.CB(s1,m.h),'Jdirect':m.W(s1,m.K)}
    baseline_tests=[(.99,.01),(.5,.14),(.6,m.a(.6)+1e-4),(.7,m.K),(.4,.1)]
    integration=[candidate_integration(m,s,i) for s,i in baseline_tests]
    s=.6;i=m.a(s)+1e-4;eta=m.cap_hit(s,i)
    bad_domain={'state':[s,i],'old_formula_Sigma':m.p*m.c*(1-i*(s-m.r)/(m.K*(eta-m.r))),
      'actual_region':m.evaluate(s,i).region,'cap_hit':eta,'sB':m.sB}
    safe_ui=m.p/(m.a(m.e)*(m.e-m.r))
    epss=[1e-4,1e-5,1e-6]
    safe_limits=[m.evaluate(s,m.a(s)+eps).gradient[1] for eps in epss]
    old_safe_ui=m.p/(m.a(s)*(s-m.r))
    immediate={'region':m.evaluate(.5,.14).region,'cost':m.evaluate(.5,.14).value,
      'past_gamma_s':m.gamma_hit(m.phi(.5,.14))[0]}
    algebra=exact_algebra()
    passed={
      'all_exact_identities':all(algebra.values()),
      'sampled_HJB_equation':max(Hmins)<2e-9,
      'sampled_HJB_inequality':max(negative_residuals)<2e-9,
      'sampled_strict_branch_signs':all(branch_signs),
      'sampled_gradient_finite_differences':max(fd_errors)<5e-5,
      'sampled_switching_geometry':all(geometry),
      'candidate_ODE_costs':max(float(x['cost_error']) for x in integration)<2e-8,
      'candidate_ODE_capacity':max(float(x['capacity_excess']) for x in integration)<2e-8,
      'candidate_ODE_terminal':max(float(x['terminal_residual']) for x in integration)<2e-8,
      'old_capacity_domain_regression':bad_domain['old_formula_Sigma']<0 and bad_domain['actual_region']=='wait_gamma',
      'immediate_control_regression':immediate['region']=='tracking' and immediate['past_gamma_s']>.5,
      'safe_boundary_branch_regression':abs(safe_limits[-1]-safe_ui)<.002 and abs(old_safe_ui-safe_ui)>1,
      'benchmark_cost':abs(benchmark['Jstar']-1.5295111602)<1e-9}
    return {'status':'PASS' if all(passed.values()) else 'FAIL','groups':passed,
      'exact_algebra':algebra,'sample_count':evaluated,'sample_counts':dict(counts),
      'gradient_fd_count':len(fd_errors),'max_relative_gradient_fd_error':max(fd_errors),
      'max_abs_sampled_min_H':max(Hmins),'max_negative_H_violation':max(negative_residuals),
      'geometry_sample_count':len(geometry),'models':per_model,'benchmark':benchmark,
      'candidate_ODE_checks':integration,'old_domain_regression':bad_domain,
      'safe_boundary_regression':{'correct_limit_Ui':safe_ui,'incorrect_Wi':old_safe_ui,'eps':epss,'computed_Ui':safe_limits},
      'immediate_control_regression':immediate}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('revision_results.json'))
    args=parser.parse_args()
    report:dict[str,Any]={'generated_utc':datetime.now(timezone.utc).isoformat(),
      'scope':'Computational checks only; no global proof or formal verification by this script.',
      'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sympy':sp.__version__}}
    try:
        report.update(checks())
        tex=Path(__file__).resolve().parents[1]/'latex'/'main.tex'
        if tex.exists():
            sc=source_checks(tex);report['latex_static']=sc
            if sc['duplicate_labels'] or sc['undefined_references'] or sc['missing_bibliography_keys']:
                report['status']='FAIL'
    except Exception as exc:
        report.update({'status':'ERROR','error_type':type(exc).__name__,'error':str(exc)})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
