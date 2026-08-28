"""Panel A (eta-lever, N=2e4) and Panel B (N-lever, eta=100) trajectory figures.
Style matched to the dominance panels (serif, blank background, no grid).
Colours are locked to the dom-figure sampling roles for cross-figure linkage."""
import sys, numpy as np
# 求解器模块 (threshold_landscape_analysis / xian_control_comparison /
# effective_population_sensitivity / plot_eta_80_100_150_inflection) 需在 PYTHONPATH 上；
# 目录结构见 README（pkg/ 平铺 + 真实数据/ 放在 pkg 的父目录）。
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
import xian_control_comparison as xcc
import threshold_landscape_analysis as tla
import effective_population_sensitivity as eps
from plot_eta_80_100_150_inflection import build_plot_series, compute_inflection

OUT = Path(__file__).resolve().parent / "dominance_panels"
OUT.mkdir(parents=True, exist_ok=True)
OBS = xcc.load_observed_data()
IPEAK_T, JT = 151.90, 49.35
# TDINN 是"已发生"的现实控制：其控制函数 c_real/q_real 与 I0 均在西安全市人口口径下
# 拟合到同一份真实日报数据，结果 (peak 151.90 / J 49.35 / cum 2096.76 / clear 45.27 d)
# 作为固定的现实参照尺子，不随 N_eff 变。常规控制与阈值控制是"未发生"的反事实，
# 必须在各自的 N_eff 上求解。
N_FULL = 13_163_000.0
Q0, QINF = 0.3230, 1.0 - 1.0 / (2.0 * (1.0 - 0.1498))   # 0.4119 (threshold inflection level)

# confirmed scale-invariant thresholds (theta = eta/N)
TH = {"interior": 5.612e-3, "dur45": 3.762e-3, "cost": 1.656e-3, "dur150": 1.137e-3}
# role colours / styles -- identical to dom RC_COL
COL = {"interior": "#6a3d9a", "dur45": "#4575b4", "cost": "#e08214", "dur150": "#2ca25f",
       "clear": "#c0563f", "cum": "#2f6db0"}
LS = {"interior": ":", "dur45": "-", "cost": "--", "dur150": "-.", "clear": "-", "cum": "-"}
LAB = {"interior": r"interior ($\Delta t{=}30$d)", "dur45": "dur 45 d", "cost": "cost",
       "dur150": "dur 150 d", "clear": r"clear $\leq$ 45.3 d", "cum": "cumulative"}

_cache = {}
def prep(N):
    N = float(N)
    if N not in _cache:
        p = tla.LandscapeParams(N=N)
        fit = eps.fit_initial_condition_for_N(OBS, p)
        rout = tla.solve_time_control_param("routine", fit, p, tla.c_const(p), tla.q_const(p))
        _cache[N] = (p, fit, rout)
    return _cache[N]

def solve_threshold(N, eta):
    p, fit, rout = prep(N)
    df, d = tla.solve_threshold_fast(fit, eta, p, rout)
    return p, df, d

def solve_tdinn(N):
    p, fit, rout = prep(N)
    return tla.solve_time_control_param("TDINN", fit, p, xcc.c_real, xcc.q_real)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "STIX", "DejaVu Serif"],
    "mathtext.fontset": "stix", "axes.unicode_minus": False,
    "font.size": 9.0, "axes.labelsize": 10.0, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 7.4, "axes.linewidth": 0.9, "axes.edgecolor": "#444444",
    "xtick.color": "#555", "ytick.color": "#555", "xtick.labelcolor": "#222", "ytick.labelcolor": "#222",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1, "legend.labelspacing": 0.3,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ============================ diagnostics first ============================
if __name__ == "__main__" and (len(sys.argv) > 1 and sys.argv[1] == "diag"):
    N = 2e4
    print("Panel A threshold rows (N=2e4):")
    for r, th in TH.items():
        eta = th * N
        p, df, d = solve_threshold(N, eta)
        try:
            infl = compute_inflection(eta, p, d)
            ti = infl["t_inflection"]
        except Exception as e:
            ti = float("nan")
        print(f"  {r:8s} eta={eta:7.2f}  peak={d.get('peak_I', float('nan')) if 'peak_I' in d else float('nan')}"
              f"  clear={float(d['clear_time']):7.2f}  t1={float(d['t1']):.2f} t2={float(d['t2']):.2f} infl_t={ti if ti==ti else float('nan'):.2f} status={d['status']}")
    td = solve_tdinn(N_FULL)   # 现实基准：全市口径，单条曲线
    print(f"  TDINN peakI={td['I'].max():.2f} clear~={td['t'].iloc[-1]:.1f}")
    p, fit, rout = prep(N)
    print(f"  routine peakI={rout['I'].max():.1f} clear~={rout['t'].iloc[-1]:.1f}")
    sys.exit(0)


