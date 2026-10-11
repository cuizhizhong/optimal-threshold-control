"""在独立输出目录实际编译校样，记录退出码并发布 PDF。"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
LATEX = PROJECT / "latex"
BUILD = PROJECT / "tmp/prose_compression_20261010_build"
ISSUES = re.compile(
    r"(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|"
    r"Missing character|Undefined control sequence)", re.M
)


def compile_document(name):
    BUILD.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    source_hash = hashlib.sha256((LATEX / "main.tex").read_bytes()).hexdigest()
    xelatex = [shutil.which("xelatex"), "-interaction=nonstopmode",
               "-halt-on-error", f"-output-directory={BUILD}", f"{name}.tex"]
    commands = [xelatex, [shutil.which("bibtex"), name], xelatex, xelatex]
    report = {"document": name, "source_sha256": source_hash, "commands": [],
              "success": False}
    report_path = HERE / f"build_{name}_report.json"
    for number, command in enumerate(commands, 1):
        assert command[0], "Missing TeX executable."
        done = subprocess.run(command, cwd=BUILD if number == 2 else LATEX,
                              env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        output = done.stdout.decode("utf-8", errors="replace")
        log = HERE / f"{name}_build_{number}.log"
        log.write_text(output, encoding="utf-8")
        report["commands"].append({"command": command,
                                   "exit_code": done.returncode,
                                   "log": log.name})
        print(f"{name} step={number} exit_code={done.returncode}", flush=True)
        if done.returncode:
            report_path.write_text(json.dumps(report, ensure_ascii=False,
                                             indent=2) + "\n", encoding="utf-8")
            print(output[-4000:], flush=True)
            raise SystemExit(done.returncode)
    final_log = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    report["final_log_issues"] = [line for line in final_log.splitlines()
                                 if ISSUES.search(line)]
    assert not report["final_log_issues"], report["final_log_issues"]
    assert source_hash == hashlib.sha256((LATEX / "main.tex").read_bytes()).hexdigest(), \
        "Source changed during compilation; retain output without publishing."
    pdf = BUILD / f"{name}.pdf"
    pdf_bytes = pdf.read_bytes()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    report.update(success=True, pages=len(reader.pages),
                  pdf_sha256=hashlib.sha256(pdf_bytes).hexdigest())
    if name == "main":
        report["numerical_and_appendix_pages"] = [
            n for n, page in enumerate(reader.pages, 1) if n > 20 and any(
                phrase in (page.extract_text() or "") for phrase in
                ["数值方法与实验设置", "实际控制输出", "容量退出的检测区间",
                 "从初始时刻进入完全跟踪", "默认协议已记录", "数值复现说明"])
        ]
    os.replace(pdf, LATEX / f"{name}.pdf")
    assert (LATEX / f"{name}.pdf").read_bytes() == pdf_bytes
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ["document", "success", "pages", "pdf_sha256"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True, choices=["main", "theory_only"])
    compile_document(parser.parse_args().document)
