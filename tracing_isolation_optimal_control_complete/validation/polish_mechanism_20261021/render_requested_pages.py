"""按最终目录页码实际渲染本轮要求的章节和图页，不覆盖已有渲染记录。"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = HERE / "rendered_pages_150dpi"
    destination.mkdir(exist_ok=False)
    executable = shutil.which("pdftoppm")
    assert executable, "pdftoppm 不可用"
    tasks, coverage = [], {}
    for document in ("main", "theory_only"):
        build = PROJECT / "tmp/polish_mechanism_20261021/attempt1"
        contents = (build / f"{document}.toc").read_text(encoding="utf-8")
        pages = {}
        for line in contents.splitlines():
            if line.startswith(r"\contentsline {section}"):
                match = re.search(r"\{(\d+)\}\{section\.(\d+)\}", line)
                if match:
                    pages[int(match[2])] = int(match[1])
        sections = (3, 15, 20) if document == "main" else (3, 15)
        selected = set()
        coverage[document] = {}
        for section in sections:
            # 后一节起始页也渲染，以覆盖同页收尾的段落。
            span = list(range(pages[section], pages[section + 1] + 1))
            selected.update(span)
            coverage[document][str(section)] = span
        auxiliary = (build / f"{document}.aux").read_text(encoding="utf-8")
        figure = re.search(r"\\newlabel\{fig:optimal-partition\}\{\{[^}]*\}\{(\d+)\}", auxiliary)
        assert figure
        selected.add(int(figure[1]))
        coverage[document]["figure1"] = int(figure[1])
        for page in sorted(selected):
            pdf = PROJECT / "latex" / f"{document}.pdf"
            prefix = destination / f"{document}_page{page}"
            argv = [executable, "-f", str(page), "-l", str(page), "-r", "150",
                    "-singlefile", "-png", str(pdf), str(prefix)]
            tasks.append((document, page, pdf, prefix, argv))

    def render(task):
        document, page, pdf, prefix, argv = task
        result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        prefix.with_suffix(".log").write_bytes(result.stdout)
        assert result.returncode == 0, result.stdout
        png = prefix.with_suffix(".png")
        return {"document": document, "page": page, "dpi": 150, "argv": argv,
                "exit_code": result.returncode, "pdf_sha256": sha256(pdf),
                "png": str(png.relative_to(PROJECT)), "png_sha256": sha256(png)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(render, tasks))
    (HERE / "render_manifest.json").write_text(
        json.dumps({"coverage": coverage, "pages": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({"coverage": coverage, "rendered_count": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
