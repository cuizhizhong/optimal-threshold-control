"""Fast plot of Panel B from cached panelB.pkl next to this file (no solving).
Two stacked axes: (a) I(t) with routine/TDINN ribbons, (b) q_c(t)."""
import pickle, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
from pathlib import Path

OUT = Path(__file__).resolve().parent / "dominance_panels"
CACHE = Path(__file__).resolve().parent / "panelB.pkl"
IPEAK_T, ITCUM_T, ETA = 151.90, 2096.76, 100.0
BETA, GAMMA, C0 = 0.1498, 0.2953, 12.8872
Q0, QINF = 0.3230, 1.0 - 1.0 / (2.0 * (1.0 - 0.1498))   # 0.4119
COL = {"interior": "#084a91", "dur45": "#073068", "cost": "#206FB6", "dur150": "#6BADD7",
       "clear": "#9a6b5a", "cum": "#238b8e"}
LS = {"interior": "-", "dur45": "-", "cost": "-", "dur150": "-", "clear": "-", "cum": "-"}
ROLE_LW = {"interior": 1.8, "dur45": 1.8, "cost": 2.0, "dur150": 1.8,
           "clear": 1.8, "cum": 1.8}
LAB = {"interior": r"interior", "dur45": "dur 45 d", "cost": "cost", "dur150": "dur 150 d",
       "clear": r"clear $\leq$ 45.3 d", "cum": "cumulative"}
ALPHA = {"clear": 0.85}


def threshold_q_parts(t, I, q, q0=Q0, tol=1e-8):
    """从缓存恢复控制段及 t1、t2、动态清零时刻。"""
    t = np.asarray(t, dtype=float)
    I = np.asarray(I, dtype=float)
    q = np.asarray(q, dtype=float)
    active = np.flatnonzero(q > q0 + tol)
    finite_i = np.flatnonzero(np.isfinite(I))
    if active.size == 0 or finite_i.size == 0:
        raise ValueError("cached threshold trajectory has no active or finite segment")
    shown = np.full(q.shape, np.nan, dtype=float)
    stop = min(active[-1] + 2, q.size)
    shown[active[0]:stop] = q[active[0]:stop]
    t2_index = min(active[-1] + 1, q.size - 1)
    return {
        "shown": shown,
        "t1": float(t[active[0]]),
        "q1": float(q[active[0]]),
        "t2": float(t[t2_index]),
        "clear": float(t[finite_i[-1]]),
    }


def cumulative_at_cached_clearance(built, part):
    """由三段解析式从缓存轨迹恢复动态清零时的总累计感染。"""
    t = np.asarray(built["t"], dtype=float)
    I = np.asarray(built["I"], dtype=float)
    N = float(built["N"])
    finite = np.isfinite(t) & np.isfinite(I)
    if finite.sum() < 2:
        raise ValueError("cached threshold trajectory has insufficient finite points")

    t_clear = float(part["clear"])
    tail = finite & (t >= float(part["t2"]) - 1.0e-10) & (t <= t_clear + 1.0e-10)
    if tail.sum() < 2:
        raise ValueError("cached threshold trajectory has insufficient post-control points")

    # 逐 N 拟合采用 R(0)=0、S0=N-I0；q(t1+) 反推出 S*，t2 时 S=Sc。
    S0 = N - float(I[finite][0])
    S_star = GAMMA * N / (BETA * C0 * (1.0 - float(part["q1"])))
    S_c = GAMMA * N / (BETA * C0 * (1.0 - Q0))
    S_bar = (1.0 - BETA) * GAMMA * N / (BETA * C0)

    tail_I = float(np.trapz(I[tail], t[tail]))
    tail_decay = C0 * (BETA + Q0 * (1.0 - BETA)) * tail_I / N
    S_end = S_c * np.exp(-tail_decay)
    routine_factor = BETA / (BETA + Q0 * (1.0 - BETA))
    return float(
        routine_factor * (S0 - S_star)
        + BETA * (
            (S_star - S_c)
            + S_bar * np.log((S_star - S_bar) / (S_c - S_bar))
        )
        + routine_factor * (S_c - S_end)
    )


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "STIX", "DejaVu Serif"],
    "mathtext.fontset": "stix", "axes.unicode_minus": False,
    "font.size": 9.0, "axes.labelsize": 10.0, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 7.2, "axes.linewidth": 0.9, "axes.edgecolor": "#000000",
    "xtick.color": "#000000", "ytick.color": "#000000", "xtick.labelcolor": "#000000", "ytick.labelcolor": "#000000",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1, "legend.labelspacing": 0.3,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

