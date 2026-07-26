"""情景一阈值控制相对 TDINN 控制的占优区域图，以及 TDINN 基准的 N 不变性复核。

对应主论文 §"占优区域" 的 Algorithm 与局限第 (2) 条。

阈值侧完全自洽（只依赖解析标度公式，不需要数据文件），可直接运行生成图。
TDINN 基准默认取常数 (I_peak^T, J^T, cum_T)=(151.90, 49.35, 2096.76)；若在你的仓库里运行，
可用 --recompute-tdinn 通过 xcc/eps/tla 逐 N 重算并做不变性复核。

用法:
    python dominance_region.py                 # 用默认 TDINN 常数出图
    python dominance_region.py --recompute-tdinn   # 复核 TDINN 基准（需数据与模块）
"""
from __future__ import annotations
import argparse
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import quad

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ----------------------------------------------------------------------
# 1. 西安参数与只依赖 theta=eta/N 的解析标度量（无量纲侧，记 sigma=S/N）
# ----------------------------------------------------------------------
BETA, GAMMA, C0, Q0 = 0.1498, 0.2953, 12.8872, 0.3230
S0_FRAC, I0_FRAC = 1.0, 0.0          # 归一化初值 s0=S0/N, i0=I0/N（可改）

H      = BETA + Q0 * (1 - BETA)
A      = BETA * (1 - Q0) / H          # = beta2^0/beta1^0
RHO1N  = GAMMA / (C0 * H)             # 无量纲 rho1 = rho1_dim / N = a * sigma_c
KAPPA  = GAMMA / (BETA * C0)
SIG_BAR = KAPPA * (1 - BETA)          # \bar S / N
SIG_C   = KAPPA / (1 - Q0)            # S_c   / N
IOTA    = I0_FRAC + A * (S0_FRAC - SIG_C) + RHO1N * np.log(SIG_C / S0_FRAC)  # I_max^no / N

# TDINN 基准（默认常数；--recompute-tdinn 可覆盖）。
# 到清零口径下的西安全市重拟合值（近似锚定，非严格不变，见局限）。
TDINN = dict(peak=151.90, J=49.35, cum=2096.76)


def sigma_star(theta: float) -> float:
    """归一化干预启动点 S*/N，唯一根（= Lambert W_{-1} 分支）。"""
    f = lambda s: A * (1 - s) + RHO1N * np.log(s) - (theta - I0_FRAC)
    return brentq(f, SIG_C * (1 + 1e-12), 1 - 1e-13)


def Dt(theta: float) -> float:
    ss = sigma_star(theta)
    return np.log((ss - SIG_BAR) / (SIG_C - SIG_BAR)) / (C0 * theta)


def Jcost(theta: float) -> float:
    """二次加权成本 J，w_c=1,w_q=2（情景一 c≡c0 故只剩 q 项）。"""
    ss = sigma_star(theta)
    integrand = lambda s: 2.0 * ((1 - KAPPA / s - Q0) / (1 - Q0)) ** 2 / (s - SIG_BAR)
    val, _ = quad(integrand, SIG_C, ss, limit=200)
    return val / (C0 * theta)


def h_t2(theta: float) -> float:
    """到 t2 的累计感染分数 I_{t2,cum}/N（theta-only，对应 eff-pop 笔记 It2,cum/N 列）。"""
    ss = sigma_star(theta)
    pre  = (BETA / H) * (S0_FRAC - ss)
    plat = BETA * ((ss - SIG_C) + SIG_BAR * np.log((ss - SIG_BAR) / (SIG_C - SIG_BAR)))
    return pre + plat


def sigma_end(theta: float, N: float) -> float:
    """到清零(I=1，即 i=1/N)时的归一化易感者 S_end/N，下降支根（= Lambert W_0 分支）。"""
    C2 = theta + A * SIG_C - RHO1N * np.log(SIG_C)      # 后期常规段首次积分常数(i(t2)=theta)
    floor = 1.0 / N
    f = lambda sig: (-A * sig + RHO1N * np.log(sig) + C2) - floor
    return brentq(f, 1e-12, SIG_C * (1 - 1e-9))


def h_clear(theta: float, N: float) -> float:
    """到清零的三段累计分数 I_{t,cum}/N（Theorem 3.7）。含真实 S_end，故弱依赖 N（清零地板 1/N）。"""
    ss = sigma_star(theta)
    se = sigma_end(theta, N)
    seg1 = (BETA / H) * (S0_FRAC - ss)                                        # 进入段 [0,t1]
    seg2 = BETA * ((ss - SIG_C) + SIG_BAR * np.log((ss - SIG_BAR) / (SIG_C - SIG_BAR)))  # 平台段 [t1,t2]
    seg3 = (BETA / H) * (SIG_C - se)                                          # 退出段 [t2,t_end]
    return seg1 + seg2 + seg3


