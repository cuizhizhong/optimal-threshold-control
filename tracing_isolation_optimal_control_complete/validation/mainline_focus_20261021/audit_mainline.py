"""以作者指定的 84a8943 为基准，只读核对正文范围与既有数值证据。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = HERE.parents[2]
PREFIX = PROJECT.name + "/"
BASE = "84a89431349681b02a82224d86120e63c191f412"


def read(path):
    absolute = str(Path(path).resolve())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = "\\\\?\\" + absolute
    with open(absolute, "rb") as handle:
        return handle.read()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lf(data):
    # 只统一 Windows 换行；不删除任何空格、公式或正文。
    return data.replace(b"\r\n", b"\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def old(relative):
    return git("show", BASE + ":" + PREFIX + relative)


def current(relative):
    return read(PROJECT / relative)


def normalize_safe_name(data):
    # 唯一允许的辅助安全集改名；原来的 A 已在物理初值范围内。
    return data.replace(b"\\widehat{\\Acal}", b"\\Acal")


def labeled_math(data):
    pattern = rb"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}.*?\\end\{\1\}"
    result = {}
    for match in re.finditer(pattern, data, re.S):
        labels = re.findall(rb"\\label\{([^}]+)\}", match.group())
        for label in labels:
            result[label.decode()] = match.group()
    return result


def statements_and_proofs(data):
    """按命题标签配对陈述和紧随其后的证明，不使用定理编号。"""
    result = {}
    pattern = rb"\\begin\{(theorem|proposition|lemma|corollary)\}(?:\[[^\n]*?\])?.*?\\end\{\1\}"
    for match in re.finditer(pattern, data, re.S):
        labels = re.findall(rb"\\label\{([^}]+)\}", match.group())
        if not labels:
            continue
        label = labels[0].decode()
        proof = re.match(rb"\s*\\begin\{proof\}.*?\\end\{proof\}", data[match.end():], re.S)
        result[label] = {"statement": match.group(), "proof": proof.group().lstrip() if proof else None}
    return result


def main():
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    capture = json.loads(read(HERE / "baseline_sha256.json"))
    check("base_capture_matches_author_commit", capture["base_commit"] == BASE)
    before, after = lf(old("latex/main.tex")), lf(current("latex/main.tex"))
    text = after.decode("utf-8")
    removed_section = before[before.index(b"\\subsection{\xe5\x8f\x97\xe9\x99\x90\xe8\xb7\x9f\xe8\xb8\xaa\xe8\x83\xbd\xe5\x8a\x9b\xe4\xb8\x8e\xe5\x8f\xaf\xe8\xa1\x8c\xe5\x9f\x9f}"):
                             before.index(b"\\section{", before.index(b"\\label{sec:restricted-feasibility}"))]
    removed_labels = set(re.findall(rb"\\label\{([^}]+)\}", removed_section))
    removed_labels.update(x.encode() for x in ("eq:all-control-safe", "eq:overview-safe", "eq:viability-definition", "eq:viability-endpoints", "fig:two-layer-regions"))
    remaining_labels = re.findall(rb"\\label\{([^}]+)\}", after)
    remaining_refs = re.findall(rb"\\(?:ref|eqref|pageref|autoref)\{([^}]+)\}", after)
    unique_labels = set(remaining_labels)
    check("deleted_labels_absent", not (removed_labels & unique_labels),
          removed_labels=sorted(label.decode() for label in removed_labels))
    # \ref{#1} 是已存在的宏形参，实例化后才成为实际引用。
    dangling = sorted(label for label in set(remaining_refs) - unique_labels - {b"LastPage"}
                      if not re.fullmatch(rb"#\d", label))
    check("no_dangling_references", not dangling, dangling=[x.decode() for x in dangling])
    duplicates = sorted(x for x in unique_labels if remaining_labels.count(x) > 1)
    check("all_source_labels_unique", not duplicates, duplicates=[x.decode() for x in duplicates])

    math_before, math_after = labeled_math(before), labeled_math(after)
    allowed_changed = {"eq:value-definition", "eq:safe-set"}
    mathematical_changes = []
    retained = []
    for label, expression in math_before.items():
        if label.encode() in removed_labels or label in allowed_changed:
            continue
        retained.append(label)
        if label not in math_after or normalize_safe_name(expression) != math_after[label]:
            mathematical_changes.append(label)
    added_math = sorted(set(math_after) - set(math_before))
    check("retained_labeled_formulas_exact_except_A_rename", not mathematical_changes,
          checked_labels=len(retained), changed_labels=mathematical_changes,
          explicitly_changed_definition_labels=sorted(allowed_changed), added_labels=added_math)
    check("P0_definition_exact", math_before["eq:uncontrolled-future-peak"] == math_after.get("eq:uncontrolled-future-peak"))
    disease_line = "疾病灭绝轴须另取 $P_0(s,0)=0$，因为此时感染恒为零；\n它不由 $s>h$ 时的正感染分支连续外推，且不属于本文正感染主定理的状态域。"
    check("disease_extinction_axis_statement_exact", disease_line in text)

    stm_before, stm_after = statements_and_proofs(before), statements_and_proofs(after)
    changed_statements = []
    changed_proofs = []
    for label, record in stm_before.items():
        if label == "prop:restricted-feasibility":
            continue
        if label not in stm_after:
            changed_statements.append(label)
            changed_proofs.append(label)
            continue
        expected_statement = normalize_safe_name(record["statement"])
        if label == "thm:main-overview":
            # 定理从 x0∈D 出发，首次入 A 与首次入 A∩D 等价。
            expected_statement = expected_statement.replace(b"\\Acal$", b"\\Acal\\cap\\Dcal$", 1)
        if label not in {"prop:safe-exact", "lem:safe-invariant"} and expected_statement != stm_after[label]["statement"]:
            changed_statements.append(label)
        if label != "lem:safe-invariant" and normalize_safe_name(record["proof"] or b"") != (stm_after[label]["proof"] or b""):
            changed_proofs.append(label)
    check("retained_theorem_statements_unchanged_except_safe_scope", not changed_statements,
          checked_statements=len(stm_before) - 3, changed=changed_statements)
    check("retained_proofs_unchanged_except_safe_invariance_endpoint_removal", not changed_proofs,
          checked_proofs=sum(x["proof"] is not None for label, x in stm_before.items()
                             if label not in {"prop:restricted-feasibility", "lem:safe-invariant"}), changed=changed_proofs)
    safe_exact = stm_after.get("prop:safe-exact", {})
    check("safe_exact_proof_unchanged", stm_before["prop:safe-exact"]["proof"] == safe_exact.get("proof"))
    check("V_zero_restricted_to_physical_safe_states", b"\\Acal\\cap\\Dcal" in safe_exact.get("statement", b""))
    expected_safe_statement = stm_before["prop:safe-exact"]["statement"].replace(
        "因此 $V=0$ 于 $\\Acal$".encode(), "因此 $V=0$ 于 $\\Acal\\cap\\Dcal$".encode(), 1)
    check("safe_exact_statement_only_physical_scope_clarified", expected_safe_statement == safe_exact.get("statement"))
    expected_safe_proof = stm_before["lem:safe-invariant"]["proof"].replace(
        "这给出 $\\Acal\\subset\\mathcal A^0$；反向包含由零控制属于所有允许控制之一得到。\n".encode(), b"", 1)
    check("safe_invariance_proof_only_deleted_endpoint_sentence", expected_safe_proof == stm_after["lem:safe-invariant"]["proof"])

    pattern = rb"% BEGIN AUTO-GENERATED ([^\r\n]+)\n.*?% END AUTO-GENERATED \1(?:\n|$)"
    auto_before, auto_after = list(re.finditer(pattern, before, re.S)), list(re.finditer(pattern, after, re.S))
    check("two_numerical_auto_blocks_byte_identical", len(auto_before) == len(auto_after) == 2 and
          all(a.group() == b.group() for a, b in zip(auto_before, auto_after)),
          blocks=[{"name": match.group(1).decode(), "sha256": sha(match.group())} for match in auto_after])
    section_model = lambda data: data[data.index(b"\\section{\xe6\xa8\xa1\xe5\x9e\x8b\xe4\xb8\x8e\xe6\x8e\xa7\xe5\x88\xb6\xe9\x97\xae\xe9\xa2\x98}"):
                                     data.index(b"\\label{sec:main-results}")].rsplit(b"\\section{", 1)[0]
    check("model_section_exact", section_model(before) == section_model(after))
    check("all_appendices_exact", before[before.index(b"\\appendix"):] == after[after.index(b"\\appendix"):])
    abstract = lambda data: re.search(rb"\\begin\{abstract\}.*?\\end\{abstract\}", data, re.S).group()
    check("abstract_exact", abstract(before) == abstract(after))
    check("one_auxiliary_safe_set_definition", len(re.findall(r"\\Acal\s*(?::=|=)\s*\\\{x\\in\\Omega:P_0\(x\)\\le K\\\}", text)) == 1
          and r"\widehat{\Acal}" not in text
          and r"\mathcal A^0" not in text)
    check("Omega_defined_before_safe_set", text.index(r"\Omega=\{") < text.index(r"\label{eq:safe-set}"))
    check("stage_table_explicitly_restricted_to_D", "表中集合均与物理域 $\\Dcal$ 取交" in text)
    check("old_two_layer_and_restricted_symbols_removed", all(token not in text for token in
          ("两层", "第一层", "第二层", "可行包络", r"\mathcal V", r"h_{\bar q}", r"\mathcal I_{\bar q}", r"\mathcal C_{\bar q}")))
    # 从 label 向前取最近的 remark，避免把更早的注记一并包含。
    remark_end = text.index(r"\label{rem:unproved-extensions}")
    remark_start = text.rfind(r"\begin{remark}", 0, remark_end)
    remark_end = text.index(r"\end{remark}", remark_end) + len(r"\end{remark}")
    remark = text[remark_start:remark_end]
    outside_remark = text[:remark_start] + text[remark_end:]
    check("bar_q_occurs_only_in_unstudied_extension", r"\bar q" in remark and r"\bar q" not in outside_remark)
    check("extension_keeps_boundary_condition_and_non_substitution", r"\bar q\ge1-h/s" in remark
          and "不能只把" in remark and "未在本稿研究" in remark)
    limits = text[text.index(r"\label{sec:limitations}"):text.index(r"\label{rem:unproved-extensions}")]
    check("perfect_tracing_limitation_explicit", "完美" in limits and "$q=1$" in limits)

    # 总量耗散对所有控制成立，但完整 D 的不变性只能对可行轨道陈述。
    overview = text[text.index(r"\label{sec:main-results}"):text.index(r"\subsection{安全集与可行性}")]
    check("physical_domain_scope_separates_total_and_capacity", "任意" in overview and "可行" in overview
          and r"\eqref{eq:sum-decay}" in overview
          and "对任意控制正向不变" not in overview)
    safe_lemma = stm_after.get("lem:safe-invariant", {}).get("statement", b"").decode()
    check("safe_lemma_only_forward_invariance", r"\Acal" in safe_lemma and "任意" in safe_lemma
          and r"\mathcal A^0" not in safe_lemma)
    check("single_new_figure_reference", text.count(r"\label{fig:optimal-partition}") == 1
          and r"\includegraphics[width=\linewidth]{numerical_scenarios/FigN1_optimal_partition.pdf}" in text
          and "FigN1_two_layers" not in text and "fig:two-layer-regions" not in text)

    allowed_deleted = {PREFIX + "figures/numerical_scenarios/FigN1_two_layers" + ext for ext in (".pdf", ".png")}
    categories = {"saved_data": [], "historical_validation": [], "matlab_sources": [], "other_figures": []}
    mismatches = {key: [] for key in categories}
    for path, expected in capture["working_files"].items():
        if path in allowed_deleted:
            continue
        category = ("saved_data" if path.startswith(PREFIX + "data/") else
                    "historical_validation" if path.startswith(PREFIX + "validation/") else
                    "matlab_sources" if path.startswith(PREFIX + "matlab/") else "other_figures")
        categories[category].append(path)
        try:
            actual = sha(read(REPO / path))
        except OSError as error:
            actual = repr(error)
        if actual != expected:
            mismatches[category].append({"path": path, "before": expected, "after": actual})
    for category in categories:
        check(category + "_all_captured_SHA256_unchanged", not mismatches[category],
              checked_files=len(categories[category]), mismatches=mismatches[category])
    check("old_two_layer_outputs_deleted_as_authorized", all(not (REPO / path).exists() for path in allowed_deleted))
    check("new_single_figure_outputs_exist", all((PROJECT / "figures/numerical_scenarios" / ("FigN1_optimal_partition" + ext)).is_file()
          for ext in (".pdf", ".png")))
    check("bibliography_and_theory_wrapper_unchanged", all(lf(old(path)) == lf(current(path)) for path in
          ("latex/references.bib", "latex/theory_only.tex")))

    allowed_tracked = {PREFIX + path for path in ("latex/main.tex", "latex/main.pdf", "latex/theory_only.pdf",
        "ai/claude_revision_plan/REVISION_PLAN.md", "ai/claude_revision_plan/SYMBOL_TABLE.md")}
    allowed_tracked |= allowed_deleted
    allowed_tracked |= {PREFIX + "figures/numerical_scenarios/FigN1_optimal_partition" + ext for ext in (".pdf", ".png")}
    changed = git("diff", "--name-only", BASE, "--", PREFIX).decode().splitlines()
    outside = [path for path in changed if path not in allowed_tracked and not path.startswith(PREFIX + "validation/mainline_focus_20261021/")]
    check("tracked_changes_within_authorized_scope", not outside, changed=changed, outside=outside)

    report = {"base_commit": BASE, "status": "pass" if all(x["passed"] for x in checks) else "fail",
              "passed": sum(x["passed"] for x in checks), "total": len(checks), "checks": checks,
              "source_audit_sha256": sha(read(Path(__file__))),
              "main_tex_before_SHA256_git_LF": sha(before), "main_tex_after_SHA256_git_LF": sha(after),
              "scope": "independent source and saved data audit; no compilation, MATLAB, ODE or OCP execution",
              "text_comparison": "Git LF canonical bytes; CRLF-to-LF only; mathematical safe-set renaming explicitly recorded"}
    (HERE / "mainline_source_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "passed", "total")}, ensure_ascii=False))
    for item in checks:
        if not item["passed"]:
            print(json.dumps(item, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
