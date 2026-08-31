"""Figure 22 (fig_panel_B) 的 N_eff 轨迹分解图：把三类 I(t) 轨迹按 N_eff 拆开画。

新增文件，唯一目的是让 N_eff 对常规控制轨迹、阈值平台时长的影响直接可读；不进正文、
不带图题/图例，只保留 (a)-(f) 角标。产物写到 dominance_panels/ 下的新文件名，不覆盖
fig_panel_B.pdf，不进 figures/，不改 .tex（见 22-steady-cookie.md 计划）。

依赖处理（务必遵守）：
  - 绝不 import plot_B ——它是脚本式模块，import 会立刻重绘并覆盖
    dominance_panels/fig_panel_B.pdf。因此 threshold_q_parts 函数与 COL/ETA/IPEAK_T/
    Q0/ALPHA/ROLE_LW 常量都是从 plot_B.py 原样复制过来的（而非 import），下面逐一标注。
  - import panels 是安全的：其绘图入口都挂在 if __name__ == "__main__" 之下，import
    只会触发 rcParams 设置、OUT.mkdir、caliber 求根等副作用，不会重绘任何图。rcParams
    直接沿用 panels 导入时设好的那一份（serif/Times、font.size 9.0、pdf.fonttype 42 等），
    本文件不再重复设置。

横轴口径（定版决策，勿随手改回共用横轴）：六格 xlim 各自贴合自身内容，
xmax = 1.05 x 该格实际画到的最晚清零时刻。这样 (a)/(b) 的三条线才分得开——共用横轴时
clear/cum 两格的 threshold、conventional、TDINN 会挤成一团。
**代价**：第一排四格的横轴随平台一起放大，平台时长从 6.3 d 涨到 102.8 d（16 倍）这件事
在图上看不出来，四个平台宽度看着差不多。因此 **N 杠杆对平台时长的作用必须由正文文字
补足**，不能指望读者从第一排读出来；(f) 把四条平台叠在同一横轴上，是图内唯一能直读
时长差异的地方。写图注/正文解释本图意义时务必补这一句。

figsize 说明：figsize=(6.151, 4.0) 已按 xian_dom/README.md 的规矩复量，tight bbox
= 451.26 bp（目标 451.28 = 主论文 \textwidth），故正文用 width=\textwidth 时缩放 1.0x。
改 figsize 后必须用 pdfinfo 复量（bbox_inches="tight" 使成图尺寸 != figsize）。
"""
import sys
import pickle
from pathlib import Path

import numpy as np

