"""
情景一阈值控制律 q_c(t) 的拐点分析：参考实现。

核心事实（全部只用论文已有记号 beta, q0, c0, eta, N, S*, S_c, Sbar）：
  1. 拐点隔离强度   q_inf = 1 - 1/(2(1-beta))            只由 beta 决定
  2. 内部拐点存在   <=>  q0 < q_inf < q_max              等价于 S_c < 2*Sbar < S*
  3. 两段时长       前段 = (N/(c0*eta)) * ln((S*-Sbar)/Sbar)
                    后段 = (N/(c0*eta)) * ln(Sbar/(S_c-Sbar))   <- 只含 S_c, Sbar
  4. 二阶导分解     q_c'' = (c0*eta/N)^2 / (1-beta) * g(x),  x = S/Sbar
                    g(x) = (x-1)(2-x)/x^3,  g(2)=0(拐点), max|g| = 1/(6*sqrt3) 于 x=3±sqrt3

用法见文件末尾 __main__。MATLAB 移植：Lambert W_{-1} 用 lambertw(-1, z)。
"""
import numpy as np
from scipy.special import lambertw
from scipy.optimize import brentq, minimize_scalar

SQRT3 = np.sqrt(3.0)
G_MAX = 1.0 / (6.0 * SQRT3)          # |g(x)| 的上界 ≈ 0.09623
X_GMAX = (3.0 - SQRT3, 3.0 + SQRT3)  # g 的极值点 ≈ 1.2679, 4.7321


# ----------------------------------------------------------------------
# 单组参数求解
# ----------------------------------------------------------------------
def solve(beta, gamma, c0, q0, eta, N, S0, I0):
    """求情景一阈值控制的关键量；不可行时返回 status != 'ok'。"""
    den = beta + q0 * (1.0 - beta)
    a = beta * (1.0 - q0) / den
    rho1 = gamma * N / (c0 * den)
    S_c = gamma * N / (beta * c0 * (1.0 - q0))
    S_bar = gamma * N * (1.0 - beta) / (beta * c0)
    C0 = I0 + a * S0 - rho1 * np.log(S0)

    out = dict(beta=beta, gamma=gamma, c0=c0, q0=q0, eta=eta, N=N,
               S0=S0, I0=I0,
               S_c=S_c, S_bar=S_bar, R0=beta * c0 * (1 - q0) * S0 / (gamma * N),
               q_inf=1.0 - 1.0 / (2.0 * (1.0 - beta)))

    # 可行性：初值须处于增长支（否则常规控制轨道不会先上升再触线）
    if not (S0 > S_c):
        out['status'] = 'no_initial_growth'
        return out

    # 可行性：常规控制峰值须越过 eta，且初值未越线
    I_max_no = I0 + a * (S0 - S_c) + rho1 * np.log(S_c / S0)
    out['I_max_no'] = I_max_no
    if not (I_max_no > eta and I0 < eta):
        out['status'] = 'no_crossing'
        return out

    arg = -np.exp(-(C0 - eta) / rho1) / S_c
    if arg <= -np.exp(-1.0) or arg >= 0.0:
        out['status'] = 'lambert_out_of_range'
        return out
    S_star = -S_c * np.real(lambertw(arg, -1))
    if not (S_c < S_star <= S0):
        out['status'] = 'S_star_invalid'
        return out

    q_max = 1.0 - gamma * N / (beta * c0 * S_star)
    rate = c0 * eta / N                       # S-Sbar 的指数衰减率
    dt = np.log((S_star - S_bar) / (S_c - S_bar)) / rate

    out.update(S_star=S_star, q_max=q_max, rate=rate, dt=dt, status='ok')

    # ---- 拐点：q_c 经过 q_inf 的时刻 ----
    q_inf = out['q_inf']
    if q_inf <= q0:
        # 2*Sbar <= S_c：控制期内恒有 S >= 2Sbar，故 q_c'' < 0 全程
        out.update(has_inflection=False, exit_side='t2',
                   regime='全程加速释放 (q_c\'\'<0)', t_inf=np.nan,
                   seg_high=np.nan, seg_low=np.nan,
                   lam=np.nan, seg_high_frac=np.nan)
    elif q_inf >= q_max:
        out.update(has_inflection=False, exit_side='t1',
                   regime='全程减速释放 (q_c\'\'>0)', t_inf=np.nan,
                   seg_high=np.nan, seg_low=np.nan,
                   lam=np.nan, seg_high_frac=np.nan)
    else:
        seg_high = np.log((S_star - S_bar) / S_bar) / rate   # t_inf - t1
        seg_low = np.log(S_bar / (S_c - S_bar)) / rate       # t2 - t_inf
        # lam = 拐点相对位置 (t_inf-t1)/(t2-t1)；->0 靠 t1，->1 靠 t2
        out.update(has_inflection=True, exit_side=None,
                   regime='存在内部拐点', t_inf=seg_high,
                   seg_high=seg_high, seg_low=seg_low,
                   lam=seg_high / dt, seg_high_frac=seg_high / dt)
    return out


