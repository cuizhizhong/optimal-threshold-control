"""Dominance panels -- aesthetic combined build (side-by-side 1x2, rendered at
final double-column size so line weights are correct in print).

Adopts the sound parts of the styling review:
  * render at final size (7.2 x 3.35 in), shared eta axis           [sec 2]
  * explicit line-weight hierarchy (main/primary/secondary/skeleton) [sec 3]
  * opaque wedge in (a); no muddy alpha overlaps                     [sec 6]
  * (b): mutually-exclusive opaque region bands (clr inner, cum      [sec 7]
    outer annulus) -> no grey-purple blend
  * (b): neutral-grey constraint skeleton, colour arcs as leads      [sec 8]
  * pure-numpy PCHIP display-smoothing of the arcs (data unchanged)  [sec 9]
  * decluttered 3-item (b) legend                                    [sec 11]
Deliberately NOT applied: re-introducing N_cum / N_clr verticals or a
second N* caliber -- the user fixed on strict N*_45 and dropped those lines.
"""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory
from pathlib import Path

OUT = Path(__file__).resolve().parent / "dominance_panels"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- fixed model quantities (solver-confirmed) ----------
IPEAK, IMAX_NO = 151.90363, 0.104653
th_cost, th_d45, th_d150 = 1.656154e-3, 3.761624e-3, 1.137090e-3
th_int = 5.612e-3
Nstar_45 = IPEAK / th_d45          # strict caliber ~= 40377

# ---------- arcs (embedded) ----------
# 由 caliber.py 在全节单一口径（固定绝对初值 I0 = 1.0066e-3 人，i0 = I0/N）上求根生成，
# 见 caliber.N_cum / caliber.N_clr。累计弧与旧口径逐点相同（只经 theta 及弱 1/N 进入）；
# 清零弧经 t1 对 i0 敏感，故随口径移动（固定 i0 口径下最大值 2439，此处 5166）。
cum_eta = np.array([
    10.0000, 11.9887, 14.3728, 17.2311, 20.6578, 24.7660, 29.6912, 35.5958,
    42.6746, 51.1612, 61.3355, 73.5332, 88.1565, 105.6880, 126.7059, 151.9036
], float)
cum_N = np.array([
    12176.6, 12075.0, 11965.5, 11847.5, 11720.3, 11583.1, 11435.1, 11275.5,
    11103.5, 10918.2, 10718.7, 10503.9, 10273.0, 10024.6, 9757.8, 9471.0
], float)
clr_eta = cum_eta.copy()
clr_N = np.array([
    865.86, 978.73, 1106.08, 1249.66, 1411.39, 1593.39, 1798.00, 2027.81,
    2285.63, 2574.55, 2897.91, 3259.32, 3662.62, 4111.91, 4611.47, 5165.70
], float)

# 最小相容易感池 N_floor = I_cum^T + I_q,cum^T / beta = 605.40 + 1491.36/0.1498。
# 由 dSq/dt = (1-beta)/beta * dIq_cum/dt（Sq 无回流）得该次疫情消耗的易感者总数，
# 再由 S0 <= N 即得 N_eff >= N_floor。该恒等式与 N、c(t)、q(t) 及速率函数形式无关。
# 旧下界只计感染者 (I^T_tcum = 2096.76)，偏松 5.04 倍。
N_FLOOR = 10561.05
N_FLOOR_OLD = 2096.76
# 清零弧全段最大值 5166 < N_FLOOR（低 2.04 倍），故清零占优区为空集，该弧全线虚线绘出。
# 累计弧在 eta = 70.16 处穿过 N_FLOOR，在 (11762, 19.48) 处穿出楔形。
ETA_CUM_FLOOR = 70.16


