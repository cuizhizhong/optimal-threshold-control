"""检查本次论文整合的引用、编译结果和科学文件保护范围。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPOSITORY = PROJECT.parent
INCOMING = PROJECT / "ai/optimal_threshold_control_revised"
BASELINE = "09140ec16983fa98f1103b873fc03706ff7dd627"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_checks(path: Path, bibliography: set[str]) -> dict:
    text = path.read_text(encoding="utf-8")
    # 网格表等标签定义在共享输入文件中，随实际编译入口一起检查。
    for relative in re.findall(r"\\input\{([^}]+)\}", text):
        included = path.parent / relative
        if not included.suffix:
            included = included.with_suffix(".tex")
        text += "\n" + included.read_text(encoding="utf-8")
    # 忽略纯注释行；宏定义中的 #1 并非实际引用键。
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("%"))
    labels = re.findall(r"\\label\{([^}]+)\}", text)
    references = re.findall(r"\\(?:ref|eqref|pageref)\{([^}]+)\}", text)
    citations = [key.strip() for group in re.findall(
        r"\\cite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}", text
    ) for key in group.split(",")]
    environments = []
    for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", text):
        action, environment = match.groups()
        if action == "begin":
            environments.append(environment)
        else:
            if not environments or environments.pop() != environment:
                raise AssertionError(f"环境嵌套不匹配：{path.name}, {environment}")
    assert not environments
    result = {
        "label_count": len(labels),
        "duplicate_labels": sorted({label for label in labels if labels.count(label) > 1}),
        "undefined_references": sorted(set(references) - set(labels) - {"#1"}),
        "undefined_citations": sorted(set(citations) - bibliography),
        "environment_nesting_passed": True,
    }
    assert not result["duplicate_labels"]
    assert not result["undefined_references"]
    assert not result["undefined_citations"]
    return result


def main() -> None:
    bibliography = set(re.findall(
        r"@\w+\s*\{\s*([^,]+)",
        (PROJECT / "latex/references.bib").read_text(encoding="utf-8"),
    ))
    documents = {}
    for name in ("main", "supplementary"):
        checks = source_checks(PROJECT / f"latex/{name}.tex", bibliography)
        log = (PROJECT / f"latex/{name}.log").read_text(encoding="utf-8", errors="replace")
        diagnostics = [line for line in log.splitlines() if re.search(
            r"Overfull|Underfull|Missing character|undefined|multiply defined|^!|LaTeX Warning|Package .+ Warning", line
        )]
        assert not diagnostics, diagnostics
        pdf = PROJECT / f"latex/{name}.pdf"
        pages = len(PdfReader(pdf).pages)
        assert f"({pages} pages)" in log
        documents[name] = {
            **checks, "pages": pages, "final_log_diagnostics": diagnostics,
            "source_sha256": sha256(PROJECT / f"latex/{name}.tex"),
            "pdf_sha256": sha256(pdf),
        }
    protected = [
        "matlab", "data/numerical_scenarios", "figures",
        "latex/generated/numerical_values.tex", "latex/generated/scaling_values.tex",
    ]
    changed_scientific = subprocess.check_output(
        ["git", "diff", "--name-only", BASELINE, "--", *[
            (PROJECT / relative).relative_to(REPOSITORY).as_posix() for relative in protected
        ]], cwd=REPOSITORY, text=True,
    ).splitlines()
    assert not changed_scientific, changed_scientific
    crosswalk = json.loads((HERE / "run_identity_crosswalk.json").read_text(encoding="utf-8"))
    assert len(crosswalk) == 15
    assert all(row["all_arrays_equal"] and row["cost_equal"] for row in crosswalk)
    analytic = json.loads((HERE / "analytic_verification.json").read_text(encoding="utf-8"))
    assert analytic["summary"]["all_checks_passed"]
    grid = json.loads((PROJECT / "data/revision_grid_error_audit.json").read_text(encoding="utf-8"))
    assert grid["row_count"] == 15
    tests = (HERE / "python_tests.log").read_text(encoding="utf-8-sig", errors="replace")
    assert "Ran 9 tests" in tests and "OK" in tests
    assert sha256(HERE / "baseline_main.tex") == sha256(INCOMING / "review/original_main.tex")
    report = {
        "baseline_commit": BASELINE,
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=REPOSITORY, text=True
        ).strip(),
        "baseline_exactly_matches_incoming_original": True,
        "documents": documents,
        "protected_scientific_paths": protected,
        "changed_protected_scientific_files": changed_scientific,
        "raw_array_crosswalk_pairs": len(crosswalk),
        "all_crosswalk_arrays_and_costs_identical": True,
        "grid_rows": grid["row_count"],
        "grid_identity_differences_preserved": len(grid["historical_id_differences"]),
        "analytic_checks": analytic["summary"],
        "fixture_check_passed": True,
        "python_unit_tests_passed": 9,
        "new_optimization_solves": 0,
        "new_ode_reintegrations": 0,
        "build_note": (
            "First Windows build stopped when xdvipdfmx could not open supplementary.pdf; "
            "the retry hit the same Windows mapped-file restriction. Main compiled normally; "
            "supplementary compiled twice under an isolated job name, then its PDF was "
            "published by atomic replacement. See the retained build logs."
        ),
        "verification_limit": (
            "Textual and algebraic proof review plus finite numerical formula checks; "
            "not formal proof verification or a new optimizer experiment."
        ),
    }
    (HERE / "integration_verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"documents": documents, "protected_scientific_files_changed": 0,
                      "grid_rows": 15, "unit_tests": 9}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
