"""G4 保护性核对：数学、数值、图形、旧数据与指定原句。"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import subprocess

here = Path(__file__).resolve().parent
project = here.parents[1]
repo = project.parent
baseline = json.loads((here / 'baseline.json').read_text(encoding='utf-8'))
old = subprocess.check_output(['git', 'show', baseline['head'] + ':tracing_isolation_optimal_control_complete/latex/main.tex'], cwd=repo).decode('utf-8')
main = (project / 'latex/main.tex').read_text(encoding='utf-8')
shared = (project / 'latex/generated/numerical_values.tex').read_text(encoding='utf-8')
si = (project / 'latex/supplementary.tex').read_text(encoding='utf-8')
norm = lambda s: re.sub(r'\s+', ' ', s).strip()

def environments(text, names):
    return Counter(norm(m.group(0)) for m in re.finditer(r'\\begin\{(' + names + r')\}(.*?)\\end\{\1\}', text, re.S))

def block(text, name):
    begin = '% BEGIN AUTO-GENERATED NUMERICAL ' + name
    end = '% END AUTO-GENERATED NUMERICAL ' + name
    return text.split(begin, 1)[1].split(end, 1)[0]

old_body = old.split('\\appendix', 1)[1].split('\\section{补充材料 S：', 1)[0]
new_body = main.split('\\appendix', 1)[1].split('\\bibliographystyle', 1)[0]
checks = {
    'protected_sentence_unchanged': baseline['protected_sentence'] in main,
    'statements_unchanged': environments(old, 'theorem|lemma|proposition|corollary|definition') == environments(main, 'theorem|lemma|proposition|corollary|definition'),
    'proofs_unchanged': environments(old, 'proof') == environments(main, 'proof'),
    'equation_environments_unchanged': environments(old, r'equation\*?|align\*?|gather\*?|multline\*?') == environments(main, r'equation\*?|align\*?|gather\*?|multline\*?'),
    'unlabelled_displays_unchanged': Counter(map(norm, re.findall(r'\\\[(.*?)\\\]', old, re.S))) == Counter(map(norm, re.findall(r'\\\[(.*?)\\\]', main, re.S))),
    'appendices_A_F_unchanged': old_body.strip() == new_body.strip(),
    'reference_macros_unchanged': norm(block(old, 'REFERENCE VALUES')) == norm(block(shared, 'REFERENCE VALUES')),
    'result_macros_only_planned_wording': norm(block(old, 'RESULTS').replace('条件开关由 main.tex 定义', '条件开关由本文件定义').replace('复现附录', '补充材料')) == norm(block(shared, 'RESULTS')),
    'supplement_exactly_three_sections': len(re.findall(r'^\\section\{', si, re.M)) == 3,
    'main_figures_unchanged': main.count('\\begin{figure}') == old.count('\\begin{figure}') == 5,
    'main_tables_unchanged': main.count('\\begin{table}') == old.count('\\begin{table}') == 4,
    'main_loads_shared_once': main.count('\\input{generated/numerical_values.tex}') == 1,
    'supplement_loads_shared_once': si.count('\\input{generated/numerical_values.tex}') == 1,
    'old_supplement_label_removed': 'app:numerical-reproducibility' not in main,
}
for stem, text in [('main', main), ('supplementary', si)]:
    labels = re.findall(r'\\label\{([^}]+)\}', text)
    refs = set(re.findall(r'\\(?:eq)?ref\{([^}#]+)\}', text))
    checks[stem + '_labels_unique'] = len(labels) == len(set(labels))
    checks[stem + '_references_defined'] = not (refs - set(labels))

changed = []
protected_changes = []
for rel, expected in baseline['tracked_sha256'].items():
    path = repo / rel
    if not path.is_file():
        changed.append(rel)
    elif hashlib.sha256(Path('\\\\?\\' + str(path.resolve())).read_bytes()).hexdigest() != expected:
        changed.append(rel)
    else:
        continue
    package_rel = rel.split('tracing_isolation_optimal_control_complete/', 1)[-1]
    if (package_rel.startswith(('data/', 'figures/', 'validation/'))
            and package_rel != 'data/numerical_scenarios/export_provenance.json'):
        protected_changes.append(rel)
checks['old_data_figures_validation_unchanged'] = not protected_changes
solve_files = [x['path'] for x in json.loads((project / 'data/numerical_scenarios/export_provenance.json').read_text(encoding='utf-8'))['source_files']]
report = {'checks': checks, 'passed': all(checks.values()),
          'statement_count': sum(environments(main, 'theorem|lemma|proposition|corollary|definition').values()),
          'proof_count': sum(environments(main, 'proof').values()),
          'changed_tracked_paths': changed, 'protected_changes': protected_changes,
          'baseline_tracked_count': len(baseline['tracked_sha256']),
          'optimizer_calls': 0, 'new_ocp_solves': 0}
(here / 'audit_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report['passed']:
    raise SystemExit(1)
