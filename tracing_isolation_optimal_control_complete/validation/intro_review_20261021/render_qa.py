"""渲染 B 的修改页、目录和参考文献；仅检查所列页面，不声称逐页检查全文。"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUT = PROJECT / "tmp/intro_review_20261021/qa"
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {"main": [1, 2, 3, 4, 5, 37, 38], "theory_only": [1, 2, 3, 4, 5, 28, 29]}
report = {"scope": "B 摘要、目录、引言、模型衔接和参考文献；仅渲染所列页", "documents": []}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, pages in PAGES.items():
    pdf = PROJECT / "latex" / f"{name}.pdf"
    reader = PdfReader(pdf)
    doc = {"name": name, "pdf_sha256": sha(pdf), "page_count": len(reader.pages), "pages": pages, "commands": []}
    report["documents"].append(doc)
    files = []
    for page in pages:
        prefix = OUT / f"{name}_{page}"
        cmd = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page), "-scale-to", "1600",
               "-png", "-singlefile", str(pdf), str(prefix)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        files.append(prefix.with_suffix(".png"))
        doc["commands"].append({"argv": cmd, "exit_code": 0, "png_sha256": sha(files[-1])})
        (OUT / f"{name}_{page}.txt").write_text(reader.pages[page - 1].extract_text(), encoding="utf-8")
    doc["contact_sheets"] = []
    for number, start in enumerate(range(0, len(files), 2), 1):
        images = [Image.open(path).convert("RGB") for path in files[start:start + 2]]
        sheet = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images)), "white")
        left = 0
        for im in images:
            sheet.paste(im, (left, 0))
            left += im.width
        output = OUT / f"{name}_sheet_{number}.png"
        sheet.save(output)
        doc["contact_sheets"].append(str(output))
(HERE / "render_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({name: pages for name, pages in PAGES.items()}))
