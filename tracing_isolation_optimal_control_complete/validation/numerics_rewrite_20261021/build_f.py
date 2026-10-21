"""阶段 F 双稿严格构建及仅从 git index 导出的自包含构建。

不发布 PDF、不调用 MATLAB。每稿完整四阶段独立记录，前后均可增加 XeLaTeX；
失败记录不覆盖。改变附加编译次数时必须使用新的 --attempt。
"""
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
REPO = PROJECT.parent
WORK = PROJECT / "tmp/numerics_rewrite_20261021"
BASELINE = "89d9cc3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def git(*args, data=None):
    return subprocess.run([shutil.which("git"), *args], cwd=REPO, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def diagnostics(path):
    if path.suffix == ".blg":
        pattern = (r"^Warning--|^I couldn't open|^I found no|^I was expecting|^Repeated entry|"
                   r"^Illegal|---line \d+|^\(There (?:was|were) \d+ (?:error messages?|warnings?)\)")
    else:
        pattern = (r"^!|(?:LaTeX(?: Font)?|Package \S+|Class \S+|XeTeX|pdfTeX) "
                   r"(?:Warning|Error)\b|^(?:Warning|Error):|Overfull \\[hv]box|"
                   r"Underfull \\[hv]box|Missing character:|Undefined control sequence|"
                   r"(?:xdvipdfmx|dvipdfmx):(?:warning|error):")
    return [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if re.search(pattern, line, re.I)]


def source_snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in (root / "latex").rglob("*")
            if p.is_file() and p.suffix in (".tex", ".bib", ".sty", ".cls", ".bst")}


def top_sections(reader):
    return [{"title": entry.title, "start_page": reader.get_destination_page_number(entry) + 1}
            for entry in reader.outline if not isinstance(entry, list)]


def page_body(text):
    # 这两稿第一页起连续使用阿拉伯页码；页眉含总页数，不属于正文。
    lines = text.splitlines()
    if lines and "感染阈值约束下跟踪隔离的全域最优控制" in lines[0]:
        lines = lines[1:]
    return "\n".join(lines).strip()


def content_before_heading(text, title):
    """判断同页下一节标题前是否仍有上一节正文，避免漏算共享页面。"""
    first = re.search(r"[\u4e00-\u9fff]+", title)
    assert first, title
    body = page_body(text)
    # 目录不用于此处，定位来自 PDF outline 的实际目标页。
    match = re.search(r"(?m)^\s*(?:\d+|[A-Z])\s*" + re.escape(first.group(0)), body)
    if match is None:
        compact = re.sub(r"\s+", "", body)
        pos = compact.find(first.group(0))
        assert pos >= 0, f"在目标页未找到节标题：{title}"
        prefix = re.sub(r"(?:\d+|[A-Z])$", "", compact[:pos]).strip()
    else:
        prefix = body[:match.start()].strip()
    return bool(prefix)


def section_spans(reader):
    entries = top_sections(reader)
    text = [p.extract_text() or "" for p in reader.pages]
    result = {"section_starts": entries}
    for key, exact_title in (("section17", "数值方法与实验设置"),
                             ("section18", "不同初值区域下的数值验证")):
        positions = [i for i, entry in enumerate(entries) if entry["title"] == exact_title]
        if not positions:
            continue
        assert len(positions) == 1
        index = positions[0]
        start = entries[index]["start_page"]
        next_entry = entries[index + 1]
        next_page = next_entry["start_page"]
        shared = content_before_heading(text[next_page - 1], next_entry["title"])
        end = next_page if shared else next_page - 1
        result[key] = {"title": exact_title, "start_page": start, "end_page": end,
                       "pages": list(range(start, end + 1)), "physical_page_count": end - start + 1,
                       "shares_last_page_with_next_section": shared}
    if "section17" in result and "section18" in result:
        pages = sorted(set(result["section17"]["pages"] + result["section18"]["pages"]))
        result["numerical_sections"] = {"pages": pages, "physical_page_count": len(pages)}
    supplement = [entry for entry in entries if "数值复现说明" == entry["title"] or
                  "补充材料S" in re.sub(r"\s+", "", entry["title"])]
    if supplement:
        assert len(supplement) == 1
        start = supplement[0]["start_page"]
        references = [i + 1 for i, value in enumerate(text) if i + 1 >= start and
                      re.search(r"(?m)^\s*(?:参考文献|References)\s*$", page_body(value))]
        end = min(references) - 1 if references else len(reader.pages)
        result["supplement"] = {"title": supplement[0]["title"], "start_page": start,
                                "end_page": end, "pages": list(range(start, end + 1))}
    return result