# ----------------------------------------------------------------------
# 解析参数敏感性
# ----------------------------------------------------------------------
def startup_sensitivities(res):
    """返回启动点 S* 对 eta、c0、beta、q0、theta=eta/N 的解析偏导。

    这里只要求常规控制轨道发生非退化首次触碰，即 ``res['status']=='ok'``；
    启动点的偏导不要求控制期内存在内部拐点。
    """
    if res.get('status') != 'ok':
        raise ValueError("startup_sensitivities 要求 res['status']=='ok'")

    beta, gamma = res['beta'], res['gamma']
    c0, q0 = res['c0'], res['q0']
    N, S0 = res['N'], res['S0']
    S_star, S_c, S_bar = res['S_star'], res['S_c'], res['S_bar']

    den = beta + q0 * (1.0 - beta)
    rho1 = gamma * N / (c0 * den)
    inv_gap = 1.0 / S_star - 1.0 / S_c  # 严格为负
    pos_gap = -inv_gap                   # 严格为正

    dS_deta = 1.0 / (rho1 * inv_gap)
    dS_dc0 = np.log(S_star / S0) / (c0 * inv_gap)
    dS_dbeta = (
        q0 * (1.0 - q0) * (S0 - S_star) / den ** 2
        - rho1 * (1.0 - q0) * np.log(S_star / S0) / den
    ) / (rho1 * pos_gap)
    dS_dq0 = -(
        beta * ((S0 - S_star) - S_bar * np.log(S0 / S_star))
    ) / (den ** 2 * rho1 * pos_gap)

    return dict(
        dS_deta=dS_deta,
        dS_dc0=dS_dc0,
        dS_dbeta=dS_dbeta,
        dS_dq0=dS_dq0,
        dS_dtheta=N * dS_deta,
    )


def lambda_sensitivities(res):
    """返回内部拐点相对位置 lambda 的解析偏导与 q0 驻点残差。

    ``q0_stationarity_residual`` 是 lambda_q0 的正分母省略后的分子，
    因而与 ``dlambda_dq0`` 同号。A、B 仅在本函数内部用于缩短计算。
    """
    if res.get('status') != 'ok':
        raise ValueError("lambda_sensitivities 要求 res['status']=='ok'")
    if not res.get('has_inflection', False):
        raise ValueError("lambda_sensitivities 要求存在内部拐点")

    beta, q0 = res['beta'], res['q0']
    c0, N = res['c0'], res['N']
    S_star, S_c, S_bar = res['S_star'], res['S_c'], res['S_bar']
    ds = startup_sensitivities(res)

    den = beta + q0 * (1.0 - beta)
    A = np.log((S_star - S_bar) / S_bar)
    B = np.log(S_bar / (S_c - S_bar))
    lambda_den = (A + B) ** 2

    dA_deta = ds['dS_deta'] / (S_star - S_bar)
    dA_dc0 = (ds['dS_dc0'] + S_star / c0) / (S_star - S_bar)
    dA_dbeta = (
        ds['dS_dbeta'] + S_star / (beta * (1.0 - beta))
    ) / (S_star - S_bar)
    dA_dq0 = ds['dS_dq0'] / (S_star - S_bar)

    dB_dbeta = -1.0 / ((1.0 - beta) * den)
    dB_dq0 = -1.0 / ((1.0 - q0) * den)

    dlambda_deta = B * dA_deta / lambda_den
    dlambda_dc0 = B * dA_dc0 / lambda_den
    dlambda_dbeta = (B * dA_dbeta - A * dB_dbeta) / lambda_den
    q0_stationarity_residual = B * dA_dq0 - A * dB_dq0
    dlambda_dq0 = q0_stationarity_residual / lambda_den

    return dict(
        dlambda_deta=dlambda_deta,
        dlambda_dc0=dlambda_dc0,
        dlambda_dbeta=dlambda_dbeta,
        dlambda_dq0=dlambda_dq0,
        dlambda_dtheta=N * dlambda_deta,
        q0_stationarity_residual=q0_stationarity_residual,
    )


