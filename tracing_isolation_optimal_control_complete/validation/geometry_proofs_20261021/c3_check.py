"""C3 的解析恒等式与常值控制 ODE 核对；优化器、OCP 调用均为零。"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp


ROOT = Path(__file__).resolve().parent


def constants(beta, c, gamma, qbar):
    h = gamma / (beta * c)
    varpi = beta + (1 - beta) * qbar
    return h, varpi, beta * (1 - qbar) / varpi, gamma / (c * varpi)


def envelope(s, beta, c, gamma, K, qbar):
    if qbar == 1:
        return K
    h, _, _, d = constants(beta, c, gamma, qbar)
    hbar = h / (1 - qbar)
    if s <= hbar:
        return K
    z = (s - hbar) / hbar
    return K - d * (z - math.log1p(z))


def peak_max_ode(s0, i0, beta, c, gamma, qbar):
    h = gamma / (beta * c)
    if qbar < 1 and s0 > h / (1 - qbar):
        hbar = h / (1 - qbar)

        def event(t, y):
            return y[0] - hbar

        event.terminal = True
        event.direction = -1
        bound = math.log(s0 / hbar) / (beta * c * i0)
        t_end = 1.01 * bound + 1 / gamma
    else:
        event = None
        t_end = 30 / gamma

    def rhs(t, y):
        s, i = y
        return [-c * (beta + (1 - beta) * qbar) * s * i,
                (beta * c * (1 - qbar) * s - gamma) * i]

    sol = solve_ivp(rhs, [0, t_end], [s0, i0], events=event,
                    rtol=2e-12, atol=2e-14, max_step=0.25)
    assert sol.success, sol.message
    if event is not None:
        assert len(sol.t_events[0]) == 1, "理论保证的有限首次到达未在 ODE 核对中检出"
        return float(sol.y_events[0][0][1]), int(sol.nfev), float(sol.t_events[0][0])
    return float(np.max(sol.y[1])), int(sol.nfev), None


def run():
    beta, c, gamma, m, q, s, i = sp.symbols(
        "beta c gamma m q s i", positive=True)
    h = gamma / (beta * c)
    p = (1 - beta) * h
    varpi = beta + (1 - beta) * m
    nu = beta * (1 - m) / varpi
    d = gamma / (c * varpi)
    sd = -c * (beta + (1 - beta) * q) * s * i
    idot = (beta * c * (1 - q) * s - gamma) * i
    residue = sp.factor(idot + (nu - d / s) * sd
                        - beta * c * (m - q) * (s - p) * i / varpi)
    assert residue == 0
    results = {
        "scope": "C3 symbolic identities and constant-control IVP integration only",
        "optimizer_calls": 0,
        "new_ocp_solves": 0,
        "symbolic_F_derivative_residue": str(residue),
        "ode_checks": [],
        "physical_truncation_checks": [],
        "axis_checks": "i=0 and s=0 treated analytically; excluded from positive-domain formula",
    }

    # 只测试正文允许的 0<beta<1；靠近端点不等于端点推广。
    parameters = [
        ("baseline_q0", 0.5, 2.0, 0.3, 0.15, 0.0),
        ("baseline_small_q", 0.5, 2.0, 0.3, 0.15, 1e-10),
        ("baseline_q02", 0.5, 2.0, 0.3, 0.15, 0.2),
        ("baseline_q06", 0.5, 2.0, 0.3, 0.15, 0.6),
        ("physical_tangent", 0.5, 2.0, 0.3, 0.15, 1 - 0.3 / 0.85),
        ("threshold_at_one", 0.5, 2.0, 0.3, 0.15, 0.7),
        ("threshold_beyond_one", 0.5, 2.0, 0.3, 0.15, 0.8),
        ("near_full_control", 0.5, 2.0, 0.3, 0.15, 1 - 1e-10),
        ("full_control", 0.5, 2.0, 0.3, 0.15, 1.0),
        ("small_beta_no_control", 1e-8, 2.0, 0.3, 0.15, 0.0),
        ("small_beta_limited", 1e-8, 2.0, 0.3, 0.15, 0.6),
        ("near_one_beta", 1 - 1e-10, 2.0, 0.3, 0.15, 0.2),
    ]
    for name, bv, cv, gv, Kv, mv in parameters:
        hv = gv / (bv * cv)
        hm = hv / (1 - mv) if mv < 1 else None
        samples = [(0.4, min(Kv, 0.1), "interior")]
        # 抽取物理域内的曲边：不是每组参数都有实际曲边。
        if hm is not None and hm < 1:
            for sv in np.linspace(hm + 0.02 * (1 - hm), 0.999, 60):
                iv = envelope(sv, bv, cv, gv, Kv, mv)
                if 1e-4 < iv < min(Kv - 1e-6, 1 - sv - 1e-5):
                    eps = min(1e-4, iv / 100, (Kv - iv) / 4,
                              (1 - sv - iv) / 4)
                    samples.extend([(float(sv), iv - eps, "below_envelope"),
                                    (float(sv), iv, "on_envelope"),
                                    (float(sv), iv + eps, "above_envelope")])
                    break
        for sv, iv, label in samples:
            assert sv > 0 and 0 < iv <= Kv and sv + iv <= 1
            peak, nfev, hit_time = peak_max_ode(sv, iv, bv, cv, gv, mv)
            expected = iv + Kv - envelope(sv, bv, cv, gv, Kv, mv)
            error = abs(peak - expected)
            assert error < 2e-10, (name, label, error)
            results["ode_checks"].append({
                "parameter_set": name, "beta": bv, "c": cv, "gamma": gv,
                "K": Kv, "qbar": mv, "h_qbar": hm,
                "point_type": label, "s0": sv, "i0": iv,
                "analytic_peak": expected, "ode_peak": peak,
                "abs_error": error, "first_s_eq_hbar": hit_time,
                "rhs_evaluations": nfev,
            })
        if hm is not None and hm >= 1 - Kv - 1e-14:
            minimum_margin = math.inf
            for sv in np.linspace(0.001, 0.999, 500):
                upper_physical = min(Kv, 1 - float(sv))
                margin = envelope(float(sv), bv, cv, gv, Kv, mv) - upper_physical
                minimum_margin = min(minimum_margin, margin)
                assert margin >= -1e-12
            results["physical_truncation_checks"].append({
                "parameter_set": name,
                "claim": "h_qbar >= 1-K implies V_qbar = D",
                "sample_count": 500,
                "minimum_envelope_minus_physical_upper_bound": minimum_margin,
            })

    # 物理曲边取负时不应纳入任何正感染初值。
    negative_example = envelope(0.99, 0.5, 2, 0.3, 0.01, 0)
    assert negative_example < 0
    results["negative_envelope_example"] = {
        "beta": 0.5, "c": 2, "gamma": 0.3, "K": 0.01,
        "qbar": 0, "s": 0.99, "envelope": negative_example,
        "positive_infection_feasible": False,
        "disease_free_axis_still_viable": True,
    }
    results["ode_check_count"] = len(results["ode_checks"])
    results["maximum_peak_error"] = max(x["abs_error"] for x in results["ode_checks"])
    results["all_passed"] = True
    (ROOT / "c3_check_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: results[key] for key in (
        "symbolic_F_derivative_residue", "ode_check_count", "maximum_peak_error",
        "optimizer_calls", "new_ocp_solves", "all_passed")}, ensure_ascii=False))


if __name__ == "__main__":
    run()