# ============================ Panel A (eta-lever, N=2e4) ============================
def panel_A():
    N = 2e4
    roles = ["interior", "dur45", "cost", "dur150"]
    data = []
    for r in roles:
        eta = TH[r] * N
        p, df, d = solve_threshold(N, eta)
        try:
            infl = compute_inflection(eta, p, d)
        except Exception:
            infl = None
        data.append((r, eta, p, df, d, infl))
    tend = 1.05 * max(float(d["clear_time"]) for _, _, _, _, d, _ in data)
    td = solve_tdinn(N_FULL)   # 现实基准：全市口径，单条曲线
    p0, fit0, rout = prep(N)

    fig, (axi, axq) = plt.subplots(2, 1, figsize=(7.0, 6.2), sharex=True,
                                   gridspec_kw={"height_ratios": [1.15, 1.0]},
                                   constrained_layout=True)
    # ---- top: I(t) log ----
    axi.axhline(IPEAK_T, color="#b2182b", lw=0.9, ls=":", alpha=0.8,
                label=r"$I_{\rm peak}^{\rm T}$", zorder=2)
    axi.plot(rout["t"], rout["I"], color="#8a8a8a", lw=1.2, ls=":", alpha=0.9,
             label="routine", zorder=2)
    axi.plot(td["t"], td["I"], color="#222222", lw=1.4, ls="-", alpha=0.95,
             label="TDINN", zorder=3)
    for r, eta, p, df, d, infl in data:
        ti = float(infl["t_inflection"]) if infl else float(d["t2"])
        s = build_plot_series(eta, p, df, d, ti, tend)
        axi.plot(s["t"], s["I"], color=COL[r], ls=LS[r], lw=1.6, label=LAB[r], zorder=4)
    for r, eta, p, df, d, infl in data:                     # 平台高度即 eta，标在下降转角处
        axi.text(float(d["t2"]) + 0.006 * tend, eta * 1.06, rf"$\eta={eta:.1f}$",
                 color=COL[r], fontsize=8.0, ha="left", va="bottom", zorder=7)
    axi.set_yscale("log"); axi.set_ylabel(r"$I(t)$"); axi.set_ylim(1, 3e3)
    axi.set_xlim(0, tend)
    axi.text(-0.008, 1.02, "(a)", transform=axi.transAxes, fontsize=11, fontweight="bold",
             ha="left", va="bottom", color="#222")
    axi.legend(loc="upper right", ncol=2, columnspacing=1.3, borderaxespad=0.4)
    axi.tick_params(length=3.5, width=0.8)

    # ---- bottom: q(t) ----
    axq.axhline(Q0, color="#666", lw=0.9, ls=":", zorder=1)
    axq.axhline(QINF, color="#999", lw=0.9, ls="--", zorder=1)
    axq.text(tend * 0.995, Q0 + 0.012, r"$q_0$", fontsize=7.6, color="#666", ha="right", va="bottom")
    axq.text(tend * 0.995, QINF + 0.012, r"$q_{\mathrm{inf}}$", fontsize=7.6, color="#999", ha="right", va="bottom")
    axq.plot(td["t"], td["q"], color="#222222", lw=1.4, ls="-", alpha=0.95,
             label=r"TDINN $q$ (rising)", zorder=3)
    for r, eta, p, df, d, infl in data:
        ti = float(infl["t_inflection"]) if infl else float(d["t2"])
        s = build_plot_series(eta, p, df, d, ti, tend)
        axq.plot(s["t"], s["q"], color=COL[r], ls=LS[r], lw=1.6, zorder=4)
        if infl:
            axq.scatter([ti], [float(infl["q_at_inflection"])], s=26, marker="o",
                        fc="white", ec=COL[r], lw=1.1, zorder=6)
    axq.set_ylabel(r"$q(t)$"); axq.set_xlabel(r"time $t$ (days)")
    axq.set_ylim(0.29, 1.02); axq.set_xlim(0, tend)
    axq.text(-0.008, 1.02, "(b)", transform=axq.transAxes, fontsize=11, fontweight="bold",
             ha="left", va="bottom", color="#222")
    axq.tick_params(length=3.5, width=0.8)

    fig.savefig(OUT / "fig_panel_A.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_panel_A.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved Panel A ; t_end=%.0f" % tend)