def input_dependencies(fls, cwd, root, isolated):
    inputs = set()
    for line in fls.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("INPUT "):
            path = Path(line[6:].strip().strip('"'))
            inputs.add(str((cwd / path).resolve() if not path.is_absolute() else path.resolve()))
    forbidden = []
    for value in inputs:
        path = Path(value)
        if isolated and path.is_relative_to(PROJECT) and not path.is_relative_to(root):
            forbidden.append(value)
        if path.is_relative_to(REPO) and "validation" in path.parts:
            forbidden.append(value)
    return {"input_paths": sorted(inputs), "forbidden_project_inputs": sorted(set(forbidden)),
            "source_root": str(root), "isolation_required": isolated}


def export_index(name, report):
    export_parent = WORK / name / "git_index_export"
    assert not export_parent.exists(), "隔离导出父目录必须全新"
    export_parent.mkdir(parents=True)
    prefix = PROJECT.relative_to(REPO).as_posix()
    names = git("ls-files", "--cached", "-z", "--", f"{prefix}/latex", f"{prefix}/figures").split(b"\0")
    names = [p for p in names if p]
    assert names
    # checkout-index 读取暂存区，不写 Git 对象、分支或索引。
    git("checkout-index", "--prefix=" + export_parent.as_posix() + "/", "--stdin", "-z",
        data=b"\0".join(names) + b"\0")
    root = export_parent / prefix
    report["index_export"] = {"method": "git checkout-index --stdin -z", "files": []}
    assert sorted(p.name for p in root.iterdir()) == ["figures", "latex"]
    report["initial_root_entries"] = sorted(p.name for p in root.iterdir())
    for raw in names:
        name_in_repo = raw.decode("utf-8")
        path = export_parent / name_in_repo
        blob = git("rev-parse", ":" + name_in_repo).decode().strip()
        filtered = git("hash-object", "--path=" + name_in_repo, "--", str(path)).decode().strip()
        assert filtered == blob, "隔离副本与 git index 不同：" + name_in_repo
        report["index_export"]["files"].append({"path": name_in_repo, "index_blob": blob,
                                                  "clean_filter_blob": filtered, "raw_sha256": sha(path)})
    # Git 跟踪了旧 main.bbl/PDF；从零构建仅在全新导出副本中移除编译产物。
    removed = []
    for path in (root / "latex").rglob("*"):
        if path.is_file() and (path.suffix in (".aux", ".bbl", ".blg", ".log", ".toc", ".out", ".fls", ".fdb_latexmk")
                               or path.name in ("main.pdf", "theory_only.pdf") or path.name.endswith(".synctex.gz")):
            removed.append({"path": path.relative_to(root).as_posix(), "sha256": sha(path)})
            path.unlink()
    report["removed_stale_build_artifacts_in_export_only"] = removed
    return root


