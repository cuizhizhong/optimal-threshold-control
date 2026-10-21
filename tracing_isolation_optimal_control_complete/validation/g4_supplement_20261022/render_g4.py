"""将已通过的最终 PDF 全页渲染，供人工检查。"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
from pypdf import PdfReader

here = Path(__file__).resolve().parent
report = json.loads((here / 'build_entry_report.json').read_text(encoding='utf-8'))
assert report['success']
work = Path(report['cwd']) / 'latex'
out = Path(r'C:\Users\cui\.codex\visualizations\2026\10\21\01a15f20-6595-7c43-b6ef-10a1c1081eca\tmp\pdfs\g4-final')
out.mkdir(parents=True, exist_ok=False)
poppler = r'C:\Users\cui\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
tasks = []
manifest = {'dpi': 100, 'documents': {}, 'pages': []}
for stem in ('main', 'supplementary'):
    pdf = work / f'{stem}.pdf'
    reader = PdfReader(pdf)
    manifest['documents'][stem] = {'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(), 'pages': len(reader.pages)}
    (here / f'{stem}_pdf_text.txt').write_text('\n\f\n'.join(p.extract_text() for p in reader.pages), encoding='utf-8')
    tasks += [(stem, page, pdf) for page in range(1, len(reader.pages) + 1)]

def render(task):
    stem, page, pdf = task
    prefix = out / f'{stem}-{page:02}'
    argv = [poppler, '-f', str(page), '-l', str(page), '-r', '100', '-singlefile', '-png', str(pdf), str(prefix)]
    result = subprocess.run(argv, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return {'document': stem, 'page': page, 'image': str(prefix) + '.png'}

with ThreadPoolExecutor(max_workers=4) as pool:
    manifest['pages'] = list(pool.map(render, tasks))
(here / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'rendered_pages': len(tasks), 'directory': str(out)}, ensure_ascii=False))
