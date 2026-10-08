"""从 Git 基准与明确成果目录制作候选临时检出，排除本机残留。"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tarfile

P = Path(__file__).resolve().parents[2]
ROOT = P.parent
V = P / "validation/numerical_scenarios"


def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, encoding="utf-8").strip()


def main():
    candidate_path = ROOT / "tmp/s12"
    # Windows 部分文件名超过 260 字符；使用长路径前缀，不改科学文件名。
    candidate = Path("\\\\?\\" + str(candidate_path)) if os.name == "nt" else candidate_path
    assert not candidate.exists(), "候选目录已经存在，禁止覆盖。"
    candidate.mkdir(parents=True)
    archive = ROOT / "tmp/stage1011_candidate_base.tar"
    subprocess.run(["git", "archive", "HEAD", "-o", str(archive), P.name], cwd=ROOT, check=True)
    with tarfile.open(archive) as src:
        src.extractall(candidate, filter="data")
    allowed = ["data", "matlab", "validation", "latex", "figures"]
    extras = ["README.md", "MANIFEST.txt", "build.bat", "build.sh"]
    copied = []
    excluded_extensions = {".aux", ".log", ".out", ".toc", ".blg", ".bbl", ".fls", ".xdv", ".fdb_latexmk", ".pyc"}
    source_project = Path("\\\\?\\" + str(P)) if os.name == "nt" else P
    files = [f for name in allowed for f in (source_project / name).rglob("*") if f.is_file()]
    files += [source_project / name for name in extras]
    for f in files:
        relative = f.relative_to(source_project)
        if "__pycache__" in relative.parts or f.suffix == ".pyc" or (relative.parts[0] == "latex" and f.suffix in excluded_extensions):
            continue
        if f.name == "step1011_main_before.tex":
            continue
        dest = candidate / P.name / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        copied.append({"path": str(Path(P.name) / relative).replace("\\", "/"),
                       "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    assessments = Path("data/numerical_scenarios/revision_checks/assessments")
    expected_assessments = {f.name for f in (source_project / assessments).glob("*.mat")}
    copied_assessments = {f.name for f in (candidate / P.name / assessments).glob("*.mat")}
    assert copied_assessments == expected_assessments, "评估记录复制不完整。"
    # 仅对本脚本创建的候选检出建立快照提交，不修改用户仓库的 Git 状态。
    subprocess.run(["git", "init", "-q"], cwd=candidate, check=True)
    subprocess.run(["git", "config", "user.name", "Codex candidate validation"], cwd=candidate, check=True)
    subprocess.run(["git", "config", "user.email", "candidate-validation@localhost"], cwd=candidate, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=candidate, check=True)
    subprocess.run(["git", "config", "core.longpaths", "true"], cwd=candidate, check=True)
    subprocess.run(["git", "add", "--", P.name], cwd=candidate, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Candidate snapshot for steps 10-11 clean validation"], cwd=candidate, check=True)
    status = run(["git", "status", "--porcelain=v1"], cwd=candidate)
    assert not status
    report = {"candidate_path": str(candidate_path), "base_head": run(["git", "rev-parse", "HEAD"]),
              "snapshot_commit": run(["git", "rev-parse", "HEAD"], cwd=candidate),
              "initial_status": status, "overlay_files": copied,
              "assessment_files_copied": len(copied_assessments),
              "excluded_local_residue": ["ai/", "archive/pending_deletion/", "tmp/", "__pycache__/", "build intermediates"],
              "openocl_root": str(ROOT / "optimal/OpenOCL-master 0104"),
              "dependency_policy": "Explicit OPENOCL_ROOT keeps the recorded environment fingerprint; dependency files are checked against tracked source and saved hashes."}
    (V / "step1011_checkout_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CLEAN_CANDIDATE_READY", report["snapshot_commit"], "files=", len(copied))


if __name__ == "__main__":
    main()
