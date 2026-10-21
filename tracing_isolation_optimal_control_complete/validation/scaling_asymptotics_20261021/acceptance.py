"""汇总 D 最终交付的构建、解析、符号、来源与保护验收。"""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details})


build, delivery = read("attempt4/build_report.json"), read("delivery_report.json")
check("final_compilation_and_delivery", delivery["success"] and delivery["compilation_success"])
check("eight_final_build_commands_exit_zero", sum(len(d["commands"]) for d in build["documents"]) == 8 and
      all(c["exit_code"] == 0 for d in build["documents"] for c in d["commands"]))
check("final_logs_without_diagnostics", all(d["success"] and not d["final_log_issues"] for d in build["documents"]))
check("pages_main46_theory36", [d["pages"] for d in build["documents"]] == [46, 36])
check("built_sources_match_final_sources", all(sha(PROJECT / "latex" / name) == digest for name, digest in build["source_sha256"].items()))
check("delivered_pdf_hashes_match_build", all(sha(PROJECT / "latex" / (d["name"] + ".pdf")) == d["pdf_sha256"] for d in build["documents"]))
numeric, results = read("analytic_checks.json"), read("analytic_results.json")
check("high_precision_analytic_checks", numeric["status"] == "passed", numeric["high_precision_residual_maxima"])
check("scan_620_with_one_explicit_mask", numeric["scan_case_count"] == 620 and len(results["scan"]["masked_rows"]) == 1)
check("small_capacity_family_35", numeric["small_K_case_count"] == 35)
check("independent_integrals_two", len(numeric["independent_quadrature_checks"]) == 2)
symbolic = read("symbolic_checks.json")
check("new_symbolic_10_and_fragments_2", symbolic["all_passed"] and symbolic["algebra_checks_passed"] == 10 and symbolic["fragment_checks_passed"] == 2)
check("symbolic_source_hashes_current", all(sha(PROJECT / path) == digest for path, digest in symbolic["source_sha256"].items()))
notation = (HERE / "notation_checks.log").read_text(encoding="utf-8")
check("original_notation_28", "Original symbolic checks: 28/28" in notation and "ALL OK" in notation)
audit = read("audit_report.json")
check("source_and_preservation_audit", audit["success"] and audit["passed"] == audit["total"], audit["total"])
render = read("render_manifest.json")
check("rendered_24_final_pages", sum(len(d["pages"]) for d in render["documents"]) == 24 and
      all(sha(PROJECT / "latex" / (d["name"] + ".pdf")) == d["pdf_sha256"] for d in render["documents"]))
visual = read("visual_qa.json")
check("visual_review_passed", visual["status"] == "passed" and visual["reviewed_page_count"] == 24)
check("zero_optimizer_ocp_ode", all(results[k] == 0 for k in ("optimizer_calls", "new_ocp_solves", "ode_solves")))
check("parameter_provenance_present", all(x in (HERE / "parameter_sources.md").read_text(encoding="utf-8") for x in ("0.3004", "0.1281", "0.2544", "q0=0.4624")))
new_tex = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
check("table_followed_by_independent_paragraph", "\\end{table}\n\n两篇文献" in new_tex)
check("relative_saving_not_renamed_G", r"\frac{\Delta J}{J_{\rm fill}}" in new_tex and r"s_1^\circ" in new_tex)
out = {"batch": "D", "passed": sum(c["passed"] for c in checks), "total": len(checks),
       "checks": checks, "success": all(c["passed"] for c in checks),
       "optimizer_calls": 0, "ocp_solves": 0, "ode_integrations": 0, "pushes": 0}
(HERE / "acceptance_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"D acceptance: {out['passed']}/{out['total']}")
assert out["success"], [c for c in checks if not c["passed"]]
