"""Panel A (eta-lever, N=2e4) 轨迹图。Panel B 已移到 compute_B.py + plot_B.py。
Style matched to the dominance panels (serif, blank background, no grid).
Colours are locked to the dom-figure sampling roles for cross-figure linkage."""
import sys, numpy as np
from pathlib import Path
# 自动把三个求解器模块目录加入 sys.path（免手动设 PYTHONPATH，任何终端/IDE 均可直接运行）。
_XCC = Path(__file__).resolve().parent.parent / "xian_control_comparison"
for _p in (_XCC, _XCC / "threshold_landscape_analysis", _XCC / "effective_population_sensitivity"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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

    # 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
    # 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
    # 注意: 画布缩小后字号(绝对 pt)相对变大，下方 eta 直标的垂直余量仅剩约 0.027 decade
    # (标签高 0.136 vs 最小间距 0.163)。再调大字号或让 eta 变成五位数就会重叠。
    fig, (axi, axq) = plt.subplots(2, 1, figsize=(6.164, 5.459), sharex=True,
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


# ===== Panel B 的共享量（N_OF、_envelope，供 compute_B.py 导入）=====
#       Panel B 本体已移到 compute_B.py + plot_B.py。
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

if __name__ == "__main__":
    panel_A()   # Panel B 已移到 compute_B.py + plot_B.py
