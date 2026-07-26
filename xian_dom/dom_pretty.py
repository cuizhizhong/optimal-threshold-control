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
IPEAK, IMAX_NO = 151.90, 0.1047
th_cost, th_d45, th_d150 = 1.656e-3, 3.762e-3, 1.137e-3
th_int = 5.612e-3
Nstar_45 = IPEAK / th_d45          # strict caliber ~= 40377

# ---------- arcs (embedded) ----------
cum_eta = np.array([10, 11.99, 14.37, 17.23, 20.66, 24.77, 29.69, 35.60,
                    42.67, 51.16, 61.33, 73.53, 88.15, 105.69, 126.70, 151.90])
cum_N = np.array([12177, 12075, 11966, 11848, 11720, 11583, 11435, 11276,
                  11104, 10918, 10719, 10504, 10273, 10025, 9758, 9471], float)
clr_N = np.array([
    1125.00, 1135.00, 1150.00, 1170.00, 1200.00, 1250.00, 1300.00, 1350.00, 1400.00, 1450.00,
    1500.00, 1539.00, 1692.00, 1860.00, 2045.00, 2096.76, 2249.00, 2472.00, 2718.00, 2988.00,
    3285.00, 3611.00, 3970.00, 4365.00, 4799.00, 5276.00, 5800.00, 5914.28], float)
clr_eta = np.array([
    10.1121, 10.2567, 10.4757, 10.7710, 11.2218, 11.9921, 12.7852, 13.5995, 14.4342, 15.2883,
    16.1612, 16.8546, 19.6776, 22.9581, 26.7787, 27.8858, 31.2378, 36.3967, 42.4289, 49.4513,
    57.6533, 67.2339, 78.4689, 91.6684, 107.1742, 125.4387, 146.9905, 151.9000])
# 有效池下界：真实疫情总累计感染 I^T_tcum=2096.76 人，有效混合池至少要装得下这些人，
# 否则"累计不劣于 TDINN"只是池子容量所迫的算术必然，与控制优劣无关。
# 该下界 (N=2096.76, eta*=27.8858, 求解器校验 clear=45.27 d) 比 I0=1 域墙 (N~1118) 更早绑定。
N_FLOOR, ETA_FLOOR = 2096.76, 27.8858
# top point (5827.5, IPEAK): clr contour meets the peak ceiling -> arc terminates
# exactly on the peak line (solver: clear=45.000 there), same as cum arc top (9471, IPEAK)


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
    "axes.linewidth": 0.9, "axes.edgecolor": "#444444",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#555555", "ytick.color": "#555555",
    "xtick.labelcolor": "#222222", "ytick.labelcolor": "#222222",
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1,
    "legend.handletextpad": 0.6, "legend.labelspacing": 0.28,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.pad_inches": 0.03,
})

# line-weight hierarchy
LW_MAIN, LW_PRIMARY, LW_SECONDARY, LW_SKELETON, LW_AUX = 2.00, 1.80, 1.50, 1.00, 0.90
S_A, S_B, MK_LW = 18, 16, 0.7          # small sampling markers, consistent across (a)/(b)

# colours
C_PEAK, C_COST, C_D45, C_D150, C_TRIG = "#b2182b", "#4575b4", "#6f8faf", "#5a9e8f", "#c9ced3"
C_WEDGE_A = "#E7EDF4"
C_CUM, C_CLR = "#2f6db0", "#c0563f"
C_SKEL, C_SKEL_LIGHT = "#A6AFB8", "#C2CAD2"
C_WEDGE_B, C_CUM_FILL, C_CLR_FILL = "#EDF1F5", "#D8E6F3", "#EFDAD5"
RC_COL = {"int": "#6a3d9a", "d45": "#4575b4", "cost": "#e08214", "d150": "#2ca25f",
          "clr": C_CLR, "cum": C_CUM}

XMIN, XMAX, YMIN, YMAX = 1e3, 1e6, 10., 4e3
Ng = np.logspace(3, 6, 700)
peak = np.full_like(Ng, IPEAK)

A_pts = [("int", 2e4, th_int * 2e4), ("d45", 2e4, th_d45 * 2e4),
         ("cost", 2e4, th_cost * 2e4), ("d150", 2e4, th_d150 * 2e4)]
B_pts = [("int", 100 / th_int, 100), ("d45", 100 / th_d45, 100),
         ("cost", 100 / th_cost, 100), ("d150", 100 / th_d150, 100),
         ("clr", 4601.9, 100),          # 直接求根值，与 Panel B 的 clear 角色一致
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


# 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
# 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.288, 2.925), sharey=True,
                               constrained_layout=True)

# ================= (a) straight-line family =================
axa.fill_between(Ng, th_cost * Ng, np.minimum(peak, IMAX_NO * Ng),
                 where=np.minimum(peak, IMAX_NO * Ng) > th_cost * Ng,
                 color=C_WEDGE_A, alpha=1.0, lw=0, zorder=1)
axa.plot(Ng, IMAX_NO * Ng, color=C_TRIG, lw=LW_AUX, ls=":", alpha=0.85, zorder=3)
axa.axhline(IPEAK, color=C_PEAK, lw=LW_PRIMARY, zorder=5)
axa.plot(Ng, th_cost * Ng, color=C_COST, lw=LW_PRIMARY, zorder=5)
axa.plot(Ng, th_d45 * Ng, color=C_D45, lw=LW_SECONDARY, ls="--", zorder=4)
axa.plot(Ng, th_d150 * Ng, color=C_D150, lw=LW_SECONDARY, ls="-.", zorder=4)
# N* vertex marker removed -> reported in caption (N*_45 = IPEAK/th_d45 ~= 40377)
for r, x, y in A_pts:
    axa.scatter([x], [y], s=S_A, marker="o", fc=RC_COL[r], ec="white", lw=MK_LW, zorder=10)
