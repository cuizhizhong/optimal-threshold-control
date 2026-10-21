"""两幅相图返修双文档四阶段实际构建；不调用 MATLAB、优化器或科学求解器。"""

import argparse
from datetime import datetime, timezone
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


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def publish_outputs(report, build):
    report["copied_outputs"] = []
    for name in ("main.pdf", "theory_only.pdf", "main.bbl"):
        destination = LATEX / name
        temporary = LATEX / ("figure1_revision_replacement_" + name)
        shutil.copyfile(build / name, temporary)
        os.replace(temporary, destination)
        report["copied_outputs"].append({"path": str(destination), "sha256": sha256(destination)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--publish-existing", action="store_true", help="只恢复已成功双编译的原子同步，不重新编译")
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error("--attempt 必须为正整数")
    logs = HERE / f"attempt{args.attempt}"
    build = PROJECT / "tmp/figure1_revision_20261021" / f"attempt{args.attempt}"
    if args.publish_existing:
        report_path = logs / "build_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert len(report["documents"]) == 2 and all(d["success"] and not d["final_log_issues"] for d in report["documents"])
        assert all(c["exit_code"] == 0 for d in report["documents"] for c in d["commands"])
        assert all(sha256(LATEX / name) == value for name, value in report["source_sha256"].items())
        assert all(sha256(PROJECT / name) == value for name, value in report["figure_sha256"].items())
        assert all(sha256(build / (d["name"]+".pdf")) == d["pdf_sha256"] for d in report["documents"])
        snapshot = logs / "build_report_before_publication_recovery.json"
        if not snapshot.exists():
            shutil.copyfile(report_path, snapshot)
        report["publication_recovery"] = {"original_failure": report.pop("failure", None),
                                           "method": "atomic_replace", "additional_tex_processes": 0}
        publish_outputs(report, build)
        report["success"] = True
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(report_path, report)
        print("双编译原产物已原子同步；未重新运行 TeX/BibTeX。")
        return
    if logs.exists():
        raise SystemExit(f"保留已有构建记录；请递增 --attempt：{logs}")
    logs.mkdir(parents=True)
    build.mkdir(parents=True, exist_ok=True)
    source_paths = [LATEX / name for name in ("main.tex", "theory_only.tex", "references.bib")]
    sources = {path.name: sha256(path) for path in source_paths}
    figure_paths = sorted((PROJECT / "figures/numerical_scenarios").glob("FigN*.pdf"))
    figures = {str(path.relative_to(PROJECT)): sha256(path) for path in figure_paths}
    report = {"batch": "figure_revision", "attempt": args.attempt,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": sources, "figure_sha256": figures, "build_directory": str(build),
              "optimizer_calls": 0, "ocp_solves": 0,
              "documents": [], "success": False}
    report_path = logs / "build_report.json"
    write_json(report_path, report)
    env = dict(os.environ)
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    engines = {name: shutil.which(name) for name in ("xelatex", "bibtex")}
    if not all(engines.values()):
        report["failure"] = f"构建程序不可用：{engines}"
        write_json(report_path, report)
        raise SystemExit(report["failure"])
    try:
        for name in ("main", "theory_only"):
            latex = [engines["xelatex"], "-interaction=nonstopmode", "-halt-on-error",
                     f"-output-directory={build}", f"{name}.tex"]
            commands = [latex, [engines["bibtex"], name], latex, latex]
            doc = {"name": name, "commands": [], "success": False}
            report["documents"].append(doc)
            for number, command in enumerate(commands, 1):
                cwd = build if number == 2 else LATEX
                result = subprocess.run(command, cwd=cwd, env=env,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                logfile = logs / f"{name}_{number}.log"
                logfile.write_bytes(result.stdout)
                doc["commands"].append({"argv": command, "cwd": str(cwd),
                                        "exit_code": result.returncode, "log": logfile.name})
                write_json(report_path, report)
                print(f"figure_revision {name} pass={number} exit={result.returncode}", flush=True)
                if result.returncode:
                    print(result.stdout.decode("utf-8", errors="replace")[-5000:], flush=True)
                    raise RuntimeError(f"停止条件：{name} 第 {number} 阶段退出码 {result.returncode}")
            doc["final_log_issues"] = []
            for suffix in ("log", "blg"):
                source_log = build / f"{name}.{suffix}"
                saved_log = logs / f"{name}_final.{suffix}"
                shutil.copyfile(source_log, saved_log)
                text = source_log.read_text(encoding="utf-8", errors="replace")
                for line in text.splitlines():
                    # .log 有宏包说明中的 warning/error 字样；.blg 也会列出 warning$ 调用计数。
                    # 仅匹配实际诊断，避免将这些程序说明和零计数当成停止条件。
                    if suffix == "log":
                        pattern = (r"^!|(?:LaTeX(?: Font)?|Package \S+|Class \S+|XeTeX|pdfTeX) "
                                   r"(?:Warning|Error)\b|^(?:Warning|Error):|"
                                   r"Overfull \\[hv]box|Underfull \\[hv]box|Missing character:|Undefined control sequence")
                    else:
                        pattern = (r"^Warning--|^I couldn't open|^I found no|^I was expecting|"
                                   r"^Repeated entry|^Illegal|---line \d+|"
                                   r"^\(There (?:was|were) \d+ (?:error messages?|warnings?)\)")
                    if re.search(pattern, line, flags=re.I):
                        doc["final_log_issues"].append({"file": saved_log.name, "line": line})
            write_json(report_path, report)
            if doc["final_log_issues"]:
                raise RuntimeError("停止条件：最终日志有 warning/error/溢出：" + str(doc["final_log_issues"]))
            assert sources == {path.name: sha256(path) for path in source_paths}, "构建期间源文件发生变化"
            assert figures == {str(path.relative_to(PROJECT)): sha256(path) for path in figure_paths}, "构建期间图件发生变化"
            pdf = build / f"{name}.pdf"
            reader = PdfReader(pdf)
            doc.update(success=True, pages=len(reader.pages), pdf_sha256=sha256(pdf),
                       pdf_title=str(reader.metadata.title or ""))
            print(f"figure_revision {name} pages={doc['pages']} issues=0", flush=True)
            write_json(report_path, report)
        # 两份文档均通过最终日志检查后，才同步交付文件。
        publish_outputs(report, build)
        report["success"] = True
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(report_path, report)
    except Exception as exc:
        report["failure"] = str(exc)
        write_json(report_path, report)
        raise


if __name__ == "__main__":
    main()
