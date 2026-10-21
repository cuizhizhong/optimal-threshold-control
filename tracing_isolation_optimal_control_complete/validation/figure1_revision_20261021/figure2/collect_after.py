"""核对本轮图2导出、既有数据和两幅未改内容的数值图。"""
from pathlib import Path
import hashlib
import json
import difflib
import shutil
import subprocess

import numpy as np
from PIL import Image
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compare_images(before, after):
    a = np.asarray(Image.open(before).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(after).convert("RGB"), dtype=np.int16)
    assert a.shape == b.shape, f"Image shape changed: {before}, {after}"
    difference = np.abs(a - b)
    return {"shape": list(a.shape), "changed_pixels": int(np.any(difference, axis=2).sum()),
            "max_channel_difference": int(difference.max()), "mean_channel_difference": float(difference.mean())}

def main():
    before = json.loads((HERE / "before_hashes.json").read_text(encoding="utf-8"))
    refresh = json.loads((HERE / "refresh_report.json").read_text(encoding="utf-8-sig"))
    regression = json.loads((HERE / "S2.7/regression_report.json").read_text(encoding="utf-8-sig"))
    assert refresh["verified"] and refresh["optimizer_executions"] == 0
    assert regression["status"] == "completed"
    assert [regression[key]["test_count"] for key in ("saved", "revision", "pending")] == [11, 3, 2]
    assert all(regression[key]["passed"] and regression[key]["actual_optimizer_calls"] == 0
               for key in ("saved", "revision", "pending"))
    assert regression["optimizer_calls"] == 0 and regression["scientific_solves"] == 0
    old_tex = HERE / "before/latex/main.tex"
    new_tex = HERE / "main_after_export.tex"
    assert old_tex.read_bytes() == new_tex.read_bytes(), "Formal main.tex bytes changed during re-export."
    file_hashes = []
    for row in before["files"]:
        if row["path"] == "latex/main.tex":
            file_hashes.append({"path": row["path"], "before": row["sha256"],
                                "after_export_snapshot": sha(new_tex)})
            continue
        file_hashes.append({"path": row["path"], "before": row["sha256"],
                            "after": sha(PROJECT / row["path"])})
    allowed = {"data/numerical_scenarios/figure_provenance.json", "data/numerical_scenarios/export_provenance.json",
               "data/numerical_scenarios/numerical_checks.json", "data/numerical_scenarios/scenario_summary.csv"}
    data_changes = []
    for row in before["data_files"]:
        current = sha(PROJECT / row["path"])
        if current != row["sha256"]:
            assert row["path"] in allowed, f"Protected saved data changed: {row['path']}"
            data_changes.append({"path": row["path"], "before": row["sha256"], "after": current})
    actual_data_paths = {path.relative_to(PROJECT).as_posix()
                         for path in (PROJECT / "data/numerical_scenarios").rglob("*") if path.is_file()}
    assert actual_data_paths == {row["path"] for row in before["data_files"]}, "Saved-data file set changed."
    provenance = json.loads((PROJECT / "data/numerical_scenarios/figure_provenance.json").read_text(encoding="utf-8-sig"))
    assert provenance["code_hash"] == refresh["figure_code_hash"]
    for figure in provenance["figures"]:
        for output in figure["outputs"]:
            assert sha(PROJECT / output["file"]) == output["sha256"]
    render_dir = HERE / "comparison_150dpi"
    render_dir.mkdir(exist_ok=True)
    comparisons = []
    commands = []
    for name in ("FigN2_waiting", "FigN3_boundary_tracking"):
        record = {"name": name}
        record["png"] = compare_images(HERE / f"before/figures/numerical_scenarios/{name}.png",
                                        PROJECT / f"figures/numerical_scenarios/{name}.png")
        renders = []
        for label, pdf in (("before", HERE / f"before/figures/numerical_scenarios/{name}.pdf"),
                           ("after", PROJECT / f"figures/numerical_scenarios/{name}.pdf")):
            prefix = render_dir / f"{name}_{label}"
            command = [shutil.which("pdftoppm"), "-r", "150", "-png", "-singlefile", str(pdf), str(prefix)]
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            commands.append({"argv": command, "exit_code": result.returncode})
            renders.append(prefix.with_suffix(".png"))
        record["pdf_render_150dpi"] = compare_images(*renders)
        readers = [PdfReader(HERE / f"before/figures/numerical_scenarios/{name}.pdf"),
                   PdfReader(PROJECT / f"figures/numerical_scenarios/{name}.pdf")]
        streams = [reader.pages[0].get_contents() for reader in readers]
        operations = [stream.operations for stream in streams]
        assert len(operations[0]) == len(operations[1])
        differences = [(index, old, new) for index, (old, new) in enumerate(zip(*operations)) if old != new]
        outside_text_displacements_identical = ([op for op in operations[0] if op[1] != b"Td"] ==
                                                [op for op in operations[1] if op[1] != b"Td"])
        assert outside_text_displacements_identical, "A PDF drawing operator changed beyond text displacement."
        max_shift = max((abs(float(old[0][0]) - float(new[0][0])) for _, old, new in differences), default=0)
        assert max_shift <= 1
        assert readers[0].pages[0].extract_text() == readers[1].pages[0].extract_text()
        diff_lines = difflib.unified_diff(streams[0].get_data().decode("latin1").splitlines(),
                                         streams[1].get_data().decode("latin1").splitlines(), n=1)
        (HERE / f"{name}_pdf_content_diff.txt").write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
        record["pdf_content_stream"] = {
            "operation_count": len(operations[0]), "changed_operations": len(differences),
            "changed_operator_names": sorted({old[1].decode() for _, old, _ in differences}),
            "max_text_horizontal_displacement_change_in_drawing_units": max_shift,
            "all_operations_except_text_displacements_identical": outside_text_displacements_identical,
            "extracted_text_identical": True,
        }
        images = [Image.open(path).convert("RGB") for path in renders]
        sheet = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images)), "white")
        offset = 0
        for im in images:
            sheet.paste(im, (offset, 0)); offset += im.width
        sheet_path = render_dir / f"{name}_before_after.png"
        sheet.save(sheet_path)
        record["contact_sheet"] = sheet_path.relative_to(HERE).as_posix()
        comparisons.append(record)
    report = {"status": "passed", "main_tex_byte_identical_to_preexport": True,
              "main_tex_check_scope": "刚完成实际导出、尚未修改图注时的完整字节快照",
              "main_after_export_snapshot_sha256": sha(new_tex),
              "regression_test_counts": [11, 3, 2], "optimizer_executions": 0, "scientific_solves": 0,
              "data_files_checked": len(before["data_files"]), "data_changes": data_changes,
              "protected_data_unchanged": True, "file_hashes": file_hashes,
              "figure_provenance_matches_actual_source_and_outputs": True,
              "comparison_commands": commands, "unchanged_content_figures": comparisons}
    (HERE / "after_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "regression": [11, 3, 2], "data_changes": data_changes,
                      "image_comparisons": comparisons}, ensure_ascii=False))

if __name__ == "__main__":
    main()
