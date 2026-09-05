#!/usr/bin/env python3
"""绘制完全不控制 q=0 与完全控制 q=1 的多初值相空间轨线。

模型（归一化人口比例）为

    s' = -c [p + (1-p) q] s I,
    I' =  p c (1-q) s I - gamma I.

脚本复用项目 ``python/common_tracing.py`` 中的基准参数，并利用 q=0、q=1
对应的解析不变量生成轨线。输出 PNG、PDF 和 SVG 三种格式。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.optimize import brentq


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PYTHON_DIR = PROJECT_DIR / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from common_tracing import Params  # noqa: E402


FIGURE_WIDTH_MM = 183.0
FIGURE_HEIGHT_MM = 112.0
X_LIMITS = (0.0, 1.0)
Y_LIMITS = (0.0, 0.40)
N_TRAJECTORY_POINTS = 1000

S_INITIALS = (0.25, 0.55, 0.85)
I_INITIALS = (0.02, 0.08, 0.14)

COLORS = {
    0.25: "#0072B2",
    0.55: "#D55E00",
    0.85: "#009E73",
}
LINESTYLES = {
    0.02: "-",
    0.08: "--",
    0.14: ":",
}


def positive_log_ratio(
    value: np.ndarray | float, reference: float
) -> np.ndarray | np.float64:
    """计算 log(value/reference)，并显式保护解析公式的正值域。"""
    value_array = np.asarray(value, dtype=float)
    if reference <= 0.0 or np.any(value_array <= 0.0):
        raise ValueError("对数不变量要求 s 和参考 s0 严格为正")
    return np.log(value_array / reference)


def configure_style() -> None:
    """设置适合中文论文图的可编辑字体和线条风格。"""
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "Arial",
                "DejaVu Sans",
                "sans-serif",
            ],
            "font.size": 7.2,
            "axes.labelsize": 8.0,
            "axes.titlesize": 8.6,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": 6.8,
            "ytick.labelsize": 6.8,
            "legend.fontsize": 6.6,
            "legend.frameon": False,
            "lines.linewidth": 1.55,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
        }
    )


def q0_terminal_s(s0: float, i0: float, h: float) -> float:
    """返回 q=0 轨线在 I=0 上的终点 s_infinity。"""

    def infectious(s: float) -> float:
        return float(i0 + s0 - s + h * positive_log_ratio(s, s0))

    upper = min(s0, h)
    lower = np.finfo(float).tiny ** 0.25
    if infectious(lower) >= 0.0 or infectious(upper) <= 0.0:
        raise RuntimeError(f"无法为 q=0 轨线找到终点：s0={s0}, I0={i0}")
    return float(brentq(infectious, lower, upper, xtol=1e-14, rtol=1e-13))


def q0_trajectory(s0: float, i0: float, par: Params) -> tuple[np.ndarray, np.ndarray]:
    """由 Phi=I+s-h ln(s) 常数生成 q=0 完整轨线。"""
    s_end = q0_terminal_s(s0, i0, par.h)
    s = np.linspace(s0, s_end, N_TRAJECTORY_POINTS)
    infectious = i0 + s0 - s + par.h * positive_log_ratio(s, s0)
    infectious[-1] = 0.0
    return s, infectious


def q1_trajectory(s0: float, i0: float, par: Params) -> tuple[np.ndarray, np.ndarray]:
    """由 Psi=I-ell ln(s) 常数生成 q=1 完整轨线。"""
    s_end = s0 * math.exp(-i0 / par.ell)
    s = np.linspace(s0, s_end, N_TRAJECTORY_POINTS)
    infectious = i0 + par.ell * positive_log_ratio(s, s0)
    infectious[-1] = 0.0
    return s, infectious


def q0_peak(s0: float, i0: float, par: Params) -> float:
    """返回给定初值下 q=0 的感染峰值。"""
    if s0 <= par.h:
        return i0
    return float(i0 + s0 - par.h + par.h * positive_log_ratio(par.h, s0))


def vector_field(
    q: float, par: Params, s_grid: np.ndarray, i_grid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """计算并归一化相平面方向场；箭长不编码实际速度。"""
    ds = -par.c * (par.p + (1.0 - par.p) * q) * s_grid * i_grid
    di = par.p * par.c * (1.0 - q) * s_grid * i_grid - par.gamma * i_grid
    speed = np.hypot(ds, di)
    valid = (speed > 0.0) & (s_grid + i_grid <= 1.0)
    u = np.full_like(ds, np.nan, dtype=float)
    v = np.full_like(di, np.nan, dtype=float)
    u[valid] = ds[valid] / speed[valid]
    v[valid] = di[valid] / speed[valid]
    return u, v


def add_direction_field(ax: plt.Axes, q: float, par: Params) -> None:
    """添加低密度、低对比度的归一化方向场。"""
    s_values = np.linspace(0.06, 0.96, 18)
    i_values = np.linspace(0.025, 0.375, 10)
    s_grid, i_grid = np.meshgrid(s_values, i_values)
    u, v = vector_field(q, par, s_grid, i_grid)
    ax.quiver(
        s_grid,
        i_grid,
        u,
        v,
        angles="xy",
        scale_units="width",
        scale=29,
        width=0.0020,
        headwidth=3.0,
        headlength=3.8,
        headaxislength=3.4,
        color="#7F8790",
        alpha=0.27,
        pivot="mid",
        zorder=1,
    )


def add_trajectory_arrow(
    ax: plt.Axes, s: np.ndarray, infectious: np.ndarray, color: str
) -> None:
    """在轨线中段添加一个沿时间方向的箭头。"""
    start = int(0.56 * (len(s) - 1))
    stop = min(start + 24, len(s) - 1)
    ax.annotate(
        "",
        xy=(s[stop], infectious[stop]),
        xytext=(s[start], infectious[start]),
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "linewidth": 0.85,
            "mutation_scale": 6.8,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=5,
    )


def add_reference_geometry(ax: plt.Axes, par: Params, show_exceedance_label: bool) -> None:
    """添加容量、传播阈值和越界区域。"""
    ax.axhspan(par.K, Y_LIMITS[1], color="#C44E52", alpha=0.055, zorder=0)
    ax.axhline(par.K, color="#B23A48", linestyle="-.", linewidth=1.05, zorder=2)
    ax.axvline(par.h, color="#555555", linestyle=(0, (2, 2)), linewidth=0.95, zorder=2)
    ax.text(
        0.975,
        par.K + 0.008,
        "I=K=0.15",
        color="#922B36",
        ha="right",
        va="bottom",
        fontsize=6.5,
    )
    ax.text(
        par.h + 0.012,
        0.385,
        "s=h=0.30",
        color="#444444",
        ha="left",
        va="top",
        rotation=90,
        rotation_mode="anchor",
        fontsize=6.5,
    )
    if show_exceedance_label:
        ax.text(
            0.965,
            0.382,
            "I>K（容量越界）",
            color="#922B36",
            ha="right",
            va="top",
            fontsize=6.5,
        )


def plot_panel(
    ax: plt.Axes,
    par: Params,
    q: int,
    trajectory_fn: Callable[[float, float, Params], tuple[np.ndarray, np.ndarray]],
    panel_label: str,
    title: str,
) -> None:
    """绘制一个固定控制水平下的九条轨线。"""
    add_reference_geometry(ax, par, show_exceedance_label=(q == 0))
    add_direction_field(ax, float(q), par)

    for s0 in S_INITIALS:
        for i0 in I_INITIALS:
            s, infectious = trajectory_fn(s0, i0, par)
            color = COLORS[s0]
            linestyle = LINESTYLES[i0]
            ax.plot(s, infectious, color=color, linestyle=linestyle, zorder=3)
            ax.scatter(
                [s0],
                [i0],
                s=19,
                marker="o",
                facecolor=color,
                edgecolor="white",
                linewidth=0.55,
                zorder=6,
            )
            add_trajectory_arrow(ax, s, infectious, color)

    ax.set_xlim(X_LIMITS)
    ax.set_ylim(Y_LIMITS)
    ax.set_xlabel("易感比例  $s$")
    ax.set_title(title, pad=7.0)
    ax.grid(True, color="#D9DDE2", linewidth=0.45, alpha=0.58, zorder=0)
    ax.tick_params(direction="out", length=2.6, width=0.7)
    ax.text(
        -0.095,
        1.045,
        panel_label,
        transform=ax.transAxes,
        fontsize=9.0,
        fontweight="bold",
        ha="left",
        va="top",
    )


def validate_trajectories(par: Params) -> dict[str, float | int]:
    """执行解析不变量、单调性、状态域和容量越界检查。"""
    q0_max_error = 0.0
    q1_max_error = 0.0
    capacity_exceedances = 0

    for s0 in S_INITIALS:
        for i0 in I_INITIALS:
            if not (s0 > 0.0 and 0.0 < i0 < par.K and s0 + i0 <= 1.0):
                raise AssertionError(f"非法初值：(s0, I0)=({s0}, {i0})")

            s_q0, i_q0 = q0_trajectory(s0, i0, par)
            phi = i_q0 + s_q0 - par.h * positive_log_ratio(s_q0, 1.0)
            q0_error = float(np.max(np.abs(phi - phi[0])))
            q0_max_error = max(q0_max_error, q0_error)
            if q0_error > 1e-8:
                raise AssertionError(f"q=0 不变量误差过大：{q0_error:.3e}")
            if np.min(s_q0) <= 0.0 or np.min(i_q0) < -1e-12:
                raise AssertionError("q=0 轨线离开正状态域")
            if np.max(s_q0 + i_q0) > 1.0 + 1e-12:
                raise AssertionError("q=0 轨线违反 s+I<=1")
            if np.max(np.diff(s_q0 + i_q0)) > 1e-12:
                raise AssertionError("q=0 轨线上 s+I 未随时间单调下降")

            analytic_peak = q0_peak(s0, i0, par)
            numeric_peak = float(np.max(i_q0))
            if abs(analytic_peak - numeric_peak) > 2e-6:
                raise AssertionError("q=0 数值轨线峰值与解析峰值不一致")
            capacity_exceedances += int(analytic_peak > par.K)

            s_q1, i_q1 = q1_trajectory(s0, i0, par)
            psi = i_q1 - par.ell * positive_log_ratio(s_q1, 1.0)
            q1_error = float(np.max(np.abs(psi - psi[0])))
            q1_max_error = max(q1_max_error, q1_error)
            if q1_error > 1e-8:
                raise AssertionError(f"q=1 不变量误差过大：{q1_error:.3e}")
            if np.min(s_q1) <= 0.0 or np.min(i_q1) < -1e-12:
                raise AssertionError("q=1 轨线离开正状态域")
            if np.max(s_q1 + i_q1) > 1.0 + 1e-12:
                raise AssertionError("q=1 轨线违反 s+I<=1")
            if not np.all(np.diff(i_q1) < 0.0):
                raise AssertionError("q=1 轨线中的 I 未严格单调下降")
            if np.max(i_q1) >= par.K:
                raise AssertionError("q=1 轨线不应越过容量 K")

    if capacity_exceedances != 4:
        raise AssertionError(f"预期 4 条 q=0 轨线越过 K，实际为 {capacity_exceedances} 条")

    return {
        "initial_condition_count": len(S_INITIALS) * len(I_INITIALS),
        "q0_max_invariant_error": q0_max_error,
        "q1_max_invariant_error": q1_max_error,
        "q0_capacity_exceedances": capacity_exceedances,
    }


def make_figure(par: Params) -> plt.Figure:
    """组装左右双面板相空间图。"""
    configure_style()
    width_in = FIGURE_WIDTH_MM / 25.4
    height_in = FIGURE_HEIGHT_MM / 25.4
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(width_in, height_in),
        sharex=True,
        sharey=True,
    )

    plot_panel(
        axes[0],
        par,
        q=0,
        trajectory_fn=q0_trajectory,
        panel_label="a",
        title="完全不控制：$q=0$",
    )
    plot_panel(
        axes[1],
        par,
        q=1,
        trajectory_fn=q1_trajectory,
        panel_label="b",
        title="完全控制：$q=1$",
    )
    axes[0].set_ylabel("感染比例  $I$")

    color_handles = [
        Line2D([0], [0], color=COLORS[s0], linewidth=2.0, label=f"s(0)={s0:.2f}")
        for s0 in S_INITIALS
    ]
    line_handles = [
        Line2D(
            [0],
            [0],
            color="#30343B",
            linewidth=1.6,
            linestyle=LINESTYLES[i0],
            label=f"I(0)={i0:.2f}",
        )
        for i0 in I_INITIALS
    ]
    fig.legend(
        handles=color_handles + line_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.035),
        ncol=6,
        handlelength=2.6,
        columnspacing=1.25,
        handletextpad=0.45,
    )

    fig.suptitle(
        "不同初始状态下的极端控制相轨线\n"
        "基准参数：p=0.5，c=2，γ=0.3，K=0.15",
        x=0.52,
        y=0.965,
        fontsize=9.2,
        linespacing=1.42,
    )
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.19, top=0.79, wspace=0.12)
    return fig


def save_figure(fig: plt.Figure) -> list[Path]:
    """保存 300 dpi PNG、可编辑 PDF 和 SVG。"""
    stem = SCRIPT_DIR / "phase_portrait_q0_q1"
    outputs = [stem.with_suffix(".png"), stem.with_suffix(".pdf"), stem.with_suffix(".svg")]
    fig.savefig(outputs[0], dpi=300)
    fig.savefig(outputs[1])
    fig.savefig(outputs[2])
    return outputs


def main() -> None:
    par = Params()
    report = validate_trajectories(par)
    fig = make_figure(par)
    outputs = save_figure(fig)
    plt.close(fig)

    print(f"基准参数：p={par.p}, c={par.c}, gamma={par.gamma}, K={par.K}")
    print(f"阈值：h={par.h:.6f}, ell={par.ell:.6f}")
    print(f"初值数量：{report['initial_condition_count']}")
    print(f"q=0 最大不变量误差：{report['q0_max_invariant_error']:.3e}")
    print(f"q=1 最大不变量误差：{report['q1_max_invariant_error']:.3e}")
    print(f"q=0 越过容量的轨线数：{report['q0_capacity_exceedances']}")
    for output in outputs:
        print(f"已保存：{output}")


if __name__ == "__main__":
    main()
