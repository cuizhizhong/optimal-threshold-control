"""从新的隔离目录编译主文和补充材料，保存逐命令证据。"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

here = Path(__file__).resolve().parent
project = here.parents[1]
repo = project.parent
attempt = int(sys.argv[1]) if len(sys.argv) > 1 else 1
evidence = here / f'attempt{attempt}'
work = repo / 'tmp' / 'g4_20261022' / f'attempt{attempt}'
evidence.mkdir(exist_ok=False)
work.mkdir(parents=True, exist_ok=False)
latex = work / 'latex'
latex.mkdir()
for source in (project / 'latex').iterdir():
    if source.is_file() and source.suffix in {'.tex', '.bib'}:
        shutil.copy2(source, latex / source.name)
shutil.copytree(project / 'latex/generated', latex / 'generated')
shutil.copytree(project / 'figures', work / 'figures')
inputs = {str(p.relative_to(work)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in work.rglob('*') if p.is_file()}
report = {'attempt': attempt, 'work_directory': str(work), 'input_sha256': inputs,
          'commands': [], 'documents': {}, 'optimizer_calls': 0, 'new_ocp_solves': 0}

def run(argv, name):
    result = subprocess.run(argv, cwd=latex, capture_output=True)
    (evidence / f'{name}.stdout.log').write_bytes(result.stdout + result.stderr)
    report['commands'].append({'argv': argv, 'cwd': str(latex), 'exit_code': result.returncode,
                               'stdout': f'{name}.stdout.log'})
    (evidence / 'build_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name}: exit {result.returncode}')

for stem in ('main', 'supplementary'):
    run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', stem + '.tex'], stem + '_xelatex1')
    aux = (latex / (stem + '.aux')).read_text(encoding='utf-8')
    if '\\bibdata' in aux:
        run(['bibtex', stem], stem + '_bibtex')
    for n in (2, 3):
        run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', stem + '.tex'], stem + f'_xelatex{n}')
    log = (latex / (stem + '.log')).read_text(encoding='utf-8', errors='replace')
    if 'Label(s) may have changed' in log or 'Rerun to get' in log:
        run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', stem + '.tex'], stem + '_xelatex4')
        log = (latex / (stem + '.log')).read_text(encoding='utf-8', errors='replace')
    from pypdf import PdfReader
    diagnostics = [line for line in log.splitlines()
                   if any(token in line for token in ('Warning', 'Overfull', 'Underfull', 'Missing character', 'Undefined', '! '))]
    for suffix in ('log', 'blg', 'fls'):
        source = latex / f'{stem}.{suffix}'
        if source.exists():
            shutil.copy2(source, evidence / f'{stem}_final.{suffix}')
    report['documents'][stem] = {'pages': len(PdfReader(latex / f'{stem}.pdf').pages),
                                'pdf_sha256': hashlib.sha256((latex / f'{stem}.pdf').read_bytes()).hexdigest(),
                                'diagnostics': diagnostics}
    print(stem, report['documents'][stem], flush=True)
report['success'] = all(not d['diagnostics'] for d in report['documents'].values())
(evidence / 'build_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
if not report['success']:
    raise SystemExit('Final build diagnostics remain; inspect before acceptance.')
