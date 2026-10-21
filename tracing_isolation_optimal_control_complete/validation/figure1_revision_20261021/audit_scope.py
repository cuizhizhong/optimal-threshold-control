"""只读核对本轮图形修改范围；以 54470c5 和修改前逐文件 SHA256 为准。"""
from __future__ import annotations

import ast
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
BASE = "54470c531e3214bdf379b073f69593ec47fecb6a"


def read(path):
    absolute = str(Path(path).resolve())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = "\\\\?\\" + absolute
    with open(absolute, "rb") as handle:
        return handle.read()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def lf(data):
    # Git 的文本 blob 使用 LF；不删除空格，不调整正文或末尾换行。
    return data.replace(b"\r\n", b"\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def old(relative):
    return git("show", BASE + ":" + PREFIX + relative)


def current(relative):
    return read(PROJECT / relative)


def main():
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    capture = json.loads(read(HERE / "baseline_sha256.json"))
    check("baseline_capture_commit", capture["base_commit"] == BASE)
    before = lf(old("latex/main.tex"))
    after = lf(current("latex/main.tex"))
    caption_pattern = rb"\\caption\{.*?\}\s*\\label\{(fig:two-layer-regions|fig:numerical-regions)\}"
    matches_before = list(re.finditer(caption_pattern, before, re.S))
    matches_after = list(re.finditer(caption_pattern, after, re.S))
    # 从每一个目标 label 向前找最近的 caption，避免跨越早前图注。
    def captions(data):
        spans = []
        for label in (b"fig:two-layer-regions", b"fig:numerical-regions"):
            token = b"\\label{" + label + b"}"
            end = data.index(token)
            start = data.rfind(b"\\caption{", 0, end)
            assert start >= 0
            spans.append((start, end, label))
        result = data
        for start, end, label in sorted(spans, reverse=True):
            result = result[:start] + b"<CAPTION:" + label + b">\n" + result[end:]
        return result, spans
    stripped_before, spans_before = captions(before)
    stripped_after, spans_after = captions(after)
    check("main_tex_only_two_caption_changes", stripped_before == stripped_after,
          before_outside_captions_sha256=digest(stripped_before),
          after_outside_captions_sha256=digest(stripped_after),
          changed_labels=[label.decode() for _, _, label in spans_after])
    block_pattern = rb"% BEGIN AUTO-GENERATED ([^\r\n]+)\n.*?% END AUTO-GENERATED \1(?:\n|$)"
    blocks_before = list(re.finditer(block_pattern, before, re.S))
    blocks_after = list(re.finditer(block_pattern, after, re.S))
    check("two_auto_generated_blocks_unchanged",
          len(blocks_before) == len(blocks_after) == 2 and
          all(a.group() == b.group() for a, b in zip(blocks_before, blocks_after)),
          blocks=[{"name": m.group(1).decode(), "sha256": digest(m.group())} for m in blocks_after])
    check("figure1_linewidth_insertion_unchanged",
          b"\\includegraphics[width=\\linewidth]{numerical_scenarios/FigN1_two_layers.pdf}" in after)

    matlab_path = "matlab/numerical_scenarios/make_numerical_figures.m"
    matlab_before, matlab_after = lf(old(matlab_path)).decode(), lf(current(matlab_path)).decode()
    expected = matlab_before.replace("hH=xline(ax,g.h,'--'", "hH=xline(ax,g.h,'-.'", 1)
    expected = expected.replace("$ (theory)", "$")
    expected = expected.replace("'Interpreter','latex','Location','northeast','NumColumns',1,'Box','off','FontSize',9);",
                                "'Interpreter','latex','Location','northwest','NumColumns',1,'Box','off','FontSize',9);", 1)
    expected = expected.replace("lg.ItemTokenSize=[16 10];\n", "lg.ItemTokenSize=[16 10];\n"
                                "% 将图例移到 s=h 右侧、i=K 上方，避开两条辅助边界和全部轨道。\n"
                                "lg.Units='normalized'; lg.Position(1)=ax.Position(1)+ax.Position(3)*(.35-.15)/(1.01-.15);\n", 1)
    check("matlab_exactly_authorized_line_style_and_legend_edits", expected == matlab_after)
    tail = "function timepanels("
    check("N2_N3_time_series_functions_unchanged",
          matlab_before[matlab_before.index(tail):] == matlab_after[matlab_after.index(tail):])
    check("N2_N3_time_series_calls_unchanged",
          re.findall(r"^timepanels\(.*$", matlab_before, re.M) == re.findall(r"^timepanels\(.*$", matlab_after, re.M))
    check("OpenOCL_legend_retained_without_theory_suffix",
          "OpenOCL (E1--E5)" in matlab_after and "(theory)" not in matlab_after)

    allowed_capture_changes = {PREFIX + matlab_path,
        PREFIX + "data/numerical_scenarios/figure_provenance.json",
        PREFIX + "data/numerical_scenarios/export_provenance.json"}
    allowed_capture_changes.update(PREFIX + "figures/numerical_scenarios/" + stem + ext
        for stem in ("FigN1_regions", "FigN1_two_layers", "FigN2_waiting", "FigN3_boundary_tracking")
        for ext in (".pdf", ".png"))
    categories = {"data_except_two_provenance": [], "historical_validation": [], "other_protected": []}
    mismatches = {key: [] for key in categories}
    for path, saved in capture["working_files"].items():
        if path in allowed_capture_changes:
            continue
        category = ("data_except_two_provenance" if path.startswith(PREFIX + "data/")
                    else "historical_validation" if path.startswith(PREFIX + "validation/")
                    else "other_protected")
        categories[category].append(path)
        try:
            actual = digest(read(REPO / path))
        except OSError as error:
            actual = str(error)
        if actual != saved:
            mismatches[category].append({"path": path, "before_sha256": saved, "actual": actual})
    for category in categories:
        check(category + "_sha256_unchanged", not mismatches[category],
              checked_files=len(categories[category]), mismatches=mismatches[category])
    old_script = "validation/geometry_proofs_20261021/make_two_layer_phase.py"
    check("old_figure1_generator_unchanged_against_git", lf(old(old_script)) == lf(current(old_script)))

    figure_before = json.loads(old("data/numerical_scenarios/figure_provenance.json"))
    figure_after = json.loads(current("data/numerical_scenarios/figure_provenance.json"))
    export_before = json.loads(old("data/numerical_scenarios/export_provenance.json"))
    export_after = json.loads(current("data/numerical_scenarios/export_provenance.json"))
    check("selected_run_ids_and_selection_hash_unchanged",
          all(a[key] == b[key] for a, b in ((figure_before, figure_after), (export_before, export_after))
              for key in ("selected_run_ids", "selection_manifest_hash")),
          selected_run_ids=figure_after["selected_run_ids"],
          selection_manifest_hash=figure_after["selection_manifest_hash"])
    def without_export_time(obj):
        return {key: value for key, value in obj.items() if key != "exported_utc"}
    check("export_provenance_only_timestamp_updated", without_export_time(export_before) == without_export_time(export_after))
    def normalized_figure_provenance(obj):
        obj = json.loads(json.dumps(obj))
        for key in ("code_hash", "exported_utc"):
            obj.pop(key, None)
        for source in obj["source_files"]:
            if source["path"] == "make_numerical_figures.m":
                source["sha256"] = "<UPDATED_FIGURE_CODE>"
        for entry in obj["figures"]:
            for output in entry["outputs"]:
                output["sha256"] = "<REGENERATED_FIGURE>"
        return obj
    check("figure_provenance_only_derived_hashes_and_timestamp_updated",
          normalized_figure_provenance(figure_before) == normalized_figure_provenance(figure_after))
    output_hashes = [{"path": item["file"], "expected": item["sha256"],
                      "actual": digest(current(item["file"]))}
                     for entry in figure_after["figures"] for item in entry["outputs"]]
    check("figure_provenance_output_hashes_current", all(x["expected"] == x["actual"] for x in output_hashes),
          outputs=output_hashes)

    changed = git("diff", "--name-only", BASE, "--", PREFIX).decode().splitlines()
    allowed_tracked = allowed_capture_changes | {PREFIX + "latex/main.tex", PREFIX + "latex/main.pdf", PREFIX + "latex/theory_only.pdf"}
    # 未来重跑审计时，新记录目录已提交也仍在本轮授权范围。
    outside = [path for path in changed if path not in allowed_tracked and
               not path.startswith(PREFIX + "validation/figure1_revision_20261021/")]
    check("tracked_change_scope", not outside, changed=changed, outside_scope=outside)

    script = current("validation/figure1_revision_20261021/make_figure1.py").decode("utf-8")
    tree = ast.parse(script)
    scipy_imports = [(node.module, [alias.name for alias in node.names]) for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("scipy")]
    imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    forbidden_calls = [name for name in calls if any(token in name.lower() for token in
        ("solve_ivp", "odeint", "minimize", "linprog", "least_squares", "matlab", "subprocess", "system", "popen"))]
    check("new_figure1_source_only_scalar_root_and_quadrature",
          sorted(scipy_imports) == [("scipy.integrate", ["quad"]), ("scipy.optimize", ["brentq"])]
          and not forbidden_calls and not any(name in ("subprocess", "matlab") for name in imports),
          scipy_imports=scipy_imports, forbidden_calls=forbidden_calls,
          note="brentq 为解析标量方程求根；quad 为解析面积积分。此项是源代码审计，不冒充运行期调用统计。")
    report = {"base_commit": BASE, "status": "pass" if all(item["passed"] for item in checks) else "fail",
              "passed": sum(item["passed"] for item in checks), "total": len(checks), "checks": checks,
              "scope": "source_and_data_only", "build_and_regression_execution_assessed": False,
              "text_comparison": "Git LF canonical bytes; no whitespace or content normalization beyond CRLF to LF",
              "source_audit_sha256": digest(read(Path(__file__)))}
    (HERE / "scope_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "passed", "total")}, ensure_ascii=False))
    for item in checks:
        if not item["passed"]:
            print(json.dumps(item, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
