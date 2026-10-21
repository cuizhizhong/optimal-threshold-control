"""D后续实际双稿四阶段构建，含仅latex/figures的隔离复制验收。"""
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
WORK = PROJECT / "tmp/scaling_followup_20261021"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def diagnostics(path):
    issues = []
    if path.suffix == ".log":
        pattern = (r"^!|(?:LaTeX(?: Font)?|Package \S+|Class \S+|XeTeX|pdfTeX) "
                   r"(?:Warning|Error)\b|^(?:Warning|Error):|Overfull \\[hv]box|"
                   r"Underfull \\[hv]box|Missing character:|Undefined control sequence")
    else:
        pattern = (r"^Warning--|^I couldn't open|^I found no|^I was expecting|^Repeated entry|"
                   r"^Illegal|---line \d+|^\(There (?:was|were) \d+ (?:error messages?|warnings?)\)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.search(pattern, line, re.I):
            issues.append(line)
    return issues


def source_snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in (root / "latex").rglob("*")
            if p.is_file() and p.suffix in (".tex", ".bib", ".sty", ".cls", ".bst")}


def input_dependencies(fls, cwd, root, isolated):
    inputs = set()
    for line in fls.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("INPUT "):
            value = line[6:].strip().strip('"')
            path = Path(value)
            inputs.add(str((cwd / path).resolve() if not path.is_absolute() else path.resolve()))
    bad = []
    for value in inputs:
        p = Path(value)
        if isolated and p.is_relative_to(PROJECT) and not p.is_relative_to(root):
            bad.append(value)
        if "validation" in p.parts and p.is_relative_to(PROJECT):
            bad.append(value)
    return {"input_paths": sorted(inputs), "forbidden_project_inputs": sorted(set(bad))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("workspace", "isolated"), required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--stabilize-first", action="store_true", help="在全新隔离副本中先生成引用，再独立执行严格四阶段验收")
    args = parser.parse_args()
    name = f"{args.mode}_attempt{args.attempt}"
    logs = HERE / name
    assert not logs.exists(), "必须保留已有构建记录，增加attempt编号"
    logs.mkdir()
    root = PROJECT
    report = {"mode": args.mode, "attempt": args.attempt, "started_utc": datetime.now(timezone.utc).isoformat(),
              "documents": [], "success": False, "matlab_calls": 0, "optimizer_calls": 0, "ocp_solves": 0}
    report_path = logs / "build_report.json"
    try:
        if args.mode == "isolated":
            root = WORK / name
            assert not root.exists(), "隔离目录必须全新"
            root.mkdir(parents=True)
            def ignore(directory, names):
                return [n for n in names if n == "__pycache__" or Path(n).suffix in
                        (".aux", ".bbl", ".blg", ".log", ".out", ".toc", ".fls", ".fdb_latexmk") or
                        n in ("main.pdf", "theory_only.pdf") or n.endswith(".synctex.gz")]
            for folder in ("latex", "figures"):
                shutil.copytree(PROJECT / folder, root / folder, ignore=ignore)
            report["initial_root_entries"] = sorted(p.name for p in root.iterdir())
            report["copied_files"] = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}
            assert report["initial_root_entries"] == ["figures", "latex"]
            assert not any(p.suffix in (".aux", ".bbl", ".blg", ".log", ".fls") for p in root.rglob("*"))
        latex = root / "latex"
        build = (WORK / name) if args.mode == "workspace" else (latex / "build")
        build.mkdir(parents=True, exist_ok=True)
        report.update(project_directory=str(root), build_directory=str(build), source_sha256=source_snapshot(root))
        for relative, digest in report["source_sha256"].items():
            assert sha(PROJECT / relative) == digest, relative
        report["figure_sha256"] = sha(root / "figures/scaling/FigD_magnitude.pdf")
        env = dict(os.environ)
        # 隔离构建不继承任何指向原工作区的TeX/Bib搜索路径。
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        env["BIBINPUTS"] = str(latex) + os.pathsep
        report["search_environment"] = {key: env.get(key) for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT")}
        save(report_path, report)
        if args.stabilize_first:
            assert args.mode == "isolated", "引用稳定仅用于全新复制验收"
            report["initial_reference_stabilization"] = []
            for doc_name in ("main", "theory_only"):
                warm_latex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error", "-recorder",
                              f"-output-directory={build}", f"{doc_name}.tex"]
                warm_commands = [warm_latex, [shutil.which("bibtex"), doc_name], warm_latex, warm_latex]
                for stage, command in enumerate(warm_commands, 1):
                    cwd = build if stage == 2 else latex
                    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    (logs / f"stabilize_{doc_name}_{stage}.log").write_bytes(result.stdout)
                    report["initial_reference_stabilization"].append({"name": doc_name, "stage": stage, "argv": command,
                                                                    "cwd": str(cwd), "exit_code": result.returncode})
                    save(report_path, report)
                    print(f"{name} stabilize {doc_name} stage={stage} exit={result.returncode}", flush=True)
                    assert result.returncode == 0, "全新副本引用初始化命令失败"
            # 初始化日志不作为最终验收；下面两稿仍各自完整执行原定四阶段，并严格检查最终日志。
        for doc_name in ("main", "theory_only"):
            probe_input = r"\AtBeginDocument{\typeout{SCALING_LINEWIDTH_PT=\the\linewidth}}\input{" + doc_name + ".tex}"
            xelatex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error", "-recorder",
                       f"-output-directory={build}", f"-jobname={doc_name}", probe_input]
            commands = [xelatex, [shutil.which("bibtex"), doc_name], xelatex, xelatex]
            doc = {"name": doc_name, "commands": [], "success": False}
            report["documents"].append(doc)
            for stage, command in enumerate(commands, 1):
                cwd = build if stage == 2 else latex
                result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                (logs / f"{doc_name}_{stage}.log").write_bytes(result.stdout)
                doc["commands"].append({"argv": command, "cwd": str(cwd), "exit_code": result.returncode})
                save(report_path, report)
                print(f"{name} {doc_name} stage={stage} exit={result.returncode}", flush=True)
                if result.returncode:
                    raise RuntimeError(f"编译退出非零：{doc_name} stage={stage}")
            doc["final_diagnostics"] = []
            for ext in ("log", "blg", "fls"):
                path = build / f"{doc_name}.{ext}"
                shutil.copyfile(path, logs / f"{doc_name}_final.{ext}")
                if ext != "fls":
                    doc["final_diagnostics"].extend(diagnostics(path))
            if doc["final_diagnostics"]:
                save(report_path, report)
                raise RuntimeError("最终日志未通过验收：" + str(doc["final_diagnostics"]))
            deps = input_dependencies(build / f"{doc_name}.fls", latex, root, args.mode == "isolated")
            save(logs / f"{doc_name}_inputs.json", deps)
            assert not deps["forbidden_project_inputs"], deps["forbidden_project_inputs"]
            reader = PdfReader(build / f"{doc_name}.pdf")
            line_width = re.search(r"SCALING_LINEWIDTH_PT=([0-9.]+)pt", (build / f"{doc_name}.log").read_text(encoding="utf-8"))
            assert line_width, "未得到正文linewidth实测值"
            doc.update(success=True, pages=len(reader.pages), pdf_sha256=sha(build / f"{doc_name}.pdf"),
                       input_count=len(deps["input_paths"]), forbidden_project_inputs=[], linewidth_tex_pt=float(line_width.group(1)))
            assert report["source_sha256"] == source_snapshot(root), "构建过程中源文件变化"
            print(f"{name} {doc_name} pages={doc['pages']} diagnostics=0", flush=True)
            save(report_path, report)
        report["success"] = True
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(report_path, report)
    except Exception as exc:
        report["failure"] = str(exc)
        save(report_path, report)
        raise


if __name__ == "__main__":
    main()
