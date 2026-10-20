"""C 的源文、公式、搬移与记录保护核对，不调用优化器或 OCP。"""
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
BASE = "e86ec62094f72c2aa56c05191c0ecaf5166d3cf6"
PREFIX = PROJECT.name + "/"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return Path("\\\\?\\" + str(path.resolve())).read_bytes() if os.name == "nt" else path.read_bytes()


def blocks(source):
    result = {}
    for m in re.finditer(r"\\begin\{(equation|align)\}(.*?)\\end\{\1\}", source, re.S):
        for label in re.findall(r"\\label\{([^{}]+)\}", m.group()):
            result[label] = m.group()
    return result


def generated(source):
    pattern = r"% BEGIN AUTO-GENERATED (?P<name>[^\r\n]+).*?% END AUTO-GENERATED (?P=name)"
    return {m.group("name"): m.group() for m in re.finditer(pattern, source, re.S)}


old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details})


check("abstract_unchanged_from_author_review", old.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0] ==
      new.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0])
check("model_section_unchanged", old.split(r"\section{模型与控制问题}", 1)[1].split(r"\section{解的适定性", 1)[0].strip() ==
      new.split(r"\section{模型与控制问题}", 1)[1].split(r"\section{主结果与两层几何}", 1)[0].strip())
check("overview_immediately_after_model", new.index(r"\label{sec:model}") < new.index(r"\label{sec:main-results}") < new.index(r"\label{sec:wellposed}"))
check("feasibility_before_cost_partitions", new.index(r"\label{eq:viability-definition}") < new.index(r"\label{def:candidate}"))
old_eqs, new_eqs = blocks(old), blocks(new)
changed = [label for label, value in old_eqs.items() if label != "eq:ac-level-set" and new_eqs.get(label) != value]
check("existing_nonstandard_equations_preserved", not changed, {"checked": len(old_eqs) - 1, "changed": changed})
check("numerical_generated_blocks_unchanged", generated(old) == generated(new), list(generated(old)))
rs = old.index(r"\begin{proof}", old.index(r"\label{prop:regularity}"))
re_ = old.index(r"\end{proof}", rs) + len(r"\end{proof}")
proof = old[rs:re_]
app = new.split(r"\label{app:regularity-proof}", 1)[1]
check("regularity_complete_proof_moved_verbatim", proof in app, sha(proof.encode()))
check("standard_lemmas_replaced_by_textbook", all(x not in new for x in ("lem:ac-level-set", "lem:ac-composition")) and "Fremlin2001Volume2" in new)
check("free_wait_variation_restricted_below_capacity", r"x=(s,i)\in\mathcal E\cap\Dcal$ 且 $i<K$" in new)
check("cost_and_Theta_mechanism_present", all(r"\label{" + k + "}" in new for k in ("eq:cost-in-Phi", "eq:waiting-marginal-cost")))
check("restricted_endpoints_and_physical_degeneracy_present", all(s in new for s in (r"\mathcal V_0=\Acal", r"\mathcal V_1=\Dcal", r"h_{\bar q}\ge1-K")))
check("all_control_set_not_defined_using_admissibility", r"\text{ 及 }q\in\mathcal C_1" in new)
check("intro_first_contribution_uses_main_theorem", r"定理\ref{thm:main-overview}给出全域最优反馈" in new)
check("old_capability_warning_updated", "其成本最优反馈和验证函数尚未构造" in new)
clean = re.sub(r"(?<!\\)%[^\n]*", "", new)
labels = re.findall(r"\\label\{([^{}]+)\}", clean)
refs = re.findall(r"\\(?:eqref|ref|pageref)\{([^{}]+)\}", clean)
unresolved = sorted(x for x in set(refs) - set(labels) - {"LastPage"} if "#" not in x)
check("labels_unique", not [k for k, n in Counter(labels).items() if n > 1])
check("source_references_resolve", not unresolved, unresolved)
bib = (PROJECT / "latex/references.bib").read_text(encoding="utf-8")
old_bib = git("show", f"{BASE}:{PREFIX}latex/references.bib").decode()
check("old_bibliography_preserved", bib.startswith(old_bib))
keys = re.findall(r"@\w+\s*\{\s*([^,]+),", bib)
cites = []
for m in re.finditer(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^{}]+)\}", clean):
    cites.extend(x.strip() for x in m.group(1).split(","))
check("citations_resolve", set(cites) <= set(keys) and len(keys) == len(set(keys)))
prior = json.loads((PROJECT / "validation/model_no_return_revision_20261020/preservation_baseline.json").read_text(encoding="utf-8"))
bad = [p for p, v in prior["protected_files"].items() if sha(read(REPO / p)) != v["working_sha256"]]
check("535_original_records_code_figures_unchanged", not bad, {"count": len(prior["protected_files"]), "changed": bad})
allowed = {PREFIX + p for p in ("latex/main.tex", "latex/references.bib", "latex/main.bbl", "latex/main.pdf", "latex/theory_only.pdf",
                              "figures/numerical_scenarios/FigN1_two_layers.pdf", "figures/numerical_scenarios/FigN1_two_layers.png")}
actual = git("diff", "--name-only", BASE).decode().splitlines()
check("tracked_scope", all(p in allowed or p.startswith(PREFIX + "validation/geometry_proofs_20261021/") for p in actual), actual)
check("B_records_not_overwritten", not git("diff", BASE, "--", PREFIX + "validation/intro_review_20261021/", PREFIX + "validation/intro_contributions_20261021/").strip())
report = {"batch": "C1--C4", "base_commit": BASE, "checks": checks,
          "passed": sum(c["passed"] for c in checks), "total": len(checks),
          "success": all(c["passed"] for c in checks), "source_sha256": sha(new.encode()),
          "optimizer_calls": 0, "ocp_solves": 0}
(HERE / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"C audit: {report['passed']}/{report['total']}")
assert report["success"], [c for c in checks if not c["passed"]]
