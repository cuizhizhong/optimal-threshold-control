"""Fast plot of Panel B from cached panelB.pkl next to this file (no solving).
Two stacked axes: (a) I(t) with routine/TDINN ribbons, (b) q_c(t)."""
import pickle, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pathlib import Path

OUT = Path(__file__).resolve().parent / "dominance_panels"
CACHE = Path(__file__).resolve().parent / "panelB.pkl"
IPEAK_T, ETA = 151.90, 100.0
Q0, QINF = 0.3230, 1.0 - 1.0 / (2.0 * (1.0 - 0.1498))   # 0.4119
COL = {"interior": "#6a3d9a", "dur45": "#4575b4", "cost": "#e08214", "dur150": "#2ca25f",
       "clear": "#c0563f", "cum": "#2f6db0"}
LS = {"interior": ":", "dur45": "-", "cost": "--", "dur150": "-.", "clear": "-", "cum": "-"}
LAB = {"interior": r"interior", "dur45": "dur 45 d", "cost": "cost", "dur150": "dur 150 d",
       "clear": r"clear $\leq$ 45.3 d", "cum": "cumulative"}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "STIX", "DejaVu Serif"],
    "mathtext.fontset": "stix", "axes.unicode_minus": False,
    "font.size": 9.0, "axes.labelsize": 10.0, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 7.2, "axes.linewidth": 0.9, "axes.edgecolor": "#444444",
    "xtick.color": "#555", "ytick.color": "#555", "xtick.labelcolor": "#222", "ytick.labelcolor": "#222",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.1, "legend.labelspacing": 0.3,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

D = pickle.load(open(CACHE, "rb"))
roles, tend, tg = D["roles"], D["tend"], D["tg"]
# 目标: tight bbox 宽度 = 451.28 bp (= \textwidth, A4 减左右各 1 in)，
# 使 \includegraphics[width=\textwidth] 缩放为 1.0×。改 figsize 后须用 pdfinfo 复量。
fig, (axi, axq) = plt.subplots(2, 1, figsize=(6.164, 5.459), sharex=True,
                               gridspec_kw={"height_ratios": [1.15, 1.0]},
                               constrained_layout=True)

# ================= (a) I(t) with ribbons =================
rlo, rhi = D["rlo"], D["rhi"]
# 绘制到最后一条成员清零为止；下包络已在 compute 端按判据 I=1 收口。
m = np.isfinite(rlo) & np.isfinite(rhi) & (rhi > 1.0)
axi.fill_between(tg[m], rlo[m], rhi[m], color="#8a8a8a", alpha=0.16, lw=0, zorder=1)
axi.plot(tg[m], rlo[m], color="#8a8a8a", lw=0.6, alpha=0.55, zorder=1)
axi.plot(tg[m], rhi[m], color="#8a8a8a", lw=0.6, alpha=0.55, zorder=1)
for N, d in D["rep_r"].items():
    axi.plot(d["t"], d["I"], color="#8a8a8a", lw=1.0, ls=":", alpha=0.9, zorder=2)
_td = D["tdinn_I"]
axi.plot(_td["t"], _td["I"], color="#222222", lw=1.4, ls="-", alpha=0.95, zorder=4)
for r in roles:
    b = D["built"][r]
    axi.plot(b["t"], b["I"], color=COL[r], ls=LS[r], lw=1.6, zorder=5)
axi.axhline(IPEAK_T, color="#b2182b", lw=0.9, ls=":", alpha=0.75, zorder=1)
axi.text(tend * 0.995, IPEAK_T * 1.06, r"$I_{\rm peak}^{\rm T}$", fontsize=7.6, color="#b2182b", ha="right", va="bottom")
axi.axhline(ETA, color="#999", lw=0.7, ls="--", alpha=0.55, zorder=1)
axi.set_yscale("log"); axi.set_ylabel(r"$I(t)$"); axi.set_ylim(1, 1.5e4); axi.set_xlim(0, tend)
axi.text(-0.008, 1.02, "(a)", transform=axi.transAxes, fontsize=11, fontweight="bold",
         ha="left", va="bottom", color="#222")
def _lab(r):                                   # 角色名 + 该曲线对应的 N_eff
    return rf"{LAB[r]}  ($N{{=}}{D['built'][r]['N']:,.0f}$)"
handles = [Line2D([], [], color=COL[r], ls=LS[r], lw=1.6, label=_lab(r)) for r in roles]
handles += [Line2D([], [], color="#222222", lw=1.4, label="TDINN"),
            Patch(fc="#8a8a8a", alpha=0.32, label="routine band")]
axi.legend(handles=handles, loc="upper right", ncol=2, columnspacing=1.2, borderaxespad=0.4)
axi.tick_params(length=3.5, width=0.8)

# ================= (b) q_c(t) =================
axq.axhline(Q0, color="#666", lw=0.9, ls=":", zorder=1)
axq.axhline(QINF, color="#999", lw=0.9, ls="--", zorder=1)
axq.text(tend * 0.995, Q0 + 0.012, r"$q_0$", fontsize=7.6, color="#666", ha="right", va="bottom")
axq.text(tend * 0.995, QINF + 0.012, r"$q_{\mathrm{inf}}$", fontsize=7.6, color="#999", ha="right", va="bottom")
tq = D["tdinn_q"]
axq.plot(tq["t"], tq["q"], color="#222222", lw=1.4, ls="-", alpha=0.95, label=r"TDINN $q$ (rising)", zorder=3)
for r in roles:
    b = D["built"][r]
    axq.plot(b["t"], b["q"], color=COL[r], ls=LS[r], lw=1.6, zorder=5)
    if np.isfinite(b["qi"]):
        axq.scatter([b["ti"]], [b["qi"]], s=26, marker="o", fc="white", ec=COL[r], lw=1.1, zorder=6)
axq.set_ylabel(r"$q_c(t)$"); axq.set_xlabel(r"time $t$ (days)")
axq.set_ylim(0.29, 1.02); axq.set_xlim(0, tend)
axq.text(-0.008, 1.02, "(b)", transform=axq.transAxes, fontsize=11, fontweight="bold",
         ha="left", va="bottom", color="#222")
axq.tick_params(length=3.5, width=0.8)

fig.savefig(OUT / "fig_panel_B.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_panel_B.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("saved Panel B (2-row) ; t_end=%.0f" % tend)