def find_q0_stationary_points(base, q0_bounds=(0.0, 0.39), n=2001,
                              near_zero_tol=1e-7, dedupe_tol=1e-7):
    """在指定 q0 区间内搜索 lambda(q0) 的数值驻点。

    变号区间用 Brent 法精化；未变号的 |残差| 局部极小点用有界最小化
    检查，并仅作为 ``candidates`` 返回。该搜索不构成驻点完备性证明。
    """
    lo, hi = map(float, q0_bounds)
    if not (lo < hi and n >= 3):
        raise ValueError("q0_bounds 必须递增且 n>=3")

    def residual_at(q0):
        p = dict(base)
        p['q0'] = float(q0)
        r = solve(**p)
        if r.get('status') != 'ok' or not r.get('has_inflection', False):
            return np.nan
        return float(lambda_sensitivities(r)['q0_stationarity_residual'])

    def append_unique(values, value):
        if not any(abs(value - old) <= dedupe_tol for old in values):
            values.append(float(value))

    xs = np.linspace(lo, hi, int(n))
    ys = np.array([residual_at(x) for x in xs], dtype=float)
    roots = []

    for i in range(len(xs) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 * y1 < 0.0:
            root = brentq(residual_at, xs[i], xs[i + 1], xtol=1e-13, rtol=1e-13)
            append_unique(roots, root)
    # 若根恰落在采样点上，仅在两侧残差异号时将其作为变号根处理。
    for i in range(1, len(xs) - 1):
        ym, y0, yp = ys[i - 1], ys[i], ys[i + 1]
        if not (np.isfinite(ym) and np.isfinite(y0) and np.isfinite(yp)):
            continue
        if abs(y0) <= 1e-14 and ym * yp < 0.0:
            root = brentq(residual_at, xs[i - 1], xs[i + 1],
                          xtol=1e-13, rtol=1e-13)
            append_unique(roots, root)

    candidates = []
    for i in range(1, len(xs) - 1):
        ym, y0, yp = ys[i - 1], ys[i], ys[i + 1]
        if not (np.isfinite(ym) and np.isfinite(y0) and np.isfinite(yp)):
            continue
        if ym * yp <= 0.0:
            continue
        if not (abs(y0) <= abs(ym) and abs(y0) <= abs(yp)):
            continue

        def objective(q):
            value = residual_at(q)
            return abs(value) if np.isfinite(value) else np.inf

        opt = minimize_scalar(objective, bounds=(xs[i - 1], xs[i + 1]),
                              method='bounded', options={'xatol': 1e-13})
        if not opt.success or not np.isfinite(opt.fun) or opt.fun > near_zero_tol:
            continue
        q_candidate = float(opt.x)
        if any(abs(q_candidate - root) <= dedupe_tol for root in roots):
            continue
        if any(abs(q_candidate - old[0]) <= dedupe_tol for old in candidates):
            continue
        candidates.append((q_candidate, float(opt.fun)))

    return dict(
        roots=sorted(roots),
        candidates=sorted(candidates),
        q0_bounds=(lo, hi),
        sample_count=int(n),
        near_zero_tol=float(near_zero_tol),
    )


def trajectory(res, n=2000):
    """返回控制期内 (t-t1, S, q_c, q_c', q_c'')；res 须为 solve() 的 status=='ok' 输出。"""
    beta, gamma, c0, q0 = res['beta'], res['gamma'], res['c0'], res['q0']
    eta, N = res['eta'], res['N']
    S_bar, S_star, rate = res['S_bar'], res['S_star'], res['rate']
    t = np.linspace(0.0, res['dt'], n)
    S = S_bar + (S_star - S_bar) * np.exp(-rate * t)
    qc = 1.0 - gamma * N / (beta * c0 * S)
    qd = -(gamma * eta / beta) * (S - S_bar) / S ** 2
    qdd = (gamma * c0 * eta ** 2 / (beta * N)) * (S - S_bar) * (2 * S_bar - S) / S ** 3
    return t, S, qc, qd, qdd


def curvature_factor(res, n=2000):
    """把 q_c'' 拆成 时间尺度因子 * 形状因子 g(x)，并给出走过的 x 范围。"""
    t, S, _, _, qdd = trajectory(res, n)
    x = S / res['S_bar']
    g = (x - 1.0) * (2.0 - x) / x ** 3
    scale = (res['c0'] * res['eta'] / res['N']) ** 2 / (1.0 - res['beta'])
    return dict(t=t, x=x, g=g, scale=scale, qdd=qdd,
                x_range=(x.min(), x.max()),
                max_abs_qdd=np.max(np.abs(qdd)),
                chord_dev=_chord_dev(res, n))


def _chord_dev(res, n=2000):
    """q_c 偏离首尾直线的最大值，占总落差的比例（衡量视觉线性度）。"""
    t, _, qc, _, _ = trajectory(res, n)
    drop = qc[0] - res['q0']
    chord = qc[0] - drop * t / res['dt']
    return np.max(np.abs(qc - chord)) / drop


# ----------------------------------------------------------------------
# 参数扫描
# ----------------------------------------------------------------------
def scan(param, values, base):
    """沿单个参数扫描，返回记录列表。base 为 solve() 的关键字参数字典。"""
    rows = []
    for v in values:
        p = dict(base)
        p[param] = v
        r = solve(**p)
        r['scan_param'] = param
        r['scan_value'] = v
        if r['status'] == 'ok':
            r['chord_dev'] = _chord_dev(r)
        rows.append(r)
    return rows


FIELDS = ['scan_param', 'scan_value', 'status', 'R0', 'S_star', 'S_c', 'S_bar',
          'q0', 'q_inf', 'q_max', 'has_inflection', 'regime', 'exit_side',
          'dt', 'seg_high', 'seg_low', 'lam', 'seg_high_frac', 'chord_dev']


def to_csv(rows, path):
    import csv
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in FIELDS})


