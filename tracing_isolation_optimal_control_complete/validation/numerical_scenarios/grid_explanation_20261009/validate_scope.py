"""核对网格解释修订的范围，保护原始科学记录和正文其余内容。"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("\\\\?\\" + str(HERE.parents[2])) if os.name == "nt" else HERE.parents[2]
DATA = ROOT / "data/numerical_scenarios"
MAIN = ROOT / "latex/main.tex"
STATEMENT = re.compile(r"^\\renewcommand\{\\NumRobustnessStatement\}\{.*\}$", re.M)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main_without_statement():
    text = MAIN.read_text(encoding="utf-8")
    text, count = STATEMENT.subn("TARGET_STATEMENT", text)
    assert count == 1
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture():
    protected = list((DATA / "runs").glob("*.mat"))
    protected += list((DATA / "runs").glob("*.solver.json"))
    protected += list((DATA / "revision_checks/assessments").glob("*.mat"))
    protected += [p for p in (ROOT / "figures/numerical_scenarios").glob("*") if p.is_file()]
    protected += [DATA / f"E{k}.mat" for k in range(1, 6)]
    protected += [DATA / name for name in ["selection_manifest.json", "run_index.json", "scenario_summary.csv"]]
    protected += [DATA / "revision_checks" / f"{name}_summary.json" for name in ["initialization", "horizon", "threshold"]]
    protected += [ROOT / "validation/numerical_scenarios" / name for name in ["scenario_inputs.json", "analytic_checkpoints.json"]]
    protected += [ROOT / "latex/references.bib"]
    code = ROOT / "matlab/numerical_scenarios"
    protected += [code / name for name in [
        "numerical_cases_config.m", "numerical_assessment_spec.m", "numerical_code_hash.m",
        "prepare_openocl_case.m", "revision_initial_guess.m", "solve_openocl_case.m", "validate_numerical_run_grid.m",
        "numerical_solver_diagnostics.m", "build_theory_geometry.m", "analytic_reference.m", "classify_initial_state.m",
        "safe_peak.m", "assess_numerical_case.m", "tail_diagnostic.m", "capacity_exit_transition.m",
        "detect_numerical_events.m", "compare_numerical_events.m", "numerical_run_consistency.m",
        "numerical_sha256.m", "assess_saved_numerical_run.m", "numerical_assessment_view.m", "revision_validation_config.m",
    ]]
    assert all(p.is_file() for p in protected), [str(p) for p in protected if not p.is_file()]
    grid = json.loads((DATA / "revision_checks/grid_summary.json").read_text(encoding="utf-8"))
    checks = json.loads((DATA / "numerical_checks.json").read_text(encoding="utf-8"))
    baseline = {
        "protected": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sorted(set(protected))},
        "main_without_statement_sha256": main_without_statement(),
        "grid": grid,
        "numerical_cases": checks["cases"],
    }
    (HERE / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BASELINE_CAPTURED protected_files={len(baseline['protected'])}")


def verify():
    before = json.loads((HERE / "baseline.json").read_text(encoding="utf-8"))
    changed = [name for name, value in before["protected"].items() if digest(ROOT / name) != value]
    assert not changed, changed
    assert main_without_statement() == before["main_without_statement_sha256"]
    grid = json.loads((DATA / "revision_checks/grid_summary.json").read_text(encoding="utf-8"))
    assert grid["rows"] == before["grid"]["rows"]
    for key in ["schema_version", "group", "status", "protocol_complete", "comparison_complete", "consistency_pass", "blockers"]:
        assert grid[key] == before["grid"][key], key
    items = {row["case_id"]: row for row in grid["case_comparisons"]}
    for old in before["grid"]["case_comparisons"]:
        current = items[old["case_id"]]
        for key in old:
            if key != "reasons":
                assert current[key] == old[key], (old["case_id"], key)
    for case in ["E2", "E4"]:
        item = items[case]
        assert item["comparison_status"] == "not_evaluated_due_to_numeric_failure"
        assert item["fine_numeric_pass"] and not item["coarse_numeric_pass"]
        assert item["fine_N"] == 8000 and item["coarse_N"] == 4000
        assert not item["event_comparison_evaluated"] and not item["cost_comparison_evaluated"]
        assert item["event_comparisons"] == [] and item["finest_relative_cost_difference"] is None
        assert not item["consistency_pass"]
    for case in ["E1", "E3", "E5"]:
        item = items[case]
        assert item["comparison_status"] == "evaluated_passed"
        assert item["event_comparison_evaluated"] and item["cost_comparison_evaluated"]
        assert item["consistency_pass"]
    checks = json.loads((DATA / "numerical_checks.json").read_text(encoding="utf-8"))
    assert checks["cases"] == before["numerical_cases"]
    assert checks["verified"] and not checks["robustness"]["consistency_pass"]
    statement = STATEMENT.search(MAIN.read_text(encoding="utf-8")).group()
    assert "最细两级的成本与事件比较未执行" in statement
    assert "容量控制比较另未通过" in statement
    assert "单项事件时间比较仍通过" in statement
    assert "阶段识别异常" in statement
    assert "未通过预定数值及事件比较" not in statement
    result = {"passed": True, "protected_file_count": len(before["protected"]),
              "scientific_rows_unchanged": True, "main_outside_statement_unchanged": True,
              "strict_grid_consistency_pass": grid["consistency_pass"],
              "grid_statuses": {key: value["comparison_status"] for key, value in items.items()}}
    (HERE / "scope_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["capture", "verify"])
    args = parser.parse_args()
    capture() if args.mode == "capture" else verify()
