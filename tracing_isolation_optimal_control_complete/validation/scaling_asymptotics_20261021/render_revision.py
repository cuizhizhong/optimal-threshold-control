"""实际渲染 D 新增正文、证明、摘要目录与参考文献页。"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUT = PROJECT / "tmp/scaling_asymptotics_20261021/qa"
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {"main": [1, 2, 3, 4, 28, 29, 30, 31, 39, 40, 45, 46],
         "theory_only": [1, 2, 3, 4, 27, 28, 29, 30, 31, 32, 35, 36]}
report = {"scope": "D 修改与相邻页、摘要目录和参考文献，仅检查所列页面", "documents": []}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, pages in PAGES.items():
    pdf = PROJECT / "latex" / f"{name}.pdf"
    reader = PdfReader(pdf)
    doc = {"name": name, "pdf_sha256": sha(pdf), "page_count": len(reader.pages),
           "pages": pages, "commands": [], "contact_sheets": []}
    report["documents"].append(doc)
    all_text = [p.extract_text() or "" for p in reader.pages]
    (OUT / f"{name}_all_pages.txt").write_text("\n\f\n".join(all_text), encoding="utf-8")
    files = []
    for page in pages:
        prefix = OUT / f"{name}_{page}"
        cmd = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page), "-r", "150",
               "-png", "-singlefile", str(pdf), str(prefix)]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        path = prefix.with_suffix(".png")
        files.append(path)
        (OUT / f"{name}_{page}.txt").write_text(all_text[page - 1], encoding="utf-8")
        doc["commands"].append({"argv": cmd, "exit_code": result.returncode, "png_sha256": sha(path)})
    for number, start in enumerate(range(0, len(files), 2), 1):
        ims = [Image.open(p).convert("RGB") for p in files[start:start + 2]]
        sheet = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)), "white")
        x = 0
        for im in ims:
            sheet.paste(im, (x, 0))
            x += im.width
        output = OUT / f"{name}_sheet_{number}.png"
        sheet.save(output)
        doc["contact_sheets"].append(str(output))
    print(f"D render {name}: {len(pages)} pages", flush=True)
(HERE / "render_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
