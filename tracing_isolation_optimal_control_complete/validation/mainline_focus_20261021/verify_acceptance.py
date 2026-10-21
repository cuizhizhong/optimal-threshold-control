"""汇总本轮已实际完成的解析、编译、保护文件及目视证据，不重新求解。"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
REPO=PROJECT.parent
BASE="84a89431349681b02a82224d86120e63c191f412"


def read(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def old_text(name):
    return subprocess.check_output(["git","show",BASE+":"+PROJECT.name+"/"+name],cwd=REPO).decode()


def main():
    checks=[]
    def check(name,passed,details=None):
        checks.append({"name":name,"passed":bool(passed),"details":details})
    source=read("mainline_source_audit.json")
    check("source_and_protected_files",source["status"]=="pass" and source["passed"]==source["total"]==35)
    notation=(HERE/"notation_checks.log").read_text(encoding="utf-8")
    check("actual_notation_checks_28",read("notation_command.json")["exit_code"]==0 and len(re.findall(r"^True\s",notation,re.M))==28 and "Original symbolic checks: 28/28" in notation)
    plan_old=old_text("ai/claude_revision_plan/REVISION_PLAN.md")
    plan_new=(PROJECT/"ai/claude_revision_plan/REVISION_PLAN.md").read_text(encoding="utf-8")
    decision="作者决定（2026-10-21）：受限能力 $q\\le\\bar q$ 移出本稿主线，C3 命题与图 1(a) 删除，图 1 改为单幅成本分区，#13 不再使用。"
    def mask_plan(t):
        t=re.sub(r"\*\*C1 .*?(?=\*\*C2 )","C1_AUTHORIZED\n\n",t,flags=re.S)
        t=re.sub(r"\*\*C3 .*?(?=\*\*C4 )","C3_AUTHORIZED\n\n",t,flags=re.S)
        t=re.sub(r"#13（[^）]+）","#13_AUTHORIZED",t)
        return t.replace(decision+"\n\n","")
    check("plan_only_C1_C3_and_13_changed",mask_plan(plan_old)==mask_plan(plan_new) and plan_new.count(decision)==3)
    symbol_old=old_text("ai/claude_revision_plan/SYMBOL_TABLE.md")
    symbol_new=(PROJECT/"ai/claude_revision_plan/SYMBOL_TABLE.md").read_text(encoding="utf-8")
    mask_symbol=lambda t:re.sub(r"^\| 13 \|.*$","SYMBOL_13_AUTHORIZED",t,flags=re.M)
    check("symbol_table_only_13_changed",mask_symbol(symbol_old)==mask_symbol(symbol_new) and "随 C3 移出不再使用" in symbol_new)
    a=read("analytic_checks.json")
    check("analytic_record_matches_current_outputs_and_sources",all(sha(PROJECT/p)==h for p,h in a["outputs_sha256"].items()) and all(sha(PROJECT/p)==h for p,h in a["sources_sha256"].items()))
    check("geometry_and_Theta",a["checkpoint_max_absolute_error"]<2e-11 and a["theta_max_absolute_residual"]<2e-10)
    check("E1_endpoints_and_rounded_macros",max(a["trajectories"]["E1"]["endpoint_residuals"].values())<2e-11 and max(a["trajectories"]["E1"]["main_tex_rounded_macro_errors"].values())<5e-9 and a["trajectories"]["E1"]["all_sampled_points_in_D"])
    check("E2_three_arc_endpoints",max(a["trajectories"]["E2"]["endpoint_residuals"].values())<2e-11 and a["trajectories"]["E2"]["all_sampled_points_in_D"])
    cost=a["E2_analytic_cost"]
    check("3_10_percent_same_denominator_as_text",cost["saving_percent_rounded"]=="3.10" and cost["checkpoint_optimal_cost_error"]<2e-12 and cost["main_tex_3_10_percent_present"],cost)
    m=a["measurement"]
    check("single_figure_print_dimensions",abs(m["width_cm"]-16.5)<1e-5 and abs(m["height_cm"]-8)<1e-8 and abs(m["insertion_scale"]-1)<1e-9 and m["tick_font_pt"]==8 and m["label_font_pt"]==9)
    collision=read("label_collision_checks.json")
    check("plot_labels_ticks_and_axes_do_not_overlap",not collision["label_curve_intersections"] and not collision["label_pair_intersections"],collision)
    check("Fig2_N2_N3_byte_identical",all(sha(PROJECT/p)==h for p,h in a["protected_outputs_unchanged"].items()))
    check("old_two_layer_products_deleted",all(not (PROJECT/f"figures/numerical_scenarios/FigN1_two_layers.{ext}").exists() for ext in ("pdf","png")))
    check("no_matlab_optimizer_OCP_or_ODE",a["optimizer_calls"]==a["ocp_solves"]==a["ode_integrations"]==a["matlab_calls"]==0)
    build=read("attempt2/build_report.json")
    check("final_actual_four_stage_double_build",build["success"] and [d["pages"] for d in build["documents"]]==[41,31] and all(d["success"] and len(d["commands"])==4 and not d["final_log_issues"] and all(c["exit_code"]==0 for c in d["commands"]) for d in build["documents"]))
    check("compiled_sources_figures_and_outputs_match",all(sha(PROJECT/"latex"/p)==h for p,h in build["source_sha256"].items()) and all(sha(PROJECT/p)==h for p,h in build["figure_sha256"].items()) and all(sha(Path(p["path"]))==p["sha256"] for p in build["copied_outputs"]))
    render=read("render_manifest.json")
    check("actual_final_150dpi_pages",render["dpi"]==150 and render["build_attempt"]==2 and len(render["pages"])==12 and all(p["exit_code"]==0 and sha(PROJECT/p["png"])==p["png_sha256"] and sha(PROJECT/"latex"/(p["document"]+".pdf"))==p["pdf_sha256"] for p in render["pages"]))
    qa=read("visual_qa.json")
    check("required_pages_visually_reviewed",qa["passed"] and qa["final_reviewed_pages"]==12)
    result={"base_commit":BASE,"passed":sum(c["passed"] for c in checks),"total":len(checks),"success":all(c["passed"] for c in checks),"checks":checks,
            "optimizer_calls":0,"new_ocp_solves":0,"matlab_calls":0,"ode_integrations":0,
            "final_pages":{"main":41,"theory_only":31},"retained_tex_builds":2,"actual_tex_bibtex_processes":16}
    (HERE/"acceptance_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Mainline focus acceptance: {result['passed']}/{result['total']}")
    assert result["success"],[c for c in checks if not c["passed"]]


if __name__=="__main__":
    main()
