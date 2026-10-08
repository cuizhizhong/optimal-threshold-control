"""核对本批保护字节、科学数据、生成宏与实际运行报告。"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from functools import lru_cache
from scipy.io import loadmat

P = Path(__file__).resolve().parents[2]
ROOT = P.parent
V = P / "validation/numerical_scenarios"
D = P / "data/numerical_scenarios"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    baseline = read(V / "step1011_baseline.json")
    for name, expected in baseline["protected"].items():
        assert sha(ROOT / name) == expected, f"Protected bytes changed: {name}"
    # 前批已冻结的完整评估文件清单补充逐字节保护，避免只检查若干入口。
    frozen = read(V / "step89_source_fingerprints.json")
    for kind in ("solve", "assessment"):
        for item in frozen[kind]["files"]:
            assert sha(P / "matlab/numerical_scenarios" / item["path"]) == item["sha256"]
    main = (P / "latex/main.tex").read_text(encoding="utf-8")
    theory = main[main.index("\\begin{abstract}"):main.index("% 数值章节已内联")]
    assert hashlib.sha256(theory.encode()).hexdigest() == baseline["theory_sha256_normalized"]
    assert main.count("\\begin{figure}[H]") == 3
    assert main.count("\\begin{table}[H]") == 1
    labels = re.findall(r"\\label\{([^}]+)\}", main)
    assert len(labels) == len(set(labels)), "Duplicate labels"
    references = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", main)
    # NumTheoryRef 的 #1 是宏参数，不能当成正文标签。
    references = [r for r in references if not re.fullmatch(r"#[1-9]", r)]
    assert not set(references) - set(labels) - {"LastPage"}
    assert "\\NumResultsVerifiedtrue" in main and "\\NumRobustnessCompletetrue" in main
    assert "\\renewcommand{\\NumRobustnessStatement}{" in main
    assert not re.search(r"(?:NaN|Inf|OLD_PASSED_SENTINEL)", main)
    rows = {}
    for group in ("initialization", "grid", "horizon"):
        summary = read(D / "revision_checks" / f"{group}_summary.json")
        for row in summary["rows"]:
            key = row["configuration_id"]
            if key in rows:
                assert rows[key]["run_id"] == row["run_id"]
            rows[key] = row
    assert len(rows) == 35
    counts = {"numeric": sum(r["numeric_pass"] for r in rows.values()),
              "agreement": sum(r["agreement_pass"] for r in rows.values()),
              "both": sum(r["numeric_pass"] and r["agreement_pass"] for r in rows.values())}
    assert counts == {"numeric": 29, "agreement": 29, "both": 28}
    index = read(D / "run_index.json")
    assert len(index["entries"]) == 35
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8").splitlines())
    dependency_count = 0
    provenance_groups = {}
    for entry in index["entries"]:
        path = D / entry["raw_file"]
        assert sha(path) == entry["raw_sha256"]
        raw = loadmat(path, simplify_cells=True)["run"]
        assert raw["run_id"] == entry["run_id"]
        assert raw["solve_fingerprint"] == entry["solve_fingerprint"]
        origin = raw["provenance"]
        key = (origin["solve_commit"], origin["solve_code_hash"], bool(origin["solve_dirty"]))
        provenance_groups[key] = provenance_groups.get(key, 0) + 1
        env = origin["environment"]
        ocl = Path(env["openocl_path"]).parent
        casadi = Path(env["casadi_binary_path"]).parent
        binary = Path(env["casadi_binary_path"])
        assert sha(binary) == env["casadi_binary_hash"]
        assert str(binary.relative_to(ROOT)).replace("\\", "/") in tracked
        for kind, folder in (("openocl_source_files", ocl), ("casadi_runtime_files", casadi), ("ipopt_binary_files", casadi)):
            files = env[kind]
            if isinstance(files, dict):
                files = [files]
            for item in files:
                f = folder / item["path"]
                assert sha(f) == item["sha256"]
                assert str(f.relative_to(ROOT)).replace("\\", "/") in tracked, f"Untracked dependency: {f}"
                dependency_count += 1
    selection = read(D / "selection_manifest.json")
    assert [e["run_id"] for e in selection["entries"]] == baseline["selected_run_ids"]
    suffixes = ["One", "Two", "Three", "Four", "Five"]
    for e, suffix in zip(selection["entries"], suffixes):
        assert sha(D / e["raw_file"]) == e["raw_sha256"]
        assert sha(D / e["compatibility_file"]) == e["compatibility_sha256"]
        raw = loadmat(D / e["raw_file"], simplify_cells=True)["run"]
        assert f"\\providecommand{{\\NumJOclE{suffix}}}{{{raw['J_openocl']:.6f}}}" in main
    figures = read(D / "figure_provenance.json")["figures"]
    assert len(figures) == 3
    expected_cases = [["E1", "E2", "E3", "E4", "E5"], ["E1", "E2"], ["E3", "E4", "E5"]]
    expected_names = ["FigN1_regions", "FigN2_waiting", "FigN3_boundary_tracking"]
    selected_ids = {e["case_id"]: e["run_id"] for e in selection["entries"]}
    for figure, ids, name in zip(figures, expected_cases, expected_names):
        assert figure["name"] == name and figure["case_ids"] == ids
        assert figure["run_ids"] == [selected_ids[k] for k in ids]
        for output in figure["outputs"]:
            assert sha(P / output["file"]) == output["sha256"]
        assert set(figure["run_ids"]).issubset(set(baseline["selected_run_ids"]))
    checks = read(D / "numerical_checks.json")
    assert checks["verified"] and checks["robustness"]["protocol_complete"]
    assert not checks["robustness"]["consistency_pass"]
    post = read(V / "step1011_postprocess_report.json")
    clean = read(V / "step1011_clean_report.json")
    assert post["optimizer_executions"] == 0 and post["export_idempotent"]
    assert clean["scientific_optimizer_executions"] == 0 and clean["trusted_cache_hits"] == 35
    assert clean["smoke_optimizer_executions"] == 1 and clean["smoke_passed"]
    assert clean["protocol_complete"] and not clean["consistency_pass"]
    build = read(V / "step1011_build_report.json")
    assert build["main"]["success"] and build["theory_only"]["success"]
    # 日志里的警告全部在 build_report 逐项保留，不只依据返回码。
    assert not build["main"]["final_log_issues"] and not build["theory_only"]["final_log_issues"]
    failures = [{k: r[k] for k in ("configuration_id", "case_id", "N", "run_id", "numeric_pass", "agreement_pass", "capacity_excess", "observed_structure")}
                for r in rows.values() if not (r["numeric_pass"] and r["agreement_pass"])]
    result = {"status": "completed", "passed": True, "protected_files": len(baseline["protected"]),
              "theory_body_unchanged": True, "main_figures": 3, "main_tables": 1,
              "labels": len(labels), "default_configurations": 35, "measured_pass_counts": counts,
              "failed_diagnostic_records": failures, "tracked_dependency_hash_checks": dependency_count,
              "solve_provenance_groups": [{"solve_commit": k[0], "solve_code_hash": k[1], "solve_dirty": k[2], "records": n} for k, n in provenance_groups.items()],
              "postprocess": post, "clean_checkout": clean, "build": build,
              "scientific_optimizer_executions_this_batch": 0, "interface_smoke_optimizer_executions": 1,
              "remaining_unrun_extended_experiments": ["N=16000", "T=600", "extra initialization attempts"],
              "scientific_anomalies_from_preserved_step89": {k: read(V / "step89_validation_report.json")[k] for k in ("solver_failures", "numeric_failures", "agreement_failures", "negative_cost_diagnostics", "unresolved_discrepancies")},
              "original_repository_head": baseline["head"], "new_delivery_commit": None,
              "limits": "协议执行完整但原网格一致性失败；浮点接受与接口smoke不构成新增理论证明。"}
    (V / "step1011_validation_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"STAGE1011_INTEGRITY_OK protected={result['protected_files']} raw=35 both=28/35 cache=35 smoke=1")


if __name__ == "__main__":
    check()
