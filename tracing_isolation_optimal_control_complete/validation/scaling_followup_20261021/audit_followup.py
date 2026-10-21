"""D后续的旧文件字节、理论和数值保护核查。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
PREFIX = PROJECT.name + "/"
BASE = "9a67992248f41dada8c02b2e1851fc87ffa54f4f"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(path):
    target = Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path
    return hashlib.sha256(target.read_bytes()).hexdigest()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def baseline():
    assert not (HERE / "preservation_baseline.json").exists()
    editable = {PREFIX + "latex/" + name for name in ("main.tex", "main.bbl", "main.pdf", "theory_only.pdf")}
    paths = {p for p in git("ls-files", "-z").decode().split("\0") if p and p not in editable}
    for folder in ("data", "matlab", "figures", "validation"):
        paths.update(p.relative_to(REPO).as_posix() for p in (PROJECT / folder).rglob("*")
                     if p.is_file() and HERE not in p.parents and "__pycache__" not in p.parts)
    save("preservation_baseline.json", {"base_commit": BASE, "initial_head": git("rev-parse", "HEAD").decode().strip(),
          "initial_status": git("status", "--porcelain=v1").decode(),
          "main_ref": git("rev-parse", "refs/heads/main").decode().strip(),
          "protected": {p: sha(REPO / p) for p in sorted(paths)}})
    print(f"D followup preservation baseline: {len(paths)} files")


def audit():
    baseline_data = json.loads((HERE / "preservation_baseline.json").read_text(encoding="utf-8"))
    old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
    new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    checks = []

    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    bad = [p for p, digest in baseline_data["protected"].items() if sha(REPO / p) != digest]
    check("existing_file_bytes_unchanged", not bad, {"count": len(baseline_data["protected"]), "changed": bad})
    pattern = r"% BEGIN AUTO-GENERATED (?P<name>[^\r\n]+).*?% END AUTO-GENERATED (?P=name)"
    blocks = lambda text: {m.group("name"): m.group() for m in re.finditer(pattern, text, re.S)}
    check("both_generated_numerical_blocks_verbatim", blocks(old) == blocks(new) and len(blocks(new)) == 2)
    environments = list(re.finditer(r"\\begin\{(theorem|proposition|lemma|corollary|assumption|proof)\}.*?\\end\{\1\}", old, re.S))
    missing = [m.group(1) for m in environments if m.group() not in new]
    check("all_theorems_and_proofs_verbatim", not missing, {"count": len(environments), "changed": missing})
    equations = list(re.finditer(r"\\begin\{(equation|align)\}.*?\\end\{\1\}", old, re.S))
    changed_equations = [re.findall(r"\\label\{([^{}]+)\}", m.group()) for m in equations if m.group() not in new]
    check("all_existing_equation_blocks_verbatim", not changed_equations, {"count": len(equations), "changed": changed_equations})
    macros = lambda text: dict(re.findall(r"\\newcommand\{\\(D\w+)\}\{([^{}]+)\}", text))
    old_macro = macros((PROJECT / "validation/scaling_asymptotics_20261021/computed_values.tex").read_text(encoding="utf-8"))
    new_macro = macros((PROJECT / "latex/generated/scaling_values.tex").read_text(encoding="utf-8"))
    check("all_17_original_D_macro_values_unchanged", len(old_macro) == 17 and all(new_macro.get(k) == v for k, v in old_macro.items()))
    check("no_validation_dependency_in_entrypoints", all("../validation" not in p.read_text(encoding="utf-8") for p in
          (PROJECT / "latex/main.tex", PROJECT / "latex/theory_only.tex")))
    check("macro_input_in_preamble", new.index(r"\input{generated/scaling_values.tex}") < new.index(r"\begin{document}"))
    check("six_D_markers_removed", not re.search(r"% (?:BEGIN|END) D (?:ABSTRACT|MAIN|APPENDIX)", new))
    check("new_scaling_figure_without_insertion_scaling", r"\includegraphics{scaling/FigD_magnitude.pdf}" in new)
    check("old_15_E2_example_removed", "其分母为 $1.578386$" not in new and r"该比较的数值示例见第\ref{sec:scaling}节。" in new)
    check("duration_not_optimization_objective", "正控制时长不是本文的优化目标" in new and "成本最优策略并不同时最小化正控制时长" in new)
    check("main_branch_unchanged", git("rev-parse", "refs/heads/main").decode().strip() == baseline_data["main_ref"])
    result = {"batch": "D_followup", "checks": checks, "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "success": all(c["passed"] for c in checks), "source_sha256": sha(PROJECT / "latex/main.tex"),
              "matlab_calls": 0, "optimizer_calls": 0, "ocp_solves": 0, "ode_integrations": 0}
    save("audit_report.json", result)
    print(f"D followup audit: {result['passed']}/{result['total']}")
    assert result["success"], [c for c in checks if not c["passed"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    baseline() if parser.parse_args().baseline else audit()
