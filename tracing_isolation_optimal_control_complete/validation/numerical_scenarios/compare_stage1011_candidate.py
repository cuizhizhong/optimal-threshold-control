"""核对候选缓存复现，明确区分数据相同、元数据更新和渲染差异。"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import numpy as np
from scipy.io import loadmat
from PIL import Image

P = Path(__file__).resolve().parents[2]
V = P / 'validation/numerical_scenarios'
Q = P.parent / 'tmp/s12' / P.name
CV = Q / 'validation/numerical_scenarios'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in set(a) | set(b) if not k.startswith('__')
                for d in differences(a.get(k), b.get(k), path + '.' + k)]
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return [path]
        return [d for k, (x, y) in enumerate(zip(a, b))
                for d in differences(x, y, f'{path}[{k}]')]
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        if a.shape != b.shape:
            return [path]
        if a.dtype == object or b.dtype == object:
            return [d for k, (x, y) in enumerate(zip(a.flat, b.flat))
                    for d in differences(x, y, f'{path}[{k}]')]
        try:
            equal = np.array_equal(a, b, equal_nan=True)
        except TypeError:
            equal = np.array_equal(a, b)
        return [] if equal else [path]
    if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
        return []
    return [] if a == b else [path]


def main():
    clean = read(CV / 'step1011_clean_report.json')
    assert clean['status'] == 'completed' and clean['trusted_cache_hits'] == 35
    assert clean['scientific_optimizer_executions'] == 0 and clean['smoke_passed']
    assert (P / 'latex/main.tex').read_bytes() == (Q / 'latex/main.tex').read_bytes()
    snapshot = read(V / 'step1011_checkout_manifest.json')
    files = {e['path']: e['sha256'] for e in snapshot['overlay_files']}
    protected = ['validation/numerical_scenarios/analytic_checkpoints.json',
                 'validation/numerical_scenarios/scenario_inputs.json']
    protected += [str(f.relative_to(Q)).replace('\\', '/')
                  for f in (Q / 'data/numerical_scenarios/runs').glob('*') if f.is_file()]
    assert all(sha(Q / n) == files[P.name + '/' + n] for n in protected)
    long_q = Path('\\\\?\\' + str(Q)) if os.name == 'nt' else Q
    assessments = list((long_q / 'data/numerical_scenarios/revision_checks/assessments').glob('*.mat'))
    assert len(assessments) == 35
    assert all(sha(f) == files[P.name + '/' + str(f.relative_to(long_q)).replace('\\', '/')] for f in assessments)
    compatibility = []
    for case in ['E1', 'E2', 'E3', 'E4', 'E5']:
        n = f'data/numerical_scenarios/{case}.mat'
        diff = differences(loadmat(P / n, simplify_cells=True), loadmat(Q / n, simplify_cells=True))
        assert set(diff) <= {'.run.selection_provenance.selected_utc'}, (case, diff)
        compatibility.append({'case_id': case, 'only_different_fields': diff,
                              'root_sha256': sha(P / n), 'candidate_sha256': sha(Q / n)})
    original_selection = read(P / 'data/numerical_scenarios/selection_manifest.json')
    candidate_selection = read(Q / 'data/numerical_scenarios/selection_manifest.json')
    selection_diff = differences(original_selection, candidate_selection)
    allowed = {'.selected_utc'} | {f'.entries[{k}].compatibility_sha256' for k in range(5)}
    assert set(selection_diff) <= allowed, selection_diff
    sources = ['export_numerical_latex.m', 'make_numerical_figures.m',
               'verify_revision_exporter.m', 'verify_saved_result_exporter.m',
               'verify_pending_result_exporter.m', 'execute_stage1011_clean.m', 'build_stage1011.py']
    for n in sources:
        folder = 'validation/numerical_scenarios' if n.endswith('.py') or n == 'execute_stage1011_clean.m' else 'matlab/numerical_scenarios'
        assert sha(P / folder / n) == sha(Q / folder / n), n
    figures = []
    for name in ['FigN1_regions', 'FigN2_waiting', 'FigN3_boundary_tracking']:
        n = f'figures/numerical_scenarios/{name}.png'
        with Image.open(P / n) as a, Image.open(Q / n) as b:
            assert a.size == b.size
            x, y = np.asarray(a.convert('RGB')), np.asarray(b.convert('RGB'))
            delta = np.abs(x.astype(np.int16) - y.astype(np.int16))
            pixels = np.any(delta != 0, axis=2)
            figures.append({'name': name, 'size': list(a.size),
                            'changed_pixels': int(pixels.sum()),
                            'total_pixels': int(pixels.size), 'max_channel_delta': int(delta.max()),
                            'root_creation_time': a.info.get('Creation Time'),
                            'candidate_creation_time': b.info.get('Creation Time'),
                            'root_sha256': sha(P / n), 'candidate_sha256': sha(Q / n)})
    for f in CV.glob('step1011_clean*.json'):
        shutil.copy2(f, V / f.name)
    for n in ['step1011_smoke_report.json', 'step1011_smoke_interface.mat']:
        shutil.copy2(CV / n, V / n)
    build = read(CV / 'step1011_build_report.json')
    assert all(build[k]['success'] and not build[k]['final_log_issues'] for k in ['main', 'theory_only'])
    shutil.copy2(CV / 'step1011_build_report.json', V / 'step1011_clean_build_report.json')
    for k in ['main', 'theory_only']:
        for command in build[k]['commands']:
            command['original_candidate_log'] = command['log']
            command['log'] = command['log'].replace('step1011_', 'step1011_clean_', 1)
        shutil.copy2(CV / f'step1011_{k}_final.log', V / f'step1011_clean_{k}_final.log')
        for j in range(1, 5):
            shutil.copy2(CV / f'step1011_{k}_build_{j}.log', V / f'step1011_clean_{k}_build_{j}.log')
    (V / 'step1011_clean_build_report.json').write_text(json.dumps(build, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'snapshot_commit': snapshot['snapshot_commit'], 'main_tex_byte_identical': True,
              'raw_solver_fixture_and_inputs_byte_unchanged': True,
              'protected_candidate_artifacts_checked': len(protected),
              'protected_assessment_files_byte_unchanged': len(assessments),
              'current_sources_match_candidate': True, 'source_files_checked': sources,
              'compatibility_scientific_content_identical': True,
              'compatibility_metadata_differences': compatibility,
              'selection_manifest_different_fields': sorted(selection_diff),
              'figure_render_differences': figures,
              'candidate_figures_visual_review': {'reviewed_all_three': True, 'defects': [],
                  'observation': '未见曲线、阶梯、物理域、Phi边界或布局的实际差别；灰色虚线穿透明图例背景的轻微现象两份都保留且可读。'},
              'limits': '图像时间戳和少量渲染像素变化保留，不声称PNG逐字节或全像素相同。'}
    (V / 'step1011_candidate_source_match.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CANDIDATE_DATA_SOURCE_MATCH_OK raw=35 source=7')
    print(json.dumps(figures, ensure_ascii=False))


if __name__ == '__main__':
    main()
