"""§8 占优分析的唯一口径与常数源。

全节采用**固定归一化初值**的纯理论口径：i0 = I0_city / N_city 跨 N_eff 固定，
不做任何逐 N 拟合。在该口径下引理"对 N 的标度不变性"无条件严格。

本模块只依赖 numpy/scipy，自包含、可直接运行自检：

    python caliber.py

TDINN 参照量取自 xian_control_comparison/xian_control_comparison_summary.csv，
作为该次疫情已发生结局的固定参照，不随 N_eff 重算。
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

# --------------------------------------------------------------------------
# 传播与背景控制参数（He et al. 2023 Table 1 + 第 7 节标定）
# --------------------------------------------------------------------------
BETA = 0.1498
GAMMA = 0.2953
Q0 = 0.3230
C0 = 12.8872

N_CITY = 13_163_000.0
# 第 7 节全市标定值（table/xian_initial_fit_table.tex 报 0.001007；
# 与 c0_sensitivity 的 full_city_I0_reference 同源）。
I0_CITY = 0.00100662823352
I0 = I0_CITY / N_CITY          # = 7.6474e-11，全节唯一归一化初值
S0 = 1.0 - I0

# --------------------------------------------------------------------------
# TDINN 固定参照（该次疫情的已发生结局，不随 N_eff 重算）
# --------------------------------------------------------------------------
IPEAK_T = 151.90363478987055
J_T = 49.35392946088784
ITCUM_T = 2096.757838966186
TEND_T = 45.272470642720634
IC_CUM_T = 605.4022667816286     # 社区累计
IQ_CUM_T = 1491.3555721845573    # 隔离累计（IC + IQ 精确等于 ITCUM_T）

# 最小相容易感池：由 dSq/dt = (1-beta)/beta * dIq_cum/dt 且 Sq 无回流，
# 该次疫情消耗的易感者总数 = Ic_cum + Iq_cum + Sq = Ic_cum + Iq_cum/beta，
# 与 N、c(t)、q(t) 及速率函数形式全无关。再由 S0 <= N 得 N_eff >= N_FLOOR。
N_FLOOR = IC_CUM_T + IQ_CUM_T / BETA          # = 10561.0

# --------------------------------------------------------------------------
# 归一化动力学导出量（均不含 N）
# --------------------------------------------------------------------------
B1 = C0 * (BETA + Q0 * (1.0 - BETA))          # ds/dt = -B1 * s * i
B2 = BETA * C0 * (1.0 - Q0)                   # di/dt =  B2 * s * i - gamma * i
S_C = GAMMA / B2                              # 背景临界易感分数
S_BAR = GAMMA * (1.0 - BETA) / (BETA * C0)    # 平台段渐近线
R_GROWTH = B2 * S0 - GAMMA                    # 初期指数增长率，约 1.011 /d


def i_of_s(s, i0=I0):
    """常规控制段的首次积分 i(s)。"""
    s0 = 1.0 - i0
    return i0 + (B2 / B1) * (s0 - s) + (GAMMA / B1) * np.log(s / s0)


def i_max_no(i0=I0):
    """常规控制（无干预）峰值分数 i_max^no。"""
    return i_of_s(S_C, i0)


def s_star(theta, i0=I0):
    """首次触碰 i = theta 时的易感分数 s^*。"""
    s0 = 1.0 - i0
    return brentq(lambda s: i_of_s(s, i0) - theta, S_C * (1.0 + 1e-12), s0 * (1.0 - 1e-14),
                  xtol=1e-17, rtol=8.9e-16)


def delta_t(theta, i0=I0):
    """平台控制时长（解析）。"""
    return (1.0 / (C0 * theta)) * np.log((s_star(theta, i0) - S_BAR) / (S_C - S_BAR))


def cost_J(theta, w_q=2.0, i0=I0):
    """二次加权成本 J（S 域解析积分；情景一 c == c0 故 J_c = 0）。"""
    ss = s_star(theta, i0)
    integrand = lambda s: ((1.0 - GAMMA / (BETA * C0 * s) - Q0) / (1.0 - Q0)) ** 2 / (s - S_BAR)
    value, _ = quad(integrand, S_C, ss, limit=500)
    return w_q / (C0 * theta) * value


# --------------------------------------------------------------------------
# 三段轨迹：t1 与清零尾段用 ODE 事件积分
#
# 不要对 1/(B1 * s * i(s)) 直接求积——尾段在 i -> 1/N 附近数值发散。
# --------------------------------------------------------------------------
def _rhs_routine(t, y):
    """常规控制段 (c=c0, q=q0)，状态 [s, i, ic_cum, iq_cum]。"""
    s, i, _, _ = y
    return [-B1 * s * i,
            B2 * s * i - GAMMA * i,
            BETA * C0 * (1.0 - Q0) * s * i,
            BETA * C0 * Q0 * s * i]


def _rhs_plateau(t, y):
    """平台段：i 恒为 theta，ds/dt = -c0*theta*(s - s_bar)。"""
    s, theta, _, _ = y
    q_c = 1.0 - GAMMA / (BETA * C0 * s)
    return [-C0 * theta * (s - S_BAR),
            0.0,
            GAMMA * theta,
            BETA * C0 * q_c * s * theta]


def solve(theta, N, i0=I0):
    """求解情景一阈值控制的三段轨迹，返回结构量与广延量。"""
    s0 = 1.0 - i0

    ev1 = lambda t, y: y[1] - theta
    ev1.terminal, ev1.direction = True, 1
    seg1 = solve_ivp(_rhs_routine, (0.0, 1e4), [s0, i0, 0.0, 0.0],
                     events=ev1, rtol=1e-11, atol=1e-16)
    if not seg1.t_events[0].size:
        raise RuntimeError(f"未触发阈值：theta={theta:g} 超出 i_max^no={i_max_no(i0):g}")
    t1 = float(seg1.t_events[0][0])
    y1 = seg1.y_events[0][0]
    ss = float(y1[0])

    ev2 = lambda t, y: y[0] - S_C
    ev2.terminal, ev2.direction = True, -1
    seg2 = solve_ivp(_rhs_plateau, (0.0, 1e6), [ss, theta, y1[2], y1[3]],
                     events=ev2, rtol=1e-12, atol=1e-16)
    dt_num = float(seg2.t_events[0][0])
    y2 = seg2.y_events[0][0]

    ev3 = lambda t, y: y[1] - 1.0 / N
    ev3.terminal, ev3.direction = True, -1
    seg3 = solve_ivp(_rhs_routine, (0.0, 1e6), [S_C, theta, y2[2], y2[3]],
                     events=ev3, rtol=1e-11, atol=1e-18)
    tail = float(seg3.t_events[0][0])
    y3 = seg3.y_events[0][0]

    h = float(y3[2] + y3[3])          # 到清零的总累计感染分数
    return {
        "theta": theta, "N": N, "eta": theta * N,
        "t1": t1, "delta_t": dt_num, "delta_t_analytic": delta_t(theta, i0),
        "tail": tail, "t_end": t1 + dt_num + tail,
        "s_star": ss, "s_end": float(y3[0]),
        "h": h, "Itcum": N * h, "J": cost_J(theta, i0=i0),
    }


# --------------------------------------------------------------------------
# 边界求解
# --------------------------------------------------------------------------
def theta_cost(w_q=2.0, i0=I0):
    """等成本阈值：J(theta_cost) = J^T。"""
    return brentq(lambda th: cost_J(th, w_q, i0) - J_T, 1e-5, 0.05, xtol=1e-16, rtol=8.9e-16)


def theta_dur(t_max, i0=I0):
    """等时长阈值：Delta t(theta_dur) = T_max。"""
    return brentq(lambda th: delta_t(th, i0) - t_max, 1e-5, 0.05, xtol=1e-16, rtol=8.9e-16)


def theta_bind(t_max=np.inf, w_q=2.0, i0=I0):
    """绑定阈值 max(theta_cost, theta_dur(T_max))；T_max=inf 时即 theta_cost。"""
    tc = theta_cost(w_q, i0)
    return tc if not np.isfinite(t_max) else max(tc, theta_dur(t_max, i0))


def N_star(t_max=np.inf, w_q=2.0, i0=I0):
    """临界有效人口 N*(T_max) = I_peak^T / theta_bind(T_max)。

    注意 theta_dur 随 T_max 递减，故 T_max 大于约 103 d 后成本约束绑定，
    N*(T_max) 封顶于 N*_inf；直接用 I_peak^T/theta_dur 会给出超出上限的错值。
    """
    return IPEAK_T / theta_bind(t_max, w_q, i0)


def N_clr(eta, i0=I0):
    """清零边界：t_end(eta/N, N) = t_end^T 的解 N。"""
    lo = np.log10(eta / (i_max_no(i0) * 0.995))
    return 10.0 ** brentq(lambda lg: solve(eta / 10 ** lg, 10 ** lg, i0)["t_end"] - TEND_T,
                          lo, 5.0, xtol=1e-12)


def N_cum(eta, i0=I0):
    """累计边界：N * h(eta/N, N) = Itcum^T 的解 N。"""
    lo = max(3.0, np.log10(eta / (i_max_no(i0) * 0.995)))
    return 10.0 ** brentq(lambda lg: solve(eta / 10 ** lg, 10 ** lg, i0)["Itcum"] - ITCUM_T,
                          lo, 5.5, xtol=1e-12)


def N_cum_star(w_q=2.0, i0=I0):
    """累计弧与成本线的交点 N*_cum,inf。"""
    th = theta_cost(w_q, i0)
    return 10.0 ** brentq(lambda lg: solve(th, 10 ** lg, i0)["Itcum"] - ITCUM_T,
                          3.5, 5.0, xtol=1e-13)


ETA_GRID = (10.0, 15.0, 20.0, 27.89, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, IPEAK_T)

# --------------------------------------------------------------------------
# beta 稳健性：沿可识别脊 beta*c0 = const 扫描
#
# 数据只识别乘积 beta*c0（沿脊 RMSE 恒定），故 beta 不可单独变动。沿脊缩放
# c_TDINN(t) 时 TDINN 参照量近似不变：I_peak^T、Itcum^T、Iq_cum^T 的残留约
# 1e-3（因 dS/dt 中的 c*q*(1-beta) 项不只以 beta*c 形式出现，脊缩放消不掉，
# 残留量级即 S/N 偏离 1 的量级）；J^T 严格不变（接触项 (1-c/c0)^2 在 c0 与
# c(t) 共同缩放下不变，且到 t_end 时被积函数已归零）。
# --------------------------------------------------------------------------
RIDGE = BETA * C0          # = 1.9305，可识别的乘积


def _ridge_scope(beta):
    """把模块级 beta/c0 及其导出量临时切到脊上的另一点。"""
    global BETA, C0, B1, B2, S_C, S_BAR, N_FLOOR
    saved = (BETA, C0, B1, B2, S_C, S_BAR, N_FLOOR)
    BETA, C0 = beta, RIDGE / beta
    B1 = C0 * (BETA + Q0 * (1.0 - BETA))
    B2 = BETA * C0 * (1.0 - Q0)
    S_C = GAMMA / B2
    S_BAR = GAMMA * (1.0 - BETA) / (BETA * C0)
    N_FLOOR = IC_CUM_T + IQ_CUM_T / BETA
    return saved


def _ridge_restore(saved):
    global BETA, C0, B1, B2, S_C, S_BAR, N_FLOOR
    BETA, C0, B1, B2, S_C, S_BAR, N_FLOOR = saved


def beta_sweep(betas=(0.10, 0.12, 0.1498, 0.20, 0.25, 0.30), w_q=2.0):
    """沿脊扫 beta，返回 (beta, c0, theta_cost, N*_inf, N_floor, 比值) 行。"""
    rows = []
    for b in betas:
        saved = _ridge_scope(b)
        try:
            tc = theta_cost(w_q)
            rows.append((b, C0, tc, IPEAK_T / tc, N_FLOOR, (IPEAK_T / tc) / N_FLOOR))
        finally:
            _ridge_restore(saved)
    return rows


def _self_check():
    print(f"i0 = {I0:.6e}   s_c = {S_C:.9f}   s_bar = {S_BAR:.9f}   r = {R_GROWTH:.4f} /d")
    print(f"i_max^no = {i_max_no():.6f}")
    print(f"N_floor  = {N_FLOOR:.1f}   (旧下界 Itcum^T = {ITCUM_T:.2f}，偏松 {N_FLOOR/ITCUM_T:.2f} 倍)")

    # 第 7 节报 t1=16.90, dt=85.07, t_end=258.11。其 solve_flat_control 对绝对 I
    # 用 atol=1e-4 而 I0 约 1e-3，故 t1/t_end 带约 0.005 d 的积分容差；本模块在
    # 归一化变量上用 atol=1e-16，数值更准（早期指数解 ln(theta/i0)/r = 16.88 d
    # 加 s 消耗减速修正，与 16.897 相符）。两者四舍五入均为 16.90。
    print("\n[1] 全局自检 (theta=0.002)：应给出 t1=16.90, dt=85.07, t_end=258.10")
    r = solve(0.002, N_CITY)
    print(f"    t1={r['t1']:.4f}  dt={r['delta_t']:.4f}  t_end={r['t_end']:.3f}  J={r['J']:.4f}")
    assert abs(r["t1"] - 16.90) < 0.01, r["t1"]
    assert abs(r["delta_t"] - 85.07) < 0.01, r["delta_t"]
    assert abs(r["t_end"] - 258.10) < 0.02, r["t_end"]
    assert abs(r["J"] - 40.7687) < 1e-3, r["J"]

    print("\n[2] t1 与 dt 跨 N_eff 严格不变：")
    for N in (5e4, 2e5, N_CITY):
        r = solve(0.002, N)
        print(f"    N={N:12,.0f}  t1={r['t1']:.6f}  dt={r['delta_t']:.6f}  t_end={r['t_end']:.3f}")

    print("\n[3] 直线族边界（口径统一后不应改变）：")
    tc = theta_cost()
    print(f"    theta_cost   = {tc:.6e}")
    for T in (45.0, 60.0, 90.0, 150.0):
        print(f"    theta_dur({T:5.0f}d) = {theta_dur(T):.6e}   theta_bind = {theta_bind(T):.6e}"
              f"   N*({T:5.0f}d) = {N_star(T):.4e}")
    print(f"    {'':21}theta_bind = {tc:.6e}   N*_inf     = {N_star():.4e}")
    T_switch = brentq(lambda T: theta_dur(T) - tc, 30.0, 400.0)
    print(f"    时长/成本绑定切换点 T_max = {T_switch:.1f} d（大于它则成本绑定，N* 封顶于 N*_inf）")
    print(f"    成本边界处平台时长 Delta t(theta_cost) = {delta_t(tc):.2f} d")
    assert abs(tc - 1.656e-3) < 1e-6 and abs(N_star() - 9.17e4) < 1e3
    assert abs(N_star(45.0) - 4.04e4) < 5e2 and abs(N_star(90.0) - 8.03e4) < 5e2
    assert N_star(150.0) == N_star(), "T_max=150d 应由成本绑定"

    print("\n[4] 主结论区间：")
    print(f"    N_eff in [{N_FLOOR:.1f}, {IPEAK_T/tc:.1f}]   宽 {IPEAK_T/tc/N_FLOOR:.3f} 倍")
    ncs = N_cum_star()
    print(f"    N*_cum,inf = {ncs:.1f} (eta={tc*ncs:.3f})   纳入累计后 [{N_FLOOR:.0f}, {ncs:.0f}]，宽 {ncs/N_FLOOR:.3f} 倍")

    print("\n[5] 两条弧：")
    print(f"    {'eta':>8} {'N_clr':>10} {'N_cum':>10}")
    for eta in ETA_GRID:
        print(f"    {eta:8.2f} {N_clr(eta):10.1f} {N_cum(eta):10.1f}")
    print(f"    清零弧全段最大值 {N_clr(IPEAK_T):.1f} < N_floor {N_FLOOR:.1f}  ->  清零占优区为空集")

    print(f"\n[6] beta 稳健性（沿脊 beta*c0 = {RIDGE:.4f}）：")
    print(f"    {'beta':>6} {'c0':>8} {'theta_cost':>12} {'N*_inf':>11} {'N_floor':>10} {'N*/N_floor':>11}")
    ratios = []
    for b, c0, tc, ns, nf, ratio in beta_sweep():
        ratios.append(ratio)
        print(f"    {b:6.4f} {c0:8.4f} {tc:12.8f} {ns:11.1f} {nf:10.1f} {ratio:11.4f}")
    spread = (max(ratios) - min(ratios)) / np.mean(ratios)
    print(f"    比值区间 [{min(ratios):.4f}, {max(ratios):.4f}]，极差 {spread*100:.2f}%")
    print("    注：这是所考察范围内的数值发现，非精确恒等式——beta*N* 与 beta*N_floor")
    print("        各自随 beta 漂移约 7.6%/7.8%，两者都不是严格 ∝ 1/beta。")
    assert spread < 0.01

    print("\n全部自检通过。")


if __name__ == "__main__":
    _self_check()
