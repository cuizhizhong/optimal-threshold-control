"""保存旧判据证据，核对容差重评没有改写求解结果或论文数学内容。"""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("\\\\?\\" + str(HERE.parents[2])) if os.name == "nt" else HERE.parents[2]
DATA = ROOT / "data/numerical_scenarios"
CODE = ROOT / "matlab/numerical_scenarios"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main_outside_generated():
    text = (ROOT / "latex/main.tex").read_text(encoding="utf-8")
    for marker in ["NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"]:
        pattern = re.compile(r"% BEGIN AUTO-GENERATED " + marker + r".*?% END AUTO-GENERATED " + marker, re.S)
        text, count = pattern.subn("GENERATED_BLOCK", text)
        assert count == 1
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture():
    assert not (HERE / "baseline.json").exists(), "基线已存在，不得覆盖旧记录。"
    protected = list((DATA / "runs").glob("*"))
    protected += list((DATA / "revision_checks/assessments").glob("*.mat"))
    protected += list((ROOT / "figures/numerical_scenarios").glob("*"))
    protected += [DATA / "run_index.json", DATA / "scenario_summary.csv",
                  ROOT / "latex/references.bib", ROOT / "latex/theory_only.tex"]
    protected += list((ROOT / "validation/numerical_scenarios/grid_explanation_20261009").rglob("*"))
    protected += [p for p in CODE.glob("*.m") if p.name not in {
        "numerical_cases_config.m", "export_numerical_latex.m", "verify_saved_result_exporter.m"}]
    protected += [ROOT / "validation/numerical_scenarios" / name for name in [
        "scenario_inputs.json", "analytic_checkpoints.json"]]
    protected = sorted({p for p in protected if p.is_file()})
    archive = [DATA / name for name in ["selection_manifest.json", "run_index.json",
               "numerical_checks.json", "scenario_summary.csv", "export_provenance.json"]]
    archive += list((DATA / "revision_checks").glob("*_summary.json"))
    archive += list((DATA / "revision_checks").glob("*_summary.csv"))
    for src in archive:
        dst = HERE / "baseline_data" / src.relative_to(DATA)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    shutil.copyfile(CODE / "numerical_cases_config.m", HERE / "baseline_numerical_cases_config.m")
    shutil.copyfile(ROOT / "latex/main.tex", HERE / "baseline_main.tex")
    manifest = json.loads((DATA / "selection_manifest.json").read_text(encoding="utf-8"))
    baseline = {"protected": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in protected},
                "main_outside_generated_sha256": main_outside_generated(),
                "assessment_files": [p.name for p in (DATA / "revision_checks/assessments").glob("*.mat")],
                "selection_manifest": manifest,
                "old_acceptance": {"state_tolerance": 1e-6, "capacity_tolerance": 1e-6,
                                   "capacity_control_tolerance": 2e-3}}
    (HERE / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOLERANCE_BASELINE_CAPTURED protected_files={len(protected)}")


def verify():
    baseline = json.loads((HERE / "baseline.json").read_text(encoding="utf-8"))
    changed = [name for name, value in baseline["protected"].items() if digest(ROOT / name) != value]
    assert not changed, changed
    external_path = HERE / "concurrent_changes.json"
    expected_main = (json.loads(external_path.read_text(encoding="utf-8"))["main_outside_generated_sha256"]
                     if external_path.exists() else baseline["main_outside_generated_sha256"])
    assert main_outside_generated() == expected_main
    manifest = json.loads((DATA / "selection_manifest.json").read_text(encoding="utf-8"))
    for old, new in zip(baseline["selection_manifest"]["entries"], manifest["entries"]):
        for field in ["case_id", "run_id", "solve_fingerprint", "raw_file", "raw_sha256"]:
            assert old[field] == new[field], (old["case_id"], field)
        assert old["assessment_fingerprint"] != new["assessment_fingerprint"]
        archived = DATA / "legacy_results" / f'{old["case_id"]}_{old["compatibility_sha256"]}.mat'
        assert digest(archived) == old["compatibility_sha256"]
    grid = json.loads((DATA / "revision_checks/grid_summary.json").read_text(encoding="utf-8"))
    assert grid["consistency_pass"] and grid["protocol_complete"]
    for row in grid["case_comparisons"]:
        assert row["comparison_status"] == "evaluated_passed"
        assert row["event_comparison_evaluated"] and row["cost_comparison_evaluated"]
    oldgrid = json.loads((HERE / "baseline_data/revision_checks/grid_summary.json").read_text(encoding="utf-8"))
    metrics = ["case_id", "configuration_id", "run_id", "solve_fingerprint", "T", "N",
               "initialization", "success", "return_status", "J_openocl", "capacity_excess",
               "state_discrepancy", "tail_max_q", "terminal_peak", "observed_structure", "event_intervals"]
    for old, new in zip(oldgrid["rows"], grid["rows"]):
        for field in metrics:
            assert old[field] == new[field], (old["configuration_id"], field)
    checks = json.loads((DATA / "numerical_checks.json").read_text(encoding="utf-8"))
    oldchecks = json.loads((HERE / "baseline_data/numerical_checks.json").read_text(encoding="utf-8"))
    expected_cases = oldchecks["cases"]
    for row in expected_cases:
        assessment = row["assessment"]
        assert assessment["event_comparison"]["capacity_control"]["tolerance"] == 2e-3
        assert assessment["event_comparison"]["thresholds"]["capacity_control_tolerance"] == 2e-3
        assert assessment["tail"]["capacity_tolerance"] == 1e-6
        assessment["event_comparison"]["capacity_control"]["tolerance"] = 3e-3
        assessment["event_comparison"]["thresholds"]["capacity_control_tolerance"] = 3e-3
        assessment["tail"]["capacity_tolerance"] = 1e-5
    assert checks["cases"] == expected_cases, "五个主结果仅允许指定容差元数据变化。"
    assert checks["verified"] and checks["robustness"]["consistency_pass"]
    assert checks["robustness"]["numeric_and_agreement_pass_count"] == 30
    current = {p.name for p in (DATA / "revision_checks/assessments").glob("*.mat")}
    assert set(baseline["assessment_files"]) <= current
    assert len(current - set(baseline["assessment_files"])) == 35
    text = (ROOT / "latex/main.tex").read_text(encoding="utf-8")
    assert "原严格判据" in text and "重新评估" in text and "阶段识别异常" in text
    result = {"passed": True, "protected_file_count": len(baseline["protected"]),
              "original_solve_and_old_assessment_bytes_unchanged": True,
              "main_selection_run_ids_unchanged": True, "main_outside_generated_unchanged": True,
              "new_assessment_count": 35, "new_finest_grid_comparison_pass_count": 5,
              "numeric_and_agreement_pass_count": 30}
    (HERE / "scope_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["capture", "verify"])
    args = parser.parse_args()
    capture() if args.mode == "capture" else verify()
