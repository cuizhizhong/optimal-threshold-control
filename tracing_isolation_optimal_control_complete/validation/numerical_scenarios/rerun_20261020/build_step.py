"""逐步实际编译主文；日志按步骤保存，最终需要时发布新 PDF。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
LATEX = PROJECT / "latex"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    logs = HERE / args.step
    logs.mkdir(exist_ok=True)
    build = PROJECT / "tmp/rerun_20261020" / args.step
    build.mkdir(parents=True, exist_ok=True)
    report_path = logs / "build_report.json"
    assert not report_path.exists(), "本步构建记录已存在，不覆盖。"
    source = hashlib.sha256((LATEX / "main.tex").read_bytes()).hexdigest()
    env = dict(os.environ)
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    tex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error",
           f"-output-directory={build}", "main.tex"]
    commands = [tex, [shutil.which("bibtex"), "main"], tex, tex]
    report = {"step": args.step, "source_sha256": source, "commands": [], "success": False}
    for number, command in enumerate(commands, 1):
        cwd = build if number == 2 else LATEX
        result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        filename = logs / f"main_{number}.log"
        filename.write_bytes(result.stdout)
        report["commands"].append({"argv": command, "cwd": str(cwd), "exit_code": result.returncode,
                                   "log": filename.name})
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{args.step} main pass={number} exit={result.returncode}", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    log = (build / "main.log").read_text(encoding="utf-8", errors="replace")
    report["final_log_issues"] = re.findall(
        r"^.*(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|Missing character|Undefined control sequence).*$",
        log, re.M)
    pages = re.search(r"Output written on .*?\((\d+) pages?\)", log, re.S)
    report["pages"] = int(pages.group(1)) if pages else None
    assert hashlib.sha256((LATEX / "main.tex").read_bytes()).hexdigest() == source
    report["success"] = bool(report["pages"]) and not report["final_log_issues"]
    if args.publish and report["success"]:
        shutil.copyfile(build / "main.pdf", LATEX / "main.pdf")
        shutil.copyfile(build / "main.bbl", LATEX / "main.bbl")
    report["published"] = args.publish and report["success"]
    report["pdf_sha256"] = hashlib.sha256((build / "main.pdf").read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert report["success"], "停止条件：编译日志或页数检查失败。"
    print(f"{args.step} BUILD_OK pages={report['pages']} issues=0", flush=True)


if __name__ == "__main__":
    main()
