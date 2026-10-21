"""D 批的改动边界、旧记录字节和正文交叉引用核查。"""
import argparse
from collections import Counter
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
BASE = "8b8f5a239193f8b5102355f9946b43eaea2b72ea"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(path):
    target = Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path
    return hashlib.sha256(target.read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generated(text):
    pat = r"% BEGIN AUTO-GENERATED (?P<name>[^\r\n]+).*?% END AUTO-GENERATED (?P=name)"
    return {m.group("name"): m.group() for m in re.finditer(pat, text, re.S)}


def baseline():
    target = HERE / "preservation_baseline.json"
    assert not target.exists(), "不得覆盖已有基线"
    tracked = git("ls-files", "-z").decode().split("\0")
    protected = set()
    editable = {PREFIX + "latex/" + name for name in
                ("main.tex", "references.bib", "main.bbl", "main.pdf", "theory_only.pdf")}
    for name in tracked:
        if name and name not in editable and not name.startswith(PREFIX + "validation/" + HERE.name + "/"):
            protected.add(name)
    for folder in ("data", "matlab", "figures", "validation"):
        for path in (PROJECT / folder).rglob("*"):
            if path.is_file() and HERE not in path.parents and "__pycache__" not in path.parts:
                protected.add(path.relative_to(REPO).as_posix())
    save(target, {"base_commit": BASE, "initial_head": git("rev-parse", "HEAD").decode().strip(),
                  "initial_status": git("status", "--porcelain=v1").decode(),
                  "main_ref": git("rev-parse", "refs/heads/main").decode().strip(),
                  "protected_files": {name: sha(REPO / name) for name in sorted(protected)}})
    print(f"D preservation baseline: {len(protected)} files")


def audit():
    prior = json.loads((HERE / "preservation_baseline.json").read_text(encoding="utf-8"))
    checks = []

    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
    new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    check("generated_numerical_blocks_verbatim", generated(old) == generated(new))
    original_eq = re.findall(r"\\begin\{(equation|align)\}.*?\\end\{\1\}", old, re.S)
    original_blocks = list(re.finditer(r"\\begin\{(equation|align)\}.*?\\end\{\1\}", old, re.S))
    changed = [re.findall(r"\\label\{([^{}]+)\}", m.group()) for m in original_blocks if m.group() not in new]
    check("existing_equation_blocks_verbatim", not changed, {"count": len(original_eq), "changed": changed})
    # 本批只插入 D 正文、附录及摘要的一句量级结论。
    clean_new = re.sub(r"% BEGIN D (?:MAIN|APPENDIX|ABSTRACT)\n.*?% END D (?:MAIN|APPENDIX|ABSTRACT)\n", "", new, flags=re.S)
    check("old_manuscript_verbatim_after_removing_additions", clean_new == old)
    bad = [name for name, digest in prior["protected_files"].items() if sha(REPO / name) != digest]
    check("existing_records_code_figures_validation_byte_identity", not bad,
          {"count": len(prior["protected_files"]), "changed": bad})
    clean = re.sub(r"(?<!\\)%[^\n]*", "", new)
    labels = re.findall(r"\\label\{([^{}]+)\}", clean)
    refs = re.findall(r"\\(?:eqref|ref|pageref)\{([^{}]+)\}", clean)
    check("unique_labels", not [x for x, count in Counter(labels).items() if count > 1])
    check("resolved_labels", not [x for x in set(refs) - set(labels) - {"LastPage"} if "#" not in x])
    bib = (PROJECT / "latex/references.bib").read_text(encoding="utf-8")
    keys = re.findall(r"@\w+\s*\{\s*([^,]+),", bib)
    citations = []
    for m in re.finditer(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^{}]+)\}", clean):
        citations.extend(x.strip() for x in m.group(1).split(","))
    check("resolved_unique_bibliography", set(citations) <= set(keys) and len(keys) == len(set(keys)))
    old_bib = git("show", f"{BASE}:{PREFIX}latex/references.bib").decode()
    check("old_bibliography_verbatim_prefix", bib.startswith(old_bib))
    check("main_branch_unchanged", prior["main_ref"] == git("rev-parse", "refs/heads/main").decode().strip())
    allowed = {PREFIX + "latex/" + name for name in
               ("main.tex", "references.bib", "main.bbl", "main.pdf", "theory_only.pdf")}
    changes = git("diff", "--name-only", BASE).decode().splitlines()
    check("tracked_edit_scope", all(p in allowed or p.startswith(PREFIX + "validation/" + HERE.name + "/") for p in changes), changes)
    result = {"batch": "D", "base_commit": BASE, "checks": checks,
              "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "success": all(c["passed"] for c in checks),
              "optimizer_calls": 0, "ocp_solves": 0, "ode_integrations": 0,
              "source_sha256": sha(PROJECT / "latex/main.tex")}
    save(HERE / "audit_report.json", result)
    print(f"D audit: {result['passed']}/{result['total']}")
    assert result["success"], [c for c in checks if not c["passed"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    baseline() if args.baseline else audit()