# ---- sys.path 注入：原样抄自 compute_B.py:6-11，使 panels/threshold_landscape_analysis
#      等模块无论从哪个工作目录运行都能被找到 ----
_XCC = Path(__file__).resolve().parent.parent / "xian_control_comparison"
for _p in (_XCC, _XCC / "threshold_landscape_analysis", _XCC / "effective_population_sensitivity"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# panels 的导入是安全的（见上方文档字符串），顺带把 rcParams 设好。
from panels import prep, N_OF
# epidemic_clear_time 用于常规控制清零时刻；确认过该名字在模块里是公开的
# (threshold_landscape_analysis.py:625: def epidemic_clear_time(df, threshold=1.0))。
import threshold_landscape_analysis as tla

HERE = Path(__file__).resolve().parent
OUT = HERE / "dominance_panels"
CACHE = HERE / "panelB.pkl"

# ---- 常量：原样复制自 plot_B.py:16-23（不 import plot_B 的替代方案，见上）----
COL = {"interior": "#084a91", "dur45": "#073068", "cost": "#206FB6", "dur150": "#6BADD7",
       "clear": "#9a6b5a", "cum": "#238b8e"}
ROLE_LW = {"interior": 1.8, "dur45": 1.8, "cost": 2.0, "dur150": 1.8,
           "clear": 1.8, "cum": 1.8}
ALPHA = {"clear": 0.85}
IPEAK_T = 151.90
ETA = 100.0
Q0 = 0.3230


def threshold_q_parts(t, I, q, q0=Q0, tol=1e-8):
    """从缓存恢复控制段及 t1、t2、动态清零时刻。

    原样复制自 plot_B.py:26-45（同源，不能 import plot_B 的原因见文件头注释）。
    """
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


# ---- 数据 ----
roles = ["clear", "cum", "dur45", "cost"]   # 丢弃 dur150 (N=87944) 与从不入图的 interior

with open(CACHE, "rb") as f:
    D = pickle.load(f)

built = {r: D["built"][r] for r in roles}   # 阈值控制 I(t)/t_inf/q_inf/N，直接读缓存，不重算
tdinn_I = D["tdinn_I"]                       # TDINN，单条固定曲线，不随 N_eff 变

# 常规控制 I(t)：缓存里只有 8 条几何间隔包络成员，不含这 4 个 N，因此需要重新求解。
# prep(N)[2] 与 compute_B.py:45 求包络成员时逐字相同的求解调用，口径不变。
rout = {r: prep(N_OF[r])[2] for r in roles}

thr_parts = {r: threshold_q_parts(built[r]["t"], built[r]["I"], built[r]["q"]) for r in roles}


def _conv_clear_time(df):
    """常规控制清零时刻，判据 I<=1。优先用 tla.epidemic_clear_time；
    若该封装不可用则退回取解序列的最后一个时刻（routine 求解本身以清零事件终止）。
    经核实 epidemic_clear_time 在本仓库中是公开的（见上方 import 处注释），这里仍保留
    try/except 作为防御。"""
    try:
        t_clear, cleared = tla.epidemic_clear_time(df)
        if np.isfinite(t_clear):
            return float(t_clear)
    except Exception:
        pass
    return float(df["t"].iloc[-1])


conv_peak = {r: float(rout[r]["I"].max()) for r in roles}
conv_tpeak = {r: float(rout[r]["t"].iloc[int(rout[r]["I"].to_numpy().argmax())]) for r in roles}
conv_clear = {r: _conv_clear_time(rout[r]) for r in roles}

thr_t1 = {r: thr_parts[r]["t1"] for r in roles}
thr_tinf = {r: float(built[r]["ti"]) for r in roles}
thr_t2 = {r: thr_parts[r]["t2"] for r in roles}
thr_dt = {r: thr_t2[r] - thr_t1[r] for r in roles}
thr_clear = {r: thr_parts[r]["clear"] for r in roles}

# ---- 校验表（口径未变的证据） ----
print(f"{'role':6s} {'N_eff':>9s} {'thr_t1':>8s} {'thr_tinf':>9s} {'thr_t2':>8s} "
      f"{'thr_dt':>8s} {'thr_clear':>10s} | {'conv_peak':>10s} {'conv_tpeak':>11s} {'conv_clear':>11s}")
for r in roles:
    print(f"{r:6s} {N_OF[r]:9.1f} {thr_t1[r]:8.3f} {thr_tinf[r]:9.3f} {thr_t2[r]:8.3f} "
          f"{thr_dt[r]:8.3f} {thr_clear[r]:10.3f} | {conv_peak[r]:10.1f} {conv_tpeak[r]:11.3f} {conv_clear[r]:11.3f}")

_tdinn_i = np.asarray(tdinn_I["I"], dtype=float)
_tdinn_t = np.asarray(tdinn_I["t"], dtype=float)
tdinn_peak = float(_tdinn_i.max())
tdinn_tpeak = float(_tdinn_t[int(_tdinn_i.argmax())])
tdinn_clear = float(_tdinn_t[-1])
print(f"TDINN peak={tdinn_peak:.2f} at t={tdinn_tpeak:.2f}  clear={tdinn_clear:.3f}  (fixed across all N_eff)")

XMAX_ALL = 1.05 * max(max(thr_clear.values()), max(conv_clear.values()))
XMAX_E = 1.05 * max(conv_clear.values())
# 第三版：逐格自适应，每个面板只按自身画到的内容定 xmax，六格不共用横轴。
# (a)-(d) 取该 N 下 threshold / conventional / TDINN 三条线清零时刻的最大值；
# (f) 只画 threshold + TDINN，故不含 conventional；(e) 只含 conventional，即 XMAX_E。
XMAX_TOP_SELF = {r: 1.05 * max(thr_clear[r], conv_clear[r], tdinn_clear) for r in roles}
XMAX_F_SELF = 1.05 * max(max(thr_clear.values()), tdinn_clear)
print(f"XMAX_ALL={XMAX_ALL:.2f}  XMAX_E={XMAX_E:.2f}  XMAX_F_SELF={XMAX_F_SELF:.2f}")
print("XMAX per-panel (a)-(d): " + "  ".join(f"{r}={XMAX_TOP_SELF[r]:.2f}" for r in roles))

# 绘制顺序：与图 22 同规则，按清零时刻降序绘制，使清零早的短曲线压在重合段上层。
order_e = sorted(roles, key=lambda r: conv_clear[r], reverse=True)
order_f = sorted(roles, key=lambda r: thr_clear[r], reverse=True)

panel_label = {"clear": "(a)", "cum": "(b)", "dur45": "(c)", "cost": "(d)"}


def _corner(ax, label):
    ax.text(-0.008, 1.02, label, transform=ax.transAxes, fontsize=11, fontweight="bold",
             ha="left", va="bottom", color="#222")


def _refs(ax):
    """两条弱化参照线，六格都画。"""
    ax.axhline(ETA, color="#999", lw=0.9, ls=":", alpha=0.55, zorder=1)
    ax.axhline(IPEAK_T, color="#a50518f4", lw=1.0, ls="--", alpha=0.50, zorder=1)


def render(stem, xmax_top, xmax_e, xmax_f):
    """xmax_top: {role: xmax} 用于 (a)-(d)；xmax_e/xmax_f 分别用于 (e)/(f)。
    传入相同值即为共用横轴版，传入逐格值即为自适应版。"""
    fig = plt.figure(figsize=(6.151, 4.0), constrained_layout=True)
    gs = GridSpec(2, 4, figure=fig)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_top = {"clear": ax_a}
    for col, r in zip((1, 2, 3), ("cum", "dur45", "cost")):
        ax_top[r] = fig.add_subplot(gs[0, col], sharey=ax_a)
    ax_e = fig.add_subplot(gs[1, 0:2], sharey=ax_a)
    ax_f = fig.add_subplot(gs[1, 2:4], sharey=ax_a)

    # ---- (a)-(d): 该 N 的 threshold(实线) + conventional(虚线) + 固定 TDINN(黑实线) ----
    for r in roles:
        ax = ax_top[r]
        _refs(ax)
        ax.plot(rout[r]["t"], rout[r]["I"], color=COL[r], ls="--", lw=1.4, zorder=2)
        ax.plot(_tdinn_t, _tdinn_i, color="#222222", ls="-", lw=1.6, alpha=0.95, zorder=3)
        ax.plot(built[r]["t"], built[r]["I"], color=COL[r], ls="-", lw=ROLE_LW[r],
                alpha=ALPHA.get(r, 1.0), zorder=4)
        if np.isfinite(built[r]["qi"]):
            ax.scatter([built[r]["ti"]], [ETA], s=28, marker="o", fc=COL[r], ec="white",
                       linewidths=0.6, alpha=ALPHA.get(r, 1.0), zorder=6)
        ax.set_yscale("log")
        ax.set_ylim(1, 1.5e4)
        ax.set_xlim(0, xmax_top[r])
        ax.set_xlabel(r"time $t$ (days)")
        _corner(ax, panel_label[r])
        if r == "clear":
            ax.set_ylabel(r"$I(t)$")
        else:
            ax.tick_params(labelleft=False)

    # ---- (e): 四个 N 的 conventional I(t)，全部实线；不画 threshold、不画 TDINN ----
    _refs(ax_e)
    for r in order_e:
        ax_e.plot(rout[r]["t"], rout[r]["I"], color=COL[r], ls="-", lw=1.4, zorder=2)
    ax_e.set_yscale("log")
    ax_e.set_ylim(1, 1.5e4)
    ax_e.set_xlim(0, xmax_e)
    ax_e.set_xlabel(r"time $t$ (days)")
    ax_e.set_ylabel(r"$I(t)$")
    _corner(ax_e, "(e)")

    # ---- (f): 四个 N 的 threshold I(t) + 拐点标记 + 唯一一条 TDINN；不画 conventional ----
    _refs(ax_f)
    ax_f.plot(_tdinn_t, _tdinn_i, color="#222222", ls="-", lw=1.6, alpha=0.95, zorder=3)
    for r in order_f:
        ax_f.plot(built[r]["t"], built[r]["I"], color=COL[r], ls="-", lw=ROLE_LW[r],
                  alpha=ALPHA.get(r, 1.0), zorder=4)
        if np.isfinite(built[r]["qi"]):
            ax_f.scatter([built[r]["ti"]], [ETA], s=28, marker="o", fc=COL[r], ec="white",
                        linewidths=0.6, alpha=ALPHA.get(r, 1.0), zorder=6)
    ax_f.set_yscale("log")
    ax_f.set_ylim(1, 1.5e4)
    ax_f.set_xlim(0, xmax_f)
    ax_f.set_xlabel(r"time $t$ (days)")
    ax_f.tick_params(labelleft=False)
    _corner(ax_f, "(f)")

    pdf_path = OUT / f"{stem}.pdf"
    png_path = OUT / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {stem}")


# 定版：六格横轴各自贴合自身内容（见文件头"横轴口径"一节）。
render("fig_panel_B_trajectory_decomposition", XMAX_TOP_SELF, XMAX_E, XMAX_F_SELF)

# 曾比较过的另两版横轴口径，保留调用方式备查（默认不生成）：
#   共用横轴:  render(stem, {r: XMAX_ALL for r in roles}, XMAX_ALL, XMAX_ALL)
#   仅 e 放大: render(stem, {r: XMAX_ALL for r in roles}, XMAX_E,   XMAX_ALL)
