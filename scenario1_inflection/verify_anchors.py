"""
拐点分析解析公式与数值锚点复现校验。

运行：conda run --no-capture-output -n thesis python -B verify_anchors.py

覆盖：
  1) N=763 基准锚点与西安实例；
  2) S* 和 lambda 的四参数解析偏导与自适应中心差分；
  3) S* 偏导不依赖内部拐点存在性的边界外校验；
  4) q0 驻点的变号根、近零候选点与两侧导数；
  5) 既有方向扫描、曲率分解和可行性守卫的数值回归检查。
"""
import numpy as np
from scipy.optimize import brentq

from inflection_analysis import (
    G_MAX,
    X_GMAX,
    _chord_dev,
    curvature_factor,
    find_q0_stationary_points,
    lambda_sensitivities,
    solve,
    startup_sensitivities,
)


BASE = dict(beta=0.155, gamma=0.3504, c0=10.0, q0=0.01526,
            eta=0.05 * 763, N=763.0, S0=762.0, I0=1.0)

# 西安主基准（取自 xian_control_comparison/xian_control_comparison.py 与初值拟合表）
XIAN = dict(beta=0.1498, gamma=0.2953, c0=12.8872, q0=0.3230,
            eta=0.002 * 13163000.0, N=13163000.0,
            S0=13163000.0 - 0.001007, I0=0.001007)

ATOL = 1e-8
RTOL = 5e-5


def val(param, v, base=BASE):
    """param='eta' 时 v 是 theta=eta/N，其余为参数本身。"""
    p = dict(base)
    p[param] = v * p['N'] if param == 'eta' else v
    return solve(**p)


def check(name, got, want, tol):
    ok = abs(got - want) < tol
    print(f"  {'OK ' if ok else 'FAIL'} {name:28s} = {got:14.7g}  (期望 {want})")
    return ok


def check_close(name, analytic, finite_diff, atol=ATOL, rtol=RTOL):
    err = abs(analytic - finite_diff)
    bound = atol + rtol * abs(finite_diff)
    ok = err <= bound
    print(f"  {'OK ' if ok else 'FAIL'} {name:28s} analytic={analytic: .8e}  "
          f"FD={finite_diff: .8e}  err={err:.2e}  tol={bound:.2e}")
    return ok


def _valid_for_fd(res, require_inflection):
    if res.get('status') != 'ok':
        return False
    return (not require_inflection) or bool(res.get('has_inflection', False))


def central_difference(base, param, output_key, require_inflection, max_halvings=20):
    """按可行域自适应缩步的中心差分；不使用单边差分。"""
    center = solve(**base)
    if not _valid_for_fd(center, require_inflection):
        raise ValueError(f"中心点不满足 {output_key} 的差分条件")

    p0 = float(base[param])
    h = 1e-5 * max(1.0, abs(p0))
    for _ in range(max_halvings + 1):
        p_minus, p_plus = dict(base), dict(base)
        p_minus[param] = p0 - h
        p_plus[param] = p0 + h
        r_minus, r_plus = solve(**p_minus), solve(**p_plus)
        if (_valid_for_fd(r_minus, require_inflection)
                and _valid_for_fd(r_plus, require_inflection)):
            return (r_plus[output_key] - r_minus[output_key]) / (2.0 * h), h
        h *= 0.5
    raise ValueError(f"{param} 在减半 {max_halvings} 次后仍无法做中心差分")


def classify(param, lo, hi, key, base=BASE, n=241, tol=1e-9):
    """数值回归用方向分类：+/-/±/×，不作为解析证明。"""
    ys = []
    for v in np.linspace(lo, hi, n):
        r = val(param, v, base)
        if r['status'] != 'ok':
            continue
        y = r.get(key, np.nan)
        if y is None or not np.isfinite(y):
            continue
        ys.append(y)
    if len(ys) < 3:
        return '?', (np.nan, np.nan), len(ys)
    d = np.diff(np.asarray(ys))
    up, dn = (d > tol).any(), (d < -tol).any()
    sign = '±' if (up and dn) else ('+' if up else ('-' if dn else '×'))
    return sign, (ys[0], ys[-1]), len(ys)


def _root_sides(base, root, initial_step=1e-5, max_halvings=20):
    """寻找驻点两侧仍位于内部拐点区的残差值。"""
    h = initial_step
    for _ in range(max_halvings + 1):
        vals = []
        for q0 in (root - h, root + h):
            p = dict(base); p['q0'] = q0
            r = solve(**p)
            if r.get('status') != 'ok' or not r.get('has_inflection', False):
                break
            vals.append(lambda_sensitivities(r)['q0_stationarity_residual'])
        if len(vals) == 2:
            return vals[0], vals[1], h
        h *= 0.5
    raise ValueError("驻点过于靠近边界，无法取得两侧内部点")


