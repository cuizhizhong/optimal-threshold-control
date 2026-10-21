"""汇总实际 G1 证据，更新正式 PDF 与可审阅记录；不提交或运行数值程序。"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = PROJECT.parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = read('preservation_audit.json')
    forward = read('forward_refs.json')
    workspace = read('workspace_attempt1/build_report.json')
    isolated = read('isolated_attempt1/build_report.json')
    assert audit['passed'] and workspace['success'] and isolated['success']
    assert forward['source_sha256'] == sha(PROJECT / 'latex/main.tex')
    assert audit['source_sha256']['new_worktree_raw'] == sha(PROJECT / 'latex/main.tex')
    assert workspace['main_sha256'] == sha(PROJECT / 'latex/main.tex')
    original_pdf = subprocess.check_output(['git', 'show', '689a627:tracing_isolation_optimal_control_complete/latex/main.pdf'], cwd=ROOT)
    import io
    baseline_pages = len(PdfReader(io.BytesIO(original_pdf)).pages)
    p1, p2 = PdfReader(workspace['pdf_path']), PdfReader(isolated['pdf_path'])
    assert len(p1.pages) == len(p2.pages) == 45
    texts = [(page.extract_text() or '') for page in p1.pages]
    isolated_texts = [(page.extract_text() or '') for page in p2.pages]
    assert texts == isolated_texts
    assert workspace['outline'] == isolated['outline']
    assert not workspace['final_diagnostics'] and not isolated['final_diagnostics']
    titles = [x['title'] for x in workspace['outline'] if x['level'] == 1]
    expected = ['引言', '模型与控制问题', '主结果与最优分区', '预备结果', '候选策略的构造', '全局最优性与唯一性', '机制与量级', '数值结果', '讨论', '结论',
                '完全跟踪成本导数的逐步计算', '容量边界成本积分的逐步计算', '完全跟踪分区可达性与不再返回等待区的证明', '梯度拼接与相对正则性的详细证明',
                '小容量渐近的完整推导', '感染阈值与医疗需求', '补充材料 S：数值复现、复核与诊断记录']
    assert titles == expected
    qa1, qa2 = read('visual_qa_primary.json'), read('visual_qa_secondary.json')
    assert all(x['passed'] for x in qa1['pages'])
    assert qa2['overall_visual_pass'] and all(not x['overlap_overflow_or_missing_glyphs_observed'] for x in qa2['pages'])
    assert {x['page'] for x in qa1['pages'] + qa2['pages']} == {1, 2, 3, 8, 13, 20, 24, 25, 35, 37, 38}
    # 第二位审阅者的实际逐页记录单独保留，不凭命令成功推定目视完成。
    render = read('render_manifest.json')
    assert render['pdf_sha256'] == workspace['pdf_sha256']
    assert {x['page'] for x in render['pages']} == {1, 2, 3, 8, 13, 20, 24, 25, 35, 37, 38}
    for item in render['pages']:
        assert sha(Path(item['image'])) == item['image_sha256']
    for ext in ['pdf', 'bbl']:
        source = Path(workspace['build_directory']) / f'main.{ext}'
        target = PROJECT / f'latex/main.{ext}'
        before, after = target.read_bytes(), source.read_bytes()
        identical = before == after if ext == 'pdf' else before.replace(b'\r\n', b'\n') == after.replace(b'\r\n', b'\n')
        if not identical:
            shutil.copyfile(source, target)
    assert sha(PROJECT / 'latex/main.pdf') == workspace['pdf_sha256']
    report = {
        'baseline': '689a6277dc478099971280909a65ffa728feb8ea', 'passed': True,
        'main_sha256': sha(PROJECT / 'latex/main.tex'), 'delivered_pdf_sha256': sha(PROJECT / 'latex/main.pdf'),
        'baseline_pages': baseline_pages, 'pages': len(p1.pages), 'page_delta': len(p1.pages) - baseline_pages,
        'workspace_commands': len(workspace['commands']), 'isolated_commands': len(isolated['commands']),
        'all_command_exit_codes': [x['exit_code'] for x in workspace['commands'] + isolated['commands']],
        'final_diagnostics': [], 'forbidden_isolated_inputs': isolated['forbidden_inputs'],
        'page_texts_identical_between_builds': True, 'outlines_identical_between_builds': True,
        'page_text_sha256': [hashlib.sha256(t.encode('utf-8')).hexdigest() for t in texts],
        'preservation': {'passed': audit['passed'], 'retained_labeled_equations': audit['equations']['new_labels'],
                         'protected_files': audit['protected_files']['count'], 'proofs': audit['proofs']},
        'forward_counts': forward['counts'], 'rendered_pages': sorted(x['page'] for x in render['pages']),
        'visual_qa_records': ['visual_qa_primary.json', 'visual_qa_secondary.json'],
        'matlab_calls': 0, 'optimizer_calls': 0, 'new_ocp_solves': 0, 'pushes': 0,
        'scope': 'G1 独立提交后停止，等待作者审阅；不执行G2–G5。'
    }
    (HERE / 'acceptance_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows = []
    for number, item in enumerate([x for x in workspace['outline'] if x['level'] == 1]):
        label = str(number + 1) if number < 10 else chr(ord('A') + number - 10)
        rows.append(f"| {label} | {item['title']} | {item['page']} |")
    outline_rows = []
    for item in workspace['outline']:
        outline_rows.append('  ' * (item['level'] - 1) + f"- {item['title']}（第 {item['page']} 页）")
    readme = '''# G1 全文结构重排与结构性删除验证

基准：`689a6277dc478099971280909a65ffa728feb8ea`。作者决定见 [G_DECISIONS.md](../../ai/claude_revision_plan/G_DECISIONS.md)。本目录只记录 G1，不授权执行 G2–G5。

## 实际结果

'''
    readme += f"- 主文 {baseline_pages} → {len(p1.pages)} 页。正文重排为 10 节，附录按指定顺序排列，补充材料 S 本批仍内联。\n"
    readme += f"- 保全审计通过：{audit['equations']['new_labels']} 个保留公式标签对应的公式逐字相同，仅删除指定 5 式；两个自动生成块逐字不变。\n"
    readme += f"- 白名单之外无旧段落缺失或新段落；段落归一化后字符多重集一致。原 {audit['paragraphs']['old_after_whitelist']} 段与新 {audit['paragraphs']['new_after_whitelist']} 段的计数差来自结构删除后相邻段落拼接，双向整段查找均通过。\n"
    readme += f"- {audit['protected_files']['count']} 个 data/、figures/、生成宏、MATLAB 源码和既有 validation/ 文件的工作区原始字节不变。历史数据、导出器、图形和已有验证记录未改。\n"
    readme += '- 完全跟踪分区引理的完整 proof 环境逐字移入附录 C；唯一性证明只剔除获准新增路线与分步前缀后，原有证明内部逐字相同。\n'
    readme += '- 工作区与 Git 暂存区导出的独立副本各运行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，再额外运行一次 XeLaTeX，共 10 条命令退出 0。最终 .log/.blg/stdout 零诊断，无未定义引用、溢出、缺图或缺字。\n'
    readme += '- 独立副本初始仅含从 Git 导出的 latex/ 和 figures/；移除副本内旧编译产物后从零构建。fls 未读入工作区其他路径或 validation/ 内容。两份 45 页 PDF 的逐页提取文本和完整目录一致；正式 PDF 与工作区最终构建 SHA-256 相同。\n'
    readme += '- 指定的 11 页已以 150 dpi 实际渲染并逐张目视：目录 1–3 页，第 4/5/6/7/9 节起始 8/13/20/25/35 页，唯一性证明 24–25 页，新增附录证明 37–38 页。未见重叠、溢出、缺字或截断。详见两份 visual_qa JSON。\n'
    readme += '- 优化器 / 新增 OCP / MATLAB 调用：**0 / 0 / 0**。未运行导出器、数据重评或图形重导出。未推送；完成一次独立提交后停止等作者审阅。\n\n'
    readme += '## 新目录与页码\n\n| 章节 | 标题 | 起始页 |\n|---|---|---:|\n' + '\n'.join(rows)
    readme += '\n\n完整层级：\n\n' + '\n'.join(outline_rows) + '\n\n'
    readme += '''## 证据与可复核命令

- [文字、公式和白名单原文/新文审计](preservation_audit.md)；机器结果为 [preservation_audit.json](preservation_audit.json)。全部白名单逐条列出，结构标题新旧清单另列。
- [前向引用依赖说明](forward_dependency_review.md)；完整清单逐项附在本 README 下方。
- [工作区构建记录](workspace_attempt1/build_report.json)、[自包含构建记录](isolated_attempt1/build_report.json)，保存每条实际 argv/cwd/退出码及最终日志。
- [150 dpi 渲染记录](render_manifest.json)、[目视记录一](visual_qa_primary.json)、[目视记录二](visual_qa_secondary.json)。
- [最终验收汇总](acceptance_report.json)。初始默认 Anaconda 缺少 pypdf 的失败保留在 initial_runtime_failure.json；未开始编译，随后使用 bundled Python。保护文件首次枚举遭遇 Windows 长路径限制的记录保留在 audit_attempt1_capture_failure.json，修正枚举后核对通过。
- [明确提交路径](changed_files.txt)与[实际暂存范围核对](commit_preflight.json)。首次暂存因已经暂存删除的路径再次作为 pathspec 传入而失败，记录见 staging_initial_failure.json 和 commit_preflight_initial_failure.json；修正后实际索引与完整预期清单逐项相同。
- 重复汇总时对已相同的 main.bbl 回写遇到 Windows `OSError: [Errno 22] Invalid argument`，记录见 finalize_repeat_failure.json。核对现有 bbl 与最终构建逐字相同后，汇总改为跳过相同成品，正式 PDF 校验通过。原始编译记录保留工具产生的行尾空格，源码与文档的 `git diff --check` 排除原始 `.log` 与 `.aux` 文件后通过。

Python 使用 `load_workspace_dependencies` 返回的 `C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。工作区初次构建和自包含初次构建均已通过，无额外隐藏预编译。构建脚本拒绝覆盖既有 attempt；重复运行须增加 `--attempt`。

```powershell
& $py -X utf8 validation/structure_g1_20261021/audit_preservation.py
& $py -X utf8 validation/structure_g1_20261021/check_forward_refs.py
& $py -X utf8 validation/structure_g1_20261021/build_g1.py --mode workspace --attempt 2
# 自包含构建前，须先用明确路径列表暂存所要验证的 LaTeX 源码和删除项。
& $py -X utf8 validation/structure_g1_20261021/build_g1.py --mode isolated --attempt 2
```

上述命令相对于项目目录；`$py` 应绑定上述 bundled Python 绝对路径。完整实际首次命令见 build_report.json；不得将示例重跑命令当成本轮执行次数。

## 作者审阅重点

请通读新第 4–6 节导读及唯一性证明分步，检查正文长引理证明思路与附录 C 的衔接。讨论只移动，现有时变接触率未完成证明的说明原样保留；未进入 G2 改写。第 3 节概览中的前向引用及第 4 节证明路线中的预告是有意导读，概览以外的证明内前向引用为 0，详见下方逐项清单及依赖说明。

---

'''
    readme += (HERE / 'forward_refs.md').read_text(encoding='utf-8')
    (HERE / 'README.md').write_text(readme, encoding='utf-8')
    # 清单登记全部本批实际交付记录，不登记 tmp/ 或运行缓存。
    manifest = PROJECT / 'MANIFEST.txt'
    original = manifest.read_text(encoding='utf-8')
    lines = original.splitlines()
    for path in sorted(HERE.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            rel = path.relative_to(PROJECT).as_posix()
            if rel not in lines:
                lines.append(rel)
    manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['passed', 'baseline_pages', 'pages', 'workspace_commands', 'isolated_commands', 'forward_counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
