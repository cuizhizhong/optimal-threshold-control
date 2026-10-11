"""实际编译两份校样并记录退出码、最终日志和修订文字所在页。"""
import hashlib
import argparse
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LATEX = ROOT / "latex"
BUILD = ROOT / "tmp/grid_explanation_20261009_build"
BUILD.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
ENV["BIBINPUTS"] = str(LATEX) + os.pathsep + ENV.get("BIBINPUTS", "")
ISSUES = re.compile(r"(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|Missing character|Undefined control sequence)", re.M)


def compile_one(name):
    commands = [[shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={BUILD}", f"{name}.tex"],
                [shutil.which("bibtex"), name]]
    commands += [commands[0], commands[0]]
    results = []
    for number, command in enumerate(commands, 1):
        assert command[0]
        done = subprocess.run(command, cwd=BUILD if number == 2 else LATEX, env=ENV,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = done.stdout.decode("utf-8", errors="replace")
        log = HERE / f"{name}_build_{number}.log"
        log.write_text(output, encoding="utf-8")
        results.append({"command": command, "exit_code": done.returncode, "log": log.name})
        print(f"{name} step={number} exit_code={done.returncode}", flush=True)
        if done.returncode:
            print(output[-5000:], flush=True)
            return {"success": False, "commands": results}
    final = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    problems = [line for line in final.splitlines() if ISSUES.search(line)]
    pdf = BUILD / f"{name}.pdf"
    pdf_bytes = pdf.read_bytes()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    result = {"success": not problems, "commands": results, "final_log_issues": problems,
              "pages": len(reader.pages), "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
    if name == "main":
        result["revised_text_pages"] = [n for n, page in enumerate(reader.pages, 1)
                                      if "成本与事件比较未执行" in (page.extract_text() or "")]
        assert result["revised_text_pages"], "Revised grid explanation is missing from the compiled PDF."
    assert not problems, problems
    os.replace(pdf, LATEX / f"{name}.pdf")
    assert (LATEX / f"{name}.pdf").read_bytes() == pdf_bytes
    print(json.dumps({"document": name, **{key: value for key, value in result.items() if key != "commands"}}, ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-only", action="store_true")
    args = parser.parse_args()
    report_path = HERE / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if args.main_only else {}
    for name in (["main"] if args.main_only else ["main", "theory_only"]):
        report[name] = compile_one(name)
    (HERE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert all(item["success"] for item in report.values()), "Compilation failed or final log issues remain."
