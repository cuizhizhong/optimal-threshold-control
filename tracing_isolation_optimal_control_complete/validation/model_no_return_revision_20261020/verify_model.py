"""核对无回流计数模型的归一化、守恒与移出聚合，不调用优化器。"""

import json
from pathlib import Path

import sympy as sp


S, Sq, I, Iq, R, N = sp.symbols("S S_q I I_q R N", positive=True)
s, sq, i, iq, r = sp.symbols("s s_q i i_q r", nonnegative=True)
c, beta, q, gamma, dq, dI, gI = sp.symbols("c beta q gamma delta_q delta_I gamma_I")
counts = [
    -c * (beta + (1 - beta) * q) * S * I / N,
    beta * c * (1 - q) * S * I / N - gamma * I,
    (1 - beta) * c * q * S * I / N,
    beta * c * q * S * I / N - dq * Iq,
    gamma * I + dq * Iq,
]
normal = [
    -c * (beta + (1 - beta) * q) * s * i,
    (beta * c * (1 - q) * s - gamma) * i,
    (1 - beta) * c * q * s * i,
    beta * c * q * s * i - dq * iq,
    gamma * i + dq * iq,
]
sub = {S: N*s, Sq: N*sq, I: N*i, Iq: N*iq, R: N*r}
checks = {f"normalize_{name}": sp.simplify(flow.subs(sub)/N - expected) == 0
          for name, flow, expected in zip(("s", "i", "s_q", "i_q", "r"), counts, normal)}
checks["population_conservation"] = sp.simplify(sum(counts)) == 0
checks["aggregate_outside_si"] = sp.simplify(sum(normal[2:]) - (c*q*s*i + gamma*i)) == 0
checks["removed_flow_gamma_aggregation"] = sp.simplify(
    counts[-1].subs(gamma, dI+gI) - ((dI+gI)*I + dq*Iq)) == 0
report = {"scope": "No-return count-model normalization and algebra; not a new OCP solve",
          "checks": checks, "passed": sum(checks.values()), "total": len(checks),
          "optimizer_calls": 0, "scientific_solves": 0}
Path(__file__).with_name("model_algebra_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
