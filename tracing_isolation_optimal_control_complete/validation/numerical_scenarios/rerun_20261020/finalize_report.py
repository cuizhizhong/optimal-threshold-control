"""只核对已保存证据并汇总 S2；不启动 MATLAB、评估或优化器。"""

import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
REPO = PROJECT.parent
PREFIX = PROJECT.name + "/"
REL = HERE.relative_to(REPO).as_posix()
S29 = HERE / "S2.9"
COMMITS = ["4a634b9", "ee0b0fd", "9d98df7", "4219874", "19a2b51",
           "d28280e", "b6f0817", "993f3d6"]


def longpath(path):
    value = str(path.resolve())
    return Path("\\\\?\\" + value if os.name == "nt" else value)


def read(path):
    return json.loads(longpath(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    result = hashlib.sha256()
    with longpath(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-c", "core.longpaths=true", *args], cwd=REPO)


def paths(blob):
    return [item for item in blob.decode("utf-8").split("\0") if item]


def manifest_paths(text):
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def main():
    execution = read(HERE / "S2.4/execution_report.json")
    assert execution["status"] == "completed"
    assert (execution["solver_calls"], execution["cache_hits"], execution["successful_count"],
            execution["failed_count"]) == (35, 0, 35, 0)
    comparison = read(HERE / "comparison_report.json")
    assert comparison["passed"] and comparison["compared_count"] == comparison["passed_count"] == 35
    rows = comparison["rows"]
    assert len({row["configuration_id"] for row in rows}) == 35
    assert all(row["passed"] for row in rows)
    differences = {key: max(row[key] for row in rows) for key in (
        "cost_relative_difference", "control_max_abs_difference", "state_max_abs_difference")}
    assert all(value == 0 for value in differences.values())
    for row in rows:
        assert digest(PROJECT / "data/numerical_scenarios" / row["new_raw_file"]) == row["new_raw_sha256"]
    criteria = read(HERE / "S2.6/assessment_revision_report.json")
    assert criteria["status"] == "completed" and criteria["assessment_calls"] == 35
    original, current = criteria["original_counts"], criteria["current_counts"]
    assert [original[key] for key in ("records", "numeric_pass", "agreement_pass", "both_pass")] == [35, 29, 29, 28]
    assert [current[key] for key in ("records", "numeric_pass", "agreement_pass", "both_pass")] == [35, 33, 30, 30]
    assert {row["new_run_id"] for row in rows} == {row["run_id"] for row in criteria["rows"]}
    unit = read(HERE / "S2.4/unit_report.json")["unit"]
    all_unit = read(HERE / "S2.4/all_report.json")["unit"]
    assert unit["passed"] and all_unit["passed"] and unit["group_count"] == all_unit["group_count"] == 13
    regression = read(HERE / "S2.7/regression_report.json")
    assert all(regression[key]["passed"] for key in ("saved", "revision", "pending"))
    assert sum(regression[key]["test_count"] for key in ("saved", "revision", "pending")) == 16
    macro = read(HERE / "S2.7/macro_comparison_report.json")
    assert macro["passed"] and macro["outside_generated_blocks_identical"]
    checkpoint = read(HERE / "S2.3/checkpoint_migration_report.json")
    assert checkpoint["status"] == "pass" and checkpoint["numeric_fields"] == 105
    assert checkpoint["largest_relative_difference"] == "0"
    preservation = read(S29 / "preservation_report.json")
    assert preservation["passed"] and preservation["old_protected_file_count"] == 141
    assert preservation["old_index_entries_unchanged"] and preservation["current_index_entries"] == 70

    builds = {f"S2.{number}": read(HERE / f"S2.{number}/build_report.json") for number in range(2, 10)}
    assert all(report["success"] and report["pages"] == 37 and not report["final_log_issues"]
               and len(report["commands"]) == 4 and all(c["exit_code"] == 0 for c in report["commands"])
               for report in builds.values())
    assert builds["S2.7"]["source_sha256"] == builds["S2.9"]["source_sha256"]
    assert digest(PROJECT / "latex/main.pdf") == builds["S2.9"]["pdf_sha256"]
    # 已提交的新 raw、solver sidecar 与评估也不允许在后处理时改变。
    git("diff", "--quiet", "d28280e", "--", PREFIX + "data/numerical_scenarios/runs",
        PREFIX + "data/numerical_scenarios/revision_checks/assessments")
    git("diff", "--quiet", "b6f0817", "--", PREFIX + "figures/numerical_scenarios")
    final_text = PROJECT / "tmp/rerun_20261020/S2.9/main_published.txt"
    subprocess.run(["pdftotext", "-layout", str(PROJECT / "latex/main.pdf"), str(final_text)], check=True)
    assert final_text.read_bytes() == (PROJECT / "tmp/rerun_20261020/S2.7/main_published.txt").read_bytes()

    steps = []
    for number, sha in enumerate(COMMITS, 1):
        full_sha = git("rev-parse", sha).decode().strip()
        message = git("show", "-s", "--format=%B", sha).decode("utf-8")
        assert message.rstrip().endswith("Co-Authored-By: Codex <noreply@openai.com>")
        files = sorted(paths(git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", sha)))
        steps.append({"step": f"S2.{number}", "commit": full_sha, "title": message.splitlines()[0],
                      "file_count": len(files), "files": files})
    final_files = {
        PREFIX + "MANIFEST.txt", PREFIX + "REVIEW_GUIDE.md",
        PREFIX + "matlab/numerical_scenarios/README.md",
        PREFIX + "ai/claude_revision_plan/code_rename_inventory.md", PREFIX + "latex/main.pdf",
        *(REL + "/" + name for name in (
            "README.md", "COMMANDS.md", "batch_commits.json", "all_changed_files.txt",
            "final_status.json", "finalize_report.py", "S2.9/README.md", "S2.9/commit_files.json",
            "S2.9/final_audit.json", "S2.9/build_report.json", "S2.9/preservation_report.json",
            "S2.9/main_1.log", "S2.9/main_2.log", "S2.9/main_3.log", "S2.9/main_4.log"))}
    final_files = sorted(final_files)
    steps.append({"step": "S2.9", "commit": "this_commit",
                  "title": "refactor: 代码符号与论文统一并重跑 35 次优化（S2）",
                  "file_count": len(final_files), "files": final_files})
    write(S29 / "commit_files.json", {"step": "S2.9", "files": final_files})
    all_files = sorted({name for step in steps for name in step["files"]})
    write(HERE / "batch_commits.json", {"baseline_tag": "pre-code-rename",
          "baseline_commit": git("rev-parse", "pre-code-rename").decode().strip(),
          "branch": git("branch", "--show-current").decode().strip(),
          "unique_changed_file_count": len(all_files), "steps": steps})
    (HERE / "all_changed_files.txt").write_text("\n".join(all_files) + "\n", encoding="utf-8")
    manifest_file = PROJECT / "MANIFEST.txt"
    manifest_text = manifest_file.read_text(encoding="utf-8-sig")
    manifest = manifest_paths(manifest_text)
    additions = sorted({name[len(PREFIX):] for name in all_files if name.startswith(PREFIX)} - set(manifest))
    appended = "\n" + "\n".join(additions) if additions else ""
    manifest_file.write_text(manifest_text.rstrip() + appended + "\n", encoding="utf-8")
    manifest += additions
    assert len(manifest) == len({name.casefold() for name in manifest})
    old_manifest = manifest_paths(git("show", "pre-code-rename:" + PREFIX + "MANIFEST.txt").decode("utf-8-sig"))
    assert set(old_manifest) <= set(manifest)
    tracked = paths(git("ls-files", "-z", "--", PREFIX + "data/numerical_scenarios"))
    counts = {}
    for key, start, suffix, expected in (
            ("raw", "data/numerical_scenarios/runs/", ".mat", 70),
            ("solver", "data/numerical_scenarios/runs/", ".solver.json", 70),
            ("assessment", "data/numerical_scenarios/revision_checks/assessments/", ".mat", 140)):
        selected = [name[len(PREFIX):] for name in tracked if name.startswith(PREFIX + start) and name.endswith(suffix)]
        assert len(selected) == expected and set(selected) <= set(manifest)
        counts[key] = len(selected)

    audit = {"status": "passed", "optimizer_calls": 0, "scientific_solves": 0,
             "new_raw_hashes_verified": 35, "new_saved_records_match_S2_6_commit": True,
             "source_and_figures_match_visually_checked_S2_7": True,
             "final_pdf_text_identical_to_visually_checked_S2_7": True,
             "manifest_paths": len(manifest), "old_manifest_paths_retained": len(old_manifest),
             "manifest_duplicate_paths": 0, "record_counts": counts,
             "independent_review": "两名独立只读审阅核对科学报告、来源哈希、MANIFEST和文档口径；两处措辞已澄清，未改实现。",
             "old_record_preservation_report": "S2.9/preservation_report.json"}
    status = {"stage": "S2", "status": "completed", "scope_after_S2": "not_executed",
              "pushed": False, "execution": execution, "strict_comparison_passed": 35,
              "largest_differences": differences, "original_counts": original, "current_counts": current,
              "python_tests_passed": 9, "compatibility_tests_passed": 9,
              "explicit_unit_groups_passed": 13, "all_internal_unit_groups_passed": 13,
              "export_regression_tests_passed": 16, "checkpoint_numeric_fields": 105,
              "macro_blocks_and_outside_text_identical": True,
              "main_builds": {key: {"pages": r["pages"], "success": r["success"]} for key, r in builds.items()},
              "S2_1_main_pages": 37, "S2_1_theory_only_pages": 29,
              "final_main_pdf_sha256": digest(PROJECT / "latex/main.pdf"),
              "old_protected_files_unchanged": 141, "old_index_entries_unchanged": 35,
              "record_counts": counts, "stop_conditions_triggered": [], "author_decisions_needed": []}
    write(S29 / "final_audit.json", audit)
    write(HERE / "final_status.json", status)
    missing = [name for name in manifest if not longpath(PROJECT / name).is_file()]
    assert not missing, missing
    changed_now = set(paths(git("diff", "--name-only", "-z")))
    assert changed_now <= set(final_files), changed_now - set(final_files)
    print(json.dumps({"status": "passed", "manifest_paths": len(manifest),
                      "unique_changed_files": len(all_files), "final_commit_files": len(final_files),
                      "record_counts": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