D = pickle.load(open(CACHE, "rb"))
# 缓存仍保留全部数值角色；定稿图隐藏 interior，不改变 panelB.pkl。
roles = [r for r in D["roles"] if r != "interior"]
tend, tg = D["tend"], D["tg"]
q_parts = {
    r: threshold_q_parts(D["built"][r]["t"], D["built"][r]["I"], D["built"][r]["q"])
    for r in roles
}
# 两个面板统一先画清零晚的轨迹，使后画的短清零轨迹位于重合段上层。
draw_roles = sorted(roles, key=lambda role: q_parts[role]["clear"], reverse=True)
# 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
# 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
fig, (axi, axq) = plt.subplots(2, 1, figsize=(6.151, 5.459), sharex=True,
                               gridspec_kw={"height_ratios": [1.15, 1.0]},
                               constrained_layout=True)

# ================= (a) I(t) with ribbons =================
rlo, rhi = D["rlo"], D["rhi"]
# 绘制到最后一条成员清零为止；下包络已在 compute 端按判据 I=1 收口。
m = np.isfinite(rlo) & np.isfinite(rhi) & (rhi > 1.0)
axi.fill_between(tg[m], rlo[m], rhi[m], color="#8a8a8a", alpha=0.16, lw=0, zorder=1)
axi.plot(tg[m], rlo[m], color="#8a8a8a", lw=0.8, alpha=0.55, zorder=1)
axi.plot(tg[m], rhi[m], color="#8a8a8a", lw=0.8, alpha=0.55, zorder=1)
for N, d in D["rep_r"].items():
    axi.plot(d["t"], d["I"], color="#8a8a8a", lw=1.6, ls="--", alpha=0.9, zorder=2)
# routine（常规控制）峰值 = 0.105 N_eff、到清零累计 = 0.348 N_eff，均为与池规模无关的
# 固定比例；不再在图上标注，改由图注给出闭式。
_td = D["tdinn_I"]
axi.plot(_td["t"], _td["I"], color="#222222", lw=1.6, ls="-", alpha=0.95, zorder=4)
for r in draw_roles:
    b = D["built"][r]
    axi.plot(b["t"], b["I"], color=COL[r], ls=LS[r], lw=ROLE_LW[r],
             alpha=ALPHA.get(r, 1.0), zorder=5)
h_peak = axi.axhline(IPEAK_T, color="#a50518f4", lw=1.6, ls="--", alpha=0.8, zorder=2)
axi.text(tend * 0.995, IPEAK_T * 1.06, r"$I_{\rm peak}^{\rm T}$", fontsize=7.6,
         color="#a50518f4", ha="right", va="bottom")
axi.axhline(ETA, color="#999", lw=0.9, ls="--", alpha=0.55, zorder=1)
axi.set_yscale("log"); axi.set_ylabel(r"$I(t)$"); axi.set_ylim(1, 1.5e4); axi.set_xlim(0, tend)
axi.text(-0.008, 1.02, "(a)", transform=axi.transAxes, fontsize=11, fontweight="bold",
         ha="left", va="bottom", color="#222")
def _lab(r):                                   # 角色名 + 该曲线对应的 N_eff
    return rf"{LAB[r]}  ($N{{=}}{D['built'][r]['N']:,.0f}$)"
handles = [Line2D([], [], color=COL[r], ls=LS[r], lw=ROLE_LW[r],
                  alpha=ALPHA.get(r, 1.0), label=_lab(r)) for r in roles]
handles += [Line2D([], [], color="#222222", lw=1.4, label="TDINN"),
            Patch(fc="#8a8a8a", alpha=0.32, label="routine band")]
axi.legend(handles=handles, loc="upper right", ncol=2, columnspacing=1.2, borderaxespad=0.4)
axi.tick_params(length=3.5, width=0.8)

# ================= (b) q_c(t) =================
axq.axhline(QINF, color="#999", lw=1.1, ls="--", zorder=1)
axq.text(tend * 0.995, QINF + 0.012, r"$q_{\mathrm{inf}}$", fontsize=7.6, color="#999", ha="right", va="bottom")
max_clear = max(q_parts[r]["clear"] for r in roles)
q0_label_x = min(tend * 0.995, max_clear + 0.015 * tend)
axq.text(q0_label_x, Q0 + 0.012, r"$q_0$", fontsize=7.6, color="#666",
         ha="right", va="bottom")
