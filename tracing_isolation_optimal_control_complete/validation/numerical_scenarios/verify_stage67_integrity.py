"""第6--7步隔离检查：历史记录保留、正文不变、35配置及新记录可追溯。"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROJECT = ROOT / "tracing_isolation_optimal_control_complete"
BASE_COMMIT = "fcd02a9365beac6dd6623cf4c699d5a36ebccaa7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protection_path = HERE / "step67_protected_files.json"
    protected_names = [f"tracing_isolation_optimal_control_complete/latex/{name}"
                       for name in ("main.tex", "main.pdf", "main.bbl", "theory_only.pdf")]
    if "--capture" in sys.argv:
        assert not protection_path.exists(), "本批原字节基准不能覆盖"
        protection = {name: sha(ROOT / name) for name in protected_names}
        # 工作区文本可能与 Git blob 的 CRLF/LF 不同；先核对内容，再保存真实原字节。
        for name in protected_names:
            committed = subprocess.check_output(["git", "show", f"{BASE_COMMIT}:{name}"], cwd=ROOT)
            current = (ROOT / name).read_bytes()
            if name.endswith((".tex", ".bbl")):
                committed, current = committed.replace(b"\r\n", b"\n"), current.replace(b"\r\n", b"\n")
            assert committed == current, name
        protection_path.write_text(json.dumps(protection, indent=2) + "\n", encoding="utf-8")
    protection = json.loads(protection_path.read_text(encoding="utf-8"))
    original = json.loads((HERE / "BASELINE.json").read_text(encoding="utf-8"))
    preserved, archived = {}, {}
    for name, expected in original["protected_sha256"].items():
        if name in {f"tracing_isolation_optimal_control_complete/latex/{n}"
                    for n in ("main.tex", "main.pdf", "main.bbl")}:
            continue  # 第5步已授权更新；下面按本批起始提交检查。
        path = ROOT / name
        if sha(path) == expected:
            preserved[name] = expected
            continue
        assert path.name in {f"E{k}.mat" for k in range(1, 6)}
        historical = path.parent / "legacy_results" / f"{path.stem}_{expected}.mat"
        assert historical.is_file() and sha(historical) == expected, name
        archived[name] = str(historical.relative_to(ROOT)).replace("\\", "/")
    unchanged = {}
    for relative, expected in protection.items():
        path = ROOT / relative
        assert sha(path) == expected, f"本批不得修改正文或编译产物: {relative}"
        unchanged[relative] = sha(path)
    data = PROJECT / "data/numerical_scenarios"
    manifests_checked = []
    inputs = json.loads((HERE / "scenario_inputs.json").read_text(encoding="utf-8"))
    def configuration_key(case_id, settings, guess):
        return (case_id, settings["T"], settings["N"], settings["d"], guess["type"],
                guess.get("seed"), guess.get("control"))
    expected_keys = set()
    for case in inputs["cases"]:
        case_id = case["case_id"]
        if case_id not in {f"E{k}" for k in range(1, 6)}:
            continue
        expected_keys.add((case_id, 300, case["main_N"], 2, "analytic_reference", None, None))
        expected_keys.add((case_id, 300, case["main_N"], 2, "constant_control", None, 0.7))
        expected_keys.add((case_id, 300, case["main_N"], 2, "seeded_random", 20261008+int(case_id[1:]), None))
        for grid_n in (2000, 4000, 8000):
            expected_keys.add((case_id, 300, grid_n, 2, "analytic_reference", None, None))
        for horizon_t, horizon_n in ((60, 1600), (120, 3200), (300, 8000)):
            expected_keys.add((case_id, horizon_t, horizon_n, 2, "analytic_reference", None, None))
    assert len(expected_keys) == 35
    for filename in (data / "revision_checks").glob("batch_*_manifest.json"):
        manifest = json.loads(filename.read_text(encoding="utf-8"))
        rows = manifest["default_experiments"]
        keys = [configuration_key(row["case_id"], row["solver_settings"], row["initialization"])
                for row in rows]
        assert len(rows) == len(set(keys)) == 35 and set(keys) == expected_keys
        assert all(row["parameters"] == inputs["parameters"] for row in rows)
        assert sum("main" in row["groups"] for row in rows) == 5
        assert sum("grid" in row["groups"] for row in rows) == 15
        assert sum("horizon" in row["groups"] for row in rows) == 15
        manifests_checked.append(filename.name)
    index = json.loads((data / "run_index.json").read_text(encoding="utf-8"))
    checked_runs = []
    for entry in index["entries"]:
        assert sha(data / entry["raw_file"]) == entry["raw_sha256"]
        diagnostic = data / "runs" / f"{entry['run_id']}.solver.json"
        record = json.loads(diagnostic.read_text(encoding="utf-8"))
        assert record["run_id"] == entry["run_id"]
        checked_runs.append(entry["run_id"])
    selection = data / "selection_manifest.json"
    selection_verified = False
    if selection.is_file():
        manifest = json.loads(selection.read_text(encoding="utf-8"))
        assert {e["case_id"] for e in manifest["entries"]} == {f"E{k}" for k in range(1, 6)}
        for entry in manifest["entries"]:
            assert entry["run_id"] in checked_runs
            assert sha(data / entry["raw_file"]) == entry["raw_sha256"]
            assert sha(data / entry["compatibility_file"]) == entry["compatibility_sha256"]
        selection_verified = True
    report = {
        "passed": True, "scope": "steps_6_to_7", "starting_commit": BASE_COMMIT,
        "historical_files_retained": len(preserved) + len(archived),
        "unchanged_historical_sha256": preserved, "byte_exact_historical_archives": archived,
        "unchanged_manuscript_and_build_sha256": unchanged,
        "scientific_run_records": len(checked_runs), "run_ids": checked_runs,
        "selection_verified": selection_verified,
        "default_distinct_configurations": 35,
        "checked_batch_manifests": manifests_checked,
    }
    (HERE / "step67_integrity_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"STAGE67_INTEGRITY_OK retained={len(preserved)+len(archived)} runs={len(checked_runs)} selection={selection_verified}")


if __name__ == "__main__":
    main()
