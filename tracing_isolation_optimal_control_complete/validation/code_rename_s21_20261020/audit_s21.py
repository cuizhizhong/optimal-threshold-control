"""S2.1 清点与字节核对；只可给历史入口加说明，不调用 MATLAB。"""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
PREFIX = PROJECT.name
BASE = "051099fba63cd6d326f2344d2bf4322c1f651282"
V = "validation/numerical_scenarios/"
HISTORY = [
    "verify_stage67_integrity.py",
    "execute_stage89.m", "execute_stage89_initialization_check.m",
    "verify_stage89_initializations.m", "verify_stage89_integrity.py", "summarize_stage89.py",
    "prepare_stage1011.py", "prepare_stage1011_checkout.py", "compare_stage1011_candidate.py",
    "build_stage1011.py", "execute_stage1011.m", "execute_stage1011_clean.m",
    "finalize_stage1011.py", "finalize_stage1011_export.m", "verify_stage1011.py",
    "tolerance_revision_20261010/refresh_tolerance_assessments.m",
    "tolerance_revision_20261010/validate_scope.py",
    "tolerance_revision_20261010/compile_pdfs.py",
]
NOTICE = "只针对标签 `pre-code-rename` 运行；历史基线与输出不得刷新。"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def read(path):
    name = str(path.resolve())
    return Path("\\\\?\\" + name if os.name == "nt" else name).read_bytes()


def annotated(original, suffix):
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    comment = (("% " if suffix == ".m" else "# ") + NOTICE).encode("utf-8") + newline
    if suffix == ".m" and original.startswith(b"function "):
        first, rest = original.split(newline, 1)
        return first + newline + comment + rest
    if original.startswith(b"#!"):
        first, rest = original.split(newline, 1)
        return first + newline + comment + rest
    return comment + original


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotate-history", action="store_true")
    args = parser.parse_args()
    assert git("rev-parse", "pre-code-rename").decode().strip() == BASE
    assert git("rev-parse", "--show-object-format").decode().strip() == "sha1"
    headers = []
    for name in HISTORY:
        path = PROJECT / V / name
        relative = path.relative_to(REPO).as_posix()
        original = git("show", f"{BASE}:{relative}")
        expected = annotated(original, path.suffix)
        if args.annotate_history:
            assert read(path) in (original, expected), f"历史脚本已有其他修改：{relative}"
            path.write_bytes(expected)
        assert read(path) == expected, f"历史脚本不是单一头注释改动：{relative}"
        if path.suffix == ".py":
            assert ast.dump(ast.parse(original.decode("utf-8-sig"))) == ast.dump(
                ast.parse(expected.decode("utf-8-sig")))
        headers.append({"file": relative, "only_notice_added": True,
                        "baseline_sha256": hashlib.sha256(original).hexdigest(),
                        "current_sha256": hashlib.sha256(expected).hexdigest()})
    protected_roots = [f"{PREFIX}/{name}" for name in (
        "data/numerical_scenarios", "matlab/numerical_scenarios", "latex",
        "validation/numerical_scenarios/scenario_inputs.json",
        "validation/numerical_scenarios/analytic_checkpoints.json",
        "validation/numerical_scenarios/generate_analytic_checkpoints.py",
        "validation/numerical_scenarios/test_analytic_checkpoints.py")]
    files = []
    for row in git("ls-tree", "-rz", BASE, "--", *protected_roots).split(b"\0"):
        if not row:
            continue
        metadata, relative_bytes = row.split(b"\t", 1)
        relative = relative_bytes.decode("utf-8")
        content = read(REPO / relative)
        digest = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        normalized = False
        if digest != metadata.split()[2].decode():
            assert Path(relative).suffix in {".json", ".csv", ".md", ".txt", ".m", ".tex", ".bib", ".bbl", ".py"}
            canonical = content.replace(b"\r\n", b"\n")
            digest = hashlib.sha1(f"blob {len(canonical)}\0".encode() + canonical).hexdigest()
            normalized = True
        assert digest == metadata.split()[2].decode(), f"受保护文件发生变化：{relative}"
        files.append({"file": relative, "sha256": hashlib.sha256(content).hexdigest(),
                      "git_content_unchanged_from_tag": True,
                      "git_crlf_normalized_for_comparison": normalized})
    byte_baseline = HERE / "protected_before.json"
    hashes = {row["file"]: row["sha256"] for row in files}
    if byte_baseline.exists():
        assert json.loads(byte_baseline.read_text(encoding="utf-8")) == hashes, "S2.1 字节快照发生变化。"
    else:
        byte_baseline.write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = PROJECT / "data/numerical_scenarios"
    index = json.loads(read(data / "run_index.json"))
    pairs = {}
    for group in ("initialization", "grid", "horizon"):
        summary = json.loads(read(data / f"revision_checks/{group}_summary.json"))
        rows = summary["rows"]
        for row in rows:
            cid, rid = row["configuration_id"], row["run_id"]
            assert cid not in pairs or pairs[cid] == rid
            pairs[cid] = rid
    assert set(pairs) == {f"C{k:02d}" for k in range(1, 36)}
    assert len(set(pairs.values())) == 35
    for rid in pairs.values():
        assert (data / f"runs/{rid}.mat").is_file()
        assert (data / f"runs/{rid}.solver.json").is_file()
    report = {
        "step": "S2.1", "base_commit": BASE, "tag": "pre-code-rename",
        "optimizer_calls": 0, "scientific_solves": 0, "cache_hits": 0,
        "protected_file_count": len(files), "protected_files": files,
        "data_file_count": sum("/data/numerical_scenarios/" in row["file"] for row in files),
        "working_tree_byte_baseline": "protected_before.json", "working_tree_bytes_unchanged": True,
        "history_notice_count": len(headers), "history_notices": headers,
        "original_run_index_entry_count": len(index["entries"]),
        "original_raw_mat_count": len(list((data / "runs").glob("*.mat"))),
        "original_solver_json_count": len(list((data / "runs").glob("*.solver.json"))),
        "original_assessment_mat_count": len(list((data / "revision_checks/assessments").glob("*.mat"))),
        "old_run_ids_by_configuration_id": dict(sorted(pairs.items())),
        "history_verifiers_executed": False, "success": True,
    }
    (HERE / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    print(f"S2.1_AUDIT_OK protected_files={len(files)} history_notices={len(headers)} old_configurations={len(pairs)} optimizer_calls=0")


if __name__ == "__main__":
    main()
