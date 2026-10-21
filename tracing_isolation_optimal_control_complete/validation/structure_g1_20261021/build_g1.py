"""G1 四阶段加额外 XeLaTeX；另从 Git 暂存区导出自包含副本。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = PROJECT.parent
WORK = PROJECT / 'tmp/structure_g1_20261021'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git(*args, data=None):
    return subprocess.run(['git', *args], cwd=ROOT, input=data, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def diagnostics(path):
    if path.suffix == '.blg':
        pattern = r'^Warning--|^I couldn.t open|^I found no|^I was expecting|^Repeated entry|^Illegal|---line \d+|^\(There (?:was|were) \d+ (?:error messages?|warnings?)\)'
    else:
        pattern = (r'^!|(?:LaTeX(?: Font)?|Package \S+|Class \S+|XeTeX|pdfTeX) (?:Warning|Error)\b|'
                   r'^(?:Warning|Error):|Overfull \\[hv]box|Underfull \\[hv]box|Missing character:|'
                   r'Undefined control sequence|(?:xdvipdfmx|dvipdfmx):(?:warning|error):')
    return [line for line in path.read_text(encoding='utf-8', errors='replace').splitlines()
            if re.search(pattern, line, re.I)]


def export_index(base, report):
    prefix = PROJECT.relative_to(ROOT).as_posix()
    names = [n for n in git('ls-files', '--cached', '-z', '--', prefix + '/latex', prefix + '/figures').split(b'\0') if n]
    base.mkdir(parents=True)
    git('checkout-index', '--prefix=' + base.as_posix() + '/', '--stdin', '-z', data=b'\0'.join(names) + b'\0')
    root = base / prefix
    report['export'] = {'method': 'git checkout-index --stdin -z', 'files': []}
    for name in names:
        rel = name.decode('utf-8')
        path = base / rel
        blob = git('rev-parse', ':' + rel).decode().strip()
        actual = git('hash-object', '--path=' + rel, '--', str(path)).decode().strip()
        assert blob == actual, rel
        report['export']['files'].append({'path': rel, 'git_blob': blob, 'raw_sha256': sha(path)})
    assert sorted(x.name for x in root.iterdir()) == ['figures', 'latex']
    assert (root / 'latex/main.tex').read_bytes().replace(b'\r\n', b'\n') == (PROJECT / 'latex/main.tex').read_bytes().replace(b'\r\n', b'\n')
    report['export']['removed_stale_artifacts'] = []
    for p in (root / 'latex').rglob('*'):
        if p.is_file() and p.suffix in ['.pdf', '.aux', '.bbl', '.blg', '.log', '.out', '.toc', '.fls']:
            report['export']['removed_stale_artifacts'].append(p.relative_to(root).as_posix())
            p.unlink()
    return root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['workspace', 'isolated'], required=True)
    parser.add_argument('--attempt', type=int, default=1)
    parser.add_argument('--pre-xelatex', type=int, default=0)
    args = parser.parse_args()
    name = f'{args.mode}_attempt{args.attempt}'
    logs = HERE / name
    assert not logs.exists(), '保留既有记录，请增加 attempt'
    logs.mkdir()
    report = {'mode': args.mode, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'success': False, 'commands': [], 'matlab_calls': 0, 'optimizer_calls': 0, 'ocp_solves': 0}
    report_path = logs / 'build_report.json'
    try:
        root = export_index(WORK / name / 'git_export', report) if args.mode == 'isolated' else PROJECT
        latex = root / 'latex'
        build = WORK / name / 'build' if args.mode == 'workspace' else latex / 'build'
        assert not build.exists()
        build.mkdir(parents=True)
        report.update(source_root=str(root), build_directory=str(build), main_sha256=sha(latex / 'main.tex'))
        env = dict(os.environ)
        for key in ['TEXINPUTS', 'BIBINPUTS', 'BSTINPUTS', 'TEXMFOUTPUT']:
            env.pop(key, None)
        env['BIBINPUTS'] = str(latex) + os.pathsep
        xe = [shutil.which('xelatex'), '-interaction=nonstopmode', '-halt-on-error', '-recorder', f'-output-directory={build}', 'main.tex']
        stages = [(f'pre_{i+1}', xe, latex) for i in range(args.pre_xelatex)]
        stages += [('1', xe, latex), ('2', [shutil.which('bibtex'), 'main'], build), ('3', xe, latex), ('4', xe, latex), ('extra', xe, latex)]
        for stage, command, cwd in stages:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            path = logs / f'main_{stage}.stdout.log'
            path.write_bytes(result.stdout)
            report['commands'].append({'stage': stage, 'argv': command, 'cwd': str(cwd), 'exit_code': result.returncode, 'stdout_log': str(path)})
            save(report_path, report)
            print(f'{name}: stage={stage}, exit={result.returncode}', flush=True)
            assert result.returncode == 0, f'{stage} 非零退出'
        issues = []
        for suffix in ['log', 'blg', 'aux', 'toc', 'fls']:
            p = build / f'main.{suffix}'
            shutil.copyfile(p, logs / f'main_final.{suffix}')
            if suffix in ['log', 'blg']:
                issues += diagnostics(p)
        issues += diagnostics(logs / 'main_extra.stdout.log')
        report['final_diagnostics'] = sorted(set(issues))
        inputs = set()
        forbidden = []
        for line in (build / 'main.fls').read_text(encoding='utf-8', errors='replace').splitlines():
            if not line.startswith('INPUT '):
                continue
            p = Path(line[6:].strip().strip('"'))
            p = (latex / p).resolve() if not p.is_absolute() else p.resolve()
            inputs.add(str(p))
            if args.mode == 'isolated' and p.is_relative_to(PROJECT) and not p.is_relative_to(root):
                forbidden.append(str(p))
            if p.is_relative_to(ROOT) and 'validation' in p.parts:
                forbidden.append(str(p))
        save(logs / 'inputs.json', {'paths': sorted(inputs), 'forbidden': sorted(set(forbidden))})
        report['forbidden_inputs'] = sorted(set(forbidden))
        reader = PdfReader(build / 'main.pdf')
        def outlines(items, level=1):
            out = []
            for item in items:
                if isinstance(item, list):
                    out += outlines(item, level + 1)
                else:
                    out.append({'level': level, 'title': item.title, 'page': reader.get_destination_page_number(item) + 1})
            return out
        report.update(pages=len(reader.pages), outline=outlines(reader.outline), pdf_sha256=sha(build / 'main.pdf'), pdf_path=str(build / 'main.pdf'))
        assert not issues, f'最终日志问题: {sorted(set(issues))}'
        assert not forbidden, f'不允许的输入: {forbidden}'
        report['success'] = True
    except Exception as exc:
        report['failure'] = str(exc)
        raise
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(report_path, report)


if __name__ == '__main__':
    main()
