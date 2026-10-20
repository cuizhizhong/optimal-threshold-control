"""核对 B 的修改边界、引用及已有数据；不调用优化器或数值求解器。"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
PREFIX = PROJECT.relative_to(REPO).as_posix() + "/"
BASE = "3be55d664b494429a86fc26ee270f14637ff3c75"
BASELINE = HERE / "preservation_baseline.json"
MARK = r"\section{模型与控制问题}"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    resolved = path.resolve()
    return Path("\\\\?\\" + str(resolved)).read_bytes() if os.name == "nt" else resolved.read_bytes()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        assert not BASELINE.exists(), "不得覆盖保护基线"
        assert git("rev-parse", "HEAD").decode().strip() == BASE
        assert not git("diff", "--name-only", BASE).strip(), "初始已有跟踪文件改动"
        paths = git("ls-tree", "-r", "--name-only", "-z", BASE, "--", PREFIX).decode().split("\0")
        protected = {p: sha(read(REPO / p)) for p in paths if p and any(
            p.startswith(PREFIX + root) for root in ("data/", "figures/", "matlab/"))}
        save(BASELINE, {"base_commit": BASE, "captured_utc": datetime.now(timezone.utc).isoformat(),
                        "protected_files": protected,
                        "initial_status": git("status", "--short").decode(),
                        "optimizer_calls": 0, "ocp_solves": 0})
        print(f"B baseline: {len(protected)} protected files")
        return
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
    new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    old_bib = git("show", f"{BASE}:{PREFIX}latex/references.bib").decode().replace("\r\n", "\n")
    bib = (PROJECT / "latex/references.bib").read_text(encoding="utf-8")
    checks = []

    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    check("model_and_all_later_text_unchanged", new.split(MARK, 1)[1] == old.split(MARK, 1)[1])
    check("preamble_unchanged", new.split(r"\begin{abstract}", 1)[0] == old.split(r"\begin{abstract}", 1)[0])
    check("existing_bibliography_unchanged", bib.startswith(old_bib.rstrip() + "\n"))
    changed = [p for p, digest in baseline["protected_files"].items() if sha(read(REPO / p)) != digest]
    check("protected_data_code_figures_unchanged", not changed, {"count": len(baseline["protected_files"]), "changed": changed})
    allowed = {PREFIX + p for p in ("latex/main.tex", "latex/references.bib", "latex/main.bbl",
                                   "latex/main.pdf", "latex/theory_only.pdf")}
    actual = git("diff", "--name-only", BASE).decode().splitlines()
    check("tracked_change_scope", all(p in allowed or p.startswith(
        PREFIX + "validation/intro_contributions_20261021/") for p in actual), actual)
    check("theory_wrapper_unchanged", read(PROJECT / "latex/theory_only.tex").replace(b"\r\n", b"\n") ==
          git("show", f"{BASE}:{PREFIX}latex/theory_only.tex").replace(b"\r\n", b"\n"))
    clean = re.sub(r"(?<!\\)%[^\n]*", "", new)
    labels = re.findall(r"\\label\{([^{}]+)\}", clean)
    refs = re.findall(r"\\(?:eqref|ref|pageref)\{([^{}]+)\}", clean)
    unresolved = sorted(set(x for x in refs if "#" not in x) - set(labels) - {"LastPage"})
    check("no_duplicate_labels", not [x for x, n in Counter(labels).items() if n > 1])
    check("references_resolve", not unresolved, unresolved)
    cites = []
    for match in re.finditer(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^{}]+)\}", clean):
        cites.extend(k.strip() for k in match.group(1).split(","))
    keys = re.findall(r"@\w+\s*\{\s*([^,]+),", bib)
    check("no_duplicate_bibkeys", len(keys) == len(set(keys)))
    check("citations_resolve", set(cites) <= set(keys), sorted(set(cites) - set(keys)))
    for key in ("AvramFreddiGoreac2022", "FreddiGoreac2024", "FreddiGoreacLiXu2022",
                "Kretzschmar2020", "Morris2021"):
        check("independent_and_cited_" + key, keys.count(key) == 1 and key in cites)
    intro = new.split(r"\label{sec:introduction}", 1)[1].split(MARK, 1)[0]
    check("no_introduction_table", r"\begin{table}" not in intro and r"\begin{tabular}" not in intro)
    check("no_return_results_or_symbols_in_abstract_intro", not re.search(
        r"\\lambda|V_0|V_\\lambda|\\tilde\s*\{?s|即时回流|两个端点|回流率", intro))
    check("three_contributions_reference_existing_results", all(r"\ref{" + label + "}" in intro for label in
        ("prop:Gamma-geometry", "cor:Gamma-labels", "thm:verification", "cor:optimal-synthesis", "thm:unique-q")))
    report = {"batch": "B", "base_commit": BASE, "checks": checks,
              "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "success": all(c["passed"] for c in checks), "optimizer_calls": 0, "ocp_solves": 0}
    save(HERE / "audit_report.json", report)
    print(f"B audit: {report['passed']}/{report['total']}")
    assert report["success"], [c for c in checks if not c["passed"]]


if __name__ == "__main__":
    main()