def baseline_documents():
    folder = WORK / f"baseline_{BASELINE}"
    folder.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, expected in (("main", 46), ("theory_only", 36)):
        relative = (PROJECT.relative_to(REPO) / "latex" / f"{name}.pdf").as_posix()
        payload = git("show", f"{BASELINE}:{relative}")
        path = folder / f"{name}.pdf"
        if path.exists():
            assert path.read_bytes() == payload, "已有基准 PDF 与 git blob 不同"
        else:
            path.write_bytes(payload)
        reader = PdfReader(path)
        assert len(reader.pages) == expected, "基准页数与预期不符"
        result[name] = {"commit": BASELINE, "path": str(path), "pages": len(reader.pages),
                        "pdf_sha256": sha(path), **section_spans(reader)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("workspace", "isolated"), required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--pre-xelatex", type=int, default=1,
                        help="完整四阶段之前的 XeLaTeX 次数；失败后用新 attempt 增加，不放宽最终诊断")
    parser.add_argument("--post-xelatex", type=int, default=0,
                        help="完整四阶段之后的 XeLaTeX 次数；单列记录，最终日志仍须严格零诊断")
    args = parser.parse_args()
    assert args.pre_xelatex >= 0 and args.post_xelatex >= 0
    name = f"{args.mode}_attempt{args.attempt}"
    logs = HERE / name
    assert not logs.exists(), "保留已有记录，请增加 attempt 编号"
    logs.mkdir()
    report_path = logs / "build_report.json"
    report = {"mode": args.mode, "attempt": args.attempt, "started_utc": datetime.now(timezone.utc).isoformat(),
              "documents": [], "success": False, "matlab_calls": 0, "optimizer_calls": 0, "ocp_solves": 0,
              "pre_xelatex_count_per_document": args.pre_xelatex,
              "post_xelatex_count_per_document": args.post_xelatex, "strict_final_diagnostics_required": True}
    try:
        for tool in ("xelatex", "bibtex", "git"):
            assert shutil.which(tool), f"缺少命令：{tool}"
        report["baseline"] = baseline_documents()
        root = export_index(name, report) if args.mode == "isolated" else PROJECT
        latex = root / "latex"
        build = WORK / name / "build" if args.mode == "workspace" else root / "latex/build"
        assert not build.exists(), "构建输出目录必须全新"
        build.mkdir(parents=True)
        report.update(project_directory=str(root), build_directory=str(build), source_sha256=source_snapshot(root))
        report["figure_sha256"] = {p.relative_to(root).as_posix(): sha(p) for p in (root / "figures").rglob("*") if p.is_file()}
        env = dict(os.environ)
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        env["BIBINPUTS"] = str(latex) + os.pathsep
        report["search_environment"] = {key: env.get(key) for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT")}
        save(report_path, report)
        for doc_name in ("main", "theory_only"):
            xelatex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error", "-recorder",
                       f"-output-directory={build}", f"{doc_name}.tex"]
            doc = {"name": doc_name, "precompile_commands": [], "commands": [],
                   "post_commands": [], "success": False}
            report["documents"].append(doc)
            stages = [(f"pre_{i}", xelatex, latex, "precompile_commands") for i in range(1, args.pre_xelatex + 1)]
            stages += [(str(stage), command, build if stage == 2 else latex, "commands")
                       for stage, command in enumerate([xelatex, [shutil.which("bibtex"), doc_name], xelatex, xelatex], 1)]
            stages += [(f"post_{i}", xelatex, latex, "post_commands") for i in range(1, args.post_xelatex + 1)]
            for stage, command, cwd, list_key in stages:
                result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output_log = logs / f"{doc_name}_{stage}.stdout.log"
                output_log.write_bytes(result.stdout)
                doc[list_key].append({"stage": stage, "argv": command, "cwd": str(cwd),
                                      "exit_code": result.returncode, "stdout_log": str(output_log)})
                save(report_path, report)
                print(f"{name} {doc_name} stage={stage} exit={result.returncode}", flush=True)
                if result.returncode:
                    raise RuntimeError(f"编译退出非零：{doc_name} stage={stage}")
            doc["final_diagnostics"] = []
            for ext in ("log", "blg", "fls", "aux", "toc"):
                path = build / f"{doc_name}.{ext}"
                assert path.is_file(), "缺少最终编译记录：" + str(path)
                shutil.copyfile(path, logs / f"{doc_name}_final.{ext}")
                if ext in ("log", "blg"):
                    doc["final_diagnostics"].extend(diagnostics(path))
            final_stage = f"post_{args.post_xelatex}" if args.post_xelatex else "4"
            doc["final_stdout_log"] = str(logs / f"{doc_name}_{final_stage}.stdout.log")
            doc["final_diagnostics"].extend(diagnostics(Path(doc["final_stdout_log"])))
            doc["final_diagnostics"] = sorted(set(doc["final_diagnostics"]))
            dependencies = input_dependencies(build / f"{doc_name}.fls", latex, root, args.mode == "isolated")
            save(logs / f"{doc_name}_inputs.json", dependencies)
            doc.update(input_count=len(dependencies["input_paths"]),
                       forbidden_project_inputs=dependencies["forbidden_project_inputs"])
            if doc["final_diagnostics"]:
                save(report_path, report)
                raise RuntimeError("最终日志未通过严格验收：" + str(doc["final_diagnostics"]))
            assert not doc["forbidden_project_inputs"], doc["forbidden_project_inputs"]
            pdf = build / f"{doc_name}.pdf"
            reader = PdfReader(pdf)
            spans = section_spans(reader)
            before = report["baseline"][doc_name]
            doc.update(success=True, pdf_path=str(pdf), pdf_sha256=sha(pdf), pages=len(reader.pages),
                       baseline_pages=before["pages"], page_delta=len(reader.pages) - before["pages"], **spans)
            if "numerical_sections" in spans:
                doc["numerical_page_delta"] = spans["numerical_sections"]["physical_page_count"] - before["numerical_sections"]["physical_page_count"]
            assert report["source_sha256"] == source_snapshot(root), "构建过程中源文件变化"
            print(f"{name} {doc_name} pages={doc['pages']} diagnostics=0", flush=True)
            save(report_path, report)
        report["success"] = True
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(report_path, report)
    except Exception as exc:
        report["failure"] = str(exc)
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(report_path, report)
        raise


if __name__ == "__main__":
    main()