# ============================ Panel B (N-lever, eta=100) ============================
N_OF = {"clear": 4601.9, "cum": 10105.5, "interior": 100 / TH["interior"],
        "dur45": 100 / TH["dur45"], "cost": 100 / TH["cost"], "dur150": 100 / TH["dur150"]}

def _envelope(solver, N_list, tg):
    """min-max envelope of I(t) across a family of trajectories on grid tg."""
    stack = []
    reps = {}
    for N in N_list:
        df = solver(N)
        Ii = np.interp(tg, df["t"].to_numpy(float), df["I"].to_numpy(float),
                       left=np.nan, right=np.nan)
        stack.append(Ii)
        reps[N] = Ii
    M = np.vstack(stack)
    lo = np.nanmin(M, axis=0); hi = np.nanmax(M, axis=0)
    return lo, hi, reps

def panel_B():
    ETA = 100.0
    roles = ["clear", "cum", "interior", "dur45", "cost", "dur150"]
    data = []
    for r in roles:
        N = N_OF[r]
        p, df, d = solve_threshold(N, ETA)
        try:
            infl = compute_inflection(ETA, p, d)
        except Exception:
            infl = None
        data.append((r, N, p, df, d, infl))
        print(f"  B {r:8s} N={N:7.0f} clear={float(d['clear_time']):7.2f} status={d['status']}")
    tend = 1.05 * max(float(d["clear_time"]) for _, _, _, _, d, _ in data)
    tg = np.linspace(0, tend, 1400)
    Nrib = np.geomspace(5800, 88000, 8)
    rlo, rhi, _ = _envelope(lambda N: prep(N)[2], Nrib, tg)       # routine ribbon
    td_full = solve_tdinn(N_FULL)                                  # TDINN 单曲线(全市)
    rep_r = {N: prep(N)[2] for N in (Nrib[0], Nrib[-1])}

    fig, ax = plt.subplots(figsize=(7.0, 4.4), constrained_layout=True)
    # routine ribbon (grey) + TDINN ribbon (ink)
    m = np.isfinite(rlo) & np.isfinite(rhi)
    ax.fill_between(tg[m], rlo[m], rhi[m], color="#8a8a8a", alpha=0.15, lw=0, zorder=1)
    ax.plot(tg[m], rlo[m], color="#8a8a8a", lw=0.6, alpha=0.6, zorder=1)
    ax.plot(tg[m], rhi[m], color="#8a8a8a", lw=0.6, alpha=0.6, zorder=1)
    for N, df in rep_r.items():
        ax.plot(df["t"], df["I"], color="#8a8a8a", lw=1.0, ls=":", alpha=0.9, zorder=2)
    ax.plot(td_full["t"], td_full["I"], color="#222222", lw=1.4, ls="-", alpha=0.95, zorder=4)
    # 6 threshold trajectories (all plateau at eta=100)
    for r, N, p, df, d, infl in data:
        ti = float(infl["t_inflection"]) if infl else float(d["t2"])
        s = build_plot_series(ETA, p, df, d, ti, tend)
        ax.plot(s["t"], s["I"], color=COL[r], ls=LS[r], lw=1.6, label=LAB[r], zorder=5)
    ax.axhline(IPEAK_T, color="#b2182b", lw=0.9, ls=":", alpha=0.75, zorder=1)
    ax.axhline(ETA, color="#999", lw=0.7, ls="--", alpha=0.6, zorder=1)
    ax.set_yscale("log"); ax.set_ylabel(r"$I(t)$"); ax.set_ylim(1, 1.5e4)
    ax.set_xlabel(r"time $t$ (days)"); ax.set_xlim(0, tend)
    ax.text(-0.01, 1.02, "(b)", transform=ax.transAxes, fontsize=11, fontweight="bold",
            ha="left", va="bottom", color="#222")
    # legend: roles + ribbon proxies
    from matplotlib.patches import Patch
    handles = [Line2D([], [], color=COL[r], ls=LS[r], lw=1.6, label=LAB[r]) for r in roles]
    handles += [Line2D([], [], color="#222222", lw=1.4, label="TDINN (city-fit)"),
                Patch(fc="#8a8a8a", alpha=0.3, label="routine band")]
    ax.legend(handles=handles, loc="upper right", ncol=2, fontsize=7.2,
              columnspacing=1.2, borderaxespad=0.4)
    ax.tick_params(length=3.5, width=0.8)
    fig.savefig(OUT / "fig_panel_B.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_panel_B.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved Panel B ; t_end=%.0f" % tend)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("A", "both"):
        panel_A()
    if which in ("B", "both"):
        panel_B()
