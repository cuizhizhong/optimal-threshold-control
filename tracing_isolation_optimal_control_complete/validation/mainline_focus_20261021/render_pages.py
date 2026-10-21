"""按最终辅助文件定位第3节、图1和删除C3后的衔接页，逐页150dpi渲染。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_of(aux,label):
    match=re.search(r"\\newlabel\{"+re.escape(label)+r"\}\{\{([^{}]+)\}\{([^{}]+)\}",aux)
    assert match,label
    return int(match.group(2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt",type=int,default=1)
    args=parser.parse_args()
    BUILD=PROJECT/f"tmp/mainline_focus_20261021/attempt{args.attempt}"
    OUT=HERE/("rendered_pages_150dpi" if args.attempt==1 else f"rendered_pages_150dpi_attempt{args.attempt}")
    OUT.mkdir(exist_ok=False)
    executable=shutil.which("pdftoppm")
    assert executable
    report={"dpi":150,"build_attempt":args.attempt,"documents":[],"pages":[]}
    for name in ("main","theory_only"):
        aux=(BUILD/(name+".aux")).read_text(encoding="utf-8")
        mapping={label:page_of(aux,label) for label in
                 ("sec:main-results","fig:optimal-partition","sec:wellposed","prop:safe-exact","sec:arcs","lem:safe-invariant")}
        section3=list(range(mapping["sec:main-results"],mapping["fig:optimal-partition"]+1))
        transition={mapping["prop:safe-exact"]-1,mapping["prop:safe-exact"],mapping["sec:arcs"],mapping["sec:arcs"]+1}
        pdf=PROJECT/"latex"/(name+".pdf")
        page_count=len(PdfReader(pdf).pages)
        pages=sorted(p for p in set(section3)|transition if 1<=p<=page_count)
        report["documents"].append({"name":name,"total_pages":page_count,"label_pages":mapping,
                                    "section3_pages":section3,"C3_deletion_transition_pages":sorted(transition),"rendered_pages":pages})
        for page in pages:
            prefix=OUT/f"{name}_page{page}"
            command=[executable,"-f",str(page),"-l",str(page),"-r","150","-singlefile","-png",str(pdf),str(prefix)]
            result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            prefix.with_suffix(".log").write_bytes(result.stdout)
            assert result.returncode==0,result.stdout
            png=prefix.with_suffix(".png")
            report["pages"].append({"document":name,"page":page,"argv":command,"exit_code":result.returncode,
                    "pdf_sha256":sha(pdf),"png":str(png.relative_to(PROJECT)),"png_sha256":sha(png)})
    manifest=HERE/"render_manifest.json"
    if manifest.exists():
        prior=json.loads(manifest.read_text(encoding="utf-8"))
        snapshot=HERE/f"render_manifest_attempt{prior['build_attempt']}.json"
        assert not snapshot.exists(),"不覆盖此前渲染记录"
        snapshot.write_bytes(manifest.read_bytes())
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"dpi":150,"rendered_pages":{d["name"]:d["rendered_pages"] for d in report["documents"]}},ensure_ascii=False))


if __name__=="__main__":
    main()
