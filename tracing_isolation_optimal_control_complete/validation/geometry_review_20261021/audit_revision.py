"""C 作者返修：检查范围、原公式、旧图件和保存记录；不调用优化器或 ODE。"""
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
BASE = "a2909a8a2988ba471180549969852bbcd43075ab"
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


def environment(source, label, kind="proof"):
    pos = source.index(r"\label{" + label + "}")
    start = source.index(r"\begin{" + kind + "}", pos)
    end = source.index(r"\end{" + kind + "}", start) + len(r"\end{" + kind + "}")
    return source[start:end]


old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details})


check("abstract_unchanged", old.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0] ==
      new.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0])
check("model_section_unchanged", old.split(r"\section{模型与控制问题}", 1)[1].split(r"\section{主结果", 1)[0] ==
      new.split(r"\section{模型与控制问题}", 1)[1].split(r"\section{主结果", 1)[0])
check("constant_scope_excludes_wellposedness", r"本节及第\ref{sec:constant-problem}--\ref{sec:constant-uniqueness}节固定" in new and
      "从本节至第" not in new)
check("mechanism_constant_scope_explicit", r"本节采用式\eqref{eq:constants}的常接触率假设。" in new)
def wellposed_statement(source):
    pos = source.index(r"\label{thm:wellposed}")
    start = source.rfind(r"\begin{theorem}", 0, pos)
    end = source.index(r"\end{theorem}", pos) + len(r"\end{theorem}")
    return source[start:end]


check("wellposedness_statement_unchanged", wellposed_statement(old) == wellposed_statement(new))
old_eqs, new_eqs = blocks(old), blocks(new)
changed = [label for label, value in old_eqs.items() if new_eqs.get(label) != value]
check("all_existing_labelled_math_preserved", not changed, {"checked": len(old_eqs), "changed": changed})
check("Phi_definition_once_and_before_overview_theorem", new.count(r"\label{eq:Phi}") == 1 and
      new.index(r"\label{eq:Phi}") < new.index(r"\label{thm:main-overview}"))
overview = new.split(r"\subsection{全域反馈与阶段结构}", 1)[1].split(r"\begin{theorem}", 1)[0]
check("overview_symbols_explained", all(token in overview for token in
      (r"\Gamma_K", "辅助条带", r"s_B", r"\Phi_B:=\Phi(s_B,K)", r"Q^*(s,i)", "分区反馈")))
table = new.split(r"\label{tab:optimal-stages}", 1)[1].split(r"\end{table}", 1)[0]
check("table_has_five_explained_regions", all(token in table for token in
      ("初始已安全，保持零控制", "立即完全跟踪", "自然等待至切换曲线", "自然等待至容量线", "已在容量平台")) and
      r"$\mathcal W_K\cup\mathcal B$" not in table)
check("capacity_platform_not_entire_capacity_line", "仅指 $i=K$ 且 $s>s_B$" in new)
check("old_N1_restored_once", new.count(r"\NumFigureOrBlank{FigN1_regions.pdf}{4.2cm}") == 1 and
      new.count(r"\label{fig:numerical-regions}") == 1)
check("old_N1_inside_numerical_section", new.index(r"\label{sec:numerical-results}") <
      new.index(r"\label{fig:numerical-regions}") < new.index(r"\section{主要结论}"))
old_phrase_count = old.count("绝对连续函数的水平集性质") + old.count("绝对连续函数的零水平集性质")
check("level_set_references_added", new.count(r"\eqref{eq:ac-level-set}") >= old_phrase_count, {"requested_occurrences": old_phrase_count})
lemma = new.split(r"\label{lem:safe-invariant}", 1)[1].split(r"\subsection{完全跟踪弧}", 1)[0]
check("duplicate_viability_endpoint_proof_removed_from_invariance_lemma", r"\mathcal V_0" not in lemma and r"\mathcal V_1" not in lemma)
restricted = r"\label{sec:restricted-feasibility}"
end = r"\section{两类控制弧与显式成本}"
check("C3_section_verbatim", old.split(restricted, 1)[1].split(end, 1)[0] == new.split(restricted, 1)[1].split(end, 1)[0])
check("regularity_proof_verbatim", environment(old, "app:regularity-proof") == environment(new, "app:regularity-proof"))
pattern = r"% BEGIN AUTO-GENERATED (?P<name>[^\r\n]+).*?% END AUTO-GENERATED (?P=name)"
generated = lambda s: {m.group("name"): m.group() for m in re.finditer(pattern, s, re.S)}
check("numerical_generated_content_unchanged", generated(old) == generated(new))
labels = re.findall(r"\\label\{([^{}]+)\}", new)
refs = re.findall(r"\\(?:eqref|ref|pageref)\{([^{}]+)\}", new)
check("no_duplicate_labels", not [k for k, n in Counter(labels).items() if n > 1])
unresolved = sorted(x for x in set(refs) - set(labels) - {"LastPage"} if "#" not in x)
check("references_resolve", not unresolved, unresolved)
for name in ("references.bib", "theory_only.tex"):
    check(name + "_unchanged", (PROJECT / "latex" / name).read_text(encoding="utf-8") ==
          git("show", f"{BASE}:{PREFIX}latex/{name}").decode())
prior = json.loads((PROJECT / "validation/model_no_return_revision_20261020/preservation_baseline.json").read_text(encoding="utf-8"))
bad = [p for p, value in prior["protected_files"].items() if sha(read(REPO / p)) != value["working_sha256"]]
check("535_saved_records_code_figures_unchanged", not bad, {"count": len(prior["protected_files"]), "changed": bad})
phase = json.loads((PROJECT / "validation/geometry_proofs_20261021/two_layer_phase_checks.json").read_text(encoding="utf-8"))
check("new_two_layer_figure_unchanged", all(sha(read(PROJECT / p)) == h for p, h in phase["outputs_sha256"].items()))
allowed = {PREFIX + p for p in ("latex/main.tex", "latex/main.bbl", "latex/main.pdf", "latex/theory_only.pdf")}
actual = git("diff", "--name-only", BASE).decode().splitlines()
check("tracked_change_scope", all(p in allowed or p.startswith(PREFIX + "validation/geometry_review_20261021/") for p in actual), actual)
check("older_validation_records_unchanged", not git("diff", BASE, "--", PREFIX + "validation/geometry_proofs_20261021/",
      PREFIX + "validation/intro_review_20261021/", PREFIX + "validation/intro_contributions_20261021/").strip())
build = PROJECT / "tmp/geometry_review_20261021/attempt1"
main_aux = (build / "main.aux").read_text(encoding="utf-8")
theory_aux = (build / "theory_only.aux").read_text(encoding="utf-8")
check("compiled_N1_main_only", r"\newlabel{fig:numerical-regions}" in main_aux and
      r"\newlabel{fig:numerical-regions}" not in theory_aux)
compiled = json.loads((HERE / "attempt1/build_report.json").read_text(encoding="utf-8"))
check("compiled_sources_match_current", compiled["success"] and all(
      sha(read(PROJECT / "latex" / name)) == value for name, value in compiled["source_sha256"].items()))
report = {"batch": "C_author_review", "base_commit": BASE, "checks": checks,
          "passed": sum(c["passed"] for c in checks), "total": len(checks),
          "success": all(c["passed"] for c in checks), "source_sha256": sha(new.encode()),
          "optimizer_calls": 0, "ocp_solves": 0, "new_ode_integrations": 0}
(HERE / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"C author review audit: {report['passed']}/{report['total']}")
assert report["success"], [c for c in checks if not c["passed"]]
