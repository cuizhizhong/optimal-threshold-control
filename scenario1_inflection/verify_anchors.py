"""
拐点分析数值锚点复现校验。所有写进论文的数值/方向都必须在这里通过。

运行：conda run --no-capture-output -n thesis python verify_anchors.py

覆盖：
  1) N=763 基准锚点（含相对位置 lam）；
  2) 西安实例：q_inf=0.4119、弦偏差≈9.6%（论文 §4.4 脚注引用）；
  3) 方向表：lam 与 dt 对 beta/q0/c0/theta 的单调性（定稿 §4.3 正文与分工表）；
  4) dt 对 c0（>=6）递减、eta/N 换单位下的曲率与弦偏差；
  5) S0>S_c 守卫。
"""
import numpy as np
from inflection_analysis import solve, curvature_factor, _chord_dev, G_MAX, X_GMAX

BASE = dict(beta=0.155, gamma=0.3504, c0=10.0, q0=0.01526,
            eta=0.05 * 763, N=763.0, S0=762.0, I0=1.0)

# 西安主基准（取自 xian_control_comparison/xian_control_comparison.py 与初值拟合表）
XIAN = dict(beta=0.1498, gamma=0.2953, c0=12.8872, q0=0.3230,
            eta=0.002 * 13163000.0, N=13163000.0,
            S0=13163000.0 - 0.001007, I0=0.001007)


def val(param, v, base=BASE):
    """param='eta' 时 v 是 theta=eta/N，其余为参数本身。"""
    p = dict(base)
    p[param] = v * p['N'] if param == 'eta' else v
    return solve(**p)


def check(name, got, want, tol):
    ok = abs(got - want) < tol
    print(f"  {'OK ' if ok else 'FAIL'} {name:24s} = {got:12.5f}  (期望 {want})")
    return ok


def classify(param, lo, hi, key, base=BASE, n=241, tol=1e-9):
    """在 [lo,hi] 上扫 param，返回 (方向符号, 端点值, 采样数)。
    方向：'+' 单调增, '-' 单调减, '±' 非单调, '×' 无变化。"""
    xs, ys = [], []
    for v in np.linspace(lo, hi, n):
        r = val(param, v, base)
        if r['status'] != 'ok':
            continue
        y = r.get(key, np.nan)
        if y is None or not np.isfinite(y):
            continue
        xs.append(v); ys.append(y)
    if len(ys) < 3:
        return '?', (np.nan, np.nan), len(ys)
    d = np.diff(np.array(ys))
    up, dn = (d > tol).any(), (d < -tol).any()
    sign = '±' if (up and dn) else ('+' if up else ('-' if dn else '×'))
    return sign, (ys[0], ys[-1]), len(ys)


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
    print(f"  {'OK ' if abs(r['seg_high']+r['seg_low']-r['dt'])<1e-9 else 'FAIL'} 两段之和 = dt")
    cf = curvature_factor(r)
    err = np.max(np.abs(cf['scale'] * cf['g'] - cf['qdd']))
    ok &= err < 1e-12
    print(f"  {'OK ' if err<1e-12 else 'FAIL'} q_c'' 因子分解误差 = {err:.2e}")
    print(f"       |g| 上界 = {G_MAX:.5f} 于 x = {X_GMAX[0]:.4f}, {X_GMAX[1]:.4f}")
    ok &= check('chord_dev(%)', 100 * _chord_dev(r), 4.4, 0.15)

    print("\n== 2) 西安实例（§4.4 脚注引用）==")
    rx = solve(**XIAN)
    assert rx['status'] == 'ok', rx['status']
    ok &= check('q_inf', rx['q_inf'], 0.4119, 1e-4)
    ok &= check('q_max=q_c(t1)', rx['q_max'], 0.8454, 1e-3)
    ok &= check('chord_dev(%)', 100 * _chord_dev(rx), 9.6, 0.1)

    print("\n== 3) 方向表：lam 与 dt（可行且有拐点的区间上）==")
    specs = [('beta', 0.065, 0.50, 'beta'), ('q0', 0.0, 0.39, 'q0'),
             ('c0', 4.2, 16.0, 'c0'), ('eta', 0.0135, 0.05, 'theta=eta/N')]
    print(f"  {'参数':<12}{'lam 方向':<10}{'lam 端点':<24}{'dt 方向':<10}{'dt 端点'}")
    for param, lo, hi, lab in specs:
        sl, (l0, l1), nl = classify(param, lo, hi, 'lam')
        sd, (d0, d1), nd = classify(param, lo, hi, 'dt')
        print(f"  {lab:<12}{sl:<10}{f'{l0:.3f} -> {l1:.3f}':<24}{sd:<10}{d0:.2f} -> {d1:.2f}")

    print("\n  PLAN_FINAL §5 的具体端点复核：")
    for param, a, b, lab in [('beta', 0.10, 0.25, 'beta'), ('c0', 5.0, 15.0, 'c0'),
                             ('eta', 0.02, 0.05, 'theta'), ('q0', 0.02, 0.30, 'q0')]:
        ra, rb = val(param, a), val(param, b)
        print(f"    {lab:<7} {a:g} -> {b:g}: lam {ra['lam']:.3f} -> {rb['lam']:.3f}")

    print("\n  低 beta 背景 (beta=0.10) 下 q0 的非单调性：")
    lowb = dict(BASE); lowb['beta'] = 0.10
    s, (y0, y1), n = classify('q0', 0.0, 0.39, 'lam', base=lowb)
    print(f"    q0 方向 = {s}   lam {y0:.3f} -> {y1:.3f}  (采样 {n})")
    lams = []
    for v in np.linspace(0.0, 0.39, 14):
        rr = val('q0', v, lowb)
        lams.append((v, rr['lam'] if rr['status'] == 'ok' else np.nan))
    print('    ' + '  '.join(f'{v:.2f}:{l:.3f}' for v, l in lams if np.isfinite(l)))

    print("\n== 4) dt 对 c0（>=6）与 eta/N 换单位 ==")
    for c0, want in [(6, 7.40), (10, 5.90), (15, 4.60), (25, 3.22)]:
        rr = val('c0', float(c0))
        ok &= check(f'dt(c0={c0})', rr['dt'], want, 0.02)
    for th, wdt, wdev in [(0.05, 5.9, 4.44), (0.005, 60.7, 4.17)]:
        rr = val('eta', th)
        cc = curvature_factor(rr)
        print(f"    theta={th:<7g} max|q_c''|={cc['max_abs_qdd']:.4f}  "
              f"dt={rr['dt']:7.2f}(期望{wdt})  弦偏差={100*cc['chord_dev']:.2f}%(期望{wdev})")

    print("\n== 5) S0>S_c 守卫 ==")
    bad = dict(BASE); bad['S0'] = 100.0; bad['I0'] = 1.0
    rb = solve(**bad)
    good = rb['status'] == 'no_initial_growth'
    ok &= good
    print(f"  {'OK ' if good else 'FAIL'} S0=100 < S_c=175.16 -> status={rb['status']}")

    print("\n==>", "全部通过" if ok else "存在 FAIL，请检查")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
