"""两句措辞修正：独立编译、源文保护与逐页像素对比。"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
from PIL import Image, ImageChops
from pypdf import PdfReader

here = Path(__file__).resolve().parent
project = here.parents[1]
repo = project.parent
baseline = '1556a0cc6cc710053562aae9fca1022c48fad917'
work = repo / 'tmp/final_wording_20261117'
work.mkdir(parents=True, exist_ok=False)
old_dir = work / 'before'
old_dir.mkdir()
latex = work / 'latex'
latex.mkdir()
old = subprocess.check_output(['git', 'show', baseline + ':tracing_isolation_optimal_control_complete/latex/main.tex'], cwd=repo).decode('utf-8')
replacements = [('时间单位与速率参数的单位一致。', '时长单位为速率参数单位的倒数。'),
                ('完全跟踪在阻止新感染的同时', '完全跟踪在阻止新的非隔离感染者生成的同时')]
expected = old
for before, after in replacements:
    assert expected.count(before) == 1
    expected = expected.replace(before, after, 1)
assert (project / 'latex/main.tex').read_text(encoding='utf-8') == expected
for source in (project / 'latex').iterdir():
    if source.is_file() and source.suffix in {'.tex', '.bib'}:
        shutil.copy2(source, latex / source.name)
shutil.copytree(project / 'latex/generated', latex / 'generated')
shutil.copytree(project / 'figures', work / 'figures')
for stem in ('main', 'supplementary'):
    shutil.copy2(project / 'latex' / f'{stem}.pdf', old_dir / f'{stem}.pdf')
source_hashes = {p.relative_to(work).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in work.rglob('*') if p.is_file() and old_dir not in p.parents}
report = {'baseline_head': baseline, 'source_only_two_replacements': True,
          'work_directory': str(work), 'input_sha256': source_hashes, 'commands': [],
          'documents': {}, 'optimizer_calls': 0, 'new_ocp_solves': 0,
          'matlab_calls': 0, 'assessment_calls': 0, 'figure_exports': 0}

def save():
    (here / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

def run(argv):
    result = subprocess.run(argv, cwd=latex, capture_output=True)
    report['commands'].append({'argv': argv, 'cwd': str(latex), 'exit_code': result.returncode})
    with (here / 'build.stdout.log').open('ab') as stream:
        stream.write(('\nCOMMAND ' + json.dumps(argv) + '\n').encode())
        stream.write(result.stdout + result.stderr)
    save()
    if result.returncode:
        raise RuntimeError(f'{argv}: exit {result.returncode}')

for stem in ('main', 'supplementary'):
    argv = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', stem + '.tex']
    run(argv)
    if '\\bibdata' in (latex / f'{stem}.aux').read_text(encoding='utf-8'):
        run(['bibtex', stem])
    run(argv)
    run(argv)
    log = (latex / f'{stem}.log').read_text(encoding='utf-8', errors='replace')
    if 'Label(s) may have changed' in log or 'Rerun to get' in log:
        run(argv)
        log = (latex / f'{stem}.log').read_text(encoding='utf-8', errors='replace')
    diagnostics = [s for s in log.splitlines() if any(t in s for t in
                   ('Warning', 'Overfull', 'Underfull', 'Missing character', 'Undefined', '! '))]
    shutil.copy2(latex / f'{stem}.log', here / f'{stem}_final.log')
    if (latex / f'{stem}.blg').exists():
        shutil.copy2(latex / f'{stem}.blg', here / f'{stem}_final.blg')
    report['documents'][stem] = {'pages': len(PdfReader(latex / f'{stem}.pdf').pages),
                                'diagnostics': diagnostics,
                                'compiled_pdf_sha256': hashlib.sha256((latex / f'{stem}.pdf').read_bytes()).hexdigest()}
    save()
    assert not diagnostics, diagnostics

images = Path(r'C:\Users\cui\.codex\visualizations\2026\10\21\01a15f20-6595-7c43-b6ef-10a1c1081eca\tmp\pdfs\final_wording_20261117')
images.mkdir(parents=True, exist_ok=False)
tasks = []
for stem, doc in report['documents'].items():
    assert len(PdfReader(old_dir / f'{stem}.pdf').pages) == doc['pages']
    for page in range(1, doc['pages'] + 1):
        tasks += [(stem, page, side) for side in ('before', 'after')]

def render(task):
    stem, page, side = task
    pdf = (old_dir if side == 'before' else latex) / f'{stem}.pdf'
    prefix = images / f'{stem}-{page:02}-{side}'
    subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '100', '-singlefile', '-png', str(pdf), str(prefix)], capture_output=True, check=True)

with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(render, tasks))
for stem, doc in report['documents'].items():
    changed = []
    for page in range(1, doc['pages'] + 1):
        with Image.open(images / f'{stem}-{page:02}-before.png') as a, Image.open(images / f'{stem}-{page:02}-after.png') as b:
            box = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox()
        if box:
            changed.append({'page': page, 'difference_bbox': box})
    doc['visually_changed_pages'] = changed
report['render_directory'] = str(images)
report['render_dpi'] = 100
report['rendered_comparison_pairs'] = sum(d['pages'] for d in report['documents'].values())
assert not report['documents']['supplementary']['visually_changed_pages']
report['success'] = True
save()
print(json.dumps({k: v for k, v in report.items() if k not in ('input_sha256', 'commands')}, ensure_ascii=False, indent=2))
