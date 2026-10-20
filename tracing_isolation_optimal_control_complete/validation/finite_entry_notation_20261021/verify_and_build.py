"""核对有限入集引理的局部改名，独立双编译；不覆盖工作区已有 PDF。"""

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
LATEX = PROJECT / "latex"
BUILD = PROJECT / "tmp/finite_entry_notation_20261021"
SOURCE_PATH = PROJECT.name + "/latex/main.tex"
OLD = (r"&=\beta c\int_0^t(s(\tau)-h)\dd\tau-\beta c\int_0^t s(\tau)q(\tau)\dd\tau\\" + "\n"
       + r"&\ge-\beta cs_0\int_0^\infty q(\tau)\dd\tau.")
NEW = (r"&=\beta c\int_0^t(s(v)-h)\dd v-\beta c\int_0^t s(v)q(v)\dd v\\" + "\n"
       + r"&\ge-\beta cs_0\int_0^\infty q(v)\dd v.")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(report):
    (HERE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assert not (HERE / "build_report.json").exists(), "已有构建记录，禁止覆盖。"
    BUILD.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    committed = subprocess.check_output(["git", "show", "HEAD:" + SOURCE_PATH], cwd=REPO).decode("utf-8")
    working = (LATEX / "main.tex").read_text(encoding="utf-8")
    assert committed.count(OLD) == working.count(NEW) == 1
    assert OLD not in working
    patched_head = committed.replace(OLD, NEW)
    patch = "".join(difflib.unified_diff(committed.splitlines(keepends=True), patched_head.splitlines(keepends=True),
                                      fromfile="a/" + SOURCE_PATH, tofile="b/" + SOURCE_PATH))
    (HERE / "finite_entry.patch").write_text(patch, encoding="utf-8", newline="\n")
    lemma = working.split(r"\label{lem:finite-entry}", 1)[1].split(r"\end{proof}", 1)[0]
    proof = lemma.split(r"\begin{proof}", 1)[1]
    assert r"\tau" not in proof and r"\tau_{\Acal}" in lemma
    source_sha = sha(LATEX / "main.tex")
    existing_pdfs = {name: sha(LATEX / f"{name}.pdf") for name in ("main", "theory_only")}
    unrelated = working.replace(NEW, OLD)
    diff = "".join(difflib.unified_diff(committed.splitlines(keepends=True), unrelated.splitlines(keepends=True)))
    report = {"baseline_commit": head, "source_sha256": source_sha,
              "optimizer_calls": 0, "scientific_solves": 0,
              "three_integrals_renamed": True, "arrival_time_retained": True,
              "unrelated_worktree_source_diff_preserved": diff,
              "published_pdfs_before": existing_pdfs, "documents": [], "success": False}
    save(report)
    source = BUILD / "source.tex"
    source.write_bytes((LATEX / "main.tex").read_bytes())
    wrapper = BUILD / "theory_source.tex"
    wrapper.write_text("\\def\\TheoryOnly{1}\n\\input{" + source.as_posix() + "}\n", encoding="utf-8")
    env = dict(os.environ)
    env["BIBINPUTS"] = str(LATEX) + os.pathsep + env.get("BIBINPUTS", "")
    for name, entry in (("main", source), ("theory_only", wrapper)):
        tex = [shutil.which("xelatex"), "-interaction=nonstopmode", "-halt-on-error",
               f"-jobname={name}", f"-output-directory={BUILD}", str(entry)]
        doc = {"name": name, "commands": []}
        report["documents"].append(doc)
        for number, command in enumerate((tex, [shutil.which("bibtex"), name], tex, tex), 1):
            cwd = BUILD if number == 2 else LATEX
            result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logfile = f"{name}_{number}.log"
            (HERE / logfile).write_bytes(result.stdout)
            doc["commands"].append({"argv": command, "cwd": str(cwd), "exit_code": result.returncode, "log": logfile})
            save(report)
            print(f"{name} phase={number} exit={result.returncode}", flush=True)
            assert result.returncode == 0, result.stdout.decode("utf-8", errors="replace")[-3000:]
        log = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="replace")
        doc["issues"] = re.findall(r"^.*(?:^!|LaTeX Warning|Package \S+ Warning|Overfull|Underfull|Missing character:|Undefined control sequence).*$", log, re.M)
        doc["pages"] = int(re.search(r"Output written on .*?\((\d+) pages?\)", log, re.S).group(1))
        assert not doc["issues"], doc["issues"]
        doc["pdf_sha256"] = sha(BUILD / f"{name}.pdf")
        text = BUILD / f"{name}.txt"
        subprocess.run([shutil.which("pdftotext"), "-layout", str(BUILD / f"{name}.pdf"), str(text)], check=True)
        page_texts = text.read_text(encoding="utf-8").split("\f")
        doc["lemma_page"] = next(index for index, page in enumerate(page_texts, 1) if "所有有限成本轨道均在有限时间进入安全集" in page)
        page = doc["lemma_page"]
        prefix = BUILD / f"{name}_lemma_page_{page}"
        subprocess.run([shutil.which("pdftoppm"), "-f", str(page), "-l", str(page), "-singlefile", "-scale-to", "1800", "-png", str(BUILD / f"{name}.pdf"), str(prefix)], check=True)
        doc["rendered_page"] = str(prefix) + ".png"
        print(f"{name} pages={doc['pages']} issues=0 lemma_page={page}", flush=True)
    assert source_sha == sha(LATEX / "main.tex"), "构建期间源文件发生变化。"
    report["published_pdfs_unchanged_by_this_build"] = all(sha(LATEX / f"{name}.pdf") == value for name, value in existing_pdfs.items())
    assert report["published_pdfs_unchanged_by_this_build"], "构建期间另一任务更新了正式PDF，请复核来源。"
    report["success"] = True
    save(report)


if __name__ == "__main__":
    main()
