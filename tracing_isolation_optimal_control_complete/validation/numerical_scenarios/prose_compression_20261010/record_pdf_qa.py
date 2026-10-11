"""记录已完成的目视检查，并关联并发构建后的正式 PDF。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageChops
from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OTHER = HERE.parent / "tolerance_revision_20261010"
BUILD = PROJECT / "tmp/prose_compression_20261010_build"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    source = digest(PROJECT / "latex/main.tex")
    other_build = read(OTHER / "build_report.json")
    other_source = read(OTHER / "source_hashes_before.json")["sha256"]
    assert source == other_source["latex/main.tex"]
    for relative, expected in other_source.items():
        assert digest(PROJECT / relative) == expected, relative
    scope = read(HERE / "scope_report.json")
    matlab = read(HERE / "matlab_report.json")
    assert scope["passed"] and matlab["passed"]
    outputs = {}
    starting_pdf_hashes = {name: digest(PROJECT / f"latex/{name}.pdf")
                           for name in ("main", "theory_only")}
    for name in ("main", "theory_only"):
        own = read(HERE / f"build_{name}_report.json")
        current = PROJECT / f"latex/{name}.pdf"
        assert own["success"] and own["source_sha256"] == source
        assert own["final_log_issues"] == []
        assert other_build[name]["success"] and other_build[name]["delivered"]
        current_reader = PdfReader(current)
        pages = len(current_reader.pages)
        assert pages == own["pages"] == other_build[name]["pages"]
        outputs[name] = {
            "path": str(current),
            "pages": pages,
            "current_pdf_sha256": digest(current),
            "this_task_build_report": f"build_{name}_report.json",
            "this_task_built_pdf_sha256": own["pdf_sha256"],
            "concurrent_build_report": "../tolerance_revision_20261010/build_report.json",
            "concurrent_recorded_pdf_sha256": other_build[name]["pdf_sha256"],
            "current_matches_concurrent_recorded_pdf_bytes": digest(current) == other_build[name]["pdf_sha256"],
            "current_source_matches_both_recorded_builds": True,
            "current_pdf_last_publisher": "unknown_concurrent_session",
        }
    images = [(27, "qa_p27.png"), (29, "qa_events-29.png"),
              (30, "qa_events-30.png"), (35, "qa_p35.png"),
              (36, "qa_p36.png")]
    for page, filename in images:
        prefix = BUILD / f"qa_final_p{page}"
        dimensions = ["-scale-to", "1700"] if page == 36 else ["-r", "110"]
        command = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page),
                   *dimensions, "-png", "-singlefile", str(PROJECT / "latex/main.pdf"), str(prefix)]
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        before = Image.open(BUILD / filename).convert("RGB")
        after = Image.open(prefix.with_suffix(".png")).convert("RGB")
        assert before.size == after.size and ImageChops.difference(before, after).getbbox() is None, page
    assert all(digest(PROJECT / f"latex/{name}.pdf") == value
               for name, value in starting_pdf_hashes.items()), "PDF changed during QA"
    assert digest(PROJECT / "latex/main.tex") == source, "Source changed during QA"
    report = {
        "passed": True,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "main_source_sha256": source,
        "outputs": outputs,
        "visual_inspection": {
            "document": "main",
            "actual_pages_inspected": [page for page, _ in images],
            "images": [{"page": page, "path": str(BUILD / filename),
                        "sha256": digest(BUILD / filename)}
                       for page, filename in images],
            "checks": ["正文摘要与附录指向", "关键事件及数学符号",
                       "图注与正文衔接", "附录路径换行与跨页",
                       "无裁切、重叠或缺字"],
            "issues": [],
            "final_current_pdf_inspected_page_pixels_identical": True,
            "final_render_prefix": str(BUILD / "qa_final_p"),
            "all_page_text_comparison_to_this_task_built_pdf": "not_performed_original_pdf_was_atomically_published",
            "theory_only_all_pages_visually_reinspected_this_task": False,
        },
        "export_regression_test_count": sum(matlab[key]["test_count"]
                                            for key in ("saved_exporter", "failure_exporter", "pending_exporter")),
        "optimizer_executions_this_task": matlab["optimizer_executions"],
        "assessment_executions_this_task": matlab["assessment_executions_this_task"],
        "raw_solver_and_figure_files_unchanged": len(scope["unchanged_raw_solver_and_figure_files"]),
        "main_prose_totals": scope["main_prose_totals"],
        "concurrent_changes_preserved": True,
    }
    (HERE / "pdf_qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PROSE_COMPRESSION_PDF_QA_OK pages=37/29 visually_inspected=27,29,30,35,36")


if __name__ == "__main__":
    main()
