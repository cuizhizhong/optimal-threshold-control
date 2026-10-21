"""发布已核验 PDF、归档150dpi页面并汇总阶段F验收，不运行科学计算。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((HERE / path).read_text(encoding="utf-8"))


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def publish():
    build = read("workspace_attempt2/build_report.json")
    assert build["success"]
    delivered = []
    for doc in build["documents"]:
        source = Path(doc["pdf_path"])
        assert sha(source) == doc["pdf_sha256"]
        target = PROJECT / "latex" / (doc["name"] + ".pdf")
        shutil.copyfile(source, target)
        assert sha(target) == doc["pdf_sha256"]
        delivered.append({"name": doc["name"], "path": str(target), "sha256": sha(target), "pages": doc["pages"]})
    save("delivery_report.json", {"success": True, "documents": delivered})
    render = read("render_manifest_attempt1.json")
    assert render["success"] and render["dpi"] == 150
    archive = HERE / "rendered_150dpi"
    archive.mkdir(exist_ok=True)
    pages = []
    observations = {
        30: "第17节开头、参数及配点方程清楚；与原第16节末衔接正常。",
        31: "保留的图2浮动页，面板、图例和中文图注完整；该图文件未修改。",
        32: "终端逻辑、条件不等式及18.1清楚，代表初值表无裁切。",
        33: "新表六列和五行完整；正负号、百分数表头及放宽容量列可辨；下方数值相图完整。",
        34: "N2控制/状态面板及图注完整；等待观测与18.3衔接正常。",
        35: "N3三组面板及图注完整；18.4残差五句全部排入正文，后续节标题正常。",
        43: "补充材料S标题、拆分说明、原复现命令及前三宏完整，无重叠或裁切。",
        44: "判据修订与粗网格诊断完整，四条路径分行清楚，无溢出。",
    }
    for doc in render["documents"]:
        for page in doc["pages"]:
            source = Path(page["png_path"])
            assert sha(source) == page["png_sha256"]
            target = archive / source.name
            shutil.copyfile(source, target)
            text_source = Path(page["text_path"])
            shutil.copyfile(text_source, archive / text_source.name)
            pages.append({"page": page["physical_page"], "dpi": 150, "path": str(target), "sha256": sha(target),
                          "observations": observations[page["physical_page"]], "passed": True})
    save("visual_qa.json", {"status": "passed", "reviewed_page_count": len(pages), "reviewer": "Codex primary agent",
          "inspection": "逐张查看150dpi原始渲染页，不以文字提取代替目视", "pages": pages,
          "scope_limit": "仅核查第17--18节所触及全部页、新表及补充材料S，不声称目视全部46页。"})


def acceptance():
    checks = []
    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details})
    matlab = read("matlab_report.json")
    check("export_and_three_regressions", matlab["status"] == "completed" and matlab["export"]["verified"] and
          all(matlab[key]["passed"] and matlab[key]["test_count"] == n for key, n in (("saved", 11), ("revision", 3), ("pending", 2))))
    check("optimizer_ocp_assessment_and_figure_export_zero", all(matlab[key] == 0 for key in
          ("optimizer_calls", "new_ocp_solves", "assessment_calls", "figure_exports")))
    audit = read("audit_error_table.json")
    check("independent_table_and_residual_data", audit["passed"] and audit["status"] == "passed")
    check("independent_audit_current_tex", audit["generated_tex_sha256"] == sha(PROJECT / "latex/main.tex"))
    preservation = read("preservation_report.json")
    check("protected_bytes_old_macros_and_scope", preservation["success"] and preservation["passed"] == preservation["total"] == 12)
    check("preservation_current_tex", preservation["source_sha256"] == sha(PROJECT / "latex/main.tex"))
    comment_search = read("comment_dependency_search.json")
    check("no_script_dependency_on_removed_comments", comment_search["safe_to_remove"] and not comment_search["hits"])
    notation = (HERE / "notation_checks.log").read_text(encoding="utf-8")
    check("28_original_notation_checks", "ALL OK" in notation and "Original symbolic checks: 28/28" in notation)
    builds = [read("workspace_attempt2/build_report.json"), read("isolated_attempt2/build_report.json")]
    for report in builds:
        mode = report["mode"]
        check(mode + "_four_stage_pair", report["success"] and len(report["documents"]) == 2 and
              all(len(d["commands"]) == 4 and all(c["exit_code"] == 0 for c in d["commands"]) for d in report["documents"]))
        check(mode + "_final_logs_and_inputs", all(not d["final_diagnostics"] and not d["forbidden_project_inputs"] for d in report["documents"]))
        if mode == "workspace":
            check(mode + "_current_sources", all(sha(PROJECT / p) == digest for p, digest in report["source_sha256"].items()))
        else:
            source_identity = []
            for p, digest in report["source_sha256"].items():
                current = PROJECT / p
                exported = Path(report["project_directory"]) / p
                # Git 的 CRLF 检出策略允许文本行尾不同；原始数据及图仍逐字节检查。
                same_text = current.read_text(encoding="utf-8") == exported.read_text(encoding="utf-8")
                source_identity.append({"path": p, "raw_hash_equal": sha(current) == digest,
                                        "normalized_text_identical": same_text,
                                        "current_sha256": sha(current), "exported_sha256": sha(exported)})
            save("git_export_source_identity.json", {"files": source_identity, "method": "UTF-8 universal-newline equality plus index clean-filter blob checks"})
            check(mode + "_current_sources_text_identity", all(item["normalized_text_identical"] for item in source_identity), source_identity)
        check(mode + "_all_figures_current", all(sha(PROJECT / p) == digest for p, digest in report["figure_sha256"].items()))
    isolated = builds[1]
    check("git_export_only_latex_and_figures", isolated["initial_root_entries"] == ["figures", "latex"] and
          all(item["index_blob"] == item["clean_filter_blob"] for item in isolated["index_export"]["files"]))
    check("fresh_build_extra_xelatex_after_four_stages", all(len(d.get("post_commands", [])) == 1 and
          not d["precompile_commands"] and d["post_commands"][0]["exit_code"] == 0 for d in isolated["documents"]))
    texts = {}
    for name in ("main", "theory_only"):
        docs = [next(d for d in b["documents"] if d["name"] == name) for b in builds]
        texts[name] = [p.extract_text() for p in PdfReader(docs[0]["pdf_path"]).pages] == [p.extract_text() for p in PdfReader(docs[1]["pdf_path"]).pages]
    check("all_page_text_identical_between_builds", all(texts.values()), texts)
    theory = next(d for d in builds[0]["documents"] if d["name"] == "theory_only")
    old_theory = builds[0]["baseline"]["theory_only"]
    check("theoryonly_all_page_text_unchanged", [p.extract_text() for p in PdfReader(theory["pdf_path"]).pages] ==
          [p.extract_text() for p in PdfReader(old_theory["path"]).pages])
    delivery = read("delivery_report.json")
    check("published_pdfs_match_actual_build", delivery["success"] and all(sha(Path(d["path"])) == d["sha256"] for d in delivery["documents"]))
    visual = read("visual_qa.json")
    check("all_eight_target_pages_at150dpi_visually_checked", visual["status"] == "passed" and visual["reviewed_page_count"] == 8 and
          all(p["passed"] and p["dpi"] == 150 and sha(Path(p["path"])) == p["sha256"] for p in visual["pages"]))
    check("known_evidence_gaps_recorded_without_new_solves", len(read("evidence_gaps.json")["gaps"]) >= 7)
    result = {"checks": checks, "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "success": all(c["passed"] for c in checks), "optimizer_calls": 0, "new_ocp_solves": 0,
              "assessment_calls": 0, "ode_calls": 0, "figure_exports": 0, "pushes": 0,
              "author_review_required": True}
    save("acceptance_report.json", result)
    print(f"F acceptance: {result['passed']}/{result['total']}")
    assert result["success"], [c for c in checks if not c["passed"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    publish() if parser.parse_args().publish else acceptance()
