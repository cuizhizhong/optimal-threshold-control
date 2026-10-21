"""仅在全部验收证据通过后交付已检查的 PDF。"""
from pathlib import Path
import hashlib
import json
import shutil

here = Path(__file__).resolve().parent
project = here.parents[1]
read = lambda name: json.loads((here / name).read_text(encoding='utf-8'))
build = read('build_entry_report.json')
audit = read('audit_report.json')
matlab = read('matlab_report.json')
visual = read('visual_qa.json')
assert build['success'] and audit['passed'] and matlab['status'] == 'completed' and visual['passed']
source_build = read('attempt3/build_report.json')
work = Path(build['cwd'])
for rel, expected in source_build['input_sha256'].items():
    original = project / rel
    assert original.is_file(), rel
    assert hashlib.sha256(original.read_bytes()).hexdigest() == expected, rel

outputs = {}
for stem in ('main', 'supplementary'):
    source = work / 'latex' / f'{stem}.pdf'
    expected = build['documents'][stem]['sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    target = project / 'latex' / f'{stem}.pdf'
    shutil.copy2(source, target)
    outputs[stem] = {'path': str(target.relative_to(project)), 'sha256': expected,
                     'pages': build['documents'][stem]['pages']}
report = {'passed': True, 'baseline_head': read('baseline.json')['head'], 'outputs': outputs,
          'exporter_regressions': sum(matlab[key]['test_count'] for key in ('saved', 'revision', 'pending')),
          'symbolic_checks': 28, 'protected_checks': len(audit['checks']),
          'protected_sentence_unchanged': audit['checks']['protected_sentence_unchanged'],
          'visual_pages': 45, 'optimizer_calls': 0, 'new_ocp_solves': 0,
          'assessment_calls': 0, 'figure_exports': 0, 'pushed': False}
(here / 'acceptance_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
