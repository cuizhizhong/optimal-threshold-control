"""冻结本批字节基准，并按语义锚点合并第 10 步的四段正文。"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

P = Path(__file__).resolve().parents[2]
ROOT = P.parent
V = P / "validation/numerical_scenarios"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline_path = V / "step1011_baseline.json"
    assert not baseline_path.exists(), "本批基准已存在，禁止覆盖。"
    main_path = P / "latex/main.tex"
    text = main_path.read_text(encoding="utf-8")
    plan_path = P / "ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md"
    plan = plan_path.read_text(encoding="utf-8")
    protected = list((P / "data/numerical_scenarios/runs").glob("*"))
    protected += list((P / "data/numerical_scenarios").glob("E?.mat"))
    protected += [P / "data/numerical_scenarios/selection_manifest.json"]
    code = P / "matlab/numerical_scenarios"
    protected += [code / name for name in (
        "prepare_openocl_case.m", "revision_initial_guess.m", "solve_openocl_case.m",
        "validate_numerical_run_grid.m", "numerical_solver_diagnostics.m",
        "build_theory_geometry.m", "analytic_reference.m", "classify_initial_state.m",
        "safe_peak.m", "revision_validation_config.m", "numerical_cases_config.m",
        "assess_numerical_case.m", "detect_numerical_events.m", "compare_numerical_events.m",
    )]
    protected += [V / "analytic_checkpoints.json", V / "scenario_inputs.json"]
    theory = text[text.index("\\begin{abstract}"):text.index("% 数值章节已内联")]
    baseline = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "initial_status": subprocess.check_output(["git", "status", "--porcelain=v1", "-uno"], cwd=ROOT, text=True),
        "plan_sha256": sha(plan_path), "main_sha256": sha(main_path),
        "theory_sha256_normalized": hashlib.sha256(theory.encode()).hexdigest(),
        "protected": {str(f.relative_to(ROOT)).replace("\\", "/"): sha(f) for f in protected if f.is_file()},
        "selected_run_ids": [e["run_id"] for e in json.loads((P / "data/numerical_scenarios/selection_manifest.json").read_text())["entries"]],
    }
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (V / "step1011_main_before.tex").write_bytes(main_path.read_bytes())
    snippets = dict(re.findall(r"## (\d\d_[^\n]+\.tex)\n\n```latex\n(.*?)\n```", plan, re.S))
    assert len(snippets) == 9
    pending = snippets["07_pending_macros.tex"].split("% 导出器必须")[0]
    text = text.replace("\\newif\\ifNumResultsVerified\n", "\\newif\\ifNumResultsVerified\n" + pending + "\n", 1)
    start = text.index("\\section{数值方法与实验设置}")
    end = text.index("\\section{不同初值区域下的数值验证}", start)
    method = snippets["06_numerical_method.tex"]
    method = method[method.index("\\section{"):]
    text = text[:start] + method + "\n\n" + text[end:]
    start = text.index("\\subsection{成本对照与结构总结}") + len("\\subsection{成本对照与结构总结}")
    end = text.index("\\FloatBarrier", start)
    interpretation = snippets["08_results_interpretation.tex"]
    interpretation = interpretation[interpretation.index("表\\ref"):]
    text = text[:start] + "\n\n" + interpretation + "\n" + text[end:]
    start = text.index("\\section{数值复现说明}")
    end = text.index("\\clearpage", start)
    appendix = snippets["09_reproducibility_appendix.tex"]
    appendix = appendix[appendix.index("\\section{"):]
    text = text[:start] + appendix + "\n" + text[end:]
    main_path.write_text(text, encoding="utf-8", newline="\r\n")
    print("STAGE1011_BASELINE_AND_PROSE_READY")


if __name__ == "__main__":
    main()
