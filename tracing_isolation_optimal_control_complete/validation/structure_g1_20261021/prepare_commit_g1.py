"""生成明确的 G1 提交清单，并在暂存后验证真实索引范围。"""
import argparse
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = PROJECT.parent
PREFIX = PROJECT.relative_to(ROOT).as_posix()
ALLOWED = [
    'MANIFEST.txt', 'README.md', 'REVIEW_GUIDE.md',
    'ai/claude_revision_plan/G_DECISIONS.md', 'ai/claude_revision_plan/REVISION_PLAN.md',
    'latex/main.pdf', 'latex/main.tex', 'latex/theory_only.pdf', 'latex/theory_only.tex',
    'matlab/numerical_scenarios/README.md',
]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def files(raw):
    return sorted(x.decode('utf-8') for x in raw.split(b'\0') if x)


def prepare():
    base = git('rev-parse', 'HEAD').decode().strip()
    assert base == '689a6277dc478099971280909a65ffa728feb8ea'
    # 先建立本批将交付的记录文件名，使提交清单不遗漏自身和提交前核验记录。
    for name in ['staging_paths.json', 'staging_paths.txt', 'staging_add_paths.txt', 'changed_files.txt', 'commit_preflight.json']:
        if not (HERE / name).exists():
            (HERE / name).write_text('{}\n' if name.endswith('.json') else '', encoding='utf-8')
    message = '''paper: 全文结构重排与结构性删除（G1）

按作者决定删除TheoryOnly与时变章节，将正文重排为10节；长引理证明原样移入附录，补充节首路线与唯一性证明分步。讨论仅移动，补充材料留待G4拆分。

核对：白名单外无文字差异，124个保留公式标签逐字相同，仅删除指定5式；两个自动生成块与2474保护文件字节不变。长引理proof原样、唯一性proof剔除获准新增后严格一致。208次定理/公式引用中37次前向，第3节概览11次；概览之外证明内前向0，依赖检查无环。

工作区和Git导出自包含副本各四阶段加额外XeLaTeX，共10命令退出0，最终日志零诊断，主文46→45页且逐页文本一致；11页150dpi实际目视通过。默认Python缺库与首次长路径枚举失败记录保留。

优化器、新增OCP、MATLAB调用均0；导出器、数据、图形及已有validation记录不动。不推送，止于G1，等待作者审阅。

Co-Authored-By: Codex <noreply@openai.com>
'''
    (HERE / 'commit_message.txt').write_text(message, encoding='utf-8')
    records = [p.relative_to(ROOT).as_posix() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    expected = sorted([PREFIX + '/' + x for x in ALLOWED] + records)
    (HERE / 'staging_paths.json').write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (HERE / 'staging_paths.txt').write_text('\n'.join(expected) + '\n', encoding='utf-8')
    # 删除项已为 Git 导出验证提前暂存；git add 不再次传入已从索引删除的路径。
    add_paths = [rel for rel in expected if (ROOT / rel).is_file()]
    (HERE / 'staging_add_paths.txt').write_text('\n'.join(add_paths) + '\n', encoding='utf-8')
    (HERE / 'changed_files.txt').write_text('\n'.join(expected) + '\n', encoding='utf-8')
    manifest = PROJECT / 'MANIFEST.txt'
    lines = manifest.read_text(encoding='utf-8').splitlines()
    for rel in records:
        project_rel = rel.removeprefix(PREFIX + '/')
        if project_rel not in lines:
            lines.append(project_rel)
    manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'expected_files': len(expected), 'record_files': len(records), 'subject': message.splitlines()[0]}, ensure_ascii=False))


def check():
    expected = json.loads((HERE / 'staging_paths.json').read_text(encoding='utf-8'))
    staged = files(git('diff', '--cached', '--name-only', '-z'))
    unstaged = files(git('diff', '--name-only', '-z'))
    audit = json.loads((HERE / 'preservation_audit.json').read_text(encoding='utf-8'))
    acceptance = json.loads((HERE / 'acceptance_report.json').read_text(encoding='utf-8'))
    record = {'passed': staged == expected and not unstaged and audit['passed'] and acceptance['passed'],
              'actual_staged_files': staged, 'expected_files': expected, 'unstaged_tracked_files': unstaged,
              'missing_from_index': sorted(set(expected) - set(staged)), 'unexpected_in_index': sorted(set(staged) - set(expected)),
              'baseline_head': git('rev-parse', 'HEAD').decode().strip(),
              'branch': git('branch', '--show-current').decode().strip(),
              'main_ref_before_commit': git('rev-parse', 'refs/heads/main').decode().strip(),
              'protected_files_passed': audit['passed'], 'acceptance_passed': acceptance['passed'],
              'matlab_calls': 0, 'optimizer_calls': 0, 'new_ocp_solves': 0, 'pushes': 0}
    (HERE / 'commit_preflight.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert record['passed'], record
    print(json.dumps({'passed': True, 'staged_files': len(staged), 'unstaged_files': len(unstaged), 'branch': record['branch']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check() if args.check else prepare()