def sort_unique(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    o = np.argsort(x); x, y = x[o], y[o]
    x, idx = np.unique(x, return_index=True)
    return x, y[idx]


cum_eta, cum_N = sort_unique(cum_eta, cum_N)
clr_eta, clr_N = sort_unique(clr_eta, clr_N)


# ---------- pure-numpy PCHIP (Fritsch-Carlson monotone cubic) ----------
def _pchip_slopes(x, y):
    h = np.diff(x)
    delta = np.diff(y) / h
    d = np.zeros_like(y)
    # interior nodes: weighted harmonic mean, zero at sign change / flats
    m0, m1 = delta[:-1], delta[1:]
    same = np.sign(m0) * np.sign(m1) > 0
    w1 = 2 * h[1:] + h[:-1]
    w2 = h[1:] + 2 * h[:-1]
    dint = np.zeros_like(m0)
    dint[same] = (w1[same] + w2[same]) / (w1[same] / m0[same] + w2[same] / m1[same])
    d[1:-1] = dint
    # endpoints: shape-preserving non-centred formula
    def edge(hh0, hh1, mm0, mm1):
        de = ((2 * hh0 + hh1) * mm0 - hh0 * mm1) / (hh0 + hh1)
        if np.sign(de) != np.sign(mm0):
            de = 0.0
        elif (np.sign(mm0) != np.sign(mm1)) and (abs(de) > 3 * abs(mm0)):
            de = 3 * mm0
        return de
    d[0] = edge(h[0], h[1], delta[0], delta[1])
    d[-1] = edge(h[-1], h[-2], delta[-1], delta[-2])
    return h, delta, d


def pchip_loglog(N, eta, n=260):
    """Monotone display curve through the arc points, smoothed in log-log."""
    eta, N = sort_unique(eta, N)
    x, y = np.log(eta), np.log(N)
    h, delta, d = _pchip_slopes(x, y)
    xd = np.log(np.geomspace(eta.min(), eta.max(), n))
    idx = np.clip(np.searchsorted(x, xd) - 1, 0, len(x) - 2)
    t = (xd - x[idx]) / h[idx]
    t2, t3 = t * t, t * t * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    yd = (h00 * y[idx] + h10 * h[idx] * d[idx]
          + h01 * y[idx + 1] + h11 * h[idx] * d[idx + 1])
    return np.exp(yd), np.exp(xd)


# ---------- style (final double-column size) ----------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "STIX", "DejaVu Serif"],
    "mathtext.fontset": "stix", "axes.unicode_minus": False,
    "font.size": 9.0, "axes.labelsize": 10.0,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 7.6,
    "axes.linewidth": 0.9, "axes.edgecolor": "#000000",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#000000", "ytick.color": "#000000",
    "xtick.labelcolor": "#000000", "ytick.labelcolor": "#000000",
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1,
    "legend.handletextpad": 0.6, "legend.labelspacing": 0.28,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.pad_inches": 0.03,
})

# line-weight hierarchy
LW_MAIN, LW_PRIMARY, LW_SECONDARY, LW_SKELETON, LW_AUX = 2.20, 2.00, 1.70, 1.20, 1.10
S_A, S_B, MK_LW = 18, 16, 0.7          # small sampling markers, consistent across (a)/(b)

# colours
C_PEAK, C_COST, C_D45, C_D150, C_TRIG = "#b2182b", "#206FB6", "#073068", "#6BADD7", "#c9ced3"
C_WEDGE_A = "#E7EDF4"
C_CUM, C_CLR = "#238b8e", "#9a6b5a"
C_SKEL, C_SKEL_LIGHT = "#A6AFB8", "#C2CAD2"
C_WEDGE_B, C_CUM_FILL, C_CLR_FILL = "#EDF1F5", "#D7EBE9", "#E7DDD8"
RC_COL = {"int": "#084a91", "d45": "#073068", "cost": "#206FB6", "d150": "#6BADD7",
          "clr": C_CLR, "cum": C_CUM}

XMIN, XMAX, YMIN, YMAX = 1e3, 1e6, 10., 4e3
Ng = np.logspace(3, 6, 700)
peak = np.full_like(Ng, IPEAK)

A_pts = [("d45", 2e4, th_d45 * 2e4), ("cost", 2e4, th_cost * 2e4),
         ("d150", 2e4, th_d150 * 2e4)]
B_pts = [("d45", 100 / th_d45, 100), ("cost", 100 / th_cost, 100),
         ("d150", 100 / th_d150, 100),
         ("clr", 3969.7, 100),          # 直接求根值，与 Panel B 的 clear 角色一致
         ("cum", np.interp(100, cum_eta, cum_N), 100)]


def axfmt(ax, tag, ylabel=True):
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(XMIN, XMAX); ax.set_ylim(YMIN, YMAX)
    ax.set_xlabel(r"$N_{\rm eff}$", labelpad=3)
    if ylabel:
        ax.set_ylabel(r"$\eta$", labelpad=4)
    ax.set_axisbelow(True)      # blank background: no grid lines
    ax.text(-0.02, 1.015, tag, transform=ax.transAxes, fontsize=11,
            fontweight="bold", ha="left", va="bottom", color="#222222", clip_on=False)
    ax.tick_params(which="major", length=4.0, width=0.8, pad=3)
    ax.tick_params(which="minor", length=2.2, width=0.65)


