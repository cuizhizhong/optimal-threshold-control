"""生成阶段F的显式暂存清单，不执行git add/commit/push。"""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
PREFIX = PROJECT.name + "/"
production = [
    "data/numerical_scenarios/export_provenance.json",
    "latex/main.tex", "latex/main.pdf", "latex/theory_only.pdf",
    "matlab/numerical_scenarios/export_numerical_latex.m",
    "matlab/numerical_scenarios/verify_saved_result_exporter.m",
    "matlab/numerical_scenarios/verify_revision_exporter.m",
    "matlab/numerical_scenarios/verify_pending_result_exporter.m",
]
assert json.loads((HERE / "acceptance_report.json").read_text(encoding="utf-8"))["success"]
message = """paper: 数值章节重写（F）

明确T=300终端延拓与放宽容量值函数的比较条件，压缩第17–18节，新增由保存数据生成的误差表和五句残差摘要；旧诊断宏移入补充材料S，记录所有已知证据缺口。

核对：导出器回归11+3+2通过，符号28/28，独立20数值与5判断及残差核对通过，保护审计12/12、最终汇总23/23。仓库内与Git导出自包含副本双稿最终日志零诊断；主文/TheoryOnly仍46/36页，数值两节7→6页；8页150dpi逐页目视。保留首次沙箱启动、排版和引用稳定性失败记录。

原记录、评估、run_index、五组图、全部旧宏及授权范围外正文保持。优化器、新增OCP、重评、ODE与图形重导出均0；MATLAB仅重新导出与三套回归。不推送，等待作者审阅。

Co-Authored-By: Codex <noreply@openai.com>
"""
(HERE / "commit_message.txt").write_text(message, encoding="utf-8", newline="\n")
paths = {PREFIX + p for p in production}
paths.update(p.relative_to(REPO).as_posix() for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
paths.update((HERE / n).relative_to(REPO).as_posix() for n in ("changed_files.txt", "staging_paths.json"))
paths = sorted(paths)
(HERE / "changed_files.txt").write_text("\n".join(paths) + "\n", encoding="utf-8", newline="\n")
(HERE / "staging_paths.json").write_text(json.dumps(paths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
assert head == "89d9cc3751951fd236f304c65ca0ee7fc2e667ef", head
print(f"F explicit staging list: {len(paths)} files (8 production + {len(paths)-8} validation)")