# ----------------------------------------------------------------------
# 2. 临界比例与临界人口
# ----------------------------------------------------------------------
def solve_criticals(T_max: float, cumulative="clear"):
    """cumulative: 'clear'(到清零,含 S_end,弱依赖 N) 或 't2'(到 t2, theta-only)。"""
    theta_cost = brentq(lambda t: Jcost(t) - TDINN["J"], 1e-4, 0.05)
    theta_dur  = brentq(lambda t: Dt(t) - T_max,        1e-4, 0.1)
    theta_bind = max(theta_cost, theta_dur)                # 占优带下端
    N_star     = TDINN["peak"] / theta_bind
    N_star_inf = TDINN["peak"] / theta_cost
    # N*_cum: 累计沿带内在 theta_bind 处最小(h 随 theta 增)，故 N*h(theta_bind)=cum_T
    if cumulative == "clear":
        N_cum = brentq(lambda N: N * h_clear(theta_bind, N) - TDINN["cum"], 3e3, 6e4)
    else:
        N_cum = TDINN["cum"] / h_t2(theta_bind)
    return dict(theta_cost=theta_cost, theta_dur=theta_dur, theta_bind=theta_bind,
                N_star=N_star, N_star_inf=N_star_inf, N_cum=N_cum)


# ----------------------------------------------------------------------
# 3. 出图
# ----------------------------------------------------------------------
def plot_dominance(T_max=90.0, cumulative="clear", outfile="dominance_region"):
    c = solve_criticals(T_max, cumulative)
    tc, td = c["theta_cost"], c["theta_dur"]
    tb, Nstar, Ninf, Ncum = c["theta_bind"], c["N_star"], c["N_star_inf"], c["N_cum"]
    peak = TDINN["peak"]

    Ngrid = np.logspace(3, 6, 700)
    Egrid = np.logspace(1, 5, 700)
    NN, EE = np.meshgrid(Ngrid, Egrid)
    TT = EE / NN

    M_pcd = (TT > tb) & (EE < peak) & (TT < IOTA)
    # W_cum: 额外 N*h(theta) <= cum_T。h_clear 弱依赖 N(清零地板)，
    # 边界近 N~Ncum，故在参考 N=Ncum 上把 h 预插成 theta 的函数以提速。
    th_ref = np.linspace(SIG_C * 1e-3, IOTA * 0.999, 400)
    if cumulative == "clear":
        h_ref = np.array([h_clear(t, Ncum) for t in th_ref])
    else:
        h_ref = np.array([h_t2(t) for t in th_ref])
    Hgrid = np.interp(np.clip(TT, th_ref[0], th_ref[-1]), th_ref, h_ref)
    M_cum = M_pcd & (NN * Hgrid <= TDINN["cum"])

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(7.4, 5.6))

    ax.contourf(NN, EE, M_pcd.astype(float), levels=[0.5, 1.5],
                colors=["#9ecae1"], alpha=0.55)
    ax.contourf(NN, EE, M_cum.astype(float), levels=[0.5, 1.5],
                colors=["none"], hatches=["////"], alpha=0.0)
    ax.contour(NN, EE, M_cum.astype(float), levels=[0.5], colors="#08519c", linewidths=0.8)

    Nline = np.logspace(3, 6, 200)
    ax.axhline(peak, color="#d95f02", lw=1.8, label=rf"peak: $\eta=I^{{\rm T}}_{{\rm peak}}={peak:.2f}$")
    ax.plot(Nline, tc * Nline, color="#7570b3", lw=1.6,
            label=rf"cost: $\eta=\theta_{{\rm cost}}N$  ($\theta_{{\rm cost}}={tc:.2e}$)")
    ax.plot(Nline, td * Nline, color="#1b9e77", lw=1.6, ls="--",
            label=rf"dur.: $\eta=\theta_{{\rm dur}}N$  ($T_{{\max}}={T_max:g}$d)")
    ax.plot(Nline, IOTA * Nline, color="#666666", lw=1.2, ls=":",
            label=rf"trigger: $\eta=i_{{\max}}^{{no}} N$  ($i_{{\max}}^{{no}}={IOTA:.3f}$)")

    ax.axvline(Ninf, color="#7570b3", lw=1.0, ls=":", alpha=0.8)
    ax.annotate(rf"$N^\ast_\infty={Ninf:,.0f}$", xy=(Ninf, 12), rotation=90,
                fontsize=8, color="#7570b3", va="bottom", ha="right")
    ax.plot([Nstar], [peak], "o", ms=8, mfc="white", mec="k", mew=1.6, zorder=6)
    ax.annotate(rf"$(N^\ast,\,{peak:.2f})$, $N^\ast={Nstar:,.0f}$", xy=(Nstar, peak),
                xytext=(-8, 10), textcoords="offset points", fontsize=8.5, ha="right")
    ax.plot([5e4], [100], "s", ms=8, mfc="#e41a1c", mec="k", mew=1.0, zorder=6)
    ax.annotate(r"$(5\times10^4,100)$", xy=(5e4, 100),
                xytext=(8, -14), textcoords="offset points", fontsize=8.5, color="#e41a1c")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(1e3, 1e6); ax.set_ylim(1e1, 1e5)
    ax.set_xlabel(r"$N_{\rm eff}$"); ax.set_ylabel(r"$\eta$")
    ax.set_title(r"Dominance region of threshold vs TDINN control", fontsize=11)

    handles = ax.get_legend_handles_labels()[0]
    handles += [Patch(facecolor="#9ecae1", alpha=0.55, label=r"$\mathcal{W}_{\rm pcd}$ (peak+cost+dur.)"),
                Patch(facecolor="white", edgecolor="#08519c", label=r"$\mathcal{W}_{\rm cum}$ (+cumulative)")]
    ax.legend(handles=handles, fontsize=8, loc="lower right", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(f"{outfile}.pdf", bbox_inches="tight")
    fig.savefig(f"{outfile}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {outfile}.pdf/.png")
    print(f"[crit] theta_cost={tc:.5f}  theta_dur({T_max:g}d)={td:.5f}  iota={IOTA:.4f}")
    print(f"[crit] N*={Nstar:,.0f}  N*_inf={Ninf:,.0f}  N*_cum={Ncum:,.0f}")
    return c


# ----------------------------------------------------------------------
# 4. TDINN 基准的 N 不变性复核（需你的仓库模块与数据）
# ----------------------------------------------------------------------
def recompute_tdinn_benchmarks(N_list=(5e4, 1e5, 3e5, 1e6, 3e6, 13_163_000.0)):
    """逐 N 重拟合 I0，报告 TDINN 的 peak / J / cum，检查是否近似不变。"""
    try:
        import xian_control_comparison as xcc
        import threshold_landscape_analysis as tla
        import effective_population_sensitivity as eps
    except Exception as e:
        print("[warn] 未找到 xcc/tla/eps 模块，跳过 TDINN 复核：", e)
        return None
    observed = xcc.load_observed_data()
    print(f"{'N_eff':>12} {'peak_T':>10} {'J_T':>8} {'cum_T':>10}")
    rows = []
    for N in N_list:
        params = tla.LandscapeParams(N=float(N))
        fit = eps.fit_initial_condition_for_N(observed, params)
        # 用你现成的 TDINN 求解与成本接口取峰值/成本/累计（按你的函数名替换）：
        df = tla.solve_time_control_param("TDINN控制", fit, params,
                                          xcc.c_tdinn(params), xcc.q_tdinn(params))
        peak = float(df["I"].max())
        cum  = float(df["Itcum"].iloc[-1]) if "Itcum" in df else float("nan")
        cost = xcc.compute_control_costs(df, params, 0.0, float(df["t"].iloc[-1]),
                                         xcc.DEFAULT_W_C, xcc.DEFAULT_W_Q)["J"]
        rows.append((N, peak, cost, cum))
        print(f"{N:>12,.0f} {peak:>10.2f} {cost:>8.2f} {cum:>10.1f}")
    arr = np.array([[r[1], r[2], r[3]] for r in rows])
    rng = arr.max(0) / arr.min(0) - 1.0
    print(f"[check] 相对波动: peak {rng[0]*100:.2f}%  J {rng[1]*100:.2f}%  cum {rng[2]*100:.2f}%")
    print("[check] 若均 < 数个百分点，则把三者当作 N-无关常数是合理的（局限第2条得到支持）。")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmax", type=float, default=90.0)
    ap.add_argument("--recompute-tdinn", action="store_true")
    ap.add_argument("--cum-t2", action="store_true", help="累计用到 t2 口径（默认到清零）")
    args = ap.parse_args()

    if args.recompute_tdinn:
        rows = recompute_tdinn_benchmarks()
        if rows:  # 用重算的均值覆盖默认常数
            arr = np.array([[r[1], r[2], r[3]] for r in rows])
            TDINN.update(peak=float(arr[:, 0].mean()),
                         J=float(arr[:, 1].mean()),
                         cum=float(arr[:, 2].mean()))
            print("[info] 已用重算均值覆盖 TDINN 基准:", TDINN)

    plot_dominance(T_max=args.tmax, cumulative=("t2" if args.cum_t2 else "clear"))
