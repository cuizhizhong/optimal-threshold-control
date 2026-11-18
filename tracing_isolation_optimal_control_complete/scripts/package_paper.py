"""从项目中的定稿、配套图件和已保存的数值记录生成投稿包。"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT = Path(__file__).resolve().parents[1]
PACKAGE = "optimal_threshold_control_submission_20261118_v3"
OUTPUT = PROJECT.parent / "output" / f"{PACKAGE}.zip"

README = """# 感染阈值约束下追踪隔离的全域最优控制

2026 年 11 月 18 日投稿稿件，第三版。主文与补充材料分别为 [主文 PDF](latex/main.pdf) 和 [补充材料 PDF](latex/supplementary.pdf)。两份文稿的 LaTeX 源码、参考文献和表格宏在同一目录。保留解压后的目录结构，从本文件所在目录运行下列命令。

## 编译

Windows 运行 `.\\build.bat`，Linux 或 macOS 运行 `bash build.sh`。需要 XeLaTeX、BibTeX、ctex 及中文字体。主文和补充材料分别输出到 `latex/main.pdf` 和 `latex/supplementary.pdf`。

## 核对表 4 和重绘图 5

```sh
python -m pip install -r requirements.txt
python scripts/verify_analytic_results.py --output reproduction/table4.json
python reproducibility/scaling/figure_followup.py --reproduce-dir reproduction/figure5
```

表 4 的成本、追踪实施时长和新增隔离的易感者比例（占总人口）共用各情景的初值和自然容量入口。核对脚本读取稿件列值与排版精度，逐项比较两种策略。随稿生成的同一份计算结果见 [解析复核记录](data/analytic_verification.json)。

图 5 的[正式作图数据](reproducibility/scaling/figure_data.json)与[绘图脚本](reproducibility/scaling/figure_followup.py)位于同一目录。脚本从解析方程重建五组参数、共 620 点的容量网格，域内 619 点用于作图。面板 (d) 绘制从同一切换点出发的两条尾段的时长差乘以 βγ，即 βγ(T₊,fill − T₊*)，横虚线为 1。程序比对四个面板的完整数据，将再生 PDF、PNG、曲线 JSON 和版面检查写入 `reproduction/figure5/`。`reproducibility/scaling/scan.csv` 保存逐点解析扫描，包括绝对时长差 `Delta_T`。

## 数值轨道和补充表

图 2–4 所用的五个主例保存在 `data/numerical_scenarios/E1.mat` 至 `E5.mat`，选取记录在同目录的 `selection_manifest.json`。使用 MATLAB 在解压根目录运行 `addpath(fullfile(pwd,'matlab','numerical_scenarios')); make_numerical_figures('waiting')` 可用保存的主例重绘图 3。三个标记对应 E2 解析最优轨道的三个事件。E2、E4 的容量退出区间见补充材料 S2。`python scripts/build_grid_error_table.py` 从保存的摘要重建补充表 S3 的 15 行网格误差结果。各组求解的汇总数据位于 `data/numerical_scenarios/revision_checks/`。

