"""核对文字压缩范围，并分别记录同期获授权的容差重评变化。"""

import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


def without_generated(text):
    for marker in ("NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"):
        pattern = rf"% BEGIN AUTO-GENERATED {marker}.*?% END AUTO-GENERATED {marker}"
        text, count = re.subn(pattern, "", text, flags=re.S)
        assert count == 1, marker
    return text


def macros(text):
    values = {}
    for match in re.finditer(
        r"^\\(?:providecommand|renewcommand)\{\\(Num\w+)\}\{(.*)\}$", text, re.M
    ):
        values[match.group(1)] = match.group(2)
    return values


def measure(text):
    return {"nonwhitespace_characters_including_tex": len(re.sub(r"\s", "", text)),
            "cjk_characters": len(re.findall(r"[\u4e00-\u9fff]", text))}


def main():
    baseline = json.loads((HERE / "baseline.json").read_text(encoding="utf-8"))
    source = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    before = (HERE / "main_before.tex").read_text(encoding="utf-8")
    concurrent = (HERE / "concurrent_main_before_export.tex").read_text(encoding="utf-8")
    appendix_anchor = "正文中的数值摘要与所选结果文件保持一一对应。\n"
    appendix_pointers = ("完整事件候选、检测区间及主结果诊断见\n"
                        "\\path{data/numerical_scenarios/numerical_checks.json}；\n"
                        "容差重评与原严格记录见\n"
                        "\\path{validation/numerical_scenarios/tolerance_revision_20261010/}。\n")
    expected = concurrent.replace(appendix_anchor, appendix_anchor + appendix_pointers)
    assert without_generated(source) == without_generated(expected), \
        "Non-generated source changed after the concurrent source snapshot."
    old, new = macros(before), macros(source)
    numeric = [key for key in old if key.startswith(("NumJRef", "NumJOcl", "NumExit", "NumSwitch"))]
    assert all(old[key] == new[key] for key in numeric), "Reported costs or event values changed."
    labels = lambda value: re.findall(r"\\label\{([^}]+)\}", value)
    assert labels(source) == labels(concurrent)
    brief = new["NumRobustnessStatement"]
    assert not re.search(r"\d+/\d+|默认协议已记录|协议是否完成", brief)
    assert "默认协议已记录" in new["NumReproducibilityDetails"]
    assert "附录" in brief and "求解后" in brief
    assert "初次干预" not in new["NumFindingWaiting"]
    assert "解除的检测区间" not in new["NumFindingWaiting"]
    assert "[0,0]" not in new["NumFindingTrackingBoundary"]
    assert "初次干预" not in new["NumFindingTrackingBoundary"]
    changed, unchanged, protected = [], [], []
    for entry in baseline["protected_files"]:
        path = PROJECT / entry["path"]
        same = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        (unchanged if same else changed).append(entry["path"])
        if entry["path"].startswith(("data/numerical_scenarios/runs/", "figures/")):
            assert same, f"Original solver record or figure changed: {entry['path']}"
            protected.append(entry["path"])
    revision_path = PROJECT / "validation/numerical_scenarios/tolerance_revision_20261010/assessment_revision_report.json"
    revision = json.loads(revision_path.read_text(encoding="utf-8"))
    assert revision["status"] == "completed" and revision["optimizer_executions"] == 0
    metrics = {key: {"before": measure(old[key]), "after": measure(new[key])}
               for key in ("NumRobustnessStatement", "NumFindingWaiting", "NumFindingTrackingBoundary")}
    totals = {stage: sum(value[stage]["nonwhitespace_characters_including_tex"]
                         for value in metrics.values()) for stage in ("before", "after")}
    report = {"passed": True, "label_count": len(labels(source)),
              "non_generated_source_equals_concurrent_snapshot_plus_appendix_pointers": True,
              "unchanged_numeric_macros": numeric,
              "unchanged_raw_solver_and_figure_files": protected,
              "initial_baseline_unchanged_count": len(unchanged),
              "concurrent_reassessment_changed_paths": changed,
              "concurrent_reassessment_status": revision["status"],
              "optimizer_executions_this_task": 0,
              "compression_metrics": metrics, "main_prose_totals": totals,
              "counting_convention": "非空白字符，包含 LaTeX 公式标记；另列中文字符数。"}
    (HERE / "scope_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    print(f"PROSE_COMPRESSION_SCOPE_OK raw/solver/figure={len(protected)} prose={totals}")


if __name__ == "__main__":
    main()
