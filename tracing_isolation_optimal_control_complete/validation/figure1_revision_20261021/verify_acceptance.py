"""只读取本轮实际证据作汇总验收；不重新运行图形、回归或编译。"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def read(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name, passed, details=None):
        checks.append({"name":name,"passed":bool(passed),"details":details})
    scope=read("scope_audit.json")
    check("source_and_data_scope",scope["passed"]==scope["total"]==18)
    analytic=read("analytic_checks.json")
    check("final_figure1_outputs_match_analytic_record",all(sha(PROJECT/p)==h for p,h in analytic["outputs_sha256"].items()))
    check("unchanged_original_script_and_geometry_inputs",all(sha(PROJECT/p)==h for p,h in analytic["sources_sha256"].items()))
    check("geometry_checkpoints",analytic["checkpoint_max_absolute_error"]<2e-11,analytic["checkpoint_max_absolute_error"])
    check("theta_matching",analytic["theta_max_absolute_residual"]<2e-10,analytic["theta_max_absolute_residual"])
    check("four_envelope_tangencies",len(analytic["envelopes"])==4 and all(abs(e["tangency_value_residual"])<1e-13 and abs(e["tangency_right_derivative"])<1e-13 for e in analytic["envelopes"]))
    check("example_three_arc_endpoints",max(analytic["trajectory"]["endpoint_residuals"].values())<2e-11 and analytic["trajectory"]["all_sampled_points_in_D"])
    measure=analytic["measurement"]
    check("final_print_dimensions_and_font_sizes",abs(measure["width_cm"]-16.5)<1e-5 and 6.5<=measure["height_cm"]<=7 and abs(measure["insertion_scale"]-1)<1e-9 and measure["tick_font_pt"]==8 and measure["axis_label_font_pt"]==9)
    check("inset_exterior_and_at_least_2cm",measure["inset_Gamma_horizontal_span_cm"]>=2 and measure["inset_does_not_overlap_main_axes"])
    regression=read("figure2/S2.7/regression_report.json")
    counts=[regression[k]["test_count"] for k in ("saved","revision","pending")]
    check("three_actual_S27_regressions",counts==[11,3,2] and all(regression[k]["passed"] for k in ("saved","revision","pending")),counts)
    refresh=read("figure2/refresh_report.json")
    after=read("figure2/after_report.json")
    check("actual_figure2_refresh_and_export",refresh["verified"] and after["status"]=="passed" and after["main_tex_byte_identical_to_preexport"])
    check("zero_optimizer_and_new_OCP",regression["optimizer_calls"]==regression["scientific_solves"]==after["optimizer_executions"]==after["scientific_solves"]==analytic["optimizer_calls"]==analytic["ocp_solves"]==0)
    check("N2_N3_content_unchanged",len(after["unchanged_content_figures"])==2 and all(f["png"]["changed_pixels"]==1 and f["pdf_content_stream"]["all_operations_except_text_displacements_identical"] and f["pdf_content_stream"]["extracted_text_identical"] for f in after["unchanged_content_figures"]))
    build=read("attempt2/build_report.json")
    check("final_actual_four_stage_double_build",build["success"] and [d["pages"] for d in build["documents"]]==[43,33] and all(d["success"] and len(d["commands"])==4 and not d["final_log_issues"] and all(c["exit_code"]==0 for c in d["commands"]) for d in build["documents"]))
    check("compiled_sources_figures_and_published_outputs_match",all(sha(PROJECT/"latex"/p)==h for p,h in build["source_sha256"].items()) and all(sha(PROJECT/p)==h for p,h in build["figure_sha256"].items()) and all(sha(Path(p["path"]))==p["sha256"] for p in build["copied_outputs"]))
    rendered=read("render_manifest.json")
    check("actual_150dpi_figure_pages",rendered["dpi"]==150 and len(rendered["pages"])==3 and all(p["exit_code"]==0 and sha(PROJECT/p["png"])==p["png_sha256"] and sha(PROJECT/"latex"/(p["document"]+".pdf"))==p["pdf_sha256"] for p in rendered["pages"]))
    qa=read("visual_qa.json")
    check("visual_review_of_final_pages_and_N2_N3",qa["passed"] and qa["final_page_count"]==3 and qa["N2_N3_individually_compared"])
    result={"base_commit":"54470c531e3214bdf379b073f69593ec47fecb6a","passed":sum(c["passed"] for c in checks),"total":len(checks),"success":all(c["passed"] for c in checks),"checks":checks,
            "optimizer_calls":0,"new_ocp_solves":0,"figure1_ode_integrations":0,
            "matlab_processes":2,"actual_export_regression_tests":counts,
            "final_pages":{"main":43,"theory_only":33},"matlab_ODE_note":"原有N2/N3图形流程含analytic_reference积分/ode45；没有另外启动ODE实验，不把全任务ODE次数写为0。"}
    (HERE/"acceptance_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Figure revision acceptance: {result['passed']}/{result['total']}")
    assert result["success"],[c for c in checks if not c["passed"]]


if __name__=="__main__":
    main()
