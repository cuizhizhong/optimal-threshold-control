"""隔离编译本轮校样；源码变化或修订文字缺失时拒绝替换交付文件。"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LATEX = ROOT / "latex"
BUILD = ROOT / "tmp/tolerance_revision_20261010_build"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
ENV["BIBINPUTS"] = str(LATEX) + os.pathsep + ENV.get("BIBINPUTS", "")
ISSUES = re.compile(r"(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|Missing character|Undefined control sequence)", re.M)
SOURCE_SUFFIXES = {".tex", ".bib", ".sty", ".cls", ".bst"}
AUX_SUFFIXES = (".aux", ".bbl", ".blg", ".log", ".out", ".toc")
TOLERANCE = re.compile(r"(?:1[eE]-0?5|10(?:\^|\*\*)?-0?5|0\.00001)")
FIVE_CASES = re.compile(r"(?:五例[^。；]{0,80}(?:通过|被接受)|五个(?:主结果|算例)[^。；]{0,80}通过|5/5)")
THIRTY = re.compile(r"(?:30/35|(?:数值接受|解析比较|解析一致性|同时通过|双通过|两者同时通过|agreement_pass)[^。；]{0,80}(?<!\d)30(?!\d)|(?<!\d)30(?:个|条|项|配置)[^。；]{0,40}(?:同时通过|双通过))")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_hashes():
    files = {path for path in LATEX.rglob("*") if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES}
    figures = ROOT / "figures/numerical_scenarios"
    if figures.is_dir():
        files.update(figures.glob("*.pdf"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(files)}


def changed_sources(before):
    after = source_hashes()
    return [{"path": path, "before_sha256": before.get(path), "after_sha256": after.get(path)}
            for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]


def compact(text):
    return re.sub(r"\s+", "", text).replace("−", "-").replace("⁻⁵", "-5")


def source_revision_locations():
    text = (LATEX / "main.tex").read_text(encoding="utf-8-sig")
    return [{"line": number, "text": line}
            for number, line in enumerate(text.splitlines(), 1)
            if "重新评估" in line or "接受容差" in line
            or "\\NumRobustnessStatement" in line or "\\NumReproducibilityDetails" in line]


def compile_one(name):
    command = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={BUILD}", f"{name}.tex"]
    commands = [command, [shutil.which("bibtex"), name], command, command]
    results = []
    for number, current in enumerate(commands, 1):
        if not current[0]:
            return {"success": False, "delivered": False, "commands": results,
                    "error": "XeLaTeX or BibTeX executable is unavailable"}
        done = subprocess.run(current, cwd=BUILD if number == 2 else LATEX, env=ENV,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = done.stdout.decode("utf-8", errors="replace")
        log = HERE / f"{name}_build_{number}.log"
        log.write_text(output, encoding="utf-8")
        results.append({"command": current, "exit_code": done.returncode, "log": log.name})
        print(f"{name} step={number} exit_code={done.returncode}", flush=True)
        if done.returncode:
            print(output[-5000:], flush=True)
            return {"success": False, "delivered": False, "commands": results}
    final = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    problems = [line for line in final.splitlines() if ISSUES.search(line)]
    pdf_bytes = (BUILD / f"{name}.pdf").read_bytes()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    result = {"success": not problems, "delivered": False, "commands": results,
              "final_log_issues": problems, "pages": len(reader.pages),
              "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest()}
    if name == "main":
        pages = [compact(page.extract_text() or "") for page in reader.pages]
        result["revised_text_pages"] = [number for number, text in enumerate(pages, 1)
                                        if "重新评估" in text or "接受容差" in text]
        result["tolerance_explanation_pages"] = [number for number, text in enumerate(pages, 1)
                                                 if "容差" in text and TOLERANCE.search(text)]
        result["five_case_or_30_statistic_pages"] = [number for number, text in enumerate(pages, 1)
                                                    if FIVE_CASES.search(text) or THIRTY.search(text)]
        result["tolerance_and_result_pages"] = sorted(set(result["tolerance_explanation_pages"])
                                                      & set(result["five_case_or_30_statistic_pages"]))
        if not result["revised_text_pages"] or not result["tolerance_and_result_pages"]:
            result["success"] = False
            result["error"] = "Compiled main PDF lacks a revision marker or a page containing the 1e-5 tolerance explanation and five-case/30-result statement"
    return result


def replace_auxiliary(source, destination):
    # 不以 wb 打开可能被 Windows 锁定的目标文件；先写同目录临时文件再替换。
    descriptor, temporary = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def deliver_one(name, result):
    pdf = BUILD / f"{name}.pdf"
    os.replace(pdf, LATEX / f"{name}.pdf")
    result["synced_auxiliary_files"] = []
    for suffix in AUX_SUFFIXES:
        source = BUILD / f"{name}{suffix}"
        if source.is_file():
            destination = LATEX / source.name
            replace_auxiliary(source, destination)
            result["synced_auxiliary_files"].append(source.name)
    actual_hash = hashlib.sha256((LATEX / f"{name}.pdf").read_bytes()).hexdigest()
    if actual_hash != result["pdf_sha256"]:
        raise RuntimeError(f"Delivered {name}.pdf hash differs from the compiled candidate")
    result["delivered"] = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-only", action="store_true")
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    names = ["main"] if args.main_only else ["main", "theory_only"]
    report_path = HERE / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if args.main_only and report_path.exists() else {}
    before = source_hashes()
    snapshot_path = HERE / "source_hashes_before.json"
    write_json(snapshot_path, {"captured_utc": datetime.now(timezone.utc).isoformat(), "sha256": before,
                               "main_revision_locations": source_revision_locations()})
    try:
        # 两份候选均编译并通过检查后才开始替换，避免主文提前交付。
        for name in names:
            report[name] = compile_one(name)
            report[name]["source_hashes_before"] = snapshot_path.name
        changes = changed_sources(before)
        if changes:
            for name in names:
                report[name].update(success=False, delivered=False, delivery_refused=True,
                                    error="Source files changed during compilation; delivery refused", changed_sources=changes)
        elif all(report[name]["success"] for name in names):
            for name in names:
                changes = changed_sources(before)
                if changes:
                    raise RuntimeError("Source files changed before delivery; replacement refused")
                deliver_one(name, report[name])
        else:
            for name in names:
                report[name]["delivery_refused"] = True
        # 替换阶段若出现并行修改，同样不能将本轮产物报告为可交付。
        changes = changed_sources(before)
        if changes:
            for name in names:
                report[name].update(success=False, delivery_refused=True,
                                    error="Source files changed during this build/delivery; result rejected", changed_sources=changes)
    except Exception as exception:
        for name in names:
            report.setdefault(name, {"commands": [], "delivered": False})
            report[name].update(success=False, delivery_refused=True, error=f"{type(exception).__name__}: {exception}")
    finally:
        write_json(report_path, report)
    for name in names:
        print(json.dumps({"document": name, **{key: value for key, value in report[name].items() if key != "commands"}}, ensure_ascii=False), flush=True)
    if not all(report[name]["success"] and report[name]["delivered"] for name in names):
        raise SystemExit("Compilation, PDF text verification, source stability, or delivery failed; inspect build_report.json")


if __name__ == "__main__":
    main()
