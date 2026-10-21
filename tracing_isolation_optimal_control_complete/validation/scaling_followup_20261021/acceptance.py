"""D后续最终数值、保护、图形及两种实际构建的汇总验收。"""
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details})


numbers, figure, scope, audit = [read(n) for n in ("duration_checks.json", "figure_checks.json", "scope_review.json", "audit_report.json")]
check("80_decimal_digit_duration_checks", numbers["status"] == "passed" and numbers["precision_decimal_digits"] == 80 and numbers["checks_passed"] == numbers["check_count"], numbers["check_count"])
check("figure_high_precision_checks", figure["status"] == "passed" and figure["precision_decimal_digits"] == 80)
check("620_scan_rows_one_mask", figure["scan_rows"] == 620 and len(figure["masks"]) == 1)
collision = read("label_collision_checks.json")
check("all_51_text_boxes_and_single_legend_clear", collision["visible_text_boxes_checked"] == 51 and
      all(not collision[k] for k in ("label_curve_intersections", "label_pair_intersections", "legend_box_curve_intersections")))
check("native_figure_size_and_fonts", figure["measurement"]["insertion_scale"] == 1 and
      figure["measurement"]["tick_font_pt"] == 8 and figure["measurement"]["label_font_pt"] == 9 and
      figure["measurement"]["math_font"] == "stix")
check("reference_line_and_no_english_footnote", figure["measurement"]["reference_line_y"] == 1 and not figure["measurement"]["english_footnote_present"])
check("independent_scope_review", scope["all_pass"] and scope["passed"] == scope["total"], scope["total"])
check("full_preservation_audit", audit["success"] and audit["passed"] == audit["total"], audit["total"])
notation = (HERE / "notation_checks.log").read_text(encoding="utf-8")
check("28_original_symbolic_checks", "ALL OK" in notation and "Original symbolic checks: 28/28" in notation)
builds = [read("workspace_attempt1/build_report.json"), read("isolated_attempt2/build_report.json")]
for report in builds:
    mode = report["mode"]
    check(mode + "_actual_four_stage_pair", report["success"] and sum(len(d["commands"]) for d in report["documents"]) == 8 and
          all(c["exit_code"] == 0 for d in report["documents"] for c in d["commands"]))
    check(mode + "_final_logs_and_pages", [d["pages"] for d in report["documents"]] == [46, 36] and
          all(not d["final_diagnostics"] and not d["forbidden_project_inputs"] for d in report["documents"]))
    check(mode + "_current_source_and_figure_hashes", all(sha(PROJECT / p) == digest for p, digest in report["source_sha256"].items()) and
          sha(PROJECT / "figures/scaling/FigD_magnitude.pdf") == report["figure_sha256"])
    check(mode + "_measured_linewidth_matches_figure", all(d["linewidth_tex_pt"] == figure["measurement"]["linewidth_tex_pt"] for d in report["documents"]))
isolated = builds[1]
check("isolated_initial_only_latex_and_figures_without_aux", isolated["initial_root_entries"] == ["figures", "latex"] and
      all(Path(p).suffix not in (".aux", ".bbl", ".blg", ".log", ".out", ".toc", ".fls") for p in isolated["copied_files"]))
check("isolated_reference_stabilization_explicit", len(isolated["initial_reference_stabilization"]) == 8 and
      all(c["exit_code"] == 0 for c in isolated["initial_reference_stabilization"]))
same_text = {}
for name in ("main", "theory_only"):
    original = PdfReader(Path(builds[0]["build_directory"]) / (name + ".pdf"))
    copied = PdfReader(Path(builds[1]["build_directory"]) / (name + ".pdf"))
    same_text[name] = [p.extract_text() for p in original.pages] == [p.extract_text() for p in copied.pages]
check("all_page_text_identical_between_actual_builds", all(same_text.values()), same_text)
delivery = read("delivery_report.json")
check("formal_pdf_delivery_matches_build", delivery["success"] and all(sha(PROJECT / "latex" / (d["name"] + ".pdf")) == d["pdf_sha256"] for d in builds[0]["documents"]))
visual = read("visual_qa.json")
render = read("render_manifest.json")
check("12_final_pages_rendered_at150dpi_and_visually_reviewed", visual["status"] == "passed" and visual["reviewed_page_count"] == 12 and
      sum(len(d["pages"]) for d in render["documents"]) == 12 and all(sha(PROJECT / "latex" / (d["name"] + ".pdf")) == d["pdf_sha256"] for d in render["documents"]))
check("matlab_optimizer_ocp_ode_all_zero", all(numbers[k] == 0 for k in ("matlab_calls", "optimizer_calls", "new_ocp_solves", "ode_solves")))
result = {"passed": sum(c["passed"] for c in checks), "total": len(checks), "checks": checks,
          "success": all(c["passed"] for c in checks), "matlab_calls": 0, "optimizer_calls": 0,
          "new_ocp_solves": 0, "ode_solves": 0, "author_review_required": True, "pushes": 0}
(HERE / "acceptance_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"D followup acceptance: {result['passed']}/{result['total']}")
assert result["success"], [c for c in checks if not c["passed"]]
