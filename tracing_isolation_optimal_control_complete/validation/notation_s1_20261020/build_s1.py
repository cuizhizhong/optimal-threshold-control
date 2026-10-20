"""S1 每步的双文档实际构建；不调用 MATLAB 或优化器。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
LATEX = PROJECT / "latex"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, choices=["S1.1", "S1.2", "S1.3", "S1.4"])
    args = parser.parse_args()
    logs = HERE / args.step
    build = PROJECT / "tmp/notation_s1_20261020" / args.step
    logs.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(LATEX / "main.tex")
    env = dict(os.environ)
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    report = {"step": args.step, "source_sha256": source_hash,
              "optimizer_calls": 0, "scientific_solves": 0, "documents": []}
    for name in ["main", "theory_only"]:
        latex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error",
                 f"-output-directory={build}", f"{name}.tex"]
        commands = [latex, [shutil.which("bibtex"), name], latex, latex]
        doc = {"name": name, "commands": [], "success": False}
        report["documents"].append(doc)
        for number, command in enumerate(commands, 1):
            result = subprocess.run(command, cwd=build if number == 2 else LATEX,
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logfile = logs / f"{name}_{number}.log"
            logfile.write_bytes(result.stdout)
            doc["commands"].append({"argv": command, "cwd": str(build if number == 2 else LATEX),
                                    "exit_code": result.returncode, "log": logfile.name})
            (logs / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{args.step} {name} pass={number} exit={result.returncode}", flush=True)
            if result.returncode:
                print(result.stdout.decode("utf-8", errors="replace")[-5000:], flush=True)
                raise SystemExit(result.returncode)
        log = (build / f"{name}.log").read_text(encoding="utf-8", errors="replace")
        doc["final_log_issues"] = re.findall(
            r"^.*(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|Missing character|Undefined control sequence).*$",
            log, re.M)
        if doc["final_log_issues"]:
            (logs / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise SystemExit("停止条件：最终编译日志有问题：" + str(doc["final_log_issues"]))
        assert sha256(LATEX / "main.tex") == source_hash, "编译过程中主文源文件发生变化"
        pdf = build / f"{name}.pdf"
        doc.update(success=True, pages=len(PdfReader(pdf).pages), pdf_sha256=sha256(pdf))
        shutil.copyfile(pdf, LATEX / f"{name}.pdf")
        if name == "main":
            shutil.copyfile(build / "main.bbl", LATEX / "main.bbl")
        print(f"{args.step} {name} pages={doc['pages']} issues=0", flush=True)
    report["success"] = True
    (logs / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
