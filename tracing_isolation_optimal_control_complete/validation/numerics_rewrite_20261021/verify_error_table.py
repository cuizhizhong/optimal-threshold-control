#!/usr/bin/env python3
"""只读复核已保存结果与阶段 F 误差表；不调用 MATLAB、ODE 或 OCP。

下降量未作为字段保存在原评估中。本脚本独立评价既有解析方程，
以保存的解析切换点初始化标量/代数求根，再与导出器新增宏比较。
写入范围仅限本脚本所在验证目录。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from decimal import Decimal
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.optimize import brentq, root

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DATA = PROJECT / "data/numerical_scenarios"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    with open(long_name(path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def long_name(path):
    # Windows 原评估文件名很长；加扩展路径前缀，不复制或改写原文件。
    name = str(path.resolve())
    if os.name == "nt" and not name.startswith("\\\\?\\"):
        name = "\\\\?\\" + name
    return name


def read_mat(path):
    return loadmat(long_name(path), simplify_cells=True)


def relative(path):
    return path.resolve().relative_to(PROJECT).as_posix()


def scalar(value):
    return float(np.asarray(value).reshape(-1)[0])


def analytical_value(case, reference, capacity):
    """只评价旧解析最优值公式，使用保存分支；无时间积分或轨道生成。

    a_K(z)=K+h-z+h log(z/h), p=h-ell, ell=gamma/c.
    完全跟踪两端满足 i_f-ell log(s_f)=a_K(z)-ell log(z).
    非平凡切换另满足 Theta(s_f,i_f)=Theta(z,a_K(z)).
    解析成本为 J_B+beta*c/gamma*log(i_f/a_K(z)).
    """
    beta, c, gamma = (float(case["parameters"][k]) for k in ("beta", "c", "gamma"))
    h, ell = gamma / (beta * c), gamma / c
    p = h - ell
    s0, i0 = map(float, case["x0"])
    a = lambda z: capacity + h - z + h * math.log(z / h)
    phi = lambda s, i: i + s - h * math.log(s)
    theta = lambda s, i: (s - h) / (i * (s - p))
    phi0 = phi(s0, i0)
    region = reference["region"]
    full_guess = np.asarray(reference["events"]["full_state"], dtype=float).reshape(-1)
    release_guess = np.asarray(reference["events"]["release_state"], dtype=float).reshape(-1)
    boundary_cost = 0.0
    if region == "A":
        return 0.0
    if region in ("B", "W_K"):
        # 以旧解析点作局部初值，同时显式验证非平凡根与解析方程残差。
        def equation(values):
            z, sf = values
            iz = a(z)
            return [iz + ell * math.log(sf / z) - capacity,
                    theta(sf, capacity) - theta(z, iz)]
        result = root(equation, [release_guess[0], full_guess[0]], tol=1e-11)
        z, sf = map(float, result.x)
        iff = capacity
        assert max(abs(v) for v in equation([z, sf])) < 2e-12
        assert h < z < sf and a(z) > 0
        sc = s0 if i0 == capacity else brentq(
            lambda s: phi(s, capacity) - phi0, h, s0, xtol=5e-15
        )
        assert sc >= sf
        boundary_cost = beta / (capacity * (1 - beta)) * (
            math.log(sc / sf) - beta * math.log((sc - p) / (sf - p))
        )
    elif region == "W_Gamma":
        def equation(values):
            z, sf = values
            iff = phi0 - sf + h * math.log(sf)
            iz = a(z)
            return [iff - iz - ell * math.log(sf / z),
                    theta(sf, iff) - theta(z, iz)]
        result = root(equation, [release_guess[0], full_guess[0]], tol=1e-11)
        z, sf = map(float, result.x)
        iff = phi0 - sf + h * math.log(sf)
        assert max(abs(v) for v in equation([z, sf])) < 2e-12
        assert h < z < sf < s0 and 0 < iff <= capacity
    else:
        assert region in ("T", "Gamma"), region
        sf, iff = s0, i0
        psi = iff - ell * math.log(sf)
        z = brentq(lambda v: a(v) - ell * math.log(v) - psi,
                   h, sf, xtol=5e-15)
    assert 0 < a(z) <= iff
    return boundary_cost + beta * c / gamma * math.log(iff / a(z))


def macro_body(text, name):
    match = re.search(r"\\(?:newcommand|renewcommand|providecommand)\{\\" + re.escape(name) + r"\}\{", text)
    if not match:
        return None
    start, depth = match.end(), 1
    for index in range(start, len(text)):
        # 括号前连续反斜线为偶数时，括号仍参与宏体配对（例如末行的 \\\\}）。
        previous = index - 1
        while previous >= 0 and text[previous] == "\\":
            previous -= 1
        escaped = (index - previous - 1) % 2 == 1
        if text[index] == "{" and not escaped:
            depth += 1
        elif text[index] == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[start:index]
    raise ValueError(f"宏未闭合: {name}")


def rounding_check(expected, literal):
    # 由实际打印的小数位确定舍入半单位；同时要求非零值为 2--3 位有效数字。
    value = Decimal(literal)
    wanted = Decimal.from_float(expected)
    exponent = value.as_tuple().exponent
    half_unit = Decimal(5).scaleb(exponent - 1)
    digits = len(value.as_tuple().digits)
    return dict(expected=expected, generated=literal,
                rounding_half_unit=str(half_unit), significant_digits=digits,
                passed=bool(abs(value - wanted) <= half_unit and
                            (expected == 0 or 2 <= digits <= 3)))


def verify_residual_summary(body, residual, gaps):
    """独立核对摘要句数、打印数值、终端结果、两套判据及粗网格异常。"""
    sentences = [part for part in body.split("。") if part.strip()]
    literals = re.findall(r"\\num\{([^}]+)\}", body)
    assert len(literals) == 4, literals
    expected = [residual["max_absolute_relative_percent"], residual["max_capacity_excess"],
                residual["max_state_discrepancy"], max(residual["tail_max_q"])]
    numbers = {key: rounding_check(value, literal) for key, value, literal in zip(
        ("relative_percent", "capacity_excess", "state_discrepancy", "tail_max_q"), expected, literals)}
    original = re.search(r"按求解前预定的原判据[^；。]*同时通过\s*(\d+)/(\d+)", body)
    revised = re.search(r"按求解后修订的判据[^；。]*同时通过\s*(\d+)/(\d+)", body)
    stage = re.search(r"(E[1-5](?:、E[1-5])*)\s*在\s*\$n=(\d+)\$\s*的阶段识别异常", body)
    cost = re.search(r"(E[1-5](?:、E[1-5])*)\s*在\s*\$n=(\d+)\$\s*的成本比较未通过", body)
    by_id = {item["id"]: item for item in gaps["gaps"]}
    stage_rows = by_id["coarse_stage_anomalies"]["evidence"]
    cost_rows = by_id["coarse_cost_failures"]["evidence"]
    checks = dict(
        five_sentences=len(sentences) == 5,
        displayed_numbers=all(item["passed"] for item in numbers.values()),
        tail_zero=max(residual["tail_max_q"]) == 0 and "末段最大控制幅值为" in body,
        terminal_safety=all(residual["terminal_safe"]) and "各例终端状态均通过零控制安全检查" in body,
        original_counts=bool(original and tuple(map(int, original.groups())) ==
                             (residual["original_counts"]["both_pass"], residual["original_counts"]["records"])),
        revised_counts=bool(revised and tuple(map(int, revised.groups())) ==
                            (residual["revised_counts"]["both_pass"], residual["revised_counts"]["records"])),
        criterion_change="修订只调整浮点接受尺度，不提供新的收敛证据" in body,
        stage_anomalies=bool(stage and set(re.findall(r"E[1-5]", stage.group(1))) ==
                             {row["case_id"] for row in stage_rows} and
                             {int(stage.group(2))} == {row["N"] for row in stage_rows}),
        cost_failures=bool(cost and set(re.findall(r"E[1-5]", cost.group(1))) ==
                           {row["case_id"] for row in cost_rows} and
                           {int(cost.group(2))} == {row["N"] for row in cost_rows}),
    )
    return dict(sentence_count=len(sentences), numbers=numbers, checks=checks,
                passed=all(checks.values()))


def audit_gaps(s26, grid, selected):
    coarse = []
    for row in s26["rows"]:
        if row["N"] != 2000:
            continue
        path = Path(row["current_assessment_file"])
        saved = read_mat(path)["assessment_record"]
        assessment = saved["assessment"]
        summary = {key: row[key] for key in ("case_id", "run_id", "N", "T")}
        summary.update({key: assessment[key] for key in
                        ("numeric_pass", "agreement_pass", "observed_structure", "status")})
        summary.update({key: scalar(assessment[key]) for key in
                        ("capacity_excess", "state_discrepancy", "signed_cost_difference",
                         "relative_cost_difference")})
        summary["cost_agreement"] = assessment["cost_agreement"]
        summary["event_diagnostic_pass"] = bool(assessment["event_comparison"]["diagnostic_pass"])
        summary["structure_pass"] = bool(assessment["event_comparison"]["structure_pass"])
        summary["event_diagnostics"] = assessment["event_detection"]["diagnostics"]
        summary["source"] = relative(path)
        if row["case_id"] == "E3":
            case = dict(parameters=selected["E3"]["parameters"], x0=selected["E3"]["x0"])
            wide = analytical_value(case, saved["reference"],
                                    case["parameters"]["K"] + summary["capacity_excess"])
            drop = float(row["J_reference"]) - wide
            summary["relaxed_capacity_drop_independently_recomputed"] = drop
            summary["negative_difference_compatible_with_capacity_excess"] = bool(
                summary["signed_cost_difference"] >= -drop
            )
        coarse.append(summary)
    all_rows = s26["rows"]
    entries = [
        dict(id="no_convergence_order", description="只对所测最细两级比较一致性；未给出网格加密收敛阶或离散最优值到无穷时域值函数的收敛证明。",
             source="data/numerical_scenarios/revision_checks/grid_summary.json",
             evidence=[{key: row[key] for key in ("case_id", "fine_N", "coarse_N", "consistency_pass")} for row in grid["case_comparisons"]]),
        dict(id="unrun_extended_configurations", description="n=16000、T=600 及额外初猜未运行；本阶段只记录，不补算。",
             source="data/numerical_scenarios/revision_checks/README.md:17",
             evidence=dict(saved_N=sorted(set(row["N"] for row in all_rows)),
                           saved_T=sorted(set(row["T"] for row in all_rows)),
                           saved_initializations=sorted(set(row["initialization"] for row in all_rows)),
                           saved_configuration_count=len(all_rows))),
        dict(id="coarse_stage_anomalies", description="E2/E4 在 n=2000 的阶段识别异常保持原分类。",
             evidence=[row for row in coarse if row["case_id"] in ("E2", "E4")]),
        dict(id="coarse_cost_failures", description="E1/E3/E5 在 n=2000 的成本比较未通过。",
             evidence=[row for row in coarse if row["case_id"] in ("E1", "E3", "E5")]),
        dict(id="E3_negative_cost_difference", description="E3 在 n=2000 的负成本差与容量超出相容；unresolved_discrepancy 原分类保留。",
             evidence=next(row for row in coarse if row["case_id"] == "E3")),
        dict(id="floating_point_diagnostics", description="重积分、终端峰值和状态差均为浮点诊断；通过浮点接受判据不是严格可行性证明。",
             source="data/numerical_scenarios/numerical_checks.json"),
        dict(id="post_solve_acceptance_revision", description="原判据同时通过 28/35，求解后修订判据同时通过 30/35；不新增收敛证据。",
             source="validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json",
             original=s26["original_counts"], revised=s26["current_counts"]),
        dict(id="relaxed_drop_not_persisted", description="原保存评估未记录 relaxed_capacity_drop 字段；表值来源是旧解析公式的评价，本脚本独立重算，不新增 OCP/ODE 或参数扫描。",
             source="matlab/numerical_scenarios/export_numerical_latex.m::relaxed_capacity_drop"),
    ]
    return dict(schema_version=1, no_new_computation_of_trajectories=True,
                optimizer_calls=0, new_ocp_solves=0, ode_calls=0, gaps=entries)


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    checks = load_json(DATA / "numerical_checks.json")
    manifest = load_json(DATA / "selection_manifest.json")
    s26 = load_json(PROJECT / "validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json")
    grid = load_json(DATA / "revision_checks/grid_summary.json")
    selected = {case["case_id"]: case for case in checks["cases"]}
    exporter_text = (PROJECT / "matlab/numerical_scenarios/export_numerical_latex.m").read_text(encoding="utf-8-sig")
    old_drop_function = re.search(r"(?ms)^function drop=relaxed_capacity_drop\(run\).*?(?=^function )", exporter_text).group()
    report = dict(schema_version=1, baseline="89d9cc3", optimizer_calls=0,
                  new_ocp_solves=0, ode_calls=0, matlab_calls=0,
                  formula_provenance=dict(
                      description="原评估无下降量字段；独立按保存参数与既有解析切换方程重算下降量，无新轨道。",
                      existing_relaxed_capacity_drop_source=old_drop_function,
                      existing_relaxed_capacity_drop_source_sha256=hashlib.sha256(old_drop_function.encode("utf-8")).hexdigest(),
                      formulas=["a_K(z)=K+h-z+h*log(z/h)",
                                "Theta(s,i)=(s-h)/(i*(s-p))",
                                "i_f=a_K(z)+ell*log(s_f/z)",
                                "Theta(s_f,i_f)=Theta(z,a_K(z))",
                                "J_B=beta/(K*(1-beta))*(log(s_c/s_B)-beta*log((s_c-p)/(s_B-p)))",
                                "J=J_B+beta*c/gamma*log(i_f/a_K(z))",
                                "drop=J_reference(K)-J_analytic(K+capacity_excess)"],
                      production_sources={name: digest(PROJECT / "matlab/numerical_scenarios" / name)
                                          for name in ("analytic_reference.m", "build_theory_geometry.m", "classify_initial_state.m")}),
                  source_hashes={relative(path): digest(path) for path in
                                 (DATA / "numerical_checks.json", DATA / "selection_manifest.json",
                                  DATA / "revision_checks/grid_summary.json",
                                  PROJECT / "validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json")},
                  rows=[])
    for entry in manifest["entries"]:
        case = selected[entry["case_id"]]
        path = next((DATA / "revision_checks/assessments").glob(
            entry["run_id"] + "_" + entry["assessment_fingerprint"] + "_*.mat"))
        saved = read_mat(path)["assessment_record"]
        assessment = saved["assessment"]
        assert saved["run_id"] == entry["run_id"]
        assert saved["assessment_fingerprint"] == entry["assessment_fingerprint"]
        for key in ("capacity_excess", "state_discrepancy", "tail_max_q", "terminal_peak"):
            assert scalar(assessment[key]) == case["assessment"][key], key
        jref, jocl = float(case["J_reference"]), float(case["J_openocl"])
        assert scalar(saved["reference"]["J_reference"]) == jref
        baseline_check = analytical_value(case, saved["reference"], case["parameters"]["K"])
        assert abs(baseline_check - jref) < 5e-12
        gap = jocl - jref
        assert gap == scalar(assessment["signed_cost_difference"])
        excess = scalar(assessment["capacity_excess"])
        wide = analytical_value(case, saved["reference"], case["parameters"]["K"] + excess) if excess > 0 else jref
        drop = jref - wide if excess > 0 else 0.0
        report["source_hashes"][relative(path)] = digest(path)
        report["rows"].append(dict(case_id=case["case_id"], run_id=entry["run_id"],
                                   J_reference=jref, J_openocl=jocl, signed_cost_difference=gap,
                                   signed_relative_percent=100 * gap / jref,
                                   capacity_excess=excess, relaxed_capacity_drop=drop,
                                   relaxed_comparison_pass=bool(gap >= -drop),
                                   baseline_formula_difference=baseline_check-jref,
                                   assessment_source=relative(path)))
    report["residual_data"] = dict(
        max_absolute_relative_percent=max(abs(row["signed_relative_percent"]) for row in report["rows"]),
        max_capacity_excess=max(case["assessment"]["capacity_excess"] for case in checks["cases"]),
        max_state_discrepancy=max(case["assessment"]["state_discrepancy"] for case in checks["cases"]),
        tail_max_q=[case["assessment"]["tail_max_q"] for case in checks["cases"]],
        terminal_safe=[case["assessment"]["terminal_safe"] for case in checks["cases"]],
        terminal_peaks=[case["assessment"]["terminal_peak"] for case in checks["cases"]],
        original_counts=s26["original_counts"], revised_counts=s26["current_counts"])
    gaps = audit_gaps(s26, grid, selected)
    tex_path = PROJECT / "latex/main.tex"
    if not tex_path.exists():
        candidates = list((PROJECT / "latex").glob("*.tex"))
        tex_path = next(path for path in candidates if "BEGIN AUTO-GENERATED NUMERICAL RESULTS" in path.read_text(encoding="utf-8-sig"))
    tex = tex_path.read_text(encoding="utf-8-sig")
    body = macro_body(tex, "NumErrorTableRows")
    report["generated_tex"] = relative(tex_path)
    if body is None:
        report["status"] = "pending_export"
        assert args.allow_pending, "新增宏尚未导出"
    else:
        comparisons = []
        generated_rows = re.split(r"\\\\", body)
        by_case = {}
        for line in generated_rows:
            line = re.sub(r"%[^\n]*", "", line).strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split("&")]
            match = re.search(r"E[1-5]", parts[0])
            assert match and len(parts) == 6, line
            by_case[match.group()] = parts
        assert set(by_case) == set(selected)
        keys = ("signed_cost_difference", "signed_relative_percent", "capacity_excess", "relaxed_capacity_drop")
        for expected in report["rows"]:
            parts = by_case[expected["case_id"]]
            fields = {}
            for key, cell in zip(keys, parts[1:5]):
                match = re.fullmatch(r"\$?\s*\\num\{([^}]+)\}\s*(?:\\%\s*)?\$?", cell)
                assert match, cell
                fields[key] = rounding_check(expected[key], match.group(1))
            judgment = parts[5]
            assert judgment in ("是", "否"), judgment
            judgment_pass = (judgment == "是") == expected["relaxed_comparison_pass"]
            comparisons.append(dict(case_id=expected["case_id"], fields=fields,
                                    generated_judgment=judgment, judgment_pass=judgment_pass,
                                    passed=bool(judgment_pass and all(item["passed"] for item in fields.values()))))
        report["macro_comparisons"] = comparisons
        summary_body = macro_body(tex, "NumResidualSummary")
        assert summary_body is not None, "缺少 NumResidualSummary"
        report["residual_summary_comparison"] = verify_residual_summary(summary_body, report["residual_data"], gaps)
        report["passed"] = all(row["passed"] for row in comparisons) and report["residual_summary_comparison"]["passed"]
        report["status"] = "passed" if report["passed"] else "failed"
        report["generated_tex_sha256"] = digest(tex_path)
    (HERE / "audit_error_table.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    (HERE / "evidence_gaps.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=report["status"], rows=report["rows"], residual_data=report["residual_data"]), ensure_ascii=False, indent=2))
    assert report.get("passed", args.allow_pending), "误差表独立核对失败"


if __name__ == "__main__":
    main()
