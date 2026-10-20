"""渲染本次改动及相邻页面，供人工检查；不会修改 PDF。"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUT = PROJECT / "tmp/model_no_return_revision_20261020/qa"
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {"main": [1, 3, 4, 5, 7, 33], "theory_only": [1, 4, 5, 7, 26]}
report = {"scope": "Selected changed and adjacent pages; visual inspection is recorded separately", "documents": []}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for name, pages in PAGES.items():
    pdf = PROJECT / "latex" / f"{name}.pdf"
    doc = {"name": name, "pdf_sha256": sha(pdf), "pages": pages, "commands": []}
    report["documents"].append(doc)
    files = []
    for page in pages:
        prefix = OUT / f"{name}_{page}"
        cmd = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page),
               "-scale-to", "1400", "-png", "-singlefile", str(pdf), str(prefix)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        files.append(prefix.with_suffix(".png"))
        doc["commands"].append({"argv": cmd, "exit_code": 0, "png_sha256": sha(files[-1])})
    for number, start in enumerate(range(0, len(files), 2), 1):
        images = [Image.open(p).convert("RGB") for p in files[start:start+2]]
        sheet = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images)), "white")
        left = 0
        for im in images:
            sheet.paste(im, (left, 0))
            left += im.width
        sheet.save(OUT / f"{name}_sheet_{number}.png")
(HERE / "render_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(PAGES))
