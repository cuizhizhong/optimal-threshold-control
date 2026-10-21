"""阶段 F 的基准保护、旧宏逐字及正文范围核查；不调用科学计算。"""
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
BASE = "89d9cc3751951fd236f304c65ca0ee7fc2e667ef"
EDITABLE = {
    PREFIX + "latex/" + n for n in ("main.tex", "main.pdf", "main.bbl", "theory_only.pdf")
} | {
    PREFIX + "matlab/numerical_scenarios/" + n for n in (
        "export_numerical_latex.m", "verify_saved_result_exporter.m",
        "verify_revision_exporter.m", "verify_pending_result_exporter.m")
} | {PREFIX + "data/numerical_scenarios/export_provenance.json"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(p):
    target = Path("\\\\?\\" + str(p.resolve())) if os.name == "nt" else p
    return hashlib.sha256(target.read_bytes()).hexdigest()


def exists(p):
    target = Path("\\\\?\\" + str(p.resolve())) if os.name == "nt" else p
    return target.exists()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def block(text, name):
    return re.search(r"% BEGIN AUTO-GENERATED " + name + r"\n.*?% END AUTO-GENERATED " + name, text, re.S).group()


def remove_macro(text, name):
    match = re.search(r"\\(?:provide|renew|new)command\{\\" + name + r"\}\{", text)
    assert match, name
    depth = 1
    pos = match.end()
    while depth:
        previous = pos - 1
        while previous >= 0 and text[previous] == "\\":
            previous -= 1
        escaped = (pos - previous - 1) % 2 == 1
        if text[pos] == "{" and not escaped:
            depth += 1
        elif text[pos] == "}" and not escaped:
            depth -= 1
        pos += 1
    if text[pos:pos+1] == "\n":
        pos += 1
    return text[:match.start()] + text[pos:]


def mask_prose(text):
    # 两个可改正文区间：第17--18节，及原数值复现附录。自动块单独严格核对。
    start = text.index(r"\section{数值方法与实验设置}")
    end = text.index(r"\section{\texorpdfstring{时变接触率", start)
    text = text[:start] + "<NUMERICAL_SECTIONS>\n" + text[end:]
    start = text.index("\\ifdefined\\TheoryOnly\\else\n\\section{", text.index(r"\label{eq:medical-threshold}"))
    end = text.index("\\fi\n\\bibliographystyle", start)
    text = text[:start] + "<NUMERICAL_APPENDIX>\n" + text[end:]
    generated = block(text, "NUMERICAL RESULTS")
    return text.replace(generated, "<NUMERICAL_RESULTS_BLOCK>")


def baseline():
    assert not (HERE / "preservation_baseline.json").exists()
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    paths = {p for p in git("ls-files", "-z").decode().split("\0") if p and p not in EDITABLE}
    for folder in ("data", "figures"):
        paths.update(p.relative_to(REPO).as_posix() for p in (PROJECT / folder).rglob("*") if p.is_file())
    paths.difference_update(EDITABLE)
    save("preservation_baseline.json", {
        "base_commit": BASE, "initial_head": BASE,
        "main_ref": git("rev-parse", "refs/heads/main").decode().strip(),
        "initial_status": git("status", "--porcelain=v1").decode(),
        "protected": {p: sha(REPO / p) for p in sorted(paths)},
        "editable": sorted(EDITABLE),
    })
    scripts = []
    for folder in ("matlab", "validation"):
        scripts.extend(p for p in (PROJECT / folder).rglob("*") if p.suffix in (".m", ".py", ".ps1", ".bat", ".sh") and HERE not in p.parents)
    needles = ("EXPERIMENT_REQUIRED", "只允许实际结果驱动", "下列宏由实际保存数据生成")
    hits = [{"path": p.relative_to(PROJECT).as_posix(), "needle": n}
            for p in scripts for n in needles if n in p.read_text(encoding="utf-8", errors="replace")]
    save("comment_dependency_search.json", {"script_count": len(scripts), "needles": needles, "hits": hits,
        "safe_to_remove": not hits})
    assert not hits, hits
    print(f"F baseline: {len(paths)} protected files; {len(scripts)} scripts searched; no comment dependency")


def audit():
    b = json.loads((HERE / "preservation_baseline.json").read_text(encoding="utf-8"))
    old = git("show", BASE + ":" + PREFIX + "latex/main.tex").decode("utf-8").replace("\r\n", "\n")
    new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    checks = []
    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details})
    bad = [p for p, digest in b["protected"].items() if not exists(REPO / p) or sha(REPO / p) != digest]
    check("existing_protected_file_bytes", not bad, {"count": len(b["protected"]), "changed": bad})
    check("reference_block_verbatim", block(old, "NUMERICAL REFERENCE VALUES") == block(new, "NUMERICAL REFERENCE VALUES"))
    result = block(new, "NUMERICAL RESULTS")
    for name in ("NumErrorTableRows", "NumResidualSummary"):
        check(name + "_defined_once", result.count("command{\\" + name + "}") == 1)
        result = remove_macro(result, name)
    check("all_old_result_definitions_and_flags_verbatim", result == block(old, "NUMERICAL RESULTS"))
    check("all_prose_outside_authorized_ranges_verbatim", mask_prose(old) == mask_prose(new))
    environments = list(re.finditer(r"\\begin\{(theorem|proposition|lemma|corollary|assumption|proof)\}.*?\\end\{\1\}", old, re.S))
    check("all_theorem_and_proof_blocks_verbatim", all(m.group() in new for m in environments), len(environments))
    figs = [p for p in b["protected"] if "/figures/" in p and any(n in p for n in
            ("FigN1_regions", "FigN2", "FigN3", "FigN1_optimal_partition", "FigD_magnitude"))]
    check("five_figure_families_bytes", len(figs) >= 5 and all(sha(REPO / p) == b["protected"][p] for p in figs), figs)
    records = [p for p in b["protected"] if "/data/numerical_scenarios/" in p]
    check("all_data_except_export_provenance_bytes", all(sha(REPO / p) == b["protected"][p] for p in records), len(records))
    check("main_ref_unchanged", git("rev-parse", "refs/heads/main").decode().strip() == b["main_ref"])
    check("requested_body_macros_moved", all(new.count("\\NumFindingParagraph{\\" + name + "}") == 1 for name in
          ("NumCheckStatement", "NumRobustnessStatement", "NumOverallFinding", "NumReproducibilityDetails")))
    check("internal_execution_comments_removed", not any(n in new for n in ("EXPERIMENT_REQUIRED", "只允许实际结果驱动", "下列宏由实际保存数据生成")))
    result = {"base_commit": BASE, "checks": checks, "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "success": all(c["passed"] for c in checks), "source_sha256": sha(PROJECT / "latex/main.tex"),
              "optimizer_calls": 0, "new_ocp_solves": 0, "pushes": 0}
    save("preservation_report.json", result)
    print(f"F preservation: {result['passed']}/{result['total']}")
    assert result["success"], [c for c in checks if not c["passed"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    baseline() if parser.parse_args().baseline else audit()
