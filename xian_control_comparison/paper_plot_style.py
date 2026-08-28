"""第 7 节论文图共用的 Matplotlib 样式。

画布宽度按主论文 ``\textwidth = 451.28 bp`` 直接换算，避免先用大画布
作图、再由 LaTeX 大比例缩小而导致字体和线条过细。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


TEXT_WIDTH_BP = 451.28
TEXT_WIDTH_IN = TEXT_WIDTH_BP / 72.0

COLORS: Dict[str, str] = {
    "navy": "#073068",
    "blue": "#206FB6",
    "sky": "#6BADD7",
    "pale_blue": "#C5DAEE",
    "pale_warm": "#FDDFD0",
    "coral": "#FC9171",
    "red": "#EE3B2A",
    "dark_red": "#A60E16",
    "routine": "#424242",
    "gray": "#6F6F6F",
    "light_gray": "#A6AFB8",
}

STRATEGY_STYLES: Dict[str, Dict[str, Any]] = {
    "TDINN控制": {
        "label": "TDINN control",
        "color": COLORS["navy"],
        "linestyle": "-",
        "linewidth": 2.2,
    },
    "情景一阈值控制": {
        "label": "Threshold control",
        "color": COLORS["sky"],
        "linestyle": "-",
        "linewidth": 2.2,
    },
    "常规控制": {
        "label": "Routine control",
        "color": COLORS["routine"],
        "linestyle": (0, (1.1, 1.7)),
        "linewidth": 1.8,
    },
}

PAPER_RC_PARAMS: Dict[str, Any] = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "font.size": 8.0,
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "axes.labelsize": 8.8,
    "axes.linewidth": 0.9,
    "axes.edgecolor": "#000000",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 7.6,
    "ytick.labelsize": 7.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.minor.size": 2.0,
    "ytick.minor.size": 2.0,
    "xtick.minor.width": 0.6,
    "ytick.minor.width": 0.6,
    "legend.fontsize": 7.2,
    "legend.frameon": False,
    "legend.handlelength": 2.5,
    "legend.handletextpad": 0.55,
    "legend.labelspacing": 0.28,
    "lines.solid_capstyle": "round",
    "lines.dash_capstyle": "round",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 320,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}

BLUE_CMAP = LinearSegmentedColormap.from_list(
    "xian_blue",
    ["#F7FAFD", COLORS["pale_blue"], COLORS["sky"], COLORS["blue"], COLORS["navy"]],
)
WARM_CMAP = LinearSegmentedColormap.from_list(
    "xian_warm",
    ["#FFF8F4", COLORS["pale_warm"], COLORS["coral"], COLORS["red"], COLORS["dark_red"]],
)
PARULA_CMAP = LinearSegmentedColormap.from_list(
    "xian_parula",
    [
        "#3D25AD",
        "#484DF1",
        "#317AFB",
        "#1FA3E2",
        "#15BEB6",
        "#5FCC73",
        "#CAC127",
        "#FDCC31",
        "#EBEC33",
    ],
)


def paper_style_context() -> mpl.rc_context:
    """返回只影响当前作图代码块的论文样式上下文。"""

    return mpl.rc_context(PAPER_RC_PARAMS)


def style_axis(ax, panel: str | None = None, panel_x: float = -0.065) -> None:
    """统一坐标轴，并可添加论文面板编号。"""

    ax.grid(False)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", direction="out", top=False, right=False)
    if panel is not None:
        ax.text(
            panel_x,
            1.015,
            panel,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.2,
            fontweight="bold",
            color="#222222",
            clip_on=False,
        )


def strategy_handles(include_observed: bool = False) -> List[Line2D]:
    """构造固定顺序的策略图例句柄。"""

    handles: List[Line2D] = []
    for strategy in ["TDINN控制", "情景一阈值控制", "常规控制"]:
        spec = STRATEGY_STYLES[strategy]
        handles.append(
            Line2D(
                [],
                [],
                color=spec["color"],
                linestyle=spec["linestyle"],
                linewidth=spec["linewidth"],
                label=spec["label"],
            )
        )
    if include_observed:
        handles.append(
            Line2D(
                [],
                [],
                color=COLORS["coral"],
                marker="o",
                linestyle="none",
                markersize=4.2,
                markeredgecolor="white",
                markeredgewidth=0.65,
                label="Observed data",
            )
        )
    return handles


def save_figure(fig, output_stem: Path, png_dpi: int = 320) -> None:
    """以固定画布保存矢量 PDF 和高分辨率 PNG。"""

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"))
    fig.savefig(output_stem.with_suffix(".png"), dpi=png_dpi)


def style_all(axes: Iterable[Any]) -> None:
    """批量应用坐标轴样式。"""

    for ax in axes:
        style_axis(ax)
