"""独立核对阶段 D 新增的小容量展开；仅做符号代数，不运行 ODE 或优化。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sympy as sp


def main() -> int:
    work_dir = Path(__file__).resolve().parent
    project_dir = work_dir.parent.parent
    beta, v, k, S, h = sp.symbols("beta v k S h", positive=True)
    f = v - sp.log(1 + v)

    # 从精确参数化出发展开，不从论文中的待验证系数构造计算式。
    u = ((1 + v) * sp.exp(f / beta) - 1).series(v, 0, 7).removeO()
    k_of_v = (u * (beta + v) * f / (beta * (u - v))).series(v, 0, 5).removeO()
    A = sp.Rational(3, 2) - beta
    B = beta - sp.Rational(19, 12) + 1 / (2 * beta)
    v_of_k = k / beta - A * k**2 / beta**3 + (
        2 * A**2 / beta**5 - B / beta**4
    ) * k**3

    # 对精确容量弧被积函数展开并积分至四阶，足以核对成本的三阶项。
    t = sp.symbols("t")
    integrand = (t / ((1 + t) * (beta + t))).series(t, 0, 4).removeO()
    integral = sp.integrate(integrand, (t, 0, u))
    fill_cost = (beta * integral / k_of_v).series(v, 0, 4).removeO()
    full_cost = (-sp.log(1 - f / k_of_v)).series(v, 0, 4).removeO()
    delta_v = sp.simplify(fill_cost - full_cost)
    delta_k = delta_v.subs(v, v_of_k).series(k, 0, 4).removeO()
    time_difference = (
        beta / k_of_v * sp.log(1 + u / beta) - full_cost
    ).series(v, 0, 2).removeO()
    C = beta / (1 - beta) * (
        sp.log(S / h)
        - beta * sp.log((S - (1 - beta) * h) / (beta * h))
    )

    differences = {
        "u_of_v_cubic": u.series(v, 0, 4).removeO()
        - (v + v**2 / (2 * beta) + v**3 / (6 * beta)),
        "k_of_v_cubic": k_of_v.series(v, 0, 4).removeO()
        - (beta * v + A * v**2 + B * v**3),
        "inverse_composition_cubic": k_of_v.subs(v, v_of_k)
        .series(k, 0, 4).removeO() - k,
        "u_of_k_quadratic": u.subs(v, v_of_k).series(k, 0, 3).removeO()
        - (k / beta - (1 - beta) * k**2 / beta**3),
        "fill_cost_quadratic": fill_cost.series(v, 0, 3).removeO()
        - (v / (2 * beta) + (2 * beta - 7) * v**2 / (12 * beta**2)),
        "full_cost_quadratic": full_cost.series(v, 0, 3).removeO()
        - (v / (2 * beta) + (4 * beta - 15) * v**2 / (24 * beta**2)),
        "delta_cost_v_cubic": delta_v
        - (v**2 / (24 * beta**2) - v**3 / (24 * beta**3)),
        "delta_cost_k_cubic": delta_k
        - (k**2 / (24 * beta**4) - (2 - beta) * k**3 / (12 * beta**6)),
        "time_difference_constant_and_linear": time_difference
        - (1 / beta - (3 - beta) * v / (2 * beta**2)),
        "C_derivative_positive_integrand": sp.diff(C, S)
        - beta * (S - h) / (S * (S - (1 - beta) * h)),
    }
    checks = []
    for name, difference in differences.items():
        residual = sp.simplify(difference)
        checks.append({"name": name, "passed": bool(residual == 0), "residual": str(residual)})

    main_path = project_dir / "latex" / "main.tex"
    main_text = main_path.read_text(encoding="utf-8")
    fragment_checks = []
    for name in ("d_main.tex", "d_appendix.tex"):
        fragment = (work_dir / name).read_text(encoding="utf-8").strip()
        fragment_checks.append({"name": name, "passed": fragment in main_text})

    source_paths = [main_path, work_dir / "d_main.tex", work_dir / "d_appendix.tex"]
    source_hashes = {
        str(path.relative_to(project_dir)).replace("\\", "/"):
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
    }
    all_passed = all(item["passed"] for item in checks + fragment_checks)
    report = {
        "review_date": "2026-10-21",
        "scope": "阶段 D 新增小容量展开的独立符号核对及片段一致性检查",
        "sympy_version": sp.__version__,
        "assumptions": ["0 < beta < 1", "c > 0", "gamma > 0", "固定参数后 K -> 0"],
        "algebra_checks_total": len(checks),
        "algebra_checks_passed": sum(item["passed"] for item in checks),
        "algebra_checks": checks,
        "fragment_checks_total": len(fragment_checks),
        "fragment_checks_passed": sum(item["passed"] for item in fragment_checks),
        "fragment_checks": fragment_checks,
        "source_sha256": source_hashes,
        "optimizer_calls": 0,
        "new_ocp_solves": 0,
        "ode_integrations": 0,
        "all_passed": all_passed,
    }
    output_path = work_dir / "symbolic_checks.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "algebra": f"{report['algebra_checks_passed']}/{len(checks)}",
        "fragment_consistency": f"{report['fragment_checks_passed']}/{len(fragment_checks)}",
        "optimizer_calls": 0, "new_ocp_solves": 0, "ode_integrations": 0,
        "all_passed": all_passed,
    }, ensure_ascii=False))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
