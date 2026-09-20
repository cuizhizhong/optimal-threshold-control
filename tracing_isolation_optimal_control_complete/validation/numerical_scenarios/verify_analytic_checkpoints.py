#!/usr/bin/env python3
"""Evaluate analytical formulas for the five planned scenarios.

This is NOT an OpenOCL run, an optimal-control NLP, or a numerical proof.
The root brackets below are intended for the fixed baseline parameters only.
Requires scipy. Run from any directory; outputs remain inside this plan bundle.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from scipy.integrate import quad
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parent
P, C, GAMMA, K = 0.5, 2.0, 0.3, 0.15
H = GAMMA / (P * C)
ELL = GAMMA / C
R = (1.0 - P) * H
PHI_A = K + H - H * math.log(H)


def phi(s: float, i: float) -> float:
    return i + s - H * math.log(s)


def a(s: float) -> float:
    return PHI_A - s + H * math.log(s)


def g(s: float) -> float:
    return (s - H) * (s - R) / s


def G(s: float) -> float:
    return a(s) - ELL * math.log(s)


def theta(s: float, i: float) -> float:
    return (s - H) / (i * (s - R))


S_K = brentq(a, H, 2.0, xtol=1e-14)
E = brentq(lambda s: a(s) - g(s), H, S_K, xtol=1e-14)


def endpoint(s: float, i: float) -> tuple[float, float]:
    if not s * math.exp(-i / ELL) < S_K:
        raise ValueError('Immediate full tracing has no positive reachable safe endpoint.')
    psi = i - ELL * math.log(s)
    z = brentq(lambda z: G(z) - psi, H, min(s, S_K), xtol=1e-14)
    j = a(z)
    if not (H < z < s and 0.0 < j < i):
        raise ValueError('Invalid positive endpoint.')
    return z, j


def D(s: float, i: float) -> float:
    z, j = endpoint(s, i)
    return theta(z, j) - theta(s, i)


S_B = brentq(lambda s: D(s, K), E + 1e-8,
             min(1.0, S_K * math.exp(K / ELL) - 1e-7), xtol=1e-14)
PHI_B = phi(S_B, K)


def waiting_time(s0: float, i0: float, s_end: float) -> float:
    if abs(s0 - s_end) < 1e-13:
        return 0.0
    label = phi(s0, i0)
    return quad(lambda s: 1.0 / (P * C * s * (label - s + H * math.log(s))),
                s_end, s0, epsabs=1e-11, epsrel=1e-11)[0]


def boundary_time(hi: float, lo: float) -> float:
    return math.log((hi - R) / (lo - R)) / (C * K)


def boundary_cost(hi: float, lo: float) -> float:
    return P / (K * (1.0 - P)) * (
        math.log(hi / lo) - P * math.log((hi - R) / (lo - R)))


def evaluate(case_id: str, s0: float, i0: float) -> dict:
    if not (s0 > 0 and 0 < i0 <= K and s0 + i0 <= 1 + 1e-14):
        raise ValueError(f'{case_id}: invalid initial condition')
    label = phi(s0, i0)
    if s0 <= H or label <= PHI_A:
        return dict(case_id=case_id, s0=s0, i0=i0, region='A',
                    J_reference=0.0, tau_wait=0.0, tau_boundary=0.0,
                    tau_full=0.0, t_release=0.0)
    tw = tb = cb = 0.0
    s_capacity = None
    if label > PHI_B:
        if abs(i0 - K) < 1e-13:
            s_capacity, region = s0, 'B'
        else:
            s_capacity = brentq(lambda s: phi(s, K) - label, H, s0, xtol=1e-14)
            region = 'W_K'
            tw = waiting_time(s0, i0, s_capacity)
        tb = boundary_time(s_capacity, S_B)
        cb = boundary_cost(s_capacity, S_B)
        s_full, i_full = S_B, K
    elif D(s0, i0) < 0:
        region, s_full, i_full = 'T', s0, i0
    else:
        region = 'W_Gamma'
        cap = brentq(lambda s: phi(s, K) - label, H, s0, xtol=1e-14)
        s_full = brentq(lambda s: D(s, label - s + H * math.log(s)),
                        cap, s0, xtol=1e-14)
        i_full = label - s_full + H * math.log(s_full)
        tw = waiting_time(s0, i0, s_full)
    sr, ir = endpoint(s_full, i_full)
    tq = math.log(i_full / ir) / GAMMA
    cost = cb + P * C * tq
    assert abs(phi(sr, ir) - PHI_A) < 1e-11
    assert abs((i_full - ELL * math.log(s_full)) - (ir - ELL * math.log(sr))) < 1e-11
    if region in ('W_Gamma', 'W_K', 'B'):
        assert abs(D(s_full, i_full)) < 1e-9
    return dict(case_id=case_id, s0=s0, i0=i0, region=region, phi0=label,
                s_capacity=s_capacity, s_full=s_full, i_full=i_full,
                s_release=sr, i_release=ir, tau_wait=tw, tau_boundary=tb,
                tau_full=tq, t_full_start=tw + tb, t_release=tw + tb + tq,
                t_natural_peak=tw + tb + tq + waiting_time(sr, ir, H),
                J_reference=cost)


def main() -> None:
    cases = [evaluate(*args) for args in [
        ('E1', .75, .01), ('E2', .99, .01), ('E3', .50, .14),
        ('E4', .70, .15), ('E5', .50, .15), ('E0', .40, .02)]]
    assert [x['region'] for x in cases] == ['W_Gamma', 'W_K', 'T', 'B', 'T', 'A']
    assert max(x['t_release'] for x in cases) < 18.0
    payload = dict(status='analytical_formula_evaluation_only', openocl_executed=False,
                   parameters=dict(p=P, c=C, gamma=GAMMA, K=K),
                   geometry=dict(h=H, ell=ELL, r=R, s_K=S_K, e=E, s_B=S_B,
                                 Phi_A=PHI_A, Phi_B=PHI_B), cases=cases)
    target = ROOT / 'analytic_checkpoints.json'
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    latex_dir = ROOT.parents[1] / 'latex'
    lines = ['% Analytical evaluations only. Not OpenOCL results.',
             '% Generated by reference_check/verify_analytic_checkpoints.py.']
    suffixes = ['One', 'Two', 'Three', 'Four', 'Five']
    for suffix, row in zip(suffixes, cases[:5]):
        lines.append(r'\providecommand{\NumJRefE' + suffix + '}{' + f"{row['J_reference']:.6f}" + '}')
    lines.extend([
        r'\providecommand{\NumSBRef}{' + f'{S_B:.8f}' + '}',
        r'\providecommand{\NumSwitchSEOneRef}{' + f"{cases[0]['s_full']:.8f}" + '}',
        r'\providecommand{\NumSwitchIEOneRef}{' + f"{cases[0]['i_full']:.8f}" + '}',
        r'\providecommand{\NumMaxReleaseRef}{' + f"{max(x['t_release'] for x in cases):.8f}" + '}',
    ])
    (latex_dir / 'numerical_reference_values.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Analytical checks passed. OpenOCL was NOT executed.')
    for row in cases:
        print(f"{row['case_id']}: {row['region']:8s} J_reference={row['J_reference']:.12f}")


if __name__ == '__main__':
    main()
