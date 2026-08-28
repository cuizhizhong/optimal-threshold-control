"""Panel A (eta-lever, four N_eff cases) 轨迹图。Panel B 已移到 compute_B.py + plot_B.py。
Style matched to the dominance panels (serif, blank background, no grid).
Colours are locked to the dom-figure sampling roles for cross-figure linkage."""
import shutil
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
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import xian_control_comparison as xcc
import threshold_landscape_analysis as tla
import effective_population_sensitivity as eps
from plot_eta_80_100_150_inflection import build_plot_series, compute_inflection

OUT = Path(__file__).resolve().parent / "dominance_panels"
OUT.mkdir(parents=True, exist_ok=True)
OBS = xcc.load_observed_data()
IPEAK_T, JT, ITCUM_T = 151.90, 49.35, 2096.76
# TDINN 是"已发生"的现实控制：其控制函数 c_real/q_real 与 I0 均在西安全市人口口径下
# 拟合到同一份真实日报数据，结果 (peak 151.90 / J 49.35 / cum 2096.76 / clear 45.27 d)
# 作为固定的现实参照尺子，不随 N_eff 变。常规控制与阈值控制是"未发生"的反事实，
# 必须在各自的 N_eff 上求解。
N_FULL = 13_163_000.0
Q0, QINF = 0.3230, 1.0 - 1.0 / (2.0 * (1.0 - 0.1498))   # 0.4119 (threshold inflection level)

# confirmed scale-invariant thresholds (theta = eta/N)
TH = {"interior": 5.612e-3, "dur45": 3.762e-3, "cost": 1.656e-3, "dur150": 1.137e-3}
# role colours / styles -- identical to dom RC_COL; shared roles deepen with eta
COL = {"interior": "#084a91", "dur45": "#073068", "cost": "#206FB6", "dur150": "#6BADD7",
       "clear": "#9a6b5a", "cum": "#238b8e"}
LS = {"interior": "-", "dur45": "-", "cost": "-", "dur150": "-", "clear": "-", "cum": "-"}
ROLE_LW = {"interior": 1.8, "dur45": 1.8, "cost": 2.0, "dur150": 1.8,
           "clear": 1.8, "cum": 1.8}
LAB = {"interior": r"interior ($\Delta t{=}30$d)", "dur45": "dur 45 d", "cost": "cost",
       "dur150": "dur 150 d", "clear": r"clear $\leq$ 45.3 d", "cum": "cumulative"}
PANEL_A_ROLES = ("dur150", "cost", "dur45")
PANEL_A_CASES = (
    (10_000.0, "fig_panel_A_N1e4"),
    (20_000.0, "fig_panel_A_N2e4"),
    (40_377.0, "fig_panel_A_N40377"),
    (91_727.0, "fig_panel_A_N91727"),
)

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

def cumulative_at_clearance(df, d):
    """总累计感染 Cc+Cq，统一取动态清零 I(t)<=1 的时刻。"""
    t_clear = float(d["clear_time"])
    t = df["t"].to_numpy(float)
    return float(np.interp(t_clear, t, df["Cc"].to_numpy(float))
                 + np.interp(t_clear, t, df["Cq"].to_numpy(float)))


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "STIX", "DejaVu Serif"],
    "mathtext.fontset": "stix", "axes.unicode_minus": False,
    "font.size": 9.0, "axes.labelsize": 10.0, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 7.4, "axes.linewidth": 0.9, "axes.edgecolor": "#000000",
    "xtick.color": "#000000", "ytick.color": "#000000", "xtick.labelcolor": "#000000", "ytick.labelcolor": "#000000",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1, "legend.labelspacing": 0.3,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ============================ diagnostics first ============================
if __name__ == "__main__" and (len(sys.argv) > 1 and sys.argv[1] == "diag"):
    for N, _ in PANEL_A_CASES:
        _, fit, rout = prep(N)
        print(f"Panel A threshold rows (N={N:,.0f}, I0={fit.I0:.6f}, "
              f"routine_peak={rout['I'].max():.2f}):")
        for r in PANEL_A_ROLES:
            eta = TH[r] * N
            p, df, d = solve_threshold(N, eta)
            try:
                infl = compute_inflection(eta, p, d)
                ti = float(infl["t_inflection"])
                t1 = float(d["t1"])
                t2 = float(d["t2"])
                lam = (ti - t1) / (t2 - t1)
                delta_inf = t2 - ti
            except Exception:
                ti = lam = delta_inf = float("nan")
            print(
                f"  {r:8s} eta={eta:8.3f} t1={float(d['t1']):7.3f} "
                f"t_inf={ti:7.3f} t2={float(d['t2']):7.3f} "
                f"lambda={lam:.6f} delta_inf={delta_inf:6.3f} "
                f"clear={float(d['clear_time']):7.3f} "
                f"cum={cumulative_at_clearance(df, d):9.3f} status={d['status']}"
            )
    td = solve_tdinn(N_FULL)   # 现实基准：全市口径，单条曲线
    print(f"  TDINN peakI={td['I'].max():.2f} clear~={td['t'].iloc[-1]:.1f}")
    sys.exit(0)


