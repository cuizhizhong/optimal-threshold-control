"""核对机制节的微分恒等式，并解析扫描 E2 容量退出成本。

仅使用 SymPy 恒等化简、解析成本、标量方程求根和一维数值积分。
密集网格扫描与 Brent 求根均不是控制优化，不调用优化器、MATLAB、ODE 或 OCP。
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.optimize import brentq
import sympy as sp


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
INPUT = PROJECT / "validation/numerical_scenarios/scenario_inputs.json"
CHECKPOINT = PROJECT / "validation/numerical_scenarios/analytic_checkpoints.json"
BASELINE_CHECKS = PROJECT / "validation/figure1_layout_20261021/analytic_checks.json"
OUTPUT = HERE / "mechanism_checks.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbolic_checks() -> dict:
    s, i, h, p, ell, beta = sp.symbols("s i h p ell beta", positive=True)
    end_theta, integral, K = sp.symbols("Theta_end integral_kappa K", real=True)
    g = (s - h) * (s - p) / s
    theta = (s - h) / (i * (s - p))
    kappa = (i - g) / (i**2 * (s - p)**2)
    # ω=M ds+N di；外微分的正向基底为 ds∧di。
    M = -beta * (1 - h / s) / (i * (s - p))
    N = -beta / (i * (s - p))
    actual_exterior = sp.diff(N, s) - sp.diff(M, i)
    total_theta = sp.diff(theta, s) + ell / s * sp.diff(theta, i)
    total_log_theta = sp.diff(sp.log(theta), s) + ell / s * sp.diff(sp.log(theta), i)
    log_formula = ell * (1 / ((s - h) * (s - p)) - 1 / (s * i))
    relation = {p: h - ell}
    residuals = {
        "domega_ds_wedge_di_coefficient": sp.simplify(actual_exterior - beta * kappa),
        "characteristic_dTheta_equals_ell_kappa": sp.simplify((total_theta - ell * kappa).subs(relation)),
        "log_derivative_matches_lem_unimodal": sp.simplify((total_log_theta - log_formula).subs(relation)),
        "Theta_times_log_derivative_equals_ell_kappa": sp.simplify((theta * log_formula - ell * kappa).subs(relation)),
    }
    # 从原文 W_s,W_i 及容量成本求导独立恢复旧边际公式。
    Ws = beta / s * end_theta
    Wi = (1 / i - end_theta) / h
    direct_D = Ws + Wi * (h - s) / s
    old_D = (s - p) / (h * s) * (end_theta - theta)
    direct_B = -beta * (s - h) / (K * s * (s - p)) + Ws
    old_B = beta / s * (end_theta - theta.subs(i, K))
    residuals["JD_from_W_gradients_matches_eq_JD_derivative"] = sp.simplify((direct_D - old_D).subs(p, (1 - beta) * h))
    residuals["JB_from_boundary_cost_and_W_matches_eq_JB_derivative"] = sp.simplify(direct_B - old_B)
    # 基本定理：Θ(end)−Θ(start)=−ℓ∫κ；再用 ℓ=βh。
    substitutions_D = {end_theta: theta - ell * integral}
    substitutions_B = {end_theta: theta.subs(i, K) - ell * integral}
    integral_D = -beta * (s - p) / s * integral
    integral_B = -beta * ell / s * integral
    residuals["JD_integral_formula_matches_eq_JD_derivative"] = sp.simplify((old_D.subs(substitutions_D) - integral_D).subs(ell, beta * h))
    residuals["JB_integral_formula_matches_eq_JB_derivative"] = sp.simplify(old_B.subs(substitutions_B) - integral_B)
    residuals["g_prime_matches_monotonicity_formula"] = sp.simplify(sp.diff(g, s) - (1 - h * p / s**2))
    assert all(residual == 0 for residual in residuals.values())
    return {
        "assumptions": "i>0, s>p, h=p+ell, ell=beta*h; characteristic di/ds=ell/s; logarithms of Theta additionally require s>h",
        "orientation": "omega=M ds+N di; d(omega)=(N_s-M_i) ds wedge di",
        "coefficient": str(sp.factor(actual_exterior)),
        "checks": {name: {"residual": str(residual), "passed": residual == 0}
                   for name, residual in residuals.items()},
        "passed_count": len(residuals),
        "total_count": len(residuals),
    }


def numerical_checks() -> dict:
    parameters = json.loads(INPUT.read_text(encoding="utf-8"))["parameters"]
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    beta, c, gamma, K = (float(parameters[name]) for name in ("beta", "c", "gamma", "K"))
    h, ell = gamma / (beta * c), gamma / c
    p = h - ell
    phi_A = K + h - h * math.log(h)
    s1, expected_sB = 0.7775221610386437, 0.5476951246795451
    root_calls = 0

    def root(fun, low, high):
        nonlocal root_calls
        root_calls += 1
        return brentq(fun, low, high, xtol=1e-14, rtol=9e-16)

    def a(s):
        return phi_A - s + h * math.log(s)

    def g(s):
        return (s - h) * (s - p) / s

    def theta(s, i):
        return (s - h) / (i * (s - p))

    def capacity_cost(high, low):
        return beta / (K * (1 - beta)) * (math.log(high / low) - beta * math.log((high - p) / (low - p)))

    def endpoint(sc, ic):
        if sc == h and ic == K:
            return h, K
        # G(z)=a(z)−ell ln z 严格下降，端点在 (h,min(sc,s_A))。
        hi = min(sc, sA)
        z = root(lambda z: a(z) - ic - ell * math.log(z / sc), h, hi)
        return z, a(z)

    def J_and_derivative(sc):
        if sc == h:
            return capacity_cost(s1, h), 0.0, h, K
        z, iz = endpoint(sc, K)
        cost = capacity_cost(s1, sc) + math.log(K / iz) / h
        derivative = beta / sc * (theta(z, iz) - theta(sc, K))
        return cost, derivative, z, iz

    sA = root(a, h, 2.0)
    e2 = next(case for case in checkpoint["cases"] if case["case_id"] == "E2")
    assert abs(s1 - e2["s_capacity"]) < 1e-14
    # 独立均匀网格；不将已知 s_B 塞入网格来制造极小点。
    grid = np.linspace(h, s1, 20001)
    rows = np.array([J_and_derivative(float(sc)) for sc in grid])
    best_index = int(np.argmin(rows[:, 0]))
    grid_smin, grid_Jmin = float(grid[best_index]), float(rows[best_index, 0])
    spacing = float(grid[1] - grid[0])
    assert abs(grid_smin - expected_sB) <= spacing
    # 在导数符号变号的网格区间只求根，不进行目标泛函优化。
    crossings = np.flatnonzero((rows[1:-1, 1] < 0) & (rows[2:, 1] > 0)) + 1
    assert len(crossings) == 1
    left = int(crossings[0])
    derivative_root = root(lambda sc: J_and_derivative(sc)[1], float(grid[left]), float(grid[left + 1]))
    Jmin, dmin, zB, iB = J_and_derivative(derivative_root)
    assert abs(derivative_root - expected_sB) < 2e-12
    assert abs(Jmin - e2["J_reference"]) < 2e-12
    assert np.all(rows[1:, 1][grid[1:] < derivative_root] < 0)
    assert np.all(rows[:, 1][grid > derivative_root] > 0)
    near_h = []
    for offset in (1e-2, 1e-3, 1e-4):
        cost, slope, z, iz = J_and_derivative(h + offset)
        assert slope < 0
        sample_s = np.linspace(z, h + offset, 301)
        differences = [K + ell * math.log(float(s) / (h + offset)) - g(float(s)) for s in sample_s]
        assert min(differences) > 0
        near_h.append({"s_c_minus_h": offset, "J_B": cost, "J_B_prime": slope,
                       "safe_endpoint": [z, iz], "entire_arc_i_minus_g_min": min(differences)})
    assert abs(near_h[2]["J_B_prime"]) < abs(near_h[1]["J_B_prime"]) < abs(near_h[0]["J_B_prime"])

    integral_checks = []
    phi0 = e2["phi0"]
    # 容量弧与自然等待弧各取多个点，以积分直接复核端点差式。
    starts = [("B", sc, K) for sc in (h + .01, .4, expected_sB, .65, s1)]
    starts += [("D", sc, phi0 - sc + h * math.log(sc)) for sc in (s1, .82, .9, .94)]
    for branch, sc, ic in starts:
        z, iz = endpoint(sc, ic)

        def kappa_on_arc(s):
            infection = ic + ell * math.log(s / sc)
            return (infection - g(s)) / (infection**2 * (s - p)**2)

        integral, error = quad(kappa_on_arc, z, sc, epsabs=2e-12, epsrel=2e-13)
        delta = theta(z, iz) - theta(sc, ic)
        multiplier = beta / sc if branch == "B" else (sc - p) / (h * sc)
        old_formula = multiplier * delta
        new_multiplier = -beta * ell / sc if branch == "B" else -beta * (sc - p) / sc
        new_formula = new_multiplier * integral
        residual = abs(old_formula - new_formula)
        # 安全端点感染很小时，边际导数可达 10^3；同时记录绝对与尺度归一化残差。
        scaled_residual = residual / max(1.0, abs(old_formula), abs(new_formula))
        assert scaled_residual < 5e-12, (branch, sc, old_formula, new_formula, scaled_residual)
        integral_checks.append({"branch": branch, "start": [sc, ic], "safe_endpoint": [z, iz],
                                "integral_kappa": integral, "quad_error_estimate": error,
                                "Theta_delta_plus_ell_integral_residual": abs(delta + ell * integral),
                                "old_derivative_formula": old_formula, "integral_derivative_formula": new_formula,
                                "absolute_residual": residual, "scaled_residual": scaled_residual})

    Jhold = capacity_cost(s1, h)
    savings = 100 * (Jhold - Jmin) / Jhold
    excess = 100 * (Jhold - Jmin) / Jmin
    assert f"{Jmin:.6f}" == "1.529511"
    assert f"{Jhold:.6f}" == "1.578386"
    assert f"{savings:.2f}" == "3.10"
    assert f"{excess:.2f}" == "3.20"
    manuscript = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    macro_J = float(re.search(r"\\providecommand\{\\NumJRefETwo\}\{([0-9.]+)\}", manuscript).group(1))
    macro_sB = float(re.search(r"\\providecommand\{\\NumSBRef\}\{([0-9.]+)\}", manuscript).group(1))
    assert abs(Jmin - macro_J) < 5e-7
    assert abs(derivative_root - macro_sB) < 5e-9
    baseline = json.loads(BASELINE_CHECKS.read_text(encoding="utf-8"))
    old_cost = baseline["E2_analytic_cost"]
    previous_errors = {
        "optimal_total": abs(Jmin - old_cost["optimal_total"]),
        "capacity_until_h_total": abs(Jhold - old_cost["capacity_until_h_total"]),
        "saving_percent_relative_to_comparison": abs(savings - old_cost["saving_percent_relative_to_comparison"]),
    }
    assert max(previous_errors.values()) < 2e-12
    return {
        "parameters": parameters,
        "constants": {"h": h, "ell": ell, "p": p, "s_A": sA},
        "E2_capacity_contact_s1": s1,
        "method": "20001-point uniform scan of analytical J_B; sole interior derivative sign change refined by brentq root solving",
        "root_solver": {"name": "scipy.optimize.brentq (scalar equation root, not optimizer)",
                        "xtol": 1e-14, "rtol": 9e-16, "calls": root_calls},
        "scan": {"range": [h, s1], "sample_count": len(grid), "spacing": spacing,
                 "h_is_limit_endpoint": True, "grid_minimizer": grid_smin, "grid_minimum": grid_Jmin,
                 "grid_minimizer_error_to_expected_sB": abs(grid_smin - expected_sB),
                 "interior_derivative_sign_changes": len(crossings),
                 "all_sc_below_sB_have_negative_derivative": True,
                 "all_sc_above_sB_have_positive_derivative": True},
        "stationary_root": {"s_B": derivative_root, "expected_s_B": expected_sB,
                            "absolute_s_B_error": abs(derivative_root - expected_sB),
                            "J_B_prime_residual": abs(dmin), "safe_endpoint": [zB, iB]},
        "near_h": near_h,
        "limit_at_h": {"J_B": Jhold, "Theta_h_K": theta(h, K), "J_B_prime_right_limit": 0,
                       "stationary_but_not_minimum": True},
        "integral_derivative_checks": integral_checks,
        "maximum_integral_derivative_residual": max(item["absolute_residual"] for item in integral_checks),
        "maximum_scaled_integral_derivative_residual": max(item["scaled_residual"] for item in integral_checks),
        "integral_derivative_acceptance_scaled_residual": 5e-12,
        "E2_costs": {"optimal": Jmin, "hold_to_h": Jhold,
                     "saving_percent_denominator_hold_cost": savings,
                     "hold_excess_percent_denominator_optimal_cost": excess,
                     "checkpoint_cost_error": abs(Jmin - e2["J_reference"]),
                     "macro_NumJRefETwo_error": abs(Jmin - macro_J), "macro_NumSBRef_error": abs(derivative_root - macro_sB),
                     "previous_figure_analytic_cost_errors": previous_errors},
        "passed": True,
    }


def main():
    result = {
        "status": "analytical_identity_and_formula_evaluation_only",
        "script_sha256": digest(Path(__file__)),
        "inputs_sha256": {str(path.relative_to(PROJECT)): digest(path) for path in (INPUT, CHECKPOINT, BASELINE_CHECKS)},
        "software_versions": {"sympy": sp.__version__, "scipy": scipy.__version__, "numpy": np.__version__},
        "symbolic": symbolic_checks(),
        "numerical": numerical_checks(),
        "execution_counts": {"MATLAB": 0, "optimizer": 0, "new_OCP_solve": 0, "ODE_solver": 0},
        "passed": True,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "symbolic_checks": result["symbolic"]["passed_count"],
                      "numerical_passed": result["numerical"]["passed"],
                      "s_B": result["numerical"]["stationary_root"]["s_B"],
                      "E2_costs": result["numerical"]["E2_costs"],
                      "maximum_integral_derivative_residual": result["numerical"]["maximum_integral_derivative_residual"],
                      "execution_counts": result["execution_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
