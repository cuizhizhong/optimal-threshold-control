"""Regenerate all CSV data used by the ten figures and the LaTeX report.

Usage
-----
    python generate_data.py
    python generate_data.py --recompute-tv

The default command regenerates all constant-contact analytical data and keeps
the included time-varying direct-transcription data.  The optional flag reruns
the three small regularized optimizations for the contact-surge experiment.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import csv
import numpy as np
from scipy.optimize import brentq
from common_tracing import (
    Params, natural_peak, optimize_constant_c, simulate_optimal,
    switching_curve, perturbation_cost_curve, q1_cost, natural_i,
    optimize_time_varying, simulate_piecewise_q, contact_time_varying,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)


def write_summary(par: Params) -> None:
    sol = optimize_constant_c(par)
    _, ipk = natural_peak(par)
    rows = [
        ('p', par.p), ('c', par.c), ('gamma', par.gamma), ('K', par.K),
        ('s0', par.s0), ('i0', par.i0), ('h', par.h), ('r', par.r),
        ('ell', par.ell), ('natural_peak', ipk),
    ]
    for key in ['regime','s1','s_switch','i_switch','s_release','i_release',
                'tau1','tau_boundary','tau_q1','cost','fill_box_cost',
                'direct_cost','boundary_cost_total']:
        rows.append((key, sol[key]))
    with (DATA / 'numerical_summary.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['quantity','value']); w.writerows(rows)

    tr = simulate_optimal(par, t_end=18, n=1801)
    arr = np.column_stack([tr['t'], tr['s'], tr['i'], tr['q'], tr['beta1'], tr['beta2']])
    np.savetxt(DATA / 'constant_c_optimal_trajectory.csv', arr, delimiter=',',
               header='time,s,i,q,beta1,beta2', comments='')

    sw_s, sw_i, te_s, te_i = switching_curve(par, s_max=par.s0, n=260)
    np.savetxt(DATA / 'switching_curve.csv', np.column_stack([sw_s,sw_i,te_s,te_i]),
               delimiter=',', header='switch_s,switch_i,terminal_s,terminal_i', comments='')

    grid, vals, _ = perturbation_cost_curve(par, n=500)
    np.savetxt(DATA / 'boundary_switch_cost_curve.csv', np.column_stack([grid,vals]),
               delimiter=',', header='switch_s,total_cost', comments='')

    s1 = float(sol['s1'])
    full_at_capacity = q1_cost(s1, par.K, par)[0]
    s_early = brentq(lambda x: natural_i(x, par)-0.10, par.h, par.s0)
    full_early = q1_cost(s_early, 0.10, par)[0]
    rows2 = [
        ('Optimal', float(sol['cost'])),
        ('Pure fill-the-box', float(sol['fill_box_cost'])),
        ('Full isolation at capacity', float(full_at_capacity)),
        ('Full isolation at i=0.10', float(full_early)),
    ]
    with (DATA / 'strategy_cost_comparison.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['strategy','cost']); w.writerows(rows2)


def write_sensitivity(base: Params) -> None:
    _, ipk = natural_peak(base)
    Ks = np.linspace(0.055, ipk*1.03, 58)
    out=[]
    for K in Ks:
        K=max(float(K),base.i0*1.02)
        par=Params(p=base.p,c=base.c,gamma=base.gamma,K=K,s0=base.s0,i0=base.i0)
        sol=optimize_constant_c(par)
        out.append((K,float(sol['cost']),float(sol['fill_box_cost']),str(sol['regime'])))
    with (DATA/'capacity_sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['K','optimal_cost','fill_box_cost','regime']);w.writerows(out)

    rows=[]
    for p in np.linspace(0.24,0.84,50):
        par=Params(p=float(p),c=2.0,gamma=0.3,K=0.15,s0=0.99,i0=0.01)
        _,peak=natural_peak(par)
        if peak<=par.K or par.s0<=par.h:
            continue
        sol=optimize_constant_c(par)
        jf=float(sol['fill_box_cost']);jo=float(sol['cost'])
        if jf>1e-10:
            rows.append((p,100*(jf-jo)/jf,jo,jf,str(sol['regime'])))
    with (DATA/'probability_sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['p','saving_percent','optimal_cost','fill_box_cost','regime']);w.writerows(rows)

    ps=np.linspace(0.25,0.85,28); Ks2=np.linspace(0.06,0.30,27)
    rows=[]; mapping={'safe':0,'direct-q1':1,'capacity-q1':2,'fill-box':3}
    for K in Ks2:
        for p in ps:
            try:
                par=Params(p=float(p),c=2.0,gamma=0.3,K=float(K),s0=0.99,i0=0.01)
                sol=optimize_constant_c(par)
                rows.append((p,K,mapping[str(sol['regime'])],str(sol['regime'])))
            except Exception:
                rows.append((p,K,np.nan,'failed'))
    with (DATA/'regime_map_long.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['p','K','regime_code','regime']);w.writerows(rows)


def write_time_varying(par: Params) -> None:
    T=18.0; n=48
    configs=[(0.10,0.008),(0.04,0.006),(0.015,0.004)]
    sols=[]
    for eps,smooth in configs:
        sol=optimize_time_varying(par,T=T,n=n,eps=eps,smooth=smooth,maxiter=500)
        if not sol['success']:
            raise RuntimeError(f'time-varying optimization failed for eps={eps}: {sol["message"]}')
        sols.append(sol)
    times=sols[0]['times']; c=sols[0]['c']
    qnodes=[np.r_[np.asarray(sol['q']),np.asarray(sol['q'])[-1]] for sol in sols]
    np.savetxt(DATA/'time_varying_multi_eps.csv',np.column_stack([times,c,*qnodes]),delimiter=',',
               header='time,c,q_eps_0p10,q_eps_0p04,q_eps_0p015',comments='')
    sol=sols[1]; qnode=np.r_[sol['q'],sol['q'][-1]]
    np.savetxt(DATA/'time_varying_regularized_solution.csv',
               np.column_stack([times,c,sol['states'][:,0],sol['states'][:,1],qnode]),delimiter=',',
               header='time,c,s,i,q_piecewise',comments='')
    no=simulate_piecewise_q(np.zeros(n),times,par,lambda t: float(contact_time_varying(t,par.c)))
    np.savetxt(DATA/'time_varying_no_control.csv',np.column_stack([times,no[:,0],no[:,1]]),delimiter=',',
               header='time,s_no,i_no',comments='')
    with (DATA/'time_varying_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['quantity','value'])
        w.writerow(['success',sol['success']]);w.writerow(['message',sol['message']])
        w.writerow(['objective',sol['objective']]);w.writerow(['max_i',sol['states'][:,1].max()])
        w.writerow(['eps',sol['eps']]);w.writerow(['smooth',sol['smooth']])


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--recompute-tv',action='store_true',help='rerun the time-varying direct-transcription experiments')
    args=parser.parse_args()
    par=Params()
    write_summary(par)
    write_sensitivity(par)
    if args.recompute_tv:
        write_time_varying(par)
    print(DATA)

if __name__=='__main__':
    main()