def main():
    ok = True

    print("== 1) N=763 基准锚点 ==")
    r = solve(**BASE)
    for name, got, want, tol in [
        ('S_star', r['S_star'], 708.3470, 1e-3),
        ('S_c', r['S_c'], 175.1602, 1e-3),
        ('q_max', r['q_max'], 0.7565, 1e-3),
        ('q_inf', r['q_inf'], 0.40828, 1e-4),
        ('dt', r['dt'], 5.9026, 1e-3),
        ('seg_high(t_inf-t1)', r['seg_high'], 2.7013, 1e-3),
        ('seg_low(t2-t_inf)', r['seg_low'], 3.2012, 1e-3),
        ('lam(相对位置)', r['lam'], 0.458, 1e-3),
    ]:
        ok &= check(name, got, want, tol)
    seg_ok = abs(r['seg_high'] + r['seg_low'] - r['dt']) < 1e-9
    ok &= seg_ok
    print(f"  {'OK ' if seg_ok else 'FAIL'} 两段之和 = dt")

    cf = curvature_factor(r)
    err = np.max(np.abs(cf['scale'] * cf['g'] - cf['qdd']))
    ok &= err < 1e-12
    print(f"  {'OK ' if err < 1e-12 else 'FAIL'} q_c'' 因子分解误差 = {err:.2e}")
    print(f"       |g| 上界 = {G_MAX:.5f} 于 x = {X_GMAX[0]:.4f}, {X_GMAX[1]:.4f}")
    ok &= check('chord_dev(%)', 100 * _chord_dev(r), 4.4, 0.15)

    print("\n== 2) 西安实例（§4.4 脚注引用）==")
    rx = solve(**XIAN)
    assert rx['status'] == 'ok', rx['status']
    ok &= check('q_inf', rx['q_inf'], 0.4119, 1e-4)
    ok &= check('q_max=q_c(t1)', rx['q_max'], 0.8454, 1e-3)
    ok &= check('chord_dev(%)', 100 * _chord_dev(rx), 9.6, 0.1)

    print("\n== 3) 四参数解析偏导与中心差分 ==")
    ds = startup_sensitivities(r)
    dl = lambda_sensitivities(r)
    specs = [
        ('eta', 'dS_deta', 'dlambda_deta'),
        ('c0', 'dS_dc0', 'dlambda_dc0'),
        ('beta', 'dS_dbeta', 'dlambda_dbeta'),
        ('q0', 'dS_dq0', 'dlambda_dq0'),
    ]
    for param, s_key, l_key in specs:
        fd_s, hs = central_difference(BASE, param, 'S_star', require_inflection=False)
        fd_l, hl = central_difference(BASE, param, 'lam', require_inflection=True)
        ok &= check_close(f'S*_{param} (h={hs:.1e})', ds[s_key], fd_s)
        ok &= check_close(f'lambda_{param} (h={hl:.1e})', dl[l_key], fd_l)

    sign_ok = (ds['dS_deta'] < 0 < ds['dS_dc0']
               and ds['dS_dbeta'] > 0 > ds['dS_dq0']
               and dl['dlambda_deta'] < 0 < dl['dlambda_dc0']
               and dl['dlambda_dbeta'] > 0)
    ok &= sign_ok
    print(f"  {'OK ' if sign_ok else 'FAIL'} 解析符号：S* 四项与 lambda 前三项")
    ok &= check_close('S*_theta = N S*_eta', ds['dS_dtheta'], r['N'] * ds['dS_deta'])
    ok &= check_close('lambda_theta = N lambda_eta', dl['dlambda_dtheta'],
                      r['N'] * dl['dlambda_deta'])

    print("\n  S* 偏导不要求内部拐点：")
    noinf = dict(BASE); noinf['c0'] = 4.0
    r_noinf = solve(**noinf)
    noinf_ok = r_noinf['status'] == 'ok' and not r_noinf['has_inflection']
    ok &= noinf_ok
    print(f"  {'OK ' if noinf_ok else 'FAIL'} c0=4: status={r_noinf['status']}, "
          f"has_inflection={r_noinf.get('has_inflection')}")
    ds_noinf = startup_sensitivities(r_noinf)
    fd_noinf, h_noinf = central_difference(noinf, 'c0', 'S_star', require_inflection=False)
    ok &= check_close(f'无拐点 S*_c0 (h={h_noinf:.1e})', ds_noinf['dS_dc0'], fd_noinf)
    try:
        lambda_sensitivities(r_noinf)
        rejected = False
    except ValueError:
        rejected = True
    ok &= rejected
    print(f"  {'OK ' if rejected else 'FAIL'} 无内部拐点时拒绝 lambda 偏导")

    print("\n== 4) q0 驻点：检测根、候选点与两侧符号 ==")
    low_beta_pos = dict(BASE); low_beta_pos.update(beta=0.10, q0=0.03)
    low_beta_neg = dict(BASE); low_beta_neg.update(beta=0.10, q0=0.15)
    lp = lambda_sensitivities(solve(**low_beta_pos))['dlambda_dq0']
    ln = lambda_sensitivities(solve(**low_beta_neg))['dlambda_dq0']
    competition_ok = lp > 0 > ln
    ok &= competition_ok
    print(f"  {'OK ' if competition_ok else 'FAIL'} beta=0.10: "
          f"lambda_q0(0.03)={lp:.6f}>0, lambda_q0(0.15)={ln:.6f}<0")

    for beta in (0.10, 0.12, 0.155):
        p = dict(BASE); p['beta'] = beta
        found = find_q0_stationary_points(p, q0_bounds=(0.0, 0.39), n=2001)
        print(f"  beta={beta:.3f}: 变号根={found['roots']}  近零候选={found['candidates']}")
        for root in found['roots']:
            pr = dict(p); pr['q0'] = root
            rr = solve(**pr)
            sens = lambda_sensitivities(rr)
            residual_ok = abs(sens['q0_stationarity_residual']) <= 1e-8
            left, right, side_h = _root_sides(p, root)
            sides_ok = left * right < 0.0
            fd_at_root, _ = central_difference(pr, 'q0', 'lam', require_inflection=True)

            def fd_derivative(q0):
                pf = dict(p); pf['q0'] = float(q0)
                value, _ = central_difference(
                    pf, 'q0', 'lam', require_inflection=True)
                return value

            fd_extremum = brentq(
                fd_derivative, root - side_h, root + side_h,
                xtol=1e-12, rtol=1e-12,
            )
            fd_ok = (abs(fd_at_root) <= 2e-5
                     and abs(fd_extremum - root) <= 5e-7)
            ok &= residual_ok and sides_ok and fd_ok
            print(f"    {'OK ' if residual_ok and sides_ok and fd_ok else 'FAIL'} "
                  f"q0={root:.9f}: residual={sens['q0_stationarity_residual']:.2e}, "
                  f"sides=({left:.3e},{right:.3e})@{side_h:.1e}, "
                  f"FD={fd_at_root:.2e}, FD-root={fd_extremum:.9f}")
        for candidate, residual in found['candidates']:
            print(f"    CANDIDATE q0={candidate:.9f}, |residual|={residual:.2e}（不计为根）")

    print("\n== 5) 方向扫描（仅作数值回归检查）==")
    scan_specs = [('beta', 0.065, 0.50, 'beta'), ('q0', 0.0, 0.39, 'q0'),
                  ('c0', 4.2, 16.0, 'c0'), ('eta', 0.0135, 0.05, 'theta=eta/N')]
    print(f"  {'参数':<12}{'lam 方向':<10}{'lam 端点':<24}{'dt 方向':<10}{'dt 端点'}")
    for param, lo, hi, lab in scan_specs:
        sl, (l0, l1), _ = classify(param, lo, hi, 'lam')
        sd, (d0, d1), _ = classify(param, lo, hi, 'dt')
        print(f"  {lab:<12}{sl:<10}{f'{l0:.3f} -> {l1:.3f}':<24}"
              f"{sd:<10}{d0:.2f} -> {d1:.2f}")

    print("\n== 6) dt、eta/N 换单位与可行性守卫 ==")
    for c0, want in [(6, 7.40), (10, 5.90), (15, 4.60), (25, 3.22)]:
        rr = val('c0', float(c0))
        ok &= check(f'dt(c0={c0})', rr['dt'], want, 0.02)
    for th, wdt, wdev in [(0.05, 5.9, 4.44), (0.005, 60.7, 4.17)]:
        rr = val('eta', th)
        cc = curvature_factor(rr)
        print(f"    theta={th:<7g} max|q_c''|={cc['max_abs_qdd']:.4f}  "
              f"dt={rr['dt']:7.2f}(期望{wdt})  弦偏差={100 * cc['chord_dev']:.2f}%(期望{wdev})")

    bad = dict(BASE); bad['S0'] = 100.0; bad['I0'] = 1.0
    rb = solve(**bad)
    guard_ok = rb['status'] == 'no_initial_growth'
    ok &= guard_ok
    print(f"  {'OK ' if guard_ok else 'FAIL'} S0=100 < S_c=175.16 -> status={rb['status']}")

    print("\n==>", "全部通过" if ok else "存在 FAIL，请检查")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
