#!/usr/bin/env python3
"""Build the manuscript's grid-error tables from saved experiment summaries.

This script performs no optimal-control solve and no ODE reintegration.
The values originate from the saved MATLAB/OpenOCL assessment records at
GitHub commit 09140ec16983fa98f1103b873fc03706ff7dd627.

Definitions checked against matlab/numerical_scenarios/assess_numerical_case.m:
  delta_J = J_openocl - J_reference;
  epsilon_K = max(0, max_t i_reintegrated(t) - K);
  epsilon_x = max_{node k, component j} |x_reintegrated_j(t_k)-x_collocation_j(t_k)|.
The reported maximum is taken over finite candidate intervals in each saved
event summary, including candidates that failed the transition-width check.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/numerical_scenarios/revision_checks/grid_detailed_summary.csv"
COMPACT = ROOT / "data/numerical_scenarios/revision_checks/grid_summary.json"
EVENTS = ("intervention", "capacity_enter", "capacity_exit", "full_start", "release")
EXPECTED = {(f"E{k}", n) for k in range(1, 6) for n in (2000, 4000, 8000)}


def finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite numeric value: {value!r}")
    return result


def tex_sci(value: float, signed: bool = False) -> str:
    formatted = f"{value:+.3e}" if signed else f"{value:.3e}"
    return rf"$\num{{{formatted}}}$"


def extract_rows() -> tuple[list[dict], list[dict]]:
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    compact_rows = json.loads(COMPACT.read_text(encoding="utf-8"))["rows"]
    compact_by_key = {(r["case_id"], int(r["N"])): r for r in compact_rows}
    rows, metadata_differences = [], []
    seen = set()
    for source in source_rows:
        case = source["case_id"]
        n = int(finite_float(source["N"]))
        key = case, n
        if key in seen:
            raise ValueError(f"Duplicate case/grid: {key}")
        seen.add(key)
        horizon = finite_float(source["T"])
        if horizon != 300.0:
            raise ValueError(f"Unexpected horizon for {key}: {horizon}")
        j_num = finite_float(source["J_openocl"])
        j_ref = finite_float(source["J_reference"])
        delta_j = finite_float(source["signed_cost_difference_to_reference"])
        if not math.isclose(j_num-j_ref, delta_j, rel_tol=1e-9, abs_tol=2e-14):
            raise ValueError(f"Inconsistent signed cost difference: {key}")
        relative = finite_float(source["relative_cost_difference_to_reference"])
        if not math.isclose(delta_j/j_ref, relative, rel_tol=1e-9, abs_tol=2e-14):
            raise ValueError(f"Inconsistent relative cost difference: {key}")
        epsilon_k = finite_float(source["capacity_excess"])
        epsilon_x = finite_float(source["state_discrepancy"])
        events = json.loads(source["events"])
        comparison = json.loads(source["event_comparison"])
        widths = []
        row = {
            "case_id": case, "N": n, "T": horizon,
            "grid_step": horizon/n, "J_reference": j_ref,
            "J_openocl": j_num, "signed_cost_difference": delta_j,
            "relative_cost_difference": relative,
            "capacity_excess": epsilon_k, "state_discrepancy": epsilon_x,
            "observed_structure": source["observed_structure"],
            "configuration_id": source["configuration_id"],
            "source_run_id": source["run_id"],
            "source_solve_fingerprint": source["solve_fingerprint"],
            "source_raw_sha256": source["raw_sha256"],
        }
        missing_expected = []
        for event in EVENTS:
            left_s = source[f"{event}_interval_left"]
            right_s = source[f"{event}_interval_right"]
            width_s = source[f"{event}_interval_width"]
            status = source[f"{event}_status"]
            row[f"{event}_status"] = status
            if width_s:
                left, right, width = map(finite_float, (left_s, right_s, width_s))
                if width < 0 or not math.isclose(right-left, width, abs_tol=1e-12):
                    raise ValueError(f"Invalid event interval for {key}, {event}")
                interval = events[event]["interval"]
                if any(not math.isclose(a,b,abs_tol=1e-12) for a,b in zip((left,right),interval)):
                    raise ValueError(f"Event fields disagree for {key}, {event}")
                row[f"{event}_interval_left"] = left
                row[f"{event}_interval_right"] = right
                row[f"{event}_interval_width"] = width
                widths.append(width)
            else:
                row[f"{event}_interval_left"] = ""
                row[f"{event}_interval_right"] = ""
                row[f"{event}_interval_width"] = ""
                if comparison["events"][event].get("applicable"):
                    missing_expected.append(event)
        if not widths:
            raise ValueError(f"No returned event intervals for {key}")
        row["max_reported_event_interval_width"] = max(widths)
        row["expected_event_missing"] = ";".join(missing_expected)
        row["event_structure_anomaly"] = (
            not bool(comparison["structure_pass"])
            or not bool(comparison["diagnostic_pass"])
            or bool(missing_expected)
        )
        compact = compact_by_key[key]
        for field in ("configuration_id", "observed_structure"):
            if compact[field] != source[field]:
                raise ValueError(f"Compact and detailed metadata differ: {key}, {field}")
        for event in EVENTS:
            detailed_event = events[event]
            compact_event = compact["event_intervals"][event]
            if compact_event["status"] != detailed_event["status"]:
                raise ValueError(f"Compact and detailed event status differs: {key}, {event}")
            left = compact_event["interval"]
            right = detailed_event["interval"]
            if len(left) != len(right) or any(
                (a is None) != (b is None)
                or (a is not None and not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12))
                for a, b in zip(left, right)
            ):
                raise ValueError(f"Compact and detailed event interval differs: {key}, {event}")
        for field, value in (("J_openocl",j_num),("capacity_excess",epsilon_k),("state_discrepancy",epsilon_x)):
            if not math.isclose(compact[field], value, rel_tol=1e-12, abs_tol=1e-15):
                raise ValueError(f"Compact and detailed numerical values differ: {key}, {field}")
        if compact["run_id"] != row["source_run_id"]:
            metadata_differences.append({"case_id":case,"N":n,
                "detailed_run_id":row["source_run_id"],"compact_run_id":compact["run_id"],
                "numeric_fields_match":True})
        rows.append(row)
    if seen != EXPECTED or set(compact_by_key) != EXPECTED:
        raise ValueError("Grid data must cover exactly E1-E5 at n=2000,4000,8000")
    return sorted(rows,key=lambda r:(r["case_id"],r["N"])), metadata_differences


def table_tex(rows: list[dict], compact: bool) -> str:
    if compact:
        caption = (r"具有容量维持阶段的算例在各网格下的误差（$T=300$，$\Delta t=T/n$）。"
                   r"$\delta J=J_{\mathrm{OCL}}-J_{\mathrm{ref}}$，其余误差定义见正文。"
                   r"全部五个算例的逐网格数值见补充材料。")
        label = "tab:grid-errors-capacity"
    else:
        caption = (r"E1--E5 的逐网格误差。"
                   r"固定 $T=300$，$n=2000,4000,8000$ 分别对应模型时间步长 $\Delta t=0.15,0.075,0.0375$。"
                   r"$\delta J=J_{\mathrm{OCL}}-J_{\mathrm{ref}}$，"
                   r"$\varepsilon_K$ 为重积分感染峰值的容量超出量，"
                   r"$\varepsilon_x$ 为重积分与配点的最大节点状态偏差，$w_{\max}$ 为候选切换区间的最大有限宽度。")
        label = "tab:grid-errors-all"
    out = ["% Generated by scripts/build_grid_error_table.py from saved results.",
           r"\begin{table}[htbp]",r"\centering\small",r"\setlength{\tabcolsep}{5pt}",
           rf"\caption{{{caption}}}",rf"\label{{{label}}}",
           r"\begin{tabular}{@{}crrrrr@{}}",r"\toprule",
           r"算例 & $n$ & $\delta J$ & $\varepsilon_K$ & $w_{\max}$ & $\varepsilon_x$\\",
           r"\midrule"]
    previous_case = None
    for r in rows:
        if previous_case and previous_case != r["case_id"]:
            out.append(r"\addlinespace[2pt]")
        previous_case = r["case_id"]
        dagger = r"^{\dagger}" if r["event_structure_anomaly"] else ""
        width = f"${r['max_reported_event_interval_width']:.4f}{dagger}$"
        out.append(f"{r['case_id']} & {r['N']} & " +
                   " & ".join((tex_sci(r['signed_cost_difference'],True),
                                tex_sci(r['capacity_excess']),width,
                                tex_sci(r['state_discrepancy']))) + r"\\")
    out += [r"\bottomrule",r"\end{tabular}",r"\par\smallskip",
            r"\begin{minipage}{0.98\linewidth}\footnotesize",
            r"标 $^{\dagger}$ 的两行均未检出容量维持阶段的起止时刻。完全追踪的起始候选区间在 E2、E4 中分别跨越 11 和 8 个网格单元，均超过允许的 2 个单元。",
            r"\end{minipage}",r"\end{table}",""]
    return "\n".join(out)


def main() -> None:
    rows, metadata_differences = extract_rows()
    csv_path = ROOT / "data/revision_grid_errors.csv"
    csv_path.parent.mkdir(parents=True,exist_ok=True)
    with csv_path.open("w",encoding="utf-8",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    generated = ROOT / "latex/generated"
    generated.mkdir(parents=True,exist_ok=True)
    (generated/"grid_error_table.tex").write_text(table_tex(rows,False),encoding="utf-8")
    (generated/"grid_error_summary.tex").write_text(
        table_tex([r for r in rows if r["case_id"] in ("E2","E4")],True),encoding="utf-8")
    report = {
        "source_commit":"09140ec16983fa98f1103b873fc03706ff7dd627",
        "source":str(SOURCE.relative_to(ROOT)),
        "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "row_count":len(rows),
        "new_optimization_solves":0,
        "new_ode_reintegrations":0,
        "numeric_fields_agree_with_compact_summary":True,
        "checked_compact_numeric_fields":["J_openocl","capacity_excess","state_discrepancy"],
        "checked_compact_metadata_fields":["configuration_id","observed_structure"],
        "checked_compact_event_fields":["status","interval"],
        "historical_id_differences":metadata_differences,
        "id_policy":(
            "Preserve source-run identity from detailed summary; do not rewrite old IDs. "
            "Detailed and compact summaries refer to distinct saved runs. Agreement of the "
            "listed summary fields is not evidence of additional independent experiments."
        ),
        "raw_array_crosswalk_report":(
            "validation/chatgpt_integration_20261117/run_identity_crosswalk.json"
        ),
        "anomalous_rows":[{"case_id":r["case_id"],"N":r["N"],
            "missing_events":r["expected_event_missing"]} for r in rows if r["event_structure_anomaly"]],
    }
    report_path=ROOT/"data/revision_grid_error_audit.json"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated {len(rows)} rows; 0 optimization solves; 0 ODE reintegrations.")
    print("Detailed-source IDs are retained; compact-summary numeric values agree.")
    print("Anomalous rows: "+", ".join(f"{r['case_id']}/n={r['N']}" for r in rows if r['event_structure_anomaly']))


if __name__ == "__main__":
    main()
