"""渲染符号密集的代表页面，供逐页目视核对。"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUT = PROJECT / "tmp/notation_s1_20261020/visual"
PAGES = [7, 10, 13, 18, 19, 20, 25, 28, 29, 31, 34, 35]


def render(page):
    prefix = OUT / f"page_{page:02d}"
    command = [shutil.which("pdftoppm"), "-f", str(page), "-l", str(page),
               "-scale-to", "1400", "-png", "-singlefile",
               str(PROJECT / "latex/main.pdf"), str(prefix)]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return str(prefix) + ".png"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(render, PAGES))
    sheets = []
    for first in range(0, len(paths), 4):
        sheet = Image.new("RGB", (1600, 2300), "#cccccc")
        draw = ImageDraw.Draw(sheet)
        for number, filename in enumerate(paths[first:first + 4]):
            page = Image.open(filename).convert("RGB")
            page.thumbnail((780, 1100))
            x, y = (number % 2) * 800 + 10, (number // 2) * 1150 + 35
            sheet.paste(page, (x, y))
            draw.text((x, y - 25), f"main.pdf page {PAGES[first + number]}", fill="black")
        path = OUT / f"sheet_{first // 4 + 1}.png"
        sheet.save(path)
        sheets.append(str(path))
    (HERE / "visual_pages.json").write_text(json.dumps({"pdf": "latex/main.pdf", "pages": PAGES,
        "images": paths, "contact_sheets": sheets, "status": "rendered_pending_visual_review"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rendered": len(PAGES), "sheets": sheets}, indent=2))


if __name__ == "__main__":
    main()
