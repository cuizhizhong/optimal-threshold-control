"""权衡前沿图 (trade-off frontier)。

把情景一阈值控制看成单参数族：以实际社区感染峰值 max I 为横轴（对数），
控制代价为纵轴（对数），画出随阈值 eta 扫描的前沿曲线，再把 TDINN 控制
和常规控制各作为一个点叠上去。

主图 (1x3, 共享横轴 max I)：
  - 控制时长 Delta t
  - 清零时间 T_clear
  - 二次加权成本 J

成本口径对照图 (1x2)：
  - 积分成本 J
  - 日均成本率 J / Delta t
用来说明低 eta 下 J 爆炸主要来自超长 Delta t，而非每天强度高。

数据来源：
  - cost_weight_analysis/cost_summary_wq2.csv  : 阈值控制 eta 扫描 (情景一阈值控制)
  - ../../xian_control_comparison_summary.csv   : TDINN / 常规控制参照点 (含 control_duration)

横轴统一用实际峰值 max I，使三条策略可比：对阈值控制 max I = eta；
TDINN 与常规的峰值不是 eta，只有用实际峰值才能落进同一坐标。

注意 (对数轴上的零值处理)：
  - 常规控制 Delta t = 0、J = 0，对数轴画不了，标注在轴底 (no enhanced control)。
  - 日均成本率里常规 Delta t = 0 会除零，直接跳过并标 N/A。

运行：conda run -n thesis python tradeoff_frontier.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "mathtext.fontset": "dejavusans",
        "figure.dpi": 120,
    }
)

HERE = Path(__file__).resolve().parent
COST_CSV = HERE.parent / "cost_weight_analysis" / "cost_summary_wq2.csv"
MAIN_SUMMARY = HERE.parents[1] / "xian_control_comparison_summary.csv"

N_POP = 13_163_000
ETA_CAP = 0.002 * N_POP  # 26326 = 医疗容量约束换算得到的社区感染者阈值

COLORS = {"threshold": "#c43c39", "tdinn": "#0068a9", "routine": "#333333"}
LABELS = {
    "threshold": "Threshold control (η sweep)",
    "tdinn": "TDINN control",
    "routine": "Routine control",
}
XLABEL = r"Community infection peak $\max I$"

METRICS = [
    ("control_duration", r"Control duration $\Delta t$ (days)"),
    ("clear_time", r"Clearance time $T_{\mathrm{clear}}$ (days)"),
    ("J", r"Quadratic weighted cost $J$"),
]


def load_data():
    """返回 (阈值扫描 DataFrame, TDINN 参照点 dict, 常规参照点 dict)。"""
    df = pd.read_csv(COST_CSV)
    thr = (
        df[df["strategy"] == "情景一阈值控制"]
        .loc[:, ["peak_I", "control_duration", "clear_time", "J"]]
        .dropna(subset=["peak_I", "control_duration", "clear_time", "J"])
        .sort_values("peak_I")
        .reset_index(drop=True)
    )
    main = pd.read_csv(MAIN_SUMMARY)

    def ref(name):
        row = main.loc[main["strategy"] == name].iloc[0]
        return {
            "peak_I": float(row["peak_I"]),
            "control_duration": float(row["control_duration"]),
            "clear_time": float(row["clear_time"]),
            "J": float(row["J"]),
        }

    tdinn = ref("TDINN控制")
    routine = ref("常规控制")
    return thr, tdinn, routine


def _legend_handles(include_cap=True):
    handles = [
        Line2D([0], [0], color=COLORS["threshold"], lw=1.9, marker="o", ms=4,
               label=LABELS["threshold"]),
        Line2D([0], [0], color=COLORS["tdinn"], marker="*", ms=12, ls="none",
               label=LABELS["tdinn"]),
        Line2D([0], [0], color=COLORS["routine"], marker="s", ms=7, ls="none",
               label=LABELS["routine"]),
    ]
    if include_cap:
        handles.append(
            Line2D([0], [0], color="#777777", lw=1.1, ls="-.",
                   label=r"$\eta_{\mathrm{cap}}=0.002N$")
        )
    return handles


def _plot_threshold_curve(ax, thr, col):
    ax.plot(thr["peak_I"], thr[col], "-", color=COLORS["threshold"], lw=1.9,
            marker="o", ms=3, zorder=3)


def _plot_reference(ax, pt, key, zero_note=None):
    """画一个参照点；若其值 <= 0（对数轴画不了），在轴底标注。"""
    v = pt["_y"]
    if v > 0:
        ax.scatter([pt["peak_I"]], [v], s=170 if key == "tdinn" else 90,
                   marker="*" if key == "tdinn" else "s", color=COLORS[key],
                   edgecolor="white", linewidth=0.6, zorder=6)
    elif zero_note is not None:
        y0 = ax.get_ylim()[0]
        ax.scatter([pt["peak_I"]], [y0], s=90, marker="s", color=COLORS[key],
                   edgecolor="white", linewidth=0.6, zorder=6, clip_on=False)
        ax.annotate(zero_note, xy=(pt["peak_I"], y0),
                    xytext=(0.97, 0.06), textcoords="axes fraction",
                    ha="right", va="bottom", fontsize=7.5, color=COLORS[key])


def plot_main(thr, tdinn, routine):
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4))
    for ax, (col, ylabel) in zip(axes, METRICS):
        _plot_threshold_curve(ax, thr, col)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.axvline(ETA_CAP, color="#777777", lw=1.1, ls="-.", zorder=1)
        for key, pt in (("tdinn", tdinn), ("routine", routine)):
            note = None
            if key == "routine" and pt[col] <= 0:
                sym = r"$\Delta t{=}0$" if col == "control_duration" else r"$J{=}0$"
                note = "Routine %s\n(no enhanced control)" % sym
            _plot_reference(ax, {**pt, "_y": pt[col]}, key, zero_note=note)
        ax.set_xlabel(XLABEL)
        ax.set_ylabel(ylabel)
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)
    axes[0].legend(handles=_legend_handles(), loc="best", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(HERE / "tradeoff_frontier_main.pdf")
    fig.savefig(HERE / "tradeoff_frontier_main.png", dpi=220)
    plt.close(fig)


def plot_cost_caliber(thr, tdinn, routine):
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.6, 4.4))

    # 左：积分成本 J
    _plot_threshold_curve(axL, thr, "J")
    axL.set_xscale("log")
    axL.set_yscale("log")
    axL.axvline(ETA_CAP, color="#777777", lw=1.1, ls="-.", zorder=1)
    _plot_reference(axL, {**tdinn, "_y": tdinn["J"]}, "tdinn")
    _plot_reference(axL, {**routine, "_y": routine["J"]}, "routine",
                    zero_note="Routine $J{=}0$\n(no enhanced control)")
    axL.set_xlabel(XLABEL)
    axL.set_ylabel(r"Integrated cost $J$")
    axL.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)

    # 右：日均成本率 J / Delta t
    daily_thr = thr["J"] / thr["control_duration"]
    axR.plot(thr["peak_I"], daily_thr, "-", color=COLORS["threshold"], lw=1.9,
             marker="o", ms=3, zorder=3)
    axR.set_xscale("log")
    axR.set_yscale("log")
    axR.axvline(ETA_CAP, color="#777777", lw=1.1, ls="-.", zorder=1)
    tdinn_daily = tdinn["J"] / tdinn["control_duration"]
    axR.scatter([tdinn["peak_I"]], [tdinn_daily], s=170, marker="*",
                color=COLORS["tdinn"], edgecolor="white", linewidth=0.6, zorder=6)
    axR.annotate("Routine: N/A\n($\\Delta t{=}0$)", xy=(0.97, 0.06),
                 xycoords="axes fraction", ha="right", va="bottom",
                 fontsize=7.5, color=COLORS["routine"])
    axR.set_xlabel(XLABEL)
    axR.set_ylabel(r"Daily cost rate $J/\Delta t$ (per day)")
    axR.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)

    axL.legend(handles=_legend_handles(), loc="best", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(HERE / "tradeoff_cost_caliber.pdf")
    fig.savefig(HERE / "tradeoff_cost_caliber.png", dpi=220)
    plt.close(fig)


def write_points_csv(thr, tdinn, routine):
    rows = []
    for _, r in thr.iterrows():
        rows.append(
            {
                "strategy": "threshold",
                "peak_I": r["peak_I"],
                "control_duration": r["control_duration"],
                "clear_time": r["clear_time"],
                "J": r["J"],
                "daily_J": r["J"] / r["control_duration"],
            }
        )
    for name, pt in (("tdinn", tdinn), ("routine", routine)):
        daily = pt["J"] / pt["control_duration"] if pt["control_duration"] > 0 else np.nan
        rows.append(
            {
                "strategy": name,
                "peak_I": pt["peak_I"],
                "control_duration": pt["control_duration"],
                "clear_time": pt["clear_time"],
                "J": pt["J"],
                "daily_J": daily,
            }
        )
    pd.DataFrame(rows).to_csv(HERE / "tradeoff_frontier_points.csv", index=False)


def print_diagnostics(thr, tdinn, routine):
    """峰值匹配诊断：在 TDINN 峰值附近，阈值控制要付多少代价。"""
    lo = thr.iloc[0]  # 最严阈值（峰值最低，最接近 TDINN 峰值一侧）
    print("[frontier] threshold sweep: %d points, peak_I in [%.1f, %.1f]"
          % (len(thr), thr["peak_I"].min(), thr["peak_I"].max()))
    print("[frontier] TDINN   : peak=%.1f  dt=%.2f  clear=%.2f  J=%.2f  daily_J=%.3f"
          % (tdinn["peak_I"], tdinn["control_duration"], tdinn["clear_time"],
             tdinn["J"], tdinn["J"] / tdinn["control_duration"]))
    print("[frontier] routine : peak=%.1f  dt=%.2f  clear=%.2f  J=%.2f"
          % (routine["peak_I"], routine["control_duration"], routine["clear_time"],
             routine["J"]))
    print("[frontier] threshold @lowest eta: peak=%.1f  dt=%.1f  clear=%.1f  J=%.1f  daily_J=%.3f"
          % (lo["peak_I"], lo["control_duration"], lo["clear_time"], lo["J"],
             lo["J"] / lo["control_duration"]))
    print("[frontier] near-equal-peak cost ratios (threshold@lowest / TDINN):"
          "  dt x%.0f   J x%.0f"
          % (lo["control_duration"] / tdinn["control_duration"],
             lo["J"] / tdinn["J"]))
    daily = thr["J"] / thr["control_duration"]
    print("[frontier] threshold daily_J range: [%.3f, %.3f] (near-constant vs %dx J range)"
          % (daily.min(), daily.max(), round(thr["J"].max() / thr["J"].min())))


def main():
    thr, tdinn, routine = load_data()
    plot_main(thr, tdinn, routine)
    plot_cost_caliber(thr, tdinn, routine)
    write_points_csv(thr, tdinn, routine)
    print_diagnostics(thr, tdinn, routine)
    print("[frontier] wrote figures + tradeoff_frontier_points.csv to %s" % HERE)


if __name__ == "__main__":
    main()
