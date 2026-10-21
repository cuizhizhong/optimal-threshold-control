"""150 dpi 渲染阶段 F 第17/18节、新误差表及补充材料S全部实际页面。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from pypdf import PdfReader

from build_f import section_spans

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT / "tmp/numerics_rewrite_20261021"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def label_page(aux, name, reader):
    match = re.search(r"\\newlabel\{" + re.escape(name) + r"\}\{\{[^{}]*\}\{([^{}]+)\}",
                      aux.read_text(encoding="utf-8"))
    assert match, "未在 AUX 中找到新表：" + name
    label = match.group(1)
    pages = [i + 1 for i, value in enumerate(reader.page_labels) if value == label]
    assert len(pages) == 1, "AUX 页码无法唯一映射到物理页：" + label
    return pages[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-report", type=Path, required=True, help="成功的 workspace build_report.json")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    build_report = json.loads(args.build_report.read_text(encoding="utf-8"))
    assert build_report["success"], "仅渲染已经严格通过的构建"
    assert shutil.which("pdftoppm"), "缺少 pdftoppm"
    out = WORK / f"render_attempt{args.attempt}"
    manifest = HERE / f"render_manifest_attempt{args.attempt}.json"
    assert not out.exists() and not manifest.exists(), "已有渲染记录不得覆盖，增加 attempt"
    out.mkdir(parents=True)
    report = {"dpi": 150, "started_utc": datetime.now(timezone.utc).isoformat(),
              "build_report": str(args.build_report.resolve()), "documents": [], "success": False,
              "scope": "主文第17/18节各实际页面、新表页面、补充材料S各页面；TheoryOnly确认上述部分被省略"}
    try:
        for document in build_report["documents"]:
            name = document["name"]
            pdf = Path(document["pdf_path"])
            assert sha(pdf) == document["pdf_sha256"], "构建 PDF 已改变，禁止渲染过时记录"
            reader = PdfReader(pdf)
            spans = section_spans(reader)
            doc = {"name": name, "source_pdf": str(pdf), "source_pdf_sha256": sha(pdf),
                   "pdf_page_count": len(reader.pages), "pages": [], "page_selection": spans}
            report["documents"].append(doc)
            if name == "theory_only":
                assert "section17" not in spans and "section18" not in spans and "supplement" not in spans
                doc["target_sections_omitted"] = True
                continue
            assert name == "main"
            assert all(key in spans for key in ("section17", "section18", "supplement"))
            aux = Path(build_report["build_directory"]) / f"{name}.aux"
            table_page = label_page(aux, "tab:numerical-errors", reader)
            selected = sorted(set(spans["section17"]["pages"] + spans["section18"]["pages"] +
                                  spans["supplement"]["pages"] + [table_page]))
            doc["error_table_page"] = table_page
            doc["selected_pages"] = selected
            all_text = [page.extract_text() or "" for page in reader.pages]
            text_path = out / f"{name}_all_pages.txt"
            text_path.write_text("\n\f\n".join(all_text), encoding="utf-8")
            doc["all_pages_text"] = str(text_path)
            for page in selected:
                prefix = out / f"{name}_p{page:03d}"
                argv = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page), "-r", "150", "-png",
                        "-singlefile", str(pdf), str(prefix)]
                result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                png = prefix.with_suffix(".png")
                text_path = prefix.with_suffix(".txt")
                text_path.write_text(all_text[page - 1], encoding="utf-8")
                reasons = [key for key in ("section17", "section18", "supplement") if page in spans[key]["pages"]]
                if page == table_page:
                    reasons.append("tab:numerical-errors")
                doc["pages"].append({"physical_page": page, "printed_page": reader.page_labels[page - 1],
                                     "reasons": reasons, "dpi": 150, "png_path": str(png), "png_sha256": sha(png),
                                     "text_path": str(text_path), "text_sha256": sha(text_path),
                                     "argv": argv, "exit_code": result.returncode,
                                     "stderr": result.stderr.decode("utf-8", errors="replace")})
                save(manifest, report)
                print(f"F render {name} page={page} dpi=150", flush=True)
        report["success"] = True
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(manifest, report)
    except Exception as exc:
        report["failure"] = str(exc)
        save(manifest, report)
        raise


if __name__ == "__main__":
    main()