C_FLOOR = "#3A3A3A"


def draw_floor(ax, label=True):
    """最小相容易感池下界：淡灰底 + 竖线。两个面板一致。

    该下界是对未知 N_eff 的约束（式 eq:dom:Nfloor），对全节一律适用，
    故直线族面板同样绘出，避免 (a) 暗示占优可延到任意小 N。
    用淡灰实色而非斜纹：斜纹在 451 bp 宽度下会盖住骨架线与弧线。
    """
    ax.axvspan(XMIN, N_FLOOR, facecolor="#8A9099", alpha=0.13, lw=0, zorder=0.5)
    ax.axvline(N_FLOOR, color=C_FLOOR, lw=1.35, zorder=5.6)
    if label:
        ax.text(N_FLOOR * 0.93, YMAX * 0.62, r"$N_{\rm floor}$", rotation=90,
                ha="right", va="top", fontsize=7.2, color=C_FLOOR, zorder=11)


# 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
# 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.288, 2.925), sharey=True,
                               constrained_layout=True)

# ================= (a) straight-line family =================
# 楔形只填到下界之右：N < N_floor 与观测不相容，不属于占优区
axa.fill_between(Ng, th_cost * Ng, np.minimum(peak, IMAX_NO * Ng),
                 where=(np.minimum(peak, IMAX_NO * Ng) > th_cost * Ng) & (Ng >= N_FLOOR),
                 color=C_WEDGE_A, alpha=1.0, lw=0, zorder=1)
axa.plot(Ng, IMAX_NO * Ng, color=C_TRIG, lw=LW_AUX, ls=":", alpha=0.85, zorder=3)
axa.axhline(IPEAK, color=C_PEAK, lw=LW_PRIMARY, zorder=5)
axa.plot(Ng, th_cost * Ng, color=C_COST, lw=LW_PRIMARY, zorder=5)
axa.plot(Ng, th_d45 * Ng, color=C_D45, lw=LW_SECONDARY, ls="--", zorder=4)
axa.plot(Ng, th_d150 * Ng, color=C_D150, lw=LW_SECONDARY, ls="-.", zorder=4)
# N* vertex marker removed -> reported in caption (N*_45 = IPEAK/th_d45 ~= 40377)
draw_floor(axa, label=False)
for r, x, y in A_pts:
    axa.scatter([x], [y], s=S_A, marker="o", fc=RC_COL[r], ec="white", lw=MK_LW, zorder=10)
axfmt(axa, "(a)", ylabel=True)
lega = [Line2D([], [], color=C_PEAK, lw=LW_PRIMARY, label=r"peak $I_{\rm peak}^{\rm T}$"),
        Line2D([], [], color=C_COST, lw=LW_PRIMARY, label="cost"),
        Line2D([], [], color=C_D45, lw=LW_SECONDARY, ls="--", label="dur 45 d"),
        Line2D([], [], color=C_D150, lw=LW_SECONDARY, ls="-.", label="dur 150 d"),
        Line2D([], [], color=C_TRIG, lw=LW_AUX, ls=":", label="trigger"),
        Line2D([], [], color=C_FLOOR, lw=1.6, label=r"$N_{\rm floor}$")]
axa.legend(handles=lega, loc="lower right", borderaxespad=0.45)

# ================= (b) arc family =================
eg = np.geomspace(YMIN, IPEAK, 600)
# 左边界由触发条件与最小相容易感池共同给出
xl = np.maximum(np.maximum(XMIN, eg / IMAX_NO), N_FLOOR)
cumN_i = np.interp(eg, cum_eta, cum_N, left=np.nan, right=np.nan)
xr_cum = np.minimum(eg / th_cost, cumN_i)
valid_cum = np.isfinite(xr_cum) & (xr_cum > xl)
# background W_pcd wedge (neutral, opaque)
axb.fill_between(Ng, th_cost * Ng, np.minimum(peak, IMAX_NO * Ng),
                 where=(np.minimum(peak, IMAX_NO * Ng) > th_cost * Ng) & (Ng >= N_FLOOR),
                 color=C_WEDGE_B, alpha=1.0, lw=0, zorder=1)
# 累计占优区：[N_FLOOR, min(eta/th_cost, N_cum)] 的窄条。它只有约 1.11 倍宽，
# 在三个数量级的对数横轴上仅几个像素，故加深填充色并描边，否则读者会以为是空集。
axb.fill_betweenx(eg, xl, xr_cum, where=valid_cum,
                  color="#9FD4D1", alpha=1.0, lw=0, zorder=2.5)
