"""只读第 8--9 步真实记录，另存详细摘要；不调用优化器或改写原结果。

默认要求四组执行报告及两份独立初猜核验报告齐备。
--allow-incomplete 仅用于检查尚未齐备的数据，不代表实验完成。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.io import loadmat


GROUPS = ("initialization", "grid", "horizon", "threshold")
EVENTS = ("intervention", "capacity_enter", "capacity_exit", "full_start", "release")


def many(value):
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, np.ndarray):
        return list(value.reshape(-1))
    return list(value) if isinstance(value, (tuple, list)) else [value]


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def num(value):
    try:
        if value is None or np.size(value) != 1:
            return None
        result = float(np.asarray(value).item())
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def vec(value):
    return np.asarray(value if value is not None else [], dtype=float).reshape(-1)


def flag(value):
    return bool(value) if np.size(value) == 1 else False


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def long_path(path):
    absolute = str(path.resolve())
    return "\\\\?\\" + absolute if os.name == "nt" and not absolute.startswith("\\\\?\\") else absolute


def sha256(path):
    h = hashlib.sha256()
    with open(long_path(path), "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_mat(path, key):
    return loadmat(long_path(path), simplify_cells=True)[key]


def finite_interval(event):
    v = vec(event.get("interval"))
    return v if len(v) == 2 and np.all(np.isfinite(v)) else None


def event_rows(events):
    out = {}
    for name in EVENTS:
        event = events.get(name, {}) if isinstance(events, dict) else {}
        interval = finite_interval(event)
        width = float(interval[1] - interval[0]) if interval is not None else None
        out[name] = {
            **clean(event),
            "original_interval_width": width,
            "original_interval": clean(interval),
        }
    return out


def comparable(run):
    a = run.get("assessment", {})
    diagnostic = a.get("event_detection", {}).get("diagnostics", {})
    return (flag(run.get("success", False)) and num(run.get("J_openocl")) is not None
            and bool(a.get("observed_structure")) and flag(diagnostic.get("passed", False))
            and isinstance(a.get("structured_events"), dict))


def events_compare(base, other):
    """仅比较两份真实事件；不把解析事件或预期结构写入观测字段。"""
    available = comparable(base) and comparable(other)
    aa = base.get("assessment", {})
    bb = other.get("assessment", {})
    same_structure = bool(aa.get("observed_structure")) and aa.get("observed_structure") == bb.get("observed_structure")
    out = {"comparison_available": available, "same_observed_structure": same_structure,
           "reference_structure": aa.get("observed_structure"), "other_structure": bb.get("observed_structure"),
           "events": {}, "passed": False}
    passed = available and same_structure
    for name in EVENTS:
        a = aa.get("structured_events", {}).get(name, {})
        b = bb.get("structured_events", {}).get(name, {})
        ia, ib = finite_interval(a), finite_interval(b)
        ca, cb = num(a.get("candidate_count")), num(b.get("candidate_count"))
        distance, allowed = None, None
        event_pass = False
        if ca == cb == 1 and ia is not None and ib is not None:
            distance = max(float(ia[0] - ib[1]), float(ib[0] - ia[1]), 0.0)
            widths = [num(a.get("local_max_cell_width")), num(b.get("local_max_cell_width"))]
            if all(v is not None for v in widths):
                allowed = max(widths)
                event_pass = available and distance <= allowed + 1e-10
        elif ca == cb == 0:
            event_pass = available
        out["events"][name] = {
            "reference_status": a.get("status"), "other_status": b.get("status"),
            "reference_candidate_count": ca, "other_candidate_count": cb,
            "reference_interval": clean(ia), "other_interval": clean(ib),
            "reference_interval_width": float(np.diff(ia)[0]) if ia is not None else None,
            "other_interval_width": float(np.diff(ib)[0]) if ib is not None else None,
            "distance_between_intervals": distance, "allowed_cell_width": allowed, "passed": event_pass,
        }
        passed = passed and event_pass
    out["passed"] = passed
    return out


def window_compare(base, other):
    out = {"interval": [0, 18], "same_control_step": False, "state_max_abs_difference": None,
           "control_max_abs_difference": None,
           "sampling": "common original control starts and reintegrated state nodes; no interpolation",
           "tolerance_interpretation": "no additional state/control amplitude acceptance tolerance was predeclared"}
    a = base.get("assessment", {}).get("reintegration", {})
    b = other.get("assessment", {}).get("reintegration", {})
    ta, tb = vec(a.get("t")), vec(b.get("t"))
    ma, mb = ta <= 18 + 1e-10, tb <= 18 + 1e-10
    if sum(ma) == 0 or sum(ma) != sum(mb) or np.max(np.abs(ta[ma] - tb[mb])) > 1e-10:
        return out
    qa, qb = vec(base.get("q_control")), vec(other.get("q_control"))
    ca, cb = vec(base.get("t_control")) <= 18 + 1e-10, vec(other.get("t_control")) <= 18 + 1e-10
    if len(qa) != len(ca) or len(qb) != len(cb) or sum(ca) != sum(cb):
        return out
    xa = np.column_stack((vec(a.get("s"))[ma], vec(a.get("i"))[ma]))
    xb = np.column_stack((vec(b.get("s"))[mb], vec(b.get("i"))[mb]))
    out.update(same_control_step=True, state_max_abs_difference=float(np.max(np.abs(xa - xb))),
               control_max_abs_difference=float(np.max(np.abs(qa[ca] - qb[cb]))))
    return out


class Evidence:
    def __init__(self, project, allow_incomplete):
        self.project = project
        self.validation = project / "validation/numerical_scenarios"
        self.data = project / "data/numerical_scenarios"
        self.checks = self.data / "revision_checks"
        self.baseline = read_json(self.validation / "step89_baseline.json")
        self.inputs = []
        self.record_input(self.validation / "step89_baseline.json")
        self.issues = []
        self.raw = {}
        self.raw_meta = {}
        self.assessments = {}
        self.reports = {}
        self.summaries = {}
        self.allow_incomplete = allow_incomplete
        self.sources = self.read(self.validation / "step89_source_fingerprints.json") or {}
        self.index = self.read(self.data / "run_index.json") or {"entries": []}
        self.selection = self.read(self.data / "selection_manifest.json") or {"entries": []}
        for group in GROUPS:
            report = self.read(self.validation / f"step89_{group}_report.json")
            summary = self.read(self.checks / f"{group}_summary.json")
            if report:
                self.reports[group] = report
                self.read(Path(report["manifest_file"]))
                if not report.get("finished_utc"):
                    self.issues.append(f"{group}: execution report has no finished_utc")
            if summary:
                self.summaries[group] = summary
            if report and summary:
                reported_rows = many(report.get("threshold", {}).get("rows")) if group == "threshold" else many(report.get("rows"))
                fields = ("case_id", "run_id", "control_threshold", "capacity_threshold") if group == "threshold" else ("case_id", "configuration_id", "run_id", "solve_fingerprint")
                reported_keys = sorted(json.dumps([r.get(k) for k in fields]) for r in reported_rows)
                summary_keys = sorted(json.dumps([r.get(k) for k in fields]) for r in many(summary.get("rows")))
                if reported_keys != summary_keys:
                    self.issues.append(f"{group}: final report and original summary do not reference the same saved rows")
            csv_path = self.checks / f"{group}_summary.csv"
            if csv_path.exists():
                self.record_input(csv_path)
                with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                    csv_rows = list(csv.DictReader(stream))
                if summary and len(csv_rows) != len(many(summary.get("rows"))):
                    self.issues.append(f"{group}: original CSV/JSON row counts differ")
            else:
                self.issues.append(f"missing input: {csv_path.relative_to(project)}")
        self.integrity = self.read(self.validation / "step89_integrity_report.json")
        self.initialization_validation = self.read(self.validation / "step89_initialization_validation.json")
        if self.integrity is not None and self.integrity.get("passed") is not True:
            self.issues.append("independent source/initial-guess integration report does not confirm passed=true")
        if self.initialization_validation is not None and self.initialization_validation.get("passed") is not True:
            self.issues.append("MATLAB actual-initialization/seed validation report does not confirm passed=true")
        self.startup = self.read(self.validation / "step89_startup_attempts.json")
        self.preflight = self.read(self.validation / "step89_preflight.json")
        if self.issues and not allow_incomplete:
            raise RuntimeError("Evidence is not complete: " + "; ".join(self.issues))
        self.load_assessments()

    def record_input(self, path):
        try:
            label = path.resolve().relative_to(self.project).as_posix()
        except ValueError:
            label = str(path.resolve())
        item = {"path": label, "sha256": sha256(path), "bytes": os.stat(long_path(path)).st_size}
        if item not in self.inputs:
            self.inputs.append(item)

    def read(self, path):
        if not path.exists():
            self.issues.append(f"missing input: {path}")
            return None
        self.record_input(path)
        return read_json(path)

    def load_assessments(self):
        desired = self.sources.get("assessment", {}).get("hash")
        for path in (self.checks / "assessments").glob("*.mat"):
            record = load_mat(path, "assessment_record")
            rid = record["run_id"]
            ap = record.get("assessment_provenance", {})
            item = (ap.get("code_hash") == desired, ap.get("checked_utc", ""), record, path)
            current = self.assessments.get(rid)
            if current is None or item[:2] > current[:2]:
                self.assessments[rid] = item

    def run(self, run_id):
        if run_id in self.raw:
            return self.raw[run_id]
        matches = [e for e in many(self.index.get("entries")) if e.get("run_id") == run_id]
        if len(matches) != 1:
            self.issues.append(f"run_index match count {len(matches)} for {run_id}")
            return {}
        entry = matches[0]
        path = self.data / entry["raw_file"]
        run = load_mat(path, "run")
        digest = sha256(path)
        self.record_input(path)
        valid = digest == entry.get("raw_sha256") and run.get("run_id") == run_id
        valid = valid and run.get("solve_fingerprint") == entry.get("solve_fingerprint")
        if not valid:
            self.issues.append(f"raw record/index mismatch: {run_id}")
        assessment = self.assessments.get(run_id)
        assessment_path = None
        if assessment:
            _, _, record, apath = assessment
            self.record_input(apath)
            assessment_path = apath.relative_to(self.project).as_posix()
            if record.get("solve_fingerprint") != run.get("solve_fingerprint"):
                self.issues.append(f"assessment/raw fingerprint mismatch: {run_id}")
            else:
                run = {**run, **{k: record[k] for k in ("reference", "assessment", "assessment_provenance", "assessment_fingerprint", "assessment_settings")}}
        self.raw[run_id] = run
        solve_source_matches = run.get("provenance", {}).get("solve_code_hash") == self.sources.get("solve", {}).get("hash")
        assessment_source_matches = run.get("assessment_provenance", {}).get("code_hash") == self.sources.get("assessment", {}).get("hash")
        if not solve_source_matches:
            self.issues.append(f"saved solve source hash differs from execution freeze: {run_id}")
        if flag(run.get("success", False)) and not assessment_source_matches:
            self.issues.append(f"successful run lacks matching frozen assessment source: {run_id}")
        self.raw_meta[run_id] = {"raw_file": entry["raw_file"], "raw_sha256": digest,
                                 "raw_integrity_pass": valid, "assessment_file": assessment_path,
                                 "solve_source_hash_matches_execution_freeze": solve_source_matches,
                                 "assessment_source_hash_matches_execution_freeze": assessment_source_matches}
        return run

    def detail(self, row, group):
        run = self.run(row.get("run_id", ""))
        if run and (row.get("solve_fingerprint") != run.get("solve_fingerprint") or row.get("case_id") != run.get("case_id")):
            self.issues.append(f"summary/index identity mismatch: {row.get('run_id')}")
        a = run.get("assessment", {})
        reference = run.get("reference", {})
        initial = run.get("initialization", {})
        ig = run.get("initial_guess", {})
        provenance = run.get("provenance", {})
        settings = run.get("solver_settings", {})
        out = {**clean(row), "group": group, "T": num(settings.get("T")), "N": num(settings.get("N")),
               "d": num(settings.get("d")), "initialization": initial.get("type"),
               "initialization_seed": num(initial.get("seed")),
               "initialization_definition": clean({k: v for k, v in initial.items() if k != "actual_control_guess"}),
               "initial_guess_capacity_excess": num(ig.get("capacity_excess")),
               "initial_guess_ode_sample_capacity_excess": num(ig.get("ode_sample_capacity_excess")),
               "initial_guess_integrator_sample_capacity_excess": num(ig.get("integrator_sample_capacity_excess")),
               "initial_guess_state_control_correspondence": ig.get("state_control_correspondence"),
               "solve_commit": provenance.get("solve_commit"), "solve_code_hash": provenance.get("solve_code_hash"),
               "solve_dirty": flag(provenance.get("solve_dirty")) if "solve_dirty" in provenance else None,
               "solve_started_utc": provenance.get("solve_started_utc"), "solve_finished_utc": provenance.get("solve_finished_utc"),
               "source_status": run.get("source_status"), "attempt": num(run.get("attempt")),
               "assessment_provenance": clean(run.get("assessment_provenance", {})),
               "solver_diagnostics": clean(run.get("solver_diagnostics", {})),
               "failure": clean(run.get("failure")), "output_validation": clean(run.get("output_validation")),
               **self.raw_meta.get(row.get("run_id"), {})}
        for key in ("success", "return_status", "J_openocl"):
            out[key] = clean(run.get(key, row.get(key)))
        out["success"] = flag(run.get("success", row.get("success", False)))
        for key in ("numeric_pass", "agreement_pass", "capacity_excess", "state_discrepancy", "tail_max_q", "terminal_peak",
                    "terminal_safe", "provenance_pass", "problem_pass", "numeric_checks", "signed_extrema", "cost_agreement"):
            out[key] = clean(a.get(key))
        for key in ("numeric_pass", "agreement_pass", "terminal_safe", "provenance_pass", "problem_pass"):
            out[key] = flag(a[key]) if key in a else None
        out["numeric_failure_reasons"] = [name for name, passed in a.get("numeric_checks", {}).items() if not flag(passed)]
        out["agreement_failure_reasons"] = []
        if a:
            agreement_components = {
                "cost_agreement": a.get("cost_agreement", {}).get("passed"),
                "event_detection_diagnostics": a.get("event_detection", {}).get("diagnostics", {}).get("passed"),
                "observed_structure_comparison": a.get("event_comparison", {}).get("structure_pass"),
                "event_comparison": a.get("event_comparison", {}).get("event_pass"),
                "capacity_control_comparison": a.get("event_comparison", {}).get("capacity_control", {}).get("passed"),
            }
            out["agreement_failure_reasons"] = [name for name, passed in agreement_components.items() if passed is not None and not flag(passed)]
        else:
            out["numeric_failure_reasons"] = ["assessment_not_available"]
            out["agreement_failure_reasons"] = ["assessment_not_available"]
        out["tail"] = clean(a.get("tail", {}))
        out["J_reference"] = num(reference.get("J_reference"))
        out["signed_cost_difference_to_reference"] = num(a.get("signed_cost_difference"))
        out["relative_cost_difference_to_reference"] = num(a.get("relative_cost_difference"))
        main_entry = next((e for e in many(self.selection.get("entries")) if e.get("case_id") == row.get("case_id")), {})
        main = self.run(main_entry.get("run_id", "")) if main_entry else {}
        jm, j = num(main.get("J_openocl")), num(run.get("J_openocl"))
        out["main_reference_run_id"] = main_entry.get("run_id")
        out["signed_cost_difference_to_main"] = j - jm if j is not None and jm is not None else None
        out["same_discrete_problem_as_main"] = clean(settings) == clean(main.get("solver_settings", {}))
        # 求解设置中的 initialization 字段必然不同；同离散问题只忽略这一字段。
        aopts = {k: clean(v) for k, v in settings.items() if k != "initialization"}
        bopts = {k: clean(v) for k, v in main.get("solver_settings", {}).items() if k != "initialization"}
        out["same_discrete_problem_as_main"] = aopts == bopts and clean(run.get("parameters")) == clean(main.get("parameters")) and clean(run.get("x0")) == clean(main.get("x0"))
        detected = row.get("detection", {}) if group == "threshold" else a.get("event_detection", {})
        events = detected.get("events", {}) if group == "threshold" else a.get("structured_events", {})
        out["observed_structure"] = detected.get("observed_structure", a.get("observed_structure"))
        out["events"] = event_rows(events)
        out["event_detection_diagnostics"] = clean(detected.get("diagnostics", {}))
        out["event_comparison"] = clean(row.get("event_comparison", a.get("event_comparison", {})))
        out["numeric_agreement_flags_source"] = "saved source-run assessment; threshold mode only reruns event detection" if group == "threshold" else "saved source-run assessment"
        if group == "threshold":
            out["optimizer_called_this_detection"] = False
        for name, event in out["events"].items():
            interval = event.get("original_interval")
            out[f"{name}_interval_left"] = interval[0] if interval else None
            out[f"{name}_interval_right"] = interval[1] if interval else None
            out[f"{name}_interval_width"] = event.get("original_interval_width")
            out[f"{name}_status"] = event.get("status")
            out[f"{name}_candidate_count"] = event.get("candidate_count")
        return out


def case_comparisons(evidence, details):
    result = {}
    escalation = []
    for group in ("initialization", "grid", "horizon"):
        out = []
        original = {r["case_id"]: r for r in many(evidence.summaries.get(group, {}).get("case_comparisons"))}
        for case in (f"E{k}" for k in range(1, 6)):
            rows = [r for r in details[group] if r.get("case_id") == case]
            runs = [evidence.run(r["run_id"]) for r in rows]
            comparison = {"case_id": case, "status": "failed_or_incomplete", "plan_suggested_consistency_pass": False,
                          "original_stricter_comparison": clean(original.get(case)), "source_run_ids": [r.get("run_id") for r in rows],
                          "reasons": []}
            if group == "initialization":
                entry = next((e for e in many(evidence.selection.get("entries")) if e.get("case_id") == case), {})
                base = evidence.run(entry.get("run_id", "")) if entry else {}
                comparison["reference_run_id"] = entry.get("run_id")
                checks = []
                for row, run in zip(rows, runs):
                    gap = row["signed_cost_difference_to_main"]
                    ec = events_compare(base, run)
                    numeric = flag(base.get("assessment", {}).get("numeric_pass", False)) and row.get("numeric_pass") is True
                    passed = numeric and row["same_discrete_problem_as_main"] and ec["passed"] and gap is not None and abs(gap) <= 1e-5
                    checks.append({"run_id": row["run_id"], "initialization": row["initialization"], "seed": row["initialization_seed"],
                                   "signed_cost_difference_to_main": gap, "numeric_comparison_accepted": numeric,
                                   "events": ec, "passed": passed})
                comparison["initialization_comparisons"] = checks
                comparison["plan_suggested_consistency_pass"] = len(checks) == 2 and all(c["passed"] for c in checks)
            elif group == "grid":
                pairs = sorted(zip(rows, runs), key=lambda x: x[0]["N"] or -1)
                if len(pairs) >= 2:
                    second_row, second = pairs[-2]
                    finest_row, finest = pairs[-1]
                    j1, j2 = num(finest.get("J_openocl")), num(second.get("J_openocl"))
                    relative = abs(j1 - j2) / max(abs(j1), 1e-12) if j1 is not None and j2 is not None else None
                    ec = events_compare(finest, second)
                    comparison.update(reference_run_id=finest_row["run_id"], finest_N=finest_row["N"], second_finest_N=second_row["N"],
                                      finest_numeric_pass=finest_row["numeric_pass"], second_finest_numeric_pass=second_row["numeric_pass"],
                                      finest_relative_cost_difference=relative, finest_event_comparison=ec,
                                      interpretation="only finest numeric_pass is required by the plan suggestion; the second level must have real comparable structure/events")
                    comparison["plan_suggested_consistency_pass"] = len(rows) == 3 and finest_row["numeric_pass"] is True and ec["passed"] and relative is not None and relative <= 1e-4
                if not comparison["plan_suggested_consistency_pass"]:
                    reason = "N=8000 finest numeric diagnosis, actual event/structure comparability, or finest-pair relative cost target failed or was incomplete"
                    comparison["reasons"].append(reason)
                    escalation.append({"case_id": case, "suggested_configuration": {"T": 300, "N": 16000, "d": 2},
                                       "reason": reason, "executed": False, "requires_separate_declared_additional_experiment": True})
            else:
                pairs = sorted(zip(rows, runs), key=lambda x: x[0]["T"] or -1)
                if pairs:
                    base_row, base = pairs[-1]
                    costs = [num(r.get("J_openocl")) for _, r in pairs]
                    span = max(costs) - min(costs) if len(costs) == 3 and all(c is not None for c in costs) else None
                    checks = []
                    for row, run in pairs:
                        ec = events_compare(base, run)
                        window = window_compare(base, run)
                        tail = run.get("assessment", {}).get("tail", {})
                        tail_pass = flag(tail.get("control_returned_to_zero", False)) and flag(tail.get("zero_control_continuation_safe", False))
                        checks.append({"run_id": row["run_id"], "T": row["T"], "N": row["N"], "numeric_pass": row["numeric_pass"],
                                       "tail": clean(tail), "tail_pass": tail_pass, "common_window": window, "events": ec,
                                       "signed_cost_difference_to_T300_same_step": num(run.get("J_openocl")) - num(base.get("J_openocl")) if num(run.get("J_openocl")) is not None and num(base.get("J_openocl")) is not None else None,
                                       "passed": row["numeric_pass"] is True and tail_pass and ec["passed"] and window["same_control_step"]})
                    comparison.update(reference_run_id=base_row["run_id"], reference_T=base_row["T"], reference_N=base_row["N"],
                                      cost_absolute_span=span, horizon_comparisons=checks)
                    comparison["plan_suggested_consistency_pass"] = len(checks) == 3 and span is not None and span <= 1e-5 and all(c["passed"] for c in checks)
                if not comparison["plan_suggested_consistency_pass"]:
                    reason = "tested horizon numeric/tail/event/shared-step diagnosis or cost span target failed or was incomplete"
                    comparison["reasons"].append(reason)
                    escalation.append({"case_id": case, "suggested_configuration": {"T": 600, "N": 16000, "d": 2, "dt": 0.0375},
                                       "reason": reason, "executed": False, "requires_separate_declared_additional_experiment": True})
            if comparison["plan_suggested_consistency_pass"]:
                comparison["status"] = "passed"
            elif not comparison["reasons"]:
                comparison["reasons"] = ["saved numeric diagnosis, same-discrete-problem check, events or cost target failed or incomplete"]
            out.append(comparison)
        result[group] = out
    return result, escalation


def write_csv(path, rows):
    # 完整 detection（含全部网格单元索引）已保留于 JSON；CSV 使用实际事件及诊断列。
    # 避免将同一份数十万字符的检测对象重复塞入每个 CSV 单元格。
    keys = list(dict.fromkeys(k for row in rows for k in row if k != "detection"))
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(clean(v), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                             if isinstance(v, (dict, list, tuple, np.ndarray)) else clean(v) for k, v in row.items() if k in keys})


def fmt(value):
    value = num(value)
    return "未验证" if value is None else f"{value:.12g}"


def render_markdown(report):
    counts = report["execution_counts"]
    lines = ["# 第 8--9 步真实执行摘要", "", "本文件由保存的执行报告、原始求解记录及独立评估生成；计划中的预期值未作为实验结果。",
             "", f"协议执行状态：`{report['protocol_status']}`；计划建议的初猜、最细网格及时域稳定性判定：`{report['consistency_status']}`；原矩阵严格判定：`{report['original_stricter_execution_consistency_pass']}`。",
             f"本批实际优化 {counts['actual_new_raw_solver_records']} 次：成功 {counts['actual_new_raw_successes']}、失败 {counts['actual_new_raw_failures']}；四组执行报告缓存命中 {counts['reported_cache_hits']} 次。",
             f"默认配置覆盖 {report['coverage']['observed_distinct_configurations']}/35；阈值复核 {report['threshold']['observed_rows']}/45 条，优化器调用 {report['threshold']['optimizer_calls']} 次。",
             f"35 个配置中，逐条 numeric_pass={report['coverage']['numeric_pass_distinct_configurations']}、agreement_pass={report['coverage']['agreement_pass_distinct_configurations']}，两者同时通过={report['coverage']['numeric_and_agreement_pass_distinct_configurations']}。全部尝试与求解器成功不代表这些逐条诊断均通过。",
             "", "各组执行记录：", "", "| 组 | 状态 | solver | cache | 成功 | 失败 | numeric | agreement |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for group, summary in report["execution_reports"].items():
        lines.append("| " + " | ".join(str(summary.get(k, "未验证")) for k in ("mode", "status", "solver_calls", "cache_hits", "successful_count", "failed_count", "numeric_pass_count", "agreement_pass_count")) + " |")
    lines += ["", "常值及固定种子随机初猜与主结果的带符号成本差：", "", "| 例 | 初猜 | seed | success | numeric | agreement | 初猜容量超出 | J−Jmain |", "|---|---|---:|---|---|---|---:|---:|"]
    for row in report["groups"]["initialization"]["rows"]:
        seed = "--" if row["initialization"] == "constant_control" else fmt(row["initialization_seed"])
        lines.append(f"| {row['case_id']} | {row['initialization']} | {seed} | {row['success']} | {row['numeric_pass']} | {row['agreement_pass']} | {fmt(row['initial_guess_capacity_excess'])} | {fmt(row['signed_cost_difference_to_main'])} |")
    lines += ["", "最细两级网格：保留原汇总判定，并独立计算计划建议判定；次细级的容量失败仍完整记录。", "", "| 例 | N次细/最细 | numeric次细/最细 | 相对成本差 | 原严格判定 | 计划建议判定 |", "|---|---|---|---:|---|---|"]
    for row in report["case_comparisons"]["grid"]:
        original = row.get("original_stricter_comparison") or {}
        lines.append(f"| {row['case_id']} | {fmt(row.get('second_finest_N'))}/{fmt(row.get('finest_N'))} | {row.get('second_finest_numeric_pass')}/{row.get('finest_numeric_pass')} | {fmt(row.get('finest_relative_cost_difference'))} | {original.get('consistency_pass')} | {row['plan_suggested_consistency_pass']} |")
    lines += ["", "固定步长时域成本跨度及尾段：", "", "| 例 | 完整成本跨度 | 全部尾段通过 | 计划建议判定 |", "|---|---:|---|---|"]
    for row in report["case_comparisons"]["horizon"]:
        checks = row.get("horizon_comparisons", [])
        lines.append(f"| {row['case_id']} | {fmt(row.get('cost_absolute_span'))} | {len(checks) == 3 and all(c['tail_pass'] for c in checks)} | {row['plan_suggested_consistency_pass']} |")
    lines += ["", "[0,18] 的逐项控制/轨道差、全部原事件区间及宽度、最后 20 时间单位控制和终端 P0 见 JSON 与四组 `*_detailed_summary.csv`。未预设幅值接受门槛的窗口差保留为实测诊断，不追加任意阈值。",
              "", f"未解决差异 {len(report['unresolved_discrepancies'])} 条；求解失败 {len(report['solver_failures'])} 条；数值诊断失败 {len(report['numeric_failures'])} 条；解析一致性失败 {len(report['agreement_failures'])} 条。"]
    failed = {r["run_id"]: r for kind in ("solver_failures", "numeric_failures", "agreement_failures") for r in report[kind]}
    if failed:
        lines += ["", "失败或未验证记录保留如下（原始数组、日志及详细事件未删除）：", "", "| 例 | T | N | 初猜 | success/numeric/agreement | 容量超出 | 相对成本差 | q_B最大差 | 失败分量 |", "|---|---:|---:|---|---|---:|---:|---:|---|"]
        for row in sorted(failed.values(), key=lambda r: (r["case_id"], r["T"] or -1, r["N"] or -1)):
            reasons = row["numeric_failure_reasons"] + row["agreement_failure_reasons"]
            if not row["success"]:
                reasons = [row.get("return_status")] + reasons
            qb_error = row.get("event_comparison", {}).get("capacity_control", {}).get("max_absolute_error")
            qb_display = "--" if num(qb_error) is None else fmt(qb_error)
            lines.append(f"| {row['case_id']} | {fmt(row['T'])} | {fmt(row['N'])} | {row['initialization']} | {row['success']}/{row['numeric_pass']}/{row['agreement_pass']} | {fmt(row['capacity_excess'])} | {fmt(row['relative_cost_difference_to_reference'])} | {qb_display} | {', '.join(str(v) for v in reasons)} |")
        lines.append("")
        for row in sorted(failed.values(), key=lambda r: (r["case_id"], r["T"] or -1, r["N"] or -1)):
            diagnostics = row.get("event_detection_diagnostics", {})
            issues = many(diagnostics.get("issues"))
            if issues:
                intervals = [f"{name}={event.get('original_interval')}（{event.get('transition_cells')} 单元）" for name, event in row["events"].items() if num(event.get("transition_cells")) is not None and num(event.get("transition_cells")) > 2]
                lines.append(f"- {row['case_id']}，N={fmt(row['N'])}：实际识别结构 `{row['observed_structure']}`；诊断 `{', '.join(str(v) for v in issues)}`；" + "，".join(intervals) + "。")
    for item in report["unresolved_discrepancies"]:
        lines.append(f"- `{item['run_id']}` {item['reason']}")
    if report["suggested_additional_experiments_not_run"]:
        lines += ["", "以下条件追加实验未运行："]
        for item in report["suggested_additional_experiments_not_run"]:
            lines.append(f"- {item['case_id']}：{item['suggested_configuration']}；原因：{item['reason']}。")
    lines += ["", "求解来源（原始记录的来源字段未改写）：", ""]
    for item in report["solve_provenance_groups"]:
        lines.append(f"- solve_commit `{item['solve_commit']}`；solve_code_hash `{item['solve_code_hash']}`；solve_dirty `{item['solve_dirty']}`；记录 {item['count']} 条。")
    lines += ["", "独立初猜积分核验和 MATLAB 种子/实际输入核验分别见 `step89_integrity_report.json`、`step89_initialization_validation.json`；完整内容与输入哈希并入本报告。",
              f"独立初猜状态积分最大差 {fmt((report.get('independent_integrity_and_initial_guess_integration') or {}).get('max_independent_initial_guess_state_difference'))}；原控制独立重积分节点最大差 {fmt((report.get('independent_integrity_and_initial_guess_integration') or {}).get('max_independent_original_control_node_difference'))}。",
              f"汇总实际使用 Python {report['summary_runtime']['python_version']}、NumPy {report['summary_runtime']['numpy_version']}、SciPy {report['summary_runtime']['scipy_version']}；入口为 `{report['summary_runtime']['python_executable']}`。独立完整性复核的实际运行环境另保留在其原报告中。",
              "", "本批未编译 main.pdf，未更新正文、主选择或图表，未覆写既有原始记录。浮点接受、有限网格趋势及多初猜重复收敛均不构成连续问题严格可行性、收敛定理或全局唯一性证明。", ""]
    if report["input_issues"]:
        lines += ["输入证据问题：", ""] + [f"- {item}" for item in report["input_issues"]] + [""]
    return "\n".join(lines)


def summarize(project, allow_incomplete=False):
    evidence = Evidence(project, allow_incomplete)
    details = {group: [evidence.detail(row, group) for row in many(evidence.summaries.get(group, {}).get("rows"))] for group in GROUPS}
    comparisons, escalation = case_comparisons(evidence, details)
    baseline_ids = {r["run_id"] for r in many(evidence.baseline["run_index_entries_at_start"])}
    new_entries = [r for r in many(evidence.index.get("entries")) if r["run_id"] not in baseline_ids]
    new_rows = [evidence.detail(r, "new_raw_attempt") for r in new_entries]
    observed = {row.get("configuration_id") for group in GROUPS for row in many(evidence.reports.get(group, {}).get("rows")) if row.get("run_id")}
    manifests = []
    for report in evidence.reports.values():
        path = Path(report["manifest_file"])
        if path.exists():
            manifests.append(read_json(path))
    default = many(manifests[0].get("default_experiments")) if manifests else []
    expected = {row["configuration_id"] for row in default}
    if manifests:
        protocol_hashes = {m.get("protocol_hash") for m in manifests}
        solve_hashes = {m.get("solve_code_hash") for m in manifests}
        config_fingerprints = {e.get("configuration_fingerprint") for e in default}
        if len(protocol_hashes) != 1 or protocol_hashes != {evidence.sources.get("protocol_hash")}:
            evidence.issues.append("four group manifests do not share the frozen protocol hash")
        if solve_hashes != {evidence.sources.get("solve", {}).get("hash")}:
            evidence.issues.append("four group manifests do not share the frozen solve source hash")
        if len(default) != 35 or len(config_fingerprints) != 35:
            evidence.issues.append("default manifest does not contain 35 distinct actual configurations")
    numeric_ids, agreement_ids = set(), set()
    for report in evidence.reports.values():
        for row in many(report.get("rows")):
            if row.get("numeric_pass"):
                numeric_ids.add(row["configuration_id"])
            if row.get("agreement_pass"):
                agreement_ids.add(row["configuration_id"])
    thresholds = details["threshold"]
    unique_thresholds = {(r.get("case_id"), r.get("control_threshold"), r.get("capacity_threshold")) for r in thresholds}
    expected_thresholds = {(case, q, capacity) for case in (f"E{k}" for k in range(1, 6))
                           for q in many(manifests[0].get("threshold_control")) for capacity in many(manifests[0].get("threshold_capacity"))} if manifests else set()
    if thresholds and unique_thresholds != expected_thresholds:
        evidence.issues.append("threshold rows do not match the frozen five-case control/capacity threshold combinations")
    threshold_report = evidence.reports.get("threshold", {})
    threshold_optimizer = evidence.summaries.get("threshold", {}).get("optimizer_calls")
    threshold_zero = threshold_optimizer == 0 and threshold_report.get("solver_calls") == 0
    counts = {"actual_new_raw_solver_records": len(new_rows), "actual_new_raw_successes": sum(r.get("success") is True for r in new_rows),
              "actual_new_raw_failures": sum(r.get("success") is not True for r in new_rows),
              "reported_solver_calls": sum(r.get("solver_calls", 0) for r in evidence.reports.values()),
              "reported_cache_hits": sum(r.get("cache_hits", 0) for r in evidence.reports.values()),
              "reported_assessment_calls": sum(r.get("assessment_calls", 0) for r in evidence.reports.values()),
              "reported_attempted_count": sum(r.get("attempted_count", 0) for r in evidence.reports.values())}
    if counts["actual_new_raw_solver_records"] != counts["reported_solver_calls"]:
        evidence.issues.append("new raw record count differs from completed four-mode solver call count; retained as separate accounting")
    provenance_groups = {}
    for row in new_rows:
        key = row["solve_commit"], row["solve_code_hash"], row["solve_dirty"]
        provenance_groups.setdefault(key, []).append(row["run_id"])
    unique = {row["run_id"]: row for group in GROUPS for row in details[group]}
    unique.update({row["run_id"]: row for row in new_rows})
    negative, unresolved = [], []
    for row in unique.values():
        signed = row.get("signed_cost_difference_to_reference")
        if signed is not None and signed < 0:
            reference = row.get("J_reference")
            tolerance = 1e-4 * max(abs(reference), 1e-12) if reference is not None else None
            beyond = tolerance is not None and abs(signed) > tolerance
            item = {"run_id": row["run_id"], "case_id": row["case_id"], "signed_cost_difference_to_reference": signed,
                    "numeric_pass": row["numeric_pass"], "capacity_excess": row["capacity_excess"],
                    "cost_tolerance": tolerance, "beyond_predeclared_cost_tolerance": beyond,
                    "numeric_checks": row.get("numeric_checks"), "tail": row["tail"],
                    "interpretation": "small capacity excess does not provide a rigorous bound on its cost effect"}
            negative.append(item)
            if beyond and row["numeric_pass"] is True:
                unresolved.append({**item, "reason": "numerically accepted saved control has cost below analytic reference beyond the predeclared comparison scale; no rigorous explanation established"})
    # 两种初猜在同一离散问题中取得明显较低且数值接受的成本，需要单列调查。
    for row in details["initialization"]:
        gap = row["signed_cost_difference_to_main"]
        if row["numeric_pass"] is True and row["same_discrete_problem_as_main"] and gap is not None and gap < -1e-5:
            unresolved.append({"run_id": row["run_id"], "case_id": row["case_id"], "signed_cost_difference_to_main": gap,
                               "reason": "accepted non-theory initialization found a lower cost than the predeclared main result by more than 1e-5"})
    protocol = (len(evidence.reports) == 4 and all(r.get("protocol_complete") for r in evidence.reports.values())
                and len(details["initialization"]) == 10 and len(details["grid"]) == 15 and len(details["horizon"]) == 15
                and len(thresholds) == len(unique_thresholds) == len(expected_thresholds) == 45
                and unique_thresholds == expected_thresholds and len(expected) == 35 and observed == expected)
    suggested = protocol and all(c["plan_suggested_consistency_pass"] for group in comparisons.values() for c in group)
    suggested = suggested and threshold_zero and all(r.get("consistency_pass") for r in thresholds) and not unresolved
    audits_verified = (evidence.integrity is not None and evidence.integrity.get("passed") is True
                       and evidence.initialization_validation is not None and evidence.initialization_validation.get("passed") is True)
    suggested = suggested and audits_verified
    def finite_max(values):
        actual = [v for v in (num(value) for value in values) if v is not None]
        return max(actual) if actual else None
    measured_maxima = {
        "numeric_accepted_initialization_absolute_cost_difference_to_main": finite_max(
            abs(r["signed_cost_difference_to_main"]) for r in details["initialization"]
            if r["numeric_pass"] is True and r["signed_cost_difference_to_main"] is not None),
        "saved_non_theory_initial_guess_capacity_excess": finite_max(r["initial_guess_capacity_excess"] for r in details["initialization"]),
        "finest_pair_relative_cost_difference": finite_max(c.get("finest_relative_cost_difference") for c in comparisons["grid"]),
        "horizon_cost_absolute_span": finite_max(c.get("cost_absolute_span") for c in comparisons["horizon"]),
        "all_observed_capacity_excess": finite_max(r.get("capacity_excess") for r in unique.values()),
        "all_observed_node_vs_reintegration_discrepancy": finite_max(r.get("state_discrepancy") for r in unique.values()),
        "horizon_common_window_state_difference": finite_max(
            h["common_window"].get("state_max_abs_difference") for c in comparisons["horizon"] for h in c.get("horizon_comparisons", [])),
        "horizon_common_window_control_difference": finite_max(
            h["common_window"].get("control_max_abs_difference") for c in comparisons["horizon"] for h in c.get("horizon_comparisons", [])),
    }
    report = {"schema_version": 1, "scope": "steps_8_to_9", "generated_utc": datetime.now(timezone.utc).isoformat(),
              "summary_runtime": {"python_executable": sys.executable, "python_version": sys.version.split()[0], "numpy_version": np.__version__, "scipy_version": scipy.__version__},
              "summary_provenance": {"script": str(Path(__file__).resolve()), "script_sha256": sha256(Path(__file__)), "optimizer_calls": 0},
              "plan_values_are_expected_only": True, "starting_commit": evidence.baseline["starting_commit"],
              "protocol_hash": evidence.sources.get("protocol_hash"), "execution_source_fingerprints": evidence.sources,
              "protocol_status": "completed" if protocol else "incomplete", "protocol_complete": protocol,
              "consistency_status": "passed" if suggested and not evidence.issues else "failed_or_unverified",
              "consistency_status_definition": "independent plan-suggested initialization/finest-grid/horizon/threshold criterion, with separate preservation of original stricter batch outcomes",
              "plan_suggested_consistency_pass": suggested and not evidence.issues,
              "original_stricter_execution_consistency_pass": len(evidence.reports) == 4 and all(r.get("consistency_pass") for r in evidence.reports.values()),
              "all_default_configurations_numeric_and_agreement_pass": len(expected) == 35 and numeric_ids & agreement_ids == expected,
              "execution_counts": counts, "execution_reports": clean(evidence.reports),
              "startup_attempts": evidence.startup, "preflight": evidence.preflight,
              "coverage": {"default_distinct_configurations": 35, "observed_distinct_configurations": len(observed),
                           "observed_fraction": f"{len(observed)}/35", "numeric_pass_distinct_configurations": len(numeric_ids),
                           "agreement_pass_distinct_configurations": len(agreement_ids), "missing_configuration_ids": sorted(expected - observed),
                           "numeric_and_agreement_pass_distinct_configurations": len(numeric_ids & agreement_ids),
                           "numeric_and_agreement_pass_configuration_ids": sorted(numeric_ids & agreement_ids),
                           "default_configuration_ids": sorted(expected), "observed_configuration_ids": sorted(observed),
                           "interpretation": "coverage counts actual saved attempts or trusted cache references, not expected outcomes"},
              "groups": {g: {"original_summary": clean(evidence.summaries.get(g)), "rows": details[g]} for g in GROUPS},
              "case_comparisons": comparisons,
              "measured_maxima": measured_maxima,
              "threshold": {"observed_rows": len(thresholds), "distinct_combinations": len(unique_thresholds), "optimizer_calls": threshold_optimizer,
                            "zero_solver_calls_verified_from_reports": threshold_zero, "source_run_ids": sorted({r["run_id"] for r in thresholds}),
                            "passed_rows": sum(r.get("consistency_pass") is True for r in thresholds)},
              "all_new_raw_attempts": new_rows,
              "solve_provenance_groups": [{"solve_commit": k[0], "solve_code_hash": k[1], "solve_dirty": k[2], "count": len(v), "run_ids": v} for k, v in provenance_groups.items()],
              "solver_failures": [r for r in unique.values() if r.get("success") is not True],
              "numeric_failures": [r for r in unique.values() if r.get("success") is True and r.get("numeric_pass") is not True],
              "agreement_failures": [r for r in unique.values() if r.get("success") is True and r.get("agreement_pass") is not True],
              "negative_cost_diagnostics": negative, "unresolved_discrepancies": unresolved,
              "suggested_additional_experiments_not_run": escalation,
              "independent_integrity_and_initial_guess_integration": evidence.integrity,
              "matlab_actual_initialization_and_seed_validation": evidence.initialization_validation,
              "independent_audits_verified": audits_verified,
              "input_issues": evidence.issues, "input_evidence": evidence.inputs,
              "main_pdf_compiled_this_batch": False, "theory_or_main_selection_changed_by_this_script": False,
              "optimizer_calls_by_this_script": 0,
              "limits": ["numeric_pass is floating-point acceptance only", "non-theory initialization repetition is not a global uniqueness proof",
                         "three finite grids do not prove continuous convergence", "tested horizons do not prove infinite-horizon equivalence",
                         "original summaries are retained; the independent plan-suggested grid criterion does not require second-finest numeric_pass"]}
    return clean(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--check-only", action="store_true", help="只读核对，不写摘要")
    args = parser.parse_args()
    project = args.project.resolve()
    report = summarize(project, args.allow_incomplete)
    if not args.check_only:
        validation = project / "validation/numerical_scenarios"
        checks = project / "data/numerical_scenarios/revision_checks"
        for group in GROUPS:
            write_csv(checks / f"{group}_detailed_summary.csv", report["groups"][group]["rows"])
        (validation / "step89_validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        (validation / "step89_results.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("protocol_status", "consistency_status", "execution_counts", "coverage", "threshold", "input_issues")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
