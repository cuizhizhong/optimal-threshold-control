"""绘制 eta=100、不同 N_eff 下的 I(t) 与 q(t) 轨迹。

每个有效人口规模都重新拟合初始种子 I0，并保持传播参数与情景一
时间开环阈值控制结构不变。q_c(t) 的拐点满足 S(t_bar)=2*S_bar。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
THRESHOLD_DIR = PARENT / "threshold_landscape_analysis"
for path in [str(PARENT), str(THRESHOLD_DIR), str(HERE)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import xian_control_comparison as xcc  # noqa: E402
import threshold_landscape_analysis as tla  # noqa: E402
import effective_population_sensitivity as eps  # noqa: E402
from plot_eta_80_100_150_inflection import (  # noqa: E402
    build_plot_series,
    compute_inflection,
)


OUTPUT_DIR = HERE / "representative_panels"
FIGURE_STEM = "Neff_40000_50000_60000_inflection_eta100"
TIMESERIES_NAME = "timeseries_Neff_40000_50000_60000_eta100.csv"
SUMMARY_NAME = "inflection_summary_Neff_40000_50000_60000_eta100.csv"

ETA = 100.0
N_EFF_VALUES = [40_000.0, 50_000.0, 60_000.0]
COLORS = {40_000.0: "#0072B2", 50_000.0: "#D55E00", 60_000.0: "#009E73"}
LINESTYLES = {40_000.0: "-", 50_000.0: "--", 60_000.0: "-."}


def plot_trajectories(all_series: pd.DataFrame, summary: pd.DataFrame, q0: float) -> None:
    """绘制固定 eta、改变 N_eff 的 I(t) 与 q(t) 双面板图。"""

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
        }
    )

    fig, (ax_i, ax_q) = plt.subplots(
        2,
        1,
        figsize=(7.2, 6.8),
        sharex=True,
        gridspec_kw={"height_ratios": [1.05, 1.0]},
        constrained_layout=True,
    )

    for n_eff in N_EFF_VALUES:
        sub = all_series[all_series["N_eff"].eq(n_eff)].sort_values("t")
        label = rf"$N_{{\rm eff}}={n_eff / 1000:g}\times10^3$"
        color = COLORS[n_eff]
        linestyle = LINESTYLES[n_eff]
        ax_i.plot(sub["t"], sub["I"], color=color, linestyle=linestyle, lw=2.0, label=label)
        ax_q.plot(sub["t"], sub["q"], color=color, linestyle=linestyle, lw=2.0, label=label)

    ax_i.axhline(
        ETA,
        color="#777777",
        lw=0.9,
        linestyle=":",
        label=rf"$\eta={ETA:g}$",
        zorder=1,
    )
    ax_i.set_ylabel(r"$I(t)$")
    ax_i.set_title(r"(a) Community infections", loc="left", fontsize=10)
    ax_i.set_ylim(bottom=0.0)
    ax_i.legend(loc="upper right", ncol=2, columnspacing=1.2, handlelength=2.4)

    ax_q.axhline(
        q0,
        color="#555555",
        lw=1.0,
        linestyle=":",
        label=rf"$q_0={q0:g}$",
        zorder=1,
    )

    annotation_offsets = {
        40_000.0: (5, 12),
        50_000.0: (5, -22),
        60_000.0: (5, 12),
    }
    for n_eff in N_EFF_VALUES:
        row = summary[summary["N_eff"].eq(n_eff)].iloc[0]
        t_inflection = float(row["t_inflection"])
        q_inflection = float(row["q_at_inflection"])
        color = COLORS[n_eff]
        ax_q.axvline(t_inflection, color=color, lw=0.9, linestyle=":", alpha=0.55, zorder=1)
        ax_q.scatter(
            [t_inflection],
            [q_inflection],
            s=38,
            facecolor="white",
            edgecolor=color,
            linewidth=1.5,
            zorder=5,
        )
        ax_q.annotate(
            rf"$\bar{{t}}_{{{n_eff / 1000:g}k}}={t_inflection:.2f}$ d",
            xy=(t_inflection, q_inflection),
            xytext=annotation_offsets[n_eff],
            textcoords="offset points",
            color=color,
            fontsize=8.2,
            ha="left",
            va="center",
        )

    ax_q.set_xlabel(r"Time $t$ (days)")
    ax_q.set_ylabel(r"$q(t)$")
    ax_q.set_title(r"(b) Quarantine control and inflection times", loc="left", fontsize=10)
    ax_q.set_ylim(0.29, 0.90)
    ax_q.legend(loc="upper right", ncol=2, columnspacing=1.2, handlelength=2.4)

    max_time = float(all_series["t"].max())
    ax_q.set_xlim(0.0, max_time)
    for ax in (ax_i, ax_q):
        ax.grid(axis="y", color="#D9D9D9", lw=0.6, alpha=0.55)
        ax.tick_params(direction="out", length=3.5, width=0.8)

    fig.suptitle(r"Effective-population sensitivity at $\eta=100$", fontsize=11)
    fig.savefig(OUTPUT_DIR / f"{FIGURE_STEM}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{FIGURE_STEM}.png", dpi=400, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    observed = xcc.load_observed_data()

    solutions: List[
        Tuple[
            float,
            tla.LandscapeParams,
            pd.DataFrame,
            Dict[str, float | str],
            Dict[str, float | bool],
        ]
    ] = []
    summary_rows: List[Dict[str, float | str | bool]] = []

    for n_eff in N_EFF_VALUES:
        params = tla.LandscapeParams(N=n_eff)
        fit = eps.fit_initial_condition_for_N(observed, params)
        routine_df = tla.solve_time_control_param(
            "常规控制", fit, params, tla.c_const(params), tla.q_const(params)
        )
        solution, details = tla.solve_threshold_fast(fit, ETA, params, routine_df)
        status = str(details.get("status", "unknown"))
        if status != "ok" or solution.empty:
            raise RuntimeError(
                f"N_eff={n_eff:g}, eta={ETA:g}: 阈值控制求解失败，status={status}。"
            )

        inflection = compute_inflection(ETA, params, details)
        plateau_error = float(details["plateau_max_error"])
        if not np.isfinite(plateau_error) or plateau_error > 1.0e-5:
            raise RuntimeError(
                f"N_eff={n_eff:g}: 平台误差 {plateau_error:.3e} 超过容差 1e-5。"
            )

        summary_rows.append(
            {
                "N_eff": params.N,
                "eta": ETA,
                "eta_fraction": ETA / params.N,
                "status": status,
                "I0_fit": fit.I0,
                "S0_fit": fit.S0,
                "fit_objective": fit.objective,
                "fit_raw_rmse": fit.raw_rmse,
                "S_star": float(details["S_star"]),
                "Sc": float(details["Sc"]),
                "Sbar": float(details["Sbar"]),
                "t1": float(details["t1"]),
                **inflection,
                "t2": float(details["t2"]),
                "control_duration": float(details["t2"]) - float(details["t1"]),
                "clear_time": float(details["clear_time"]),
                "plateau_max_error": plateau_error,
            }
        )
        solutions.append((n_eff, params, solution, details, inflection))

    summary = pd.DataFrame(summary_rows)
    common_end = 1.05 * float(summary["clear_time"].max())
    plot_frames = [
        build_plot_series(
            ETA,
            params,
            solution,
            details,
            float(inflection["t_inflection"]),
            common_end,
        )
        for _, params, solution, details, inflection in solutions
    ]
    all_series = pd.concat(plot_frames, ignore_index=True)

    all_series.to_csv(OUTPUT_DIR / TIMESERIES_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(OUTPUT_DIR / SUMMARY_NAME, index=False, encoding="utf-8-sig")
    plot_trajectories(all_series, summary, float(solutions[0][1].q0))

    print(f"Generated: {OUTPUT_DIR / (FIGURE_STEM + '.pdf')}")
    print(f"Generated: {OUTPUT_DIR / (FIGURE_STEM + '.png')}")
    print(f"Generated: {OUTPUT_DIR / TIMESERIES_NAME}")
    print(f"Generated: {OUTPUT_DIR / SUMMARY_NAME}")
    print(
        summary[
            [
                "N_eff",
                "I0_fit",
                "t1",
                "t_inflection",
                "t2",
                "clear_time",
                "plateau_max_error",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
