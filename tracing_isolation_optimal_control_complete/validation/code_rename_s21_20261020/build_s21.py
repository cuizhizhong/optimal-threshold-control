"""S2.1 的实际编译核对；产物留在临时目录，不改写现有论文 PDF。"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
LATEX = PROJECT / "latex"
BUILD = PROJECT / "tmp/code_rename_s21_20261020/final"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    logs = HERE / "build_final"
    logs.mkdir(exist_ok=True)
    report_path = HERE / "build_report.json"
    assert not report_path.exists(), "已有编译记录，禁止覆盖。"
    env = dict(os.environ)
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    report = {
        "step": "S2.1", "optimizer_calls": 0, "scientific_solves": 0,
        "source_sha256": sha256(LATEX / "main.tex"),
        "published_pdfs_unchanged": True, "documents": [],
    }
    for name in ("main", "theory_only"):
        published_sha = sha256(LATEX / f"{name}.pdf")
        tex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={BUILD}", f"{name}.tex"]
        commands = [tex, [shutil.which("bibtex"), name], tex, tex]
        doc = {"name": name, "commands": [], "success": False}
        report["documents"].append(doc)
        for number, command in enumerate(commands, 1):
            cwd = BUILD if number == 2 else LATEX
            result = subprocess.run(command, cwd=cwd, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log_path = logs / f"{name}_{number}.log"
            log_path.write_bytes(result.stdout)
            doc["commands"].append({"argv": command, "cwd": str(cwd),
                                    "exit_code": result.returncode,
                                    "log": str(log_path.relative_to(HERE))})
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
            print(f"{name} pass={number} exit={result.returncode}", flush=True)
            if result.returncode:
                raise SystemExit(result.returncode)
        final_log = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="replace")
        doc["final_log_issues"] = re.findall(
            r"^.*(?:^! |LaTeX Warning|Package .* Warning|Overfull|Underfull|Missing character|Undefined control sequence).*$",
            final_log, re.M)
        pages = re.search(r"Output written on .*?\((\d+) pages?\)", final_log, re.S)
        doc["pages"] = int(pages.group(1)) if pages else None
        assert doc["pages"], "未从实际编译日志取得页数。"
        doc["pdf_sha256"] = sha256(BUILD / f"{name}.pdf")
        texts = []
        for kind, pdf in (("existing", LATEX / f"{name}.pdf"),
                          ("compiled", BUILD / f"{name}.pdf")):
            out = BUILD / f"{name}_{kind}.txt"
            command = [shutil.which("pdftotext"), "-layout", str(pdf), str(out)]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            doc.setdefault("text_commands", []).append({"argv": command, "exit_code": result.returncode})
            assert result.returncode == 0, result.stdout
            texts.append(out.read_bytes())
        doc["pdf_text_identical_to_existing"] = texts[0] == texts[1]
        doc["published_pdf_sha256_unchanged"] = sha256(LATEX / f"{name}.pdf") == published_sha
        doc["success"] = not doc["final_log_issues"] and doc["pdf_text_identical_to_existing"]
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert doc["success"] and doc["published_pdf_sha256_unchanged"], doc
        assert sha256(LATEX / "main.tex") == report["source_sha256"]
        print(f"{name} pages={doc['pages']} issues=0 text_identical=True", flush=True)
    report["success"] = True
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