# ============================ Panel A (eta-lever, parameterized N) ============================
def panel_A(N=2e4, output_stem="fig_panel_A", aliases=(), td=None):
    N = float(N)
    # interior 数值角色仍保留在 TH/COL 中，但定稿图仅展示三条有直接比较含义的边界。
    roles = list(PANEL_A_ROLES)
    data = []
    for r in roles:
        eta = TH[r] * N
        p, df, d = solve_threshold(N, eta)
        try:
            infl = compute_inflection(eta, p, d)
        except Exception:
            infl = None
        data.append((r, eta, p, df, d, infl))
    # 两个面板统一先画清零晚的轨迹，使后画的短清零轨迹位于重合段上层。
    draw_data = sorted(data, key=lambda item: float(item[4]["clear_time"]), reverse=True)
    tend = 1.05 * max(float(d["clear_time"]) for _, _, _, _, d, _ in data)
    if td is None:
        td = solve_tdinn(N_FULL)   # 现实基准：全市口径，单条曲线
    _, _, rout = prep(N)

    # 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
    # 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
    # 累计感染 inset 完全放在坐标轴内部，因此不会扩张 tight bbox。
    fig, (axi, axq) = plt.subplots(2, 1, figsize=(6.151, 5.459), sharex=True,
                                   gridspec_kw={"height_ratios": [1.15, 1.0]},
                                   constrained_layout=True)
    # ---- top: I(t) log ----
    h_peak = axi.axhline(IPEAK_T, color="#a50518f4", lw=1.6, ls="--", alpha=0.8,
                         label=r"$I_{\rm peak}^{\rm T}$", zorder=2)
    h_routine, = axi.plot(rout["t"], rout["I"], color="#8a8a8a", lw=1.6, ls="--", alpha=0.9,
                          label="routine", zorder=2)
    # routine（常规控制）峰值 = 0.105 N_eff、到清零累计 = 0.348 N_eff，均为与池规模无关的
    # 固定比例；不再在图上标注，改由图注给出闭式（见 panel_A 图注）。
    h_tdinn, = axi.plot(td["t"], td["I"], color="#222222", lw=1.6, ls="-", alpha=0.95,
                        label="TDINN", zorder=3)
    role_handles = {}
    for r, eta, p, df, d, infl in draw_data:
        ti = float(infl["t_inflection"]) if infl else float(d["t2"])
        s = build_plot_series(eta, p, df, d, ti, tend)
        role_handles[r], = axi.plot(s["t"], s["I"], color=COL[r], ls=LS[r], lw=ROLE_LW[r],
                                    label=LAB[r], zorder=4)
        if infl:
            axi.scatter([ti], [eta], s=28, marker="o", fc=COL[r], ec="white",
                        linewidths=0.6, zorder=6)
    eta_max = max(eta for _, eta, _, _, _, _ in data)
    ylim_top = 1.35 * max(float(rout["I"].max()), eta_max, IPEAK_T)
    axi.set_yscale("log"); axi.set_ylabel(r"$I(t)$"); axi.set_ylim(1, ylim_top)
    axi.set_xlim(0, tend)
    axi.text(-0.008, 1.02, "(a)", transform=axi.transAxes, fontsize=11, fontweight="bold",
             ha="left", va="bottom", color="#222")
    spacer = Line2D([], [], color="none", lw=0, label="")
    legend_handles = [h_peak, h_routine, h_tdinn, spacer]
    legend_handles += [role_handles[r] for r in roles]
    axi.legend(handles=legend_handles, loc="upper right", ncol=2,
               columnspacing=1.3, borderaxespad=0.4)
    axi.tick_params(length=3.5, width=0.8)

    # ---- bottom: q(t) ----
    axq.axhline(QINF, color="#999", lw=1.1, ls="--", zorder=1)
    axq.text(tend * 0.995, QINF + 0.012, r"$q_{\mathrm{inf}}$", fontsize=7.6, color="#999", ha="right", va="bottom")
    max_clear = max(float(d["clear_time"]) for _, _, _, _, d, _ in data)
    q0_label_x = min(tend * 0.995, max_clear + 0.015 * tend)
    axq.text(q0_label_x, Q0 + 0.012, r"$q_0$", fontsize=7.6, color="#666",
             ha="right", va="bottom")
    axq.plot(td["t"], td["q"], color="#222222", lw=1.6, ls="-", alpha=0.95,
             label=r"TDINN $q$ (rising)", zorder=3)
    # 清零晚的轨迹先画、清零早的后画，使重合的 q0 段优先显示短清零策略。
    for r, eta, p, df, d, infl in draw_data:
        ti = float(infl["t_inflection"]) if infl else float(d["t2"])
        s = build_plot_series(eta, p, df, d, ti, tend)
        control_mask = s["phase"].eq("threshold-control")
        q_control = s["q"].where(control_mask, np.nan)
        first_control = np.flatnonzero(control_mask.to_numpy())[0]
        t1 = float(d["t1"])
        t2 = float(d["t2"])
        t_clear = float(d["clear_time"])
        q1 = float(s["q"].iloc[first_control])
        axq.plot([0.0, t1], [Q0, Q0], color=COL[r], ls="-", lw=ROLE_LW[r],
                 zorder=4)
        # t1 的瞬时跳跃单独用同色竖直虚线表示；控制段本身仍为实线。
        axq.plot([t1, t1], [Q0, q1], color=COL[r], ls="--", lw=1.2,
                 alpha=0.8, zorder=4.5)
        axq.plot(s["t"], q_control, color=COL[r], ls=LS[r], lw=ROLE_LW[r],
                 label=LAB[r], zorder=5)
        axq.plot([t2, t_clear], [Q0, Q0], color=COL[r], ls="-", lw=ROLE_LW[r],
                 zorder=4)
        axq.scatter([t_clear], [Q0], s=42, marker="|", color=COL[r],
                    linewidths=1.25, zorder=7)
        if infl:
            axq.scatter([ti], [float(infl["q_at_inflection"])], s=26, marker="o",
                        fc="white", ec=COL[r], lw=1.1, zorder=6)
    axq.set_ylabel(r"$q(t)$"); axq.set_xlabel(r"time $t$ (days)")
    axq.set_ylim(0.29, 1.02); axq.set_xlim(0, tend)
    axq.text(-0.008, 1.02, "(b)", transform=axq.transAxes, fontsize=11, fontweight="bold",
             ha="left", va="bottom", color="#222")
    axq.tick_params(length=3.5, width=0.8)

    # t≈149--244 d、q≈0.70--0.99 的空白区放累计感染 inset；
    # 柱图纵轴从 0 起，数值按 eta 递增排列，并保留固定 TDINN 现实参照。
    inset_data = data
    inset = axq.inset_axes([0.60, 0.56, 0.38, 0.40], facecolor="white", zorder=7)
    inset.patch.set_alpha(0.90)
    xpos = np.arange(len(inset_data))
    cum_values = np.array([cumulative_at_clearance(df, d)
                           for _, _, _, df, d, _ in inset_data])
    bar_colors = [COL[r] for r, _, _, _, _, _ in inset_data]
    bars = inset.bar(xpos, cum_values, width=0.50,
                     color=[COL[r] for r, _, _, _, _, _ in inset_data],
                     edgecolor=bar_colors, linewidth=0.8, alpha=0.85, zorder=2)
    inset.axhline(ITCUM_T, color="#333333", lw=0.8, ls="--", zorder=4)
    inset_right = len(inset_data) + 0.25
    inset_top = 1.15 * max(float(cum_values.max()), ITCUM_T)
    inset_offset = 0.015 * inset_top
    inset.text(inset_right - 0.10, ITCUM_T + inset_offset, "TDINN\n2,097",
               fontsize=6.0, color="#333333",
               ha="right", va="bottom", linespacing=0.85, zorder=5,
               bbox={"fc": "white", "ec": "none", "alpha": 0.82, "pad": 0.15})
    for bar, value in zip(bars, cum_values):
        inset.text(bar.get_x() + bar.get_width() / 2, value + inset_offset, f"{value:,.0f}",
                   fontsize=6.7, color="#222222", ha="center", va="bottom", zorder=5)
    inset.set_xlim(-0.50, inset_right)
    inset.set_ylim(0, inset_top)
    inset.set_xticks(xpos, [f"{eta:.1f}" for _, eta, _, _, _, _ in inset_data])
    inset.yaxis.set_major_locator(MaxNLocator(nbins=3, steps=[1, 2, 2.5, 5, 10]))
    inset.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    inset.set_xlabel(r"$\eta$", fontsize=7.2, labelpad=0.5)
    inset.set_ylabel(r"$I_{t_{\rm cum}}$", fontsize=7.2, labelpad=1.0)
    inset.tick_params(axis="both", colors="#000000", labelsize=6.7,
                      length=2.4, width=0.55, pad=1.2)
    inset.spines["top"].set_visible(False)
    inset.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        inset.spines[side].set_color("#000000")
        inset.spines[side].set_linewidth(0.55)

    pdf_path = OUT / f"{output_stem}.pdf"
    png_path = OUT / f"{output_stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    for alias in aliases:
        shutil.copyfile(pdf_path, OUT / f"{alias}.pdf")
        shutil.copyfile(png_path, OUT / f"{alias}.png")
    print(f"saved {output_stem} (N={N:,.0f}) ; t_end={tend:.0f}")


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

def generate_panel_A_cases():
    """生成四个 N_eff 案例；N=2e4 另存为正文兼容别名 fig_panel_A。"""
    td = solve_tdinn(N_FULL)
    for N, output_stem in PANEL_A_CASES:
        aliases = ("fig_panel_A",) if N == 20_000.0 else ()
        panel_A(N=N, output_stem=output_stem, aliases=aliases, td=td)


if __name__ == "__main__":
    generate_panel_A_cases()   # Panel B 已移到 compute_B.py + plot_B.py
