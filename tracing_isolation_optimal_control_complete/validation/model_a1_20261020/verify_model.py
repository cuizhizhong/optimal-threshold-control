"""A1 的独立代数核对；不积分、不调用优化器，不替代命题证明。"""

import json
from pathlib import Path

import sympy as sp


s, sq, i, iq, q, beta, c, gamma, dq, lam, dI, gI, K = sp.symbols(
    "s s_q i i_q q beta c gamma delta_q lambda delta_I gamma_I K")
sd = -c * (beta + (1 - beta) * q) * s * i + lam * sq
id_ = beta * c * (1 - q) * s * i - gamma * i
sqd = (1 - beta) * c * q * s * i - lam * sq
iqd = beta * c * q * s * i - dq * iq
rd = gamma * i + dq * iq
h = gamma / (beta * c)
Phi = i + s - h * sp.log(s)
Phi_A = K + h - h * sp.log(h)
peak = i + s - h - h * sp.log(s / h)


def equal(left, right):
    return sp.simplify(sp.expand_log(left - right, force=True)) == 0


checks = {
    "five_compartment_population_conservation": equal(sd + id_ + sqd + iqd + rd, 0),
    "removed_flow_aggregation_gamma": equal(rd.subs(gamma, dI + gI),
                                           (dI + gI) * i + dq * iq),
    "outside_2d_projection_flow": equal(sqd + iqd + rd, c * q * s * i + gamma * i - lam * sq),
    "total_susceptible_flow": equal(sd + sqd, -beta * c * s * i),
    "lambda_zero_s_projection": equal(sd.subs(lam, 0), -c * (beta + (1 - beta) * q) * s * i),
    "lambda_zero_i_projection": equal(id_, (beta * c * (1 - q) * s - gamma) * i),
    "positive_infection_peak_invariant_for_s_above_h": equal(
        sp.diff(peak, s) * sd.subs({q: 0, lam: 0}) + sp.diff(peak, i) * id_.subs(q, 0), 0),
    "positive_infection_safe_set_equivalence_for_s_above_h": equal(peak - K, Phi - Phi_A),
}
report = {
    "scope": "A1 independent symbolic identities, not a new scientific solve",
    "conditions": "0<beta<1; c,gamma,delta_q>0; lambda>=0; positive s,i for the peak formula; P0(s,0)=0 separately",
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "optimizer_calls": 0,
    "scientific_solves": 0,
}
out = Path(__file__).resolve().parent / "model_algebra_report.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
