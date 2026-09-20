"""核对发布数据、LaTeX 数值宏及粗/细网格结果，独立于 MATLAB 导出器。"""
from pathlib import Path
import json
import re
import numpy as np
from scipy.io import loadmat
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'numerical_scenarios'


def macro_number(tex, name):
    return float(re.search(r'\\'+name+r'\}\{([^}]+)\}', tex)[1])


def verify_revision(summary, tex):
    """独立核对初猜数组及过渡单元，不使用 MATLAB 导出器的比较结论代替计算。"""
    main = loadmat(DATA/'E2.mat', simplify_cells=True)['run']
    neutral = loadmat(DATA/'checks/neutral_E2/E2.mat', simplify_cells=True)['run']
    assert neutral['success'] and neutral['return_status'] == 'Solve_Succeeded'
    assert neutral['initialization'] == {'type': 'constant_control', 'control': .7}
    assert neutral['solver_settings']['initialization'] == 'constant_control'
    for key, value in main['solver_settings'].items():
        if key != 'initialization':
            assert value == neutral['solver_settings'][key]
    assert main['parameters'] == neutral['parameters']
    assert np.array_equal(main['x0'], neutral['x0'])
    assert neutral['solver_settings']['N'] == 8000
    ig = neutral['initial_guess']
    assert np.array_equal(ig['t_control'], neutral['t_control'])
    assert np.array_equal(ig['t_state'], neutral['t_state'])
    assert np.all(ig['control'] == .7)
    assert len(ig['t_integrator']) > len(ig['t_state'])
    # 使用另一积分器核对节点和内部配点确由无阶段结构的常值控制产生。
    ode = solve_ivp(lambda t, x: [-1.7*x[0]*x[1], (.3*x[0]-.3)*x[1]],
                    (0, 300), neutral['x0'], method='DOP853',
                    rtol=1e-11, atol=1e-13, dense_output=True)
    assert ode.success
    for time_key, state_key in [('t_state', 'states'), ('t_integrator', 'integrator_states')]:
        assert np.max(abs(ig[state_key]-ode.sol(ig[time_key]).T)) < 1e-8
    q, dt = neutral['q_control'], neutral['dt_control']
    assert np.isfinite(q).all() and np.isfinite(dt).all() and np.all(dt > 0)
    assert np.max(abs(np.diff(neutral['t_state'])-dt)) < 1e-10
    assert abs(np.sum(dt)-300) < 1e-9
    assert q.min() >= -1e-6 and q.max() <= 1+1e-6
    cost = neutral['parameters']['p']*neutral['parameters']['c']*np.dot(q, dt)
    assert abs(cost-neutral['J_openocl']) < 1e-11
    a = neutral['assessment']
    assert a['passed'] and a['observed_structure'] == main['assessment']['observed_structure']
    for key in ['capacity_excess', 'state_discrepancy', 'initial_error', 'state_violation', 'control_violation', 'tail_max_q']:
        assert a[key] <= 1e-6
    assert a['terminal_safe'] and a['reintegrated_terminal_peak'] <= .15+1e-6
    delta = abs(neutral['J_openocl']-main['J_openocl'])
    assert delta <= 1e-5
    reported = summary['neutral_E2_check']
    assert reported['passed'] and reported['status'] == 'passed'
    assert abs(reported['absolute_cost_difference']-delta) < 1e-15
    assert abs(macro_number(tex,'NumNeutralETwoCostDifference')-delta) < 1e-15
    assert abs(summary['additional_checks']['neutral_E2']['J_openocl']-cost) < 1e-11
    refs = (ROOT/'latex/numerical_reference_values.tex').read_text(encoding='utf-8')
    exits = {}
    for case, suffix in [('E2','Two'), ('E4','Four')]:
        r = loadmat(DATA/(case+'.mat'), simplify_cells=True)['run']
        arcs = r['assessment']['arcs']
        candidates = [arcs[j] for j in range(1,len(arcs)-1)
                      if [arcs[j-1]['type'],arcs[j]['type'],arcs[j+1]['type']] == ['q_B','transition','1']]
        assert len(candidates) == 1
        arc = candidates[0]
        theory = r['reference']['events']['full_start']
        assert arc['cells'] == 1 and arc['t_start'] <= theory <= arc['t_end']
        assert abs(arc['t_end']-arc['t_start']-r['solver_settings']['T']/r['solver_settings']['N']) < 1e-10
        report = summary['capacity_exit_checks'][case]
        assert report['supported'] and report['contains_theory']
        assert np.max(abs(np.array(report['interval'])-[arc['t_start'],arc['t_end']])) < 1e-12
        assert abs(report['theory_time']-theory) < 1e-12
        for endpoint, key in [('Start','t_start'), ('End','t_end')]:
            assert abs(macro_number(tex,'NumExitE'+suffix+endpoint)-arc[key]) < 5.1e-9
        assert abs(macro_number(refs,'NumExitE'+suffix+'Theory')-theory) < 5.1e-9
        exits[case] = report
    r4 = loadmat(DATA/'E4.mat', simplify_cells=True)['run']
    gap = r4['J_openocl']-r4['reference']['J_reference']
    assert gap < 0 and r4['assessment']['capacity_excess'] > 0
    assert abs(macro_number(tex,'NumEFourSignedCostDifference')-gap) < 1e-14
    assert abs(macro_number(tex,'NumEFourCapacityExcess')-r4['assessment']['capacity_excess']) < 1e-14
    assert '单网格过渡区间内' in tex and '严格连续时间可行控制' in tex
    assert '首个完全跟踪区间起点分别' not in tex
    return dict(neutral_E2_passed=True, neutral_E2_cost_difference=delta,
                neutral_E2_max_control_difference=float(np.max(abs(q-main['q_control']))),
                capacity_exit_checks=exits, E4_signed_cost_difference=gap)


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
             legacy_interval_cost=legacy['J_openocl'],revision=verify_revision(summary,tex))
    (Path(__file__).parent/'saved_results_audit.json').write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SAVED_RESULTS_AUDIT_OK: five main cases, refinement, neutral guess, legacy baseline and TeX costs')


if __name__=='__main__':
    main()