# 清零占优区为空集：清零弧全段 (max N = 2439) 位于 N_FLOOR 左侧，故不填充。
# neutral-grey constraint skeleton (distinguished by linestyle)
axb.plot(Ng, IMAX_NO * Ng, color=C_SKEL_LIGHT, lw=LW_AUX, ls=":", zorder=4)
axb.axhline(IPEAK, color=C_SKEL, lw=LW_SKELETON + 0.05, alpha=0.75, zorder=4)
axb.plot(Ng, th_cost * Ng, color=C_SKEL, lw=LW_SKELETON + 0.05, alpha=0.75, zorder=4)
axb.plot(Ng, th_d45 * Ng, color=C_SKEL_LIGHT, lw=LW_AUX, ls="--", zorder=4)
axb.plot(Ng, th_d150 * Ng, color=C_SKEL_LIGHT, lw=LW_AUX, ls="-.", zorder=4)
# colour arcs (PCHIP-smoothed for display)
cum_Ns, cum_es = pchip_loglog(cum_N, cum_eta)
clr_Ns, clr_es = pchip_loglog(clr_N, clr_eta)
# cum arc crosses the cost line at eta~=19.5: inside the wedge -> solid;
# the out-of-wedge tail (below the crossing) -> faded dashed (contour continues
# but no longer bounds W_cum, whose boundary there is the cost line)
_egf = np.linspace(cum_eta.min(), cum_eta.max(), 20000)
_d = np.interp(_egf, cum_eta, cum_N) - _egf / th_cost
_k = np.where(np.diff(np.sign(_d)))[0]
ec = float(_egf[_k[0]]) if len(_k) else cum_eta.min()
Nc = ec / th_cost
# 先整条淡虚线画出（等值线继续存在），再把"确实构成 W_cum 边界"的一段覆以实线。
# 有效段同时要求：在楔形内 (eta >= ec) 且不低于下界 (N >= N_FLOOR，即 eta <= ETA_CUM_FLOOR)
axb.plot(cum_Ns, cum_es,
         color=C_CUM, lw=1.5, ls=(0, (4, 2)), alpha=0.5, zorder=6)
eff = (cum_es >= ec) & (cum_es <= ETA_CUM_FLOOR)
axb.plot(cum_Ns[eff], cum_es[eff], color=C_CUM, lw=1.5, zorder=7)
# 清零弧：全段位于 N_FLOOR 左侧（与观测不相容），故全线虚线，不再有实线段
axb.plot(clr_Ns, clr_es,
         color=C_CLR, lw=1.5, ls=(0, (4.5, 2.2)), alpha=0.85, zorder=7)
draw_floor(axb, label=False)
# N* vertical line removed -> the decomposition intersections (N*_45, N*_cost,
# N_cum, N_clr, domain wall) are reported in the caption / main text instead
# cross-figure sampling markers (circle = Panel A, square = Panel B)
for r, x, y in A_pts:
    axb.scatter([x], [y], s=S_A, marker="o", fc=RC_COL[r], ec="white", lw=MK_LW,
                alpha=0.85 if r == "clr" else 1.0, zorder=9)
for r, x, y in B_pts:
    axb.scatter([x], [y], s=S_B, marker="s", fc=RC_COL[r], ec="white", lw=MK_LW,
                alpha=0.85 if r == "clr" else 1.0, zorder=9)
axfmt(axb, "(b)", ylabel=False)
legb = [Line2D([], [], color=C_CUM, lw=1.5, label="cumulative"),
        Line2D([], [], color=C_CLR, lw=1.5, ls=(0, (4.5, 2.2)), alpha=0.85,
               label=r"clear $\leq$ 45.3 d"),
        Line2D([], [], color=C_FLOOR, lw=1.6, label=r"$N_{\rm floor}$"),
        Line2D([], [], color=C_SKEL, lw=LW_SKELETON + 0.05, label="constraint skeleton")]
axb.legend(handles=legb, loc="lower right", borderaxespad=0.45)

fig.savefig(OUT / "fig_dom_combined.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_dom_combined.png", dpi=400, bbox_inches="tight")
plt.close(fig)
print("saved combined ->", OUT / "fig_dom_combined.(pdf|png)")
print("N_cum(100)=%.0f  N_clr(100)=%.0f  N*_45=%.0f"
      % (np.interp(100, cum_eta, cum_N), np.interp(100, clr_eta, clr_N), Nstar_45))
