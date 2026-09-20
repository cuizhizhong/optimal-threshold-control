"""核对发布数据、LaTeX 数值宏及粗/细网格结果，独立于 MATLAB 导出器。"""
from pathlib import Path
import json
import re
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'numerical_scenarios'


def main():
    summary = json.loads((DATA / 'numerical_checks.json').read_text(encoding='utf-8'))
    assert summary['verified']
    tex = (ROOT / 'latex' / 'numerical_pending.tex').read_text(encoding='utf-8')
    assert r'\NumResultsVerifiedtrue' in tex
    expected = ['0 -> 1 -> 0', '0 -> q_B -> 1 -> 0', '1 -> 0', 'q_B -> 1 -> 0', '1 -> 0']
    suffixes = ['One', 'Two', 'Three', 'Four', 'Five']
    results = []
    for k in range(1, 6):
        r = loadmat(DATA / f'E{k}.mat', simplify_cells=True)['run']
        t, q, dt = (r[x] for x in ('t_state', 'q_control', 'dt_control'))
        assert len(t) == len(q) + 1 == int(r['solver_settings']['N']) + 1
        assert t[0] == 0 and abs(t[-1] - 300) < 1e-9
        assert np.all(dt > 0) and np.max(abs(np.diff(t)-dt)) < 1e-10
        assert np.max(abs(t[:-1]-r['t_control'])) < 1e-10
        assert np.isfinite(q).all() and q.min() >= -1e-6 and q.max() <= 1+1e-6
        cost = r['parameters']['p']*r['parameters']['c']*np.dot(q, dt)
        assert abs(cost-r['J_openocl']) < 1e-11
        a = r['assessment']
        assert r['success'] and a['passed'] and r['return_status'] == 'Solve_Succeeded'
        assert a['observed_structure'] == expected[k-1]
        assert a['capacity_excess'] <= 1e-6 and a['state_discrepancy'] <= 1e-6
        assert a['tail_max_q'] <= 1e-6 and a['terminal_safe']
        # 正终端感染值不能被峰值公式的消去误差错误变成 0。
        assert r['i_state'][-1] > 0 and a['terminal_peak'] >= r['i_state'][-1]
        reported = float(re.search(r'\\NumJOclE'+suffixes[k-1]+r'\}\{([^}]+)\}',tex)[1])
        assert abs(reported-cost) <= 0.5e-6
        assert abs(summary['cases'][k-1]['J_openocl']-cost) < 1e-11
        if k in (2, 4):
            coarse = loadmat(DATA/'coarse'/f'E{k}.mat',simplify_cells=True)['run']
            assert coarse['solver_settings']['N'] == 4000 and r['solver_settings']['N'] == 8000
            assert coarse['assessment']['capacity_excess'] > a['capacity_excess']
        results.append(dict(case_id=f'E{k}',N=len(q),J_reference=r['reference']['J_reference'],
                            J_openocl=cost,capacity_excess=a['capacity_excess']))
    neutral=loadmat(DATA/'checks/E1.mat',simplify_cells=True)['run']
    assert neutral['initialization']['type']=='constant_control'
    assert neutral['initialization']['control']==0.7 and neutral['assessment']['passed']
    refined=loadmat(DATA/'checks/E2.mat',simplify_cells=True)['run']
    assert refined['solver_settings']['N']==8000 and refined['assessment']['passed']
    legacy=loadmat(DATA/'legacy_baseline/legacy_E2.mat',simplify_cells=True)['run']
    assert legacy['info']['success']
    out=dict(status='passed',cases=results,neutral_guess_passed=True,refinement_passed=True,
             legacy_interval_cost=legacy['J_openocl'])
    (Path(__file__).parent/'saved_results_audit.json').write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SAVED_RESULTS_AUDIT_OK: five main cases, refinement, neutral guess, legacy baseline and TeX costs')


if __name__=='__main__':
    main()
