"""按已审查的文件集合打包，优先取当前仓库字节。"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPOSITORY = PROJECT.parent
INCOMING = PROJECT / "ai/optimal_threshold_control_revised"
STAGING = REPOSITORY / "tmp/i1117"
OUTPUT = REPOSITORY / "output"
NAME = "optimal_threshold_control_integrated_20261117"


def main():
    if STAGING.exists():
        raise FileExistsError(f"暂存目录已存在，请另选目录：{STAGING}")
    STAGING.mkdir(parents=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    selected = {}
    for source in INCOMING.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(INCOMING)
        if relative.parts[0] not in {"latex", "figures", "matlab", "data", "validation", "scripts", "reproducibility"}:
            continue
        if relative.as_posix() == "data/analytic_verification.json":
            continue
        current = PROJECT / relative
        selected[relative] = current if current.is_file() else source
    for relative in ("build.bat", "build.sh", "REVIEW_GUIDE.md"):
        selected[Path(relative)] = PROJECT / relative
    for source in HERE.iterdir():
        if source.is_file() and source.name != "supplementary_previous_locked.pdf":
            selected[source.relative_to(PROJECT)] = source
    provenance = []
    for relative, source in selected.items():
        target = STAGING / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        provenance.append({
            "path": relative.as_posix(),
            "source": source.relative_to(REPOSITORY).as_posix(),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })
    (STAGING / "review").mkdir()
    shutil.copy2(PROJECT / "README.md", STAGING / "review/REPOSITORY_README.md")
    (STAGING / "README.md").write_text(
        """# 感染阈值约束下追踪隔离的全域最优控制：整合稿

2026-11-17。相对于仓库提交 `09140ec16983fa98f1103b873fc03706ff7dd627`，
已审查并整合 ChatGPT 修改稿的章节组织、证明表述和补充材料安排。

## 阅读入口

- `latex/main.pdf`：主文，43 页。
- `latex/supplementary.pdf`：数值补充材料，4 页。
- `validation/chatgpt_integration_20261117/README.md`：相对初稿的评价、采纳内容、验证结果和局限。
- `review/integration_source.diff`：现有跟踪源文件相对于基线的差异。
- `latex/main.tex`、`supplementary.tex`、`references.bib`：当前可编辑源码。

## 编译

保留目录相对位置，安装包含中文 ctex 的 TeX Live 或 MiKTeX，以 XeLaTeX 编译。
Windows 在本目录运行 `build.bat`；Linux/macOS 使用 `bash build.sh`。
编译 PDF 不需要 MATLAB、Python 或重新求解优化问题。
本包在独立暂存目录实际运行 Windows 完整构建，实际结果见
`validation/chatgpt_integration_20261117/package_build_verification.json`。
Linux/macOS 命令本轮未实际执行。

## 数值与来源

本轮新增优化求解、ODE 重积分均为零；原 MATLAB 代码、原始科学记录、图件和原数值宏保持基线字节。
`data/numerical_scenarios/` 保留五例主结果和网格表所需的原始记录子集；
本包不包含完整仓库的全部历史缓存或 MATLAB/OpenOCL/CasADi 依赖。
完整历史实验应回到 https://github.com/cuizhizhong/optimal-threshold-control 的上述固定提交。
详细摘要与简表的不同运行标识保留，15 对数组/成本映射见本轮验证目录，不能计作本轮新实验。
`reproducibility/scaling/` 保留原修改包附带的解析扫描代码与保存结果；
`data/archived_validation/` 以及 MATLAB 目录原 README 属于历史说明。

从本目录可以运行：

```powershell
python scripts/build_grid_error_table.py
python scripts/verify_analytic_results.py --output data/analytic_verification_fresh.json
```

第一个仅需 Python 标准库；第二个需要 `mpmath`，只核对解析公式，不运行优化器。
QA 脚本的额外依赖为 `pypdf` 和 Pillow，不影响论文编译。

`PACKAGE_PROVENANCE.json` 逐项记录来源，`MANIFEST.sha256` 校验包内最终文件。
评阅报告中仓库 `ai/`、完整历史记录及临时渲染图路径用于定位原项目，并未全部复制进本包。
""", encoding="utf-8"
    )
    diff = subprocess.check_output([
        "git", "diff", "09140ec16983fa98f1103b873fc03706ff7dd627", "--",
        "tracing_isolation_optimal_control_complete/latex/main.tex",
        "tracing_isolation_optimal_control_complete/latex/supplementary.tex",
        "tracing_isolation_optimal_control_complete/latex/references.bib",
        "tracing_isolation_optimal_control_complete/README.md",
        "tracing_isolation_optimal_control_complete/REVIEW_GUIDE.md",
    ], cwd=REPOSITORY)
    (STAGING / "review/integration_source.diff").write_bytes(diff)
    (STAGING / "PACKAGE_PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Staged {len(selected)} files in {STAGING}")


def finalize():
    files = sorted(path for path in STAGING.rglob("*") if path.is_file()
                   and path.name != "MANIFEST.sha256"
                   and path.suffix not in {".aux", ".out", ".blg", ".toc", ".xdv", ".synctex.gz"}
                   and not (path.parent == STAGING / "latex" and path.suffix == ".log"))
    provenance_path = STAGING / "PACKAGE_PROVENANCE.json"
    prior_sources = {row["path"]: row["source"] for row in
                     json.loads(provenance_path.read_text(encoding="utf-8"))}
    provenance = []
    for path in files:
        relative = path.relative_to(STAGING).as_posix()
        if path == provenance_path:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row = {"path": relative, "sha256": digest}
        if relative in prior_sources:
            source = REPOSITORY / prior_sources[relative]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, relative
            row["source"] = prior_sources[relative]
        else:
            source = PROJECT / relative
            if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == digest:
                row["source"] = source.relative_to(REPOSITORY).as_posix()
            else:
                row["source"] = "generated_for_this_delivery"
        provenance.append(row)
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(STAGING).as_posix()}\n"
                       for path in files)
    (STAGING / "MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    archive = OUTPUT / f"{NAME}.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as target:
        for path in [*files, STAGING / "MANIFEST.sha256"]:
            target.write(path, f"{NAME}/{path.relative_to(STAGING).as_posix()}")
    with ZipFile(archive) as target:
        assert target.testzip() is None
        for path in files:
            assert hashlib.sha256(target.read(f"{NAME}/{path.relative_to(STAGING).as_posix()}")).hexdigest() == hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"archive": str(archive), "file_count": len(files) + 1,
              "bytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "zip_integrity_passed": True, "all_archived_file_hashes_verified": True}
    (HERE / "package_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    import sys
    finalize() if "--finalize" in sys.argv else main()