`PACKAGE_PROVENANCE.json` 记录每份文件在项目中的来源或生成命令。`MANIFEST.sha256` 给出其余全部文件的 SHA-256 校验值。
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manuscript_files() -> dict[str, str]:
    """包内路径映射到项目中的实际输入，所有正文图表都从当前工作区读取。"""
    paths = {
        "build.bat", "build.sh",
        "latex/main.tex", "latex/main.pdf", "latex/main.bbl", "latex/references.bib",
        "latex/supplementary.tex", "latex/supplementary.pdf",
        "scripts/build_grid_error_table.py", "scripts/verify_analytic_results.py",
        "data/revision_grid_error_audit.json", "data/revision_grid_errors.csv",
        "validation/figure1_revision_20261021/measure_linewidth_console.log",
        "validation/chatgpt_integration_20261117/run_identity_crosswalk.json",
        "validation/numerical_scenarios/rerun_20261020/comparison_report.json",
        "validation/numerical_scenarios/rerun_20261020/S2.4/execution_report.json",
        "validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json",
    }
    for name in ("grid_error_summary", "grid_error_table", "numerical_values", "scaling_values"):
        paths.add(f"latex/generated/{name}.tex")
    for name in ("analytic_checkpoints.json", "scenario_inputs.json",
                 "generate_analytic_checkpoints.py", "test_analytic_checkpoints.py"):
        paths.add(f"validation/numerical_scenarios/{name}")
    for stem in ("numerical_scenarios/FigN1_optimal_partition", "numerical_scenarios/FigN1_regions",
                 "numerical_scenarios/FigN2_waiting", "numerical_scenarios/FigN3_boundary_tracking",
                 "scaling/FigD_magnitude"):
        for suffix in ("pdf", "png"):
            paths.add(f"figures/{stem}.{suffix}")

    data = "data/numerical_scenarios"
    for filename in ("selection_manifest.json", "export_provenance.json", "figure_provenance.json",
                     "scenario_summary.csv"):
        paths.add(f"{data}/{filename}")
    checks = f"{data}/revision_checks"
    for group in ("main", "initialization", "grid", "horizon", "threshold"):
        paths.update((f"{checks}/{group}_summary.csv", f"{checks}/{group}_summary.json"))
        if group != "main":
            paths.add(f"{checks}/{group}_detailed_summary.csv")

    # 主图的五个兼容副本、网格表两份摘要对应的原始运行和求解器记录。
    entries = json.loads((PROJECT / data / "selection_manifest.json").read_text(encoding="utf-8"))["entries"]
    run_ids = {entry["run_id"] for entry in entries}
    paths.update(f"{data}/{entry['compatibility_file']}" for entry in entries)
    with (PROJECT / checks / "grid_detailed_summary.csv").open(encoding="utf-8-sig", newline="") as stream:
        run_ids.update(row["run_id"] for row in csv.DictReader(stream))
    compact = json.loads((PROJECT / checks / "grid_summary.json").read_text(encoding="utf-8"))
    run_ids.update(row["run_id"] for row in compact["rows"])
    for run_id in run_ids:
        paths.update((f"{data}/runs/{run_id}.mat", f"{data}/runs/{run_id}.solver.json"))
    paths.update(p.relative_to(PROJECT).as_posix() for p in (PROJECT / "matlab/numerical_scenarios").glob("*.m"))
    files = {path: path for path in paths}
    for name in ("figure_followup.py", "figure_data.json"):
        files[f"reproducibility/scaling/{name}"] = f"validation/scaling_followup_20261021/{name}"
    files["reproducibility/scaling/scan.csv"] = "validation/scaling_asymptotics_20261021/scan.csv"
    return files


def main() -> None:
    sources = manuscript_files()
    files = {name: (PROJECT / path).read_bytes() for name, path in sources.items()}
    files["README.md"] = README.encode("utf-8")
    files["requirements.txt"] = b"mpmath==1.3.0\nnumpy==1.26.4\nmatplotlib==3.9.2\n"
    with TemporaryDirectory() as temporary:
        report = Path(temporary) / "analytic_verification.json"
        subprocess.run([sys.executable, str(PROJECT / "scripts/verify_analytic_results.py"),
                        "--output", str(report)], check=True, cwd=PROJECT)
        files["data/analytic_verification.json"] = report.read_bytes()
    sources["data/analytic_verification.json"] = "scripts/verify_analytic_results.py --output data/analytic_verification.json"
    provenance = [{"path": name, "source": sources.get(name, "scripts/package_paper.py"), "sha256": sha(data)}
                  for name, data in sorted(files.items())]
    files["PACKAGE_PROVENANCE.json"] = (json.dumps(provenance, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    files["MANIFEST.sha256"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode("utf-8")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".zip", dir=OUTPUT.parent, delete=False) as handle:
        pending = Path(handle.name)
    try:
        with ZipFile(pending, "w", ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(files.items()):
                archive.writestr(f"{PACKAGE}/{name}", data)
        with ZipFile(pending) as archive:
            for name, data in files.items():
                if archive.read(f"{PACKAGE}/{name}") != data:
                    raise ValueError(f"压缩后的字节与定稿不符 {name}")
        pending.replace(OUTPUT)
    finally:
        pending.unlink(missing_ok=True)
    print(json.dumps({"archive": str(OUTPUT), "files": len(files), "bytes": OUTPUT.stat().st_size,
                      "sha256": sha(OUTPUT.read_bytes())}, indent=2))


if __name__ == "__main__":
    main()