axfmt(axa, "(a)", ylabel=True)
lega = [Line2D([], [], color=C_PEAK, lw=LW_PRIMARY, label=r"peak $I_{\rm peak}^{\rm T}$"),
        Line2D([], [], color=C_COST, lw=LW_PRIMARY, label="cost"),
        Line2D([], [], color=C_D45, lw=LW_SECONDARY, ls="--", label="dur 45 d"),
        Line2D([], [], color=C_D150, lw=LW_SECONDARY, ls="-.", label="dur 150 d"),
        Line2D([], [], color=C_TRIG, lw=LW_AUX, ls=":", label="trigger")]
axa.legend(handles=lega, loc="lower right", borderaxespad=0.45)

# ================= (b) arc family =================
eg = np.geomspace(YMIN, IPEAK, 600)
xl = np.maximum(XMIN, eg / IMAX_NO)
cumN_i = np.interp(eg, cum_eta, cum_N, left=np.nan, right=np.nan)
clrN_i = np.interp(eg, clr_eta, clr_N, left=np.nan, right=np.nan)
xr_cum = np.minimum(eg / th_cost, cumN_i)
xr_clr = np.minimum(eg / th_cost, clrN_i)
valid_cum = np.isfinite(xr_cum) & (xr_cum > xl)
valid_clr = np.isfinite(xr_clr) & (xr_clr > xl)
# background W_pcd wedge (neutral, opaque)
axb.fill_between(Ng, th_cost * Ng, np.minimum(peak, IMAX_NO * Ng),
                 where=np.minimum(peak, IMAX_NO * Ng) > th_cost * Ng,
                 color=C_WEDGE_B, alpha=1.0, lw=0, zorder=1)
# clr inner region
x_inner = np.where(valid_clr, np.minimum(xr_clr, np.where(valid_cum, xr_cum, xr_clr)), xl)
axb.fill_betweenx(eg, xl, x_inner, where=valid_clr & (x_inner > xl),
                  color=C_CLR_FILL, alpha=1.0, lw=0, zorder=3)
# cumulative outer annulus (excludes clr)
x_outer_left = np.maximum(xl, np.where(valid_clr, x_inner, xl))
axb.fill_betweenx(eg, x_outer_left, xr_cum, where=valid_cum & (xr_cum > x_outer_left),
                  color=C_CUM_FILL, alpha=1.0, lw=0, zorder=2)
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
up = cum_es >= ec
axb.plot(np.r_[Nc, cum_Ns[up]], np.r_[ec, cum_es[up]],
         color=C_CUM, lw=LW_MAIN, zorder=7)                       # inside wedge (solid)
axb.plot(np.r_[cum_Ns[~up], Nc], np.r_[cum_es[~up], ec],
         color=C_CUM, lw=1.30, ls=(0, (4, 2)), alpha=0.5, zorder=6)  # out-of-wedge tail (faded dashed)
_uc = clr_es >= ETA_FLOOR
axb.plot(np.r_[N_FLOOR, clr_Ns[_uc]], np.r_[ETA_FLOOR, clr_es[_uc]],
         color=C_CLR, lw=LW_MAIN, zorder=8)                              # 有效池内(实线)
axb.plot(np.r_[clr_Ns[~_uc], N_FLOOR], np.r_[clr_es[~_uc], ETA_FLOOR],
         color=C_CLR, lw=1.70, ls=(0, (4.5, 2.2)), alpha=0.90, zorder=7)  # N<I^T_tcum: 仍是边界,虚线示意
# N* vertical line removed -> the decomposition intersections (N*_45, N*_cost,
# N_cum, N_clr, domain wall) are reported in the caption / main text instead
# cross-figure sampling markers (circle = Panel A, square = Panel B)
for r, x, y in A_pts:
    axb.scatter([x], [y], s=S_A, marker="o", fc=RC_COL[r], ec="white", lw=MK_LW, zorder=9)
for r, x, y in B_pts:
    axb.scatter([x], [y], s=S_B, marker="s", fc=RC_COL[r], ec="white", lw=MK_LW, zorder=9)
axfmt(axb, "(b)", ylabel=False)
legb = [Line2D([], [], color=C_CUM, lw=LW_MAIN, label="cumulative"),
        Line2D([], [], color=C_CLR, lw=LW_MAIN, label=r"clear $\leq$ 45.3 d"),
        Line2D([], [], color=C_SKEL, lw=LW_SKELETON + 0.05, label="constraint skeleton")]
axb.legend(handles=legb, loc="lower right", borderaxespad=0.45)

fig.savefig(OUT / "fig_dom_combined.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_dom_combined.png", dpi=400, bbox_inches="tight")
plt.close(fig)
print("saved combined ->", OUT / "fig_dom_combined.(pdf|png)")
print("N_cum(100)=%.0f  N_clr(100)=%.0f  N*_45=%.0f"
      % (np.interp(100, cum_eta, cum_N), np.interp(100, clr_eta, clr_N), Nstar_45))