tq = D["tdinn_q"]
axq.plot(tq["t"], tq["q"], color="#222222", lw=1.6, ls="-", alpha=0.95, label=r"TDINN $q$ (rising)", zorder=3)
# 清零晚的轨迹先画、清零早的后画，使重合的 q0 段优先显示短清零策略。
for r in draw_roles:
    b = D["built"][r]
    part = q_parts[r]
    role_alpha = ALPHA.get(r, 1.0)
    axq.plot([0.0, part["t1"]], [Q0, Q0], color=COL[r], ls="-", lw=ROLE_LW[r],
             alpha=role_alpha, zorder=4)
    axq.plot([part["t1"], part["t1"]], [Q0, part["q1"]],
             color=COL[r], ls="--", lw=1.2,
             alpha=0.8 * role_alpha, zorder=4.5)
    axq.plot(b["t"], part["shown"], color=COL[r], ls=LS[r], lw=ROLE_LW[r],
             alpha=role_alpha, zorder=5)
    axq.plot([part["t2"], part["clear"]], [Q0, Q0], color=COL[r], ls="-",
             lw=ROLE_LW[r], alpha=role_alpha, zorder=4)
    axq.scatter([part["clear"]], [Q0], s=42, marker="|", color=COL[r],
                linewidths=1.25, alpha=role_alpha, zorder=7)
    if np.isfinite(b["qi"]):
        axq.scatter([b["ti"]], [b["qi"]], s=26, marker="o", fc="white", ec=COL[r],
                    lw=1.1, alpha=role_alpha, zorder=6)
axq.set_ylabel(r"$q_c(t)$"); axq.set_xlabel(r"time $t$ (days)")
axq.set_ylim(0.29, 1.02); axq.set_xlim(0, tend)
axq.text(-0.008, 1.02, "(b)", transform=axq.transAxes, fontsize=11, fontweight="bold",
         ha="left", va="bottom", color="#222")
axq.tick_params(length=3.5, width=0.8)

# 固定 eta=100 时按 N_eff 递增排列五个角色的到清零总累计感染。
cum_values = np.array([
    cumulative_at_cached_clearance(D["built"][r], q_parts[r]) for r in roles
])
inset = axq.inset_axes([0.57, 0.55, 0.41, 0.40], facecolor="white", zorder=8)
inset.patch.set_alpha(0.90)
xpos = np.arange(len(roles))
bar_colors = [COL[r] for r in roles]
bars = inset.bar(
    xpos, cum_values, width=0.50, color=bar_colors, edgecolor=bar_colors,
    linewidth=0.8, alpha=0.85, zorder=2
)
inset.axhline(ITCUM_T, color="#333333", lw=0.8, ls="--", zorder=4)
inset_right = len(roles) + 0.25
inset_top = 1.15 * max(float(cum_values.max()), ITCUM_T)
inset_offset = 0.015 * inset_top
inset.text(
    inset_right - 0.10, ITCUM_T + inset_offset, "TDINN\n2,097",
    fontsize=5.8, color="#333333", ha="right", va="bottom", linespacing=0.85,
    zorder=5, bbox={"fc": "white", "ec": "none", "alpha": 0.82, "pad": 0.15}
)
for bar, value in zip(bars, cum_values):
    inset.text(
        bar.get_x() + bar.get_width() / 2, value + inset_offset, f"{value:,.0f}",
        fontsize=6.2, color="#222222", ha="center", va="bottom", zorder=5,
        bbox={"fc": "white", "ec": "none", "alpha": 0.78, "pad": 0.10}
    )
inset.set_xlim(-0.50, inset_right)
inset.set_ylim(0, inset_top)
inset.set_xticks(
    xpos, [f"{float(D['built'][r]['N']) / 1000.0:.1f}" for r in roles]
)
inset.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
inset.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
inset.set_xlabel(r"$N_{\rm eff}/10^3$", fontsize=7.0, labelpad=0.5)
inset.set_ylabel(r"$I_{t_{\rm cum}}$", fontsize=7.0, labelpad=1.0)
inset.tick_params(
    axis="both", colors="#000000", labelsize=6.2, length=2.4, width=0.55, pad=1.2
)
inset.spines["top"].set_visible(False)
inset.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    inset.spines[side].set_color("#000000")
    inset.spines[side].set_linewidth(0.55)

fig.savefig(OUT / "fig_panel_B.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_panel_B.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("  Itcum:", " / ".join(f"{value:.3f}" for value in cum_values))
print("saved Panel B (2-row) ; t_end=%.0f" % tend)
