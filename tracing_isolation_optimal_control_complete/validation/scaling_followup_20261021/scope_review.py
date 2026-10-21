"""独立核对 D 后续的受保护内容；不计算或调用任何优化问题。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
BASE = "9a67992248f41dada8c02b2e1851fc87ffa54f4f"
PREFIX = PROJECT.name + "/"
RECORDS: list[dict] = []


def baseline(relative: str) -> bytes:
    return subprocess.check_output(["git", "show", BASE + ":" + PREFIX + relative], cwd=REPO)


def decode(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(name: str, passed: bool, **details) -> None:
    RECORDS.append({"name": name, "passed": bool(passed), **details})


def section(text: str, label: str) -> str:
    start = text.rfind("\\section", 0, text.index("\\label{" + label + "}"))
    end = text.index("\\section", start + 1)
    return text[start:end]


def selfcontained_review() -> dict | None:
    """独立重读原始 recorder 与 BibTeX 日志，不信任驱动器的汇总判据。"""
    logs = HERE / "isolated_attempt2"
    if not (logs / "build_report.json").exists():
        return None
    report = json.loads((logs / "build_report.json").read_text(encoding="utf-8"))
    root = Path(report["project_directory"]).resolve()
    texlive = Path("E:/software/texlive/2026").resolve()
    windows_fonts = Path("C:/Windows/Fonts").resolve()
    copied = report["copied_files"]
    stale_suffixes = {".aux", ".bbl", ".blg", ".log", ".out", ".toc", ".fls", ".pdf"}
    # figures 内的 PDF 是输入资产；仅 latex 中的构建残留需要排除。
    copied_clean = all(Path(p).parts[0] in {"latex", "figures"} and
                       not (p.startswith("latex/") and Path(p).suffix in stale_suffixes) for p in copied)
    matches = all((root / p).is_file() and digest((root / p).read_bytes()) == value and
                  digest((PROJECT / p).read_bytes()) == value for p, value in copied.items())
    documents = []
    for doc in report["documents"]:
        name = doc["name"]
        raw = (logs / f"{name}_final.fls").read_text(encoding="utf-8", errors="replace").splitlines()
        cwd = Path(next(line[4:] for line in raw if line.startswith("PWD ")))
        paths = set()
        for line in raw:
            if line.startswith("INPUT "):
                path = Path(line[6:].strip().strip('"'))
                paths.add((path if path.is_absolute() else cwd / path).resolve())
        local = sorted(p.relative_to(root).as_posix() for p in paths if p.is_relative_to(root))
        forbidden = sorted(str(p) for p in paths if p.is_relative_to(PROJECT) and not p.is_relative_to(root))
        unexpected = sorted(str(p) for p in paths if not p.is_relative_to(root) and
                            not p.is_relative_to(texlive) and not p.is_relative_to(windows_fonts))
        recorded = json.loads((logs / f"{name}_inputs.json").read_text(encoding="utf-8"))
        recorded_matches = {str(p) for p in paths} == set(recorded["input_paths"])
        final_log = (logs / f"{name}_final.log").read_text(encoding="utf-8", errors="replace")
        log_issues = [line for line in final_log.splitlines() if re.search(
            r"^!|(?:LaTeX(?: Font)?|Package \S+|Class \S+|XeTeX|pdfTeX) (?:Warning|Error)\b|"
            r"Overfull \\[hv]box|Underfull \\[hv]box|Missing character:|Undefined control sequence", line)]
        blg = (logs / f"{name}_final.blg").read_text(encoding="utf-8", errors="replace")
        database = re.findall(r"^Database file #\d+: (.+)$", blg, re.M)
        final_commands = doc["commands"]
        command_order = [Path(item["argv"][0]).stem.lower() for item in final_commands]
        commands_pass = command_order == ["xelatex", "bibtex", "xelatex", "xelatex"] and all(
            item["exit_code"] == 0 and Path(item["cwd"]).resolve().is_relative_to(root) for item in final_commands)
        bib_pass = database == ["references.bib"] and report["search_environment"]["BIBINPUTS"] == str(root / "latex") + ";"
        documents.append({"name": name, "input_count": len(paths), "copied_tree_input_count": len(local),
                          "copied_tree_inputs": local, "system_input_count": len(paths) - len(local),
                          "forbidden_original_project_inputs": forbidden, "unexpected_external_inputs": unexpected,
                          "recorder_matches_saved_json": recorded_matches, "final_four_stage_commands_pass": commands_pass,
                          "final_log_issues": log_issues, "bibtex_databases": database, "bibtex_input_is_copied_database": bib_pass,
                          "pages": doc["pages"], "passed": not forbidden and not unexpected and not log_issues and
                          recorded_matches and commands_pass and bib_pass})
    stabilize = report.get("initial_reference_stabilization", [])
    result = {"attempt": "isolated_attempt2", "initial_root_entries": report["initial_root_entries"],
              "copied_input_file_count": len(copied), "copied_manifest_excludes_build_residue": copied_clean,
              "copied_manifest_matches_current_original_and_copy_sha256": matches,
              "initialization_commands": len(stabilize), "initialization_commands_all_exit_zero": len(stabilize) == 8 and all(
                  r["exit_code"] == 0 for r in stabilize), "final_acceptance_commands": sum(len(d["commands"]) for d in report["documents"]),
              "documents": documents, "limitation": "First clean four-stage attempt retained a label-rerun warning; attempt2 is a new clean copy with eight reference-initialization commands before the final eight acceptance commands. No pre-existing aux/bbl files were copied."}
    result["all_pass"] = (report["initial_root_entries"] == ["figures", "latex"] and copied_clean and matches and
                          result["initialization_commands_all_exit_zero"] and all(doc["passed"] for doc in documents))
    return result


def main() -> None:
    old = decode(baseline("latex/main.tex"))
    new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8-sig")
    check("model_section_word_for_word", section(old, "sec:model") == section(new, "sec:model"))
    environments = ["theorem", "proposition", "lemma", "corollary", "assumption", "definition", "proof"]
    counts = {}
    for env in environments:
        pattern = r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}"
        left, right = re.findall(pattern, old, re.S), re.findall(pattern, new, re.S)
        counts[env] = len(left)
        check(env + "_environments_word_for_word", left == right, baseline_count=len(left), current_count=len(right))
    # 所有旧陈列公式及编号也逐字保留，排除公式被散落正文改动的可能。
    for env in ["equation", "align", "gather", "multline"]:
        pattern = r"\\begin\{" + env + r"\*?\}.*?\\end\{" + env + r"\*?\}"
        left, right = re.findall(pattern, old, re.S), re.findall(pattern, new, re.S)
        check(env + "_display_environments_word_for_word", left == right, baseline_count=len(left), current_count=len(right))
    for marker in ["NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"]:
        pattern = r"% BEGIN AUTO-GENERATED " + marker + r".*?% END AUTO-GENERATED " + marker
        left, right = re.findall(pattern, old, re.S), re.findall(pattern, new, re.S)
        check("auto_generated_" + marker.lower().replace(" ", "_"), len(left) == len(right) == 1 and left == right,
              baseline_sha256=digest("\n".join(left).encode()), current_sha256=digest("\n".join(right).encode()))
    old_macro = decode(baseline("validation/scaling_asymptotics_20261021/computed_values.tex"))
    new_path = PROJECT / "latex/generated/scaling_values.tex"
    new_macro = new_path.read_text(encoding="utf-8-sig") if new_path.exists() else ""
    macro_pattern = r"\\newcommand\{(\\D[^}]+)\}\{([^}]+)\}"
    left, right = dict(re.findall(macro_pattern, old_macro)), dict(re.findall(macro_pattern, new_macro))
    differences = {name: {"baseline": value, "current": right.get(name)} for name, value in left.items() if right.get(name) != value}
    check("original_D_macros_unchanged", len(left) == 17 and not differences, baseline_count=len(left), current_count=len(right), differences=differences)
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "--", PREFIX + "figures/numerical_scenarios", PREFIX + "validation/scaling_asymptotics_20261021"], cwd=REPO).decode().splitlines()
    protected_figures = []
    old_evidence = []
    for repo_path in files:
        relative = repo_path[len(PREFIX):]
        protected = relative.startswith("validation/scaling_asymptotics_20261021/") or re.search(r"/FigN(?:1_regions|1_optimal_partition|2[^/]*|3[^/]*)\.(pdf|png)$", relative)
        if not protected:
            continue
        left_bytes = baseline(relative)
        path = PROJECT / relative
        right_bytes = path.read_bytes() if path.exists() else b""
        record = {"path": relative, "baseline_sha256": digest(left_bytes), "current_sha256": digest(right_bytes), "passed": left_bytes == right_bytes}
        (old_evidence if relative.startswith("validation/") else protected_figures).append(record)
    check("protected_numerical_figures_byte_identical", bool(protected_figures) and all(r["passed"] for r in protected_figures), files=protected_figures)
    check("historical_D_evidence_byte_identical", bool(old_evidence) and all(r["passed"] for r in old_evidence), file_count=len(old_evidence), files=old_evidence)
    for name in ["main.tex", "theory_only.tex"]:
        text = (PROJECT / "latex" / name).read_text(encoding="utf-8-sig")
        check(name + "_no_validation_relative_paths", "../validation" not in text)
    check("six_D_edit_markers_removed", not re.search(r"% (?:BEGIN|END) D (?:ABSTRACT|MAIN|APPENDIX)", new))
    preamble = new.split("\\begin{document}", 1)[0]
    check("generated_D_macros_loaded_in_preamble", bool(re.search(r"\\input\{generated/scaling_values(?:\.tex)?\}", preamble)))
    check("scaling_figure_uses_figures_path_without_scaling", bool(re.search(r"\\includegraphics\{scaling/FigD_magnitude(?:\.pdf)?\}", new)))
    check("duplicate_E2_mechanism_example_removed", "其分母为 $1.578386$" not in section(new, "sec:switching-mechanism"))
    check("main_conclusions_original_3_10_percent_retained", "$3.10\\%$" in section(new, "sec:conclusions"))
    check("positive_control_duration_not_claimed_as_objective", "正控制时长不是本文的优化目标" in new and "并不同时最小化正控制时长" in new)
    result = {"baseline": BASE, "comparison_mode": "Text comparisons normalize CRLF to LF only; protected binary and historical evidence comparisons use exact bytes.",
              "source_sha256": {"baseline_main_tex": digest(baseline("latex/main.tex")), "current_main_tex": digest((PROJECT / "latex/main.tex").read_bytes())},
              "environment_counts": counts, "checks": RECORDS, "passed": sum(r["passed"] for r in RECORDS), "total": len(RECORDS), "all_pass": all(r["passed"] for r in RECORDS),
              "matlab_calls": 0, "optimizer_calls": 0, "new_ocp_solves": 0}
    isolated = selfcontained_review()
    if isolated is not None:
        result["selfcontained_review"] = isolated
        result["all_pass"] = result["all_pass"] and isolated["all_pass"]
    (HERE / "scope_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["passed", "total", "all_pass", "environment_counts"]}, ensure_ascii=False))
    if not result["all_pass"]:
        print(json.dumps([r for r in RECORDS if not r["passed"]], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
