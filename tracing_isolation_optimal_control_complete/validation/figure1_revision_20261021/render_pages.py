"""将本轮最终图1、图2所在正文页按150 dpi实际渲染，并保存命令及哈希。"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
BUILD = PROJECT / "tmp/figure1_revision_20261021/attempt2"
OUT = HERE / "rendered_pages_150dpi"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    executable = shutil.which("pdftoppm")
    assert executable
    targets = [("main", "fig:two-layer-regions"), ("main", "fig:numerical-regions"),
               ("theory_only", "fig:two-layer-regions")]
    report = {"dpi":150,"build_attempt":2,"pages":[]}
    for name, label in targets:
        aux = (BUILD / (name+".aux")).read_text(encoding="utf-8")
        match = re.search(r"\\newlabel\{"+re.escape(label)+r"\}\{\{([^{}]+)\}\{([^{}]+)\}",aux)
        assert match, (name,label)
        figure, page = match.groups()
        pdf = PROJECT / "latex" / (name+".pdf")
        prefix = OUT / (name+"_figure"+figure+"_page"+page)
        command = [executable,"-f",page,"-l",page,"-r","150","-singlefile","-png",str(pdf),str(prefix)]
        result = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (prefix.with_suffix(".log")).write_bytes(result.stdout)
        assert result.returncode == 0, result.stdout
        png = prefix.with_suffix(".png")
        report["pages"].append({"document":name,"label":label,"figure":figure,"page":int(page),
            "argv":command,"exit_code":result.returncode,"pdf_sha256":sha(pdf),
            "png":str(png.relative_to(PROJECT)),"png_sha256":sha(png)})
    (HERE/"render_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"dpi":150,"pages":[(p["document"],p["page"]) for p in report["pages"]]}))


if __name__ == "__main__":
    main()