# ----------------------------------------------------------------------
# 自检：与已核对的数值锚点比对
# ----------------------------------------------------------------------
def selftest():
    base = dict(beta=0.155, gamma=0.3504, c0=10.0, q0=0.01526,
                eta=0.05 * 763, N=763.0, S0=762.0, I0=1.0)
    r = solve(**base)
    chk = [
        ('S_star', r['S_star'], 708.3470, 1e-3),
        ('S_c', r['S_c'], 175.1602, 1e-3),
        ('q_max', r['q_max'], 0.7565, 1e-3),
        ('q_inf', r['q_inf'], 0.40828, 1e-4),
        ('dt', r['dt'], 5.9026, 1e-3),
        ('seg_high', r['seg_high'], 2.7013, 1e-3),
        ('seg_low', r['seg_low'], 3.2012, 1e-3),
    ]
    ok = True
    for name, got, want, tol in chk:
        good = abs(got - want) < tol
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {name:10s} = {got:12.5f}  (期望 {want})")
    # 两段之和 = dt
    print(f"  {'OK ' if abs(r['seg_high']+r['seg_low']-r['dt'])<1e-9 else 'FAIL'} 两段之和 = dt")
    # 二阶导分解一致性
    cf = curvature_factor(r)
    err = np.max(np.abs(cf['scale'] * cf['g'] - cf['qdd']))
    print(f"  {'OK ' if err<1e-12 else 'FAIL'} q_c''分解误差 = {err:.2e}")
    # g 的理论极值
    print(f"  形状因子 |g| 上界 = {G_MAX:.5f} 于 x = {X_GMAX[0]:.4f}, {X_GMAX[1]:.4f}")
    print(f"  本例走过 x = S/Sbar ∈ [{cf['x_range'][0]:.3f}, {cf['x_range'][1]:.3f}]")
    print(f"  偏离首尾直线 = {100*cf['chord_dev']:.1f}% (总落差)")
    # eta/N 抵消检验
    print("\n  eta/N 抵消检验（弯曲程度应基本不变）：")
    for th in [0.05, 0.02, 0.005, 0.001, 0.0002]:
        p = dict(base); p['eta'] = th * 763
        rr = solve(**p)
        if rr['status'] != 'ok':
            print(f"    eta/N={th:<7g} status={rr['status']}（不可行，跳过）")
            continue
        cc = curvature_factor(rr)
        print(f"    eta/N={th:<7g} max|q_c''|={cc['max_abs_qdd']:.2e}  "
              f"dt={rr['dt']:8.1f}天  偏离直线={100*cc['chord_dev']:.1f}%")
    return ok


if __name__ == '__main__':
    print("=== 自检 ===")
    selftest()
