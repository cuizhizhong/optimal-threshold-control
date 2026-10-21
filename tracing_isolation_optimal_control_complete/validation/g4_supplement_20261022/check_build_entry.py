"""在同一隔离副本验证 Windows 双文稿构建入口。"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from pypdf import PdfReader

here = Path(__file__).resolve().parent
project = here.parents[1]
build = json.loads((here / 'attempt3/build_report.json').read_text(encoding='utf-8'))
assert build['success']
work = Path(build['work_directory'])
shutil.copy2(project / 'build.bat', work / 'build.bat')
argv = ['cmd.exe', '/d', '/c', 'build.bat']
result = subprocess.run(argv, cwd=work, capture_output=True)
(here / 'build_entry.stdout.log').write_bytes(result.stdout + result.stderr)
report = {'argv': argv, 'cwd': str(work), 'exit_code': result.returncode, 'documents': {}}
for stem in ('main', 'supplementary'):
    log = (work / 'latex' / f'{stem}.log').read_text(encoding='utf-8', errors='replace')
    diagnostics = [line for line in log.splitlines()
                   if any(t in line for t in ('Warning', 'Overfull', 'Underfull', 'Missing character', 'Undefined', '! '))]
    pdf = work / 'latex' / f'{stem}.pdf'
    report['documents'][stem] = {'pages': len(PdfReader(pdf).pages),
                                'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                                'diagnostics': diagnostics}
    shutil.copy2(work / 'latex' / f'{stem}.log', here / f'{stem}_final.log')
    if (work / 'latex' / f'{stem}.blg').exists():
        shutil.copy2(work / 'latex' / f'{stem}.blg', here / f'{stem}_final.blg')
report['success'] = result.returncode == 0 and all(not x['diagnostics'] for x in report['documents'].values())
(here / 'build_entry_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report['success']:
    raise SystemExit(1)
