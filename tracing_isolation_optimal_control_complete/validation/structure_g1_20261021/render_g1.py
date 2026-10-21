"""从最终工作区 PDF 以 150 dpi 渲染用户指定页面。"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
report = json.loads((HERE / 'workspace_attempt1/build_report.json').read_text(encoding='utf-8'))
assert report['success']
pdf = Path(report['pdf_path'])
out = HERE / 'rendered_150dpi'
out.mkdir(exist_ok=True)
reasons = {
    1: '目录起始页（与摘要同页）', 2: '目录续页', 3: '目录末页',
    8: '第4节开头', 13: '第5节开头', 20: '第6节开头',
    25: '第7节开头及唯一性证明末页', 35: '第9节开头',
    24: '唯一性定理与证明起页', 37: '新增附录C证明起页', 38: '新增附录C证明末页',
}
reader = PdfReader(pdf)
manifest = {'dpi': 150, 'pdf_path': str(pdf), 'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(), 'pages': []}
for page, reason in sorted(reasons.items()):
    prefix = out / f'page_{page:02}'
    command = [shutil.which('pdftoppm'), '-f', str(page), '-l', str(page), '-r', '150', '-png', '-singlefile', str(pdf), str(prefix)]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == 0, result.stdout.decode(errors='replace')
    image = prefix.with_suffix('.png')
    manifest['pages'].append({'page': page, 'reason': reason, 'image': str(image), 'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'argv': command, 'exit_code': result.returncode})
    print(f'page {page}: 150 dpi rendered', flush=True)
assert len(reader.pages) == report['pages']
(HERE / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
