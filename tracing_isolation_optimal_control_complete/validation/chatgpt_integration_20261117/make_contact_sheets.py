"""将 Poppler 已渲染的各页组成版面检查缩略图，不修改交付 PDF。"""

from pathlib import Path

from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[2]
PAGES = PROJECT.parent / "tmp/chatgpt_integration_20261117/pages"
CONTACTS = PAGES.parent / "contacts"
CONTACTS.mkdir(parents=True, exist_ok=True)

for name in ("main", "supplementary"):
    pages = sorted(PAGES.glob(f"{name}-*.png"))
    for start in range(0, len(pages), 4):
        canvas = Image.new("RGB", (1240, 1780), "#dddddd")
        drawing = ImageDraw.Draw(canvas)
        for offset, path in enumerate(pages[start:start + 4]):
            with Image.open(path) as source:
                thumbnail = source.convert("RGB")
                thumbnail.thumbnail((600, 850))
            left = 10 + (offset % 2) * 620
            top = 30 + (offset // 2) * 890
            canvas.paste(thumbnail, (left, top))
            drawing.text((left, top - 23), f"{name} page {start + offset + 1}", fill="black", font_size=18)
        canvas.save(CONTACTS / f"{name}_{start + 1:02d}_{min(start + 4, len(pages)):02d}.jpg", quality=92)
    print(f"{name}: {len(pages)} pages")
