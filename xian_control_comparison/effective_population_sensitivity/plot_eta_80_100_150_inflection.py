"""绘制 N_eff=50,000 下 eta=80、100、150 的 I(t) 与 q(t) 轨迹。

脚本复用有效人口敏感性模块中的初值拟合，以及阈值响应图谱模块中的
情景一时间开环控制求解。图中标记的 ``t_bar`` 是 q_c(t) 的凹凸拐点，
满足 S(t_bar)=2*S_bar，而不是控制启动或解除时刻。
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


OUTPUT_DIR = HERE / "representative_panels"
FIGURE_STEM = "eta_80_100_150_inflection_Neff50000"
TIMESERIES_NAME = "timeseries_eta_80_100_150_Neff50000.csv"
SUMMARY_NAME = "inflection_summary_eta_80_100_150_Neff50000.csv"

N_EFF = 50_000.0
ETA_VALUES = [80.0, 100.0, 150.0]
COLORS = {80.0: "#0072B2", 100.0: "#D55E00", 150.0: "#009E73"}
LINESTYLES = {80.0: "-", 100.0: "--", 150.0: "-."}


def compute_inflection(
    eta: float,
    params: tla.LandscapeParams,
    details: Dict[str, float | str],
) -> Dict[str, float | bool]:
    """计算并验证 q_c(t) 在控制期内的唯一凹凸拐点。"""

    s_star = float(details["S_star"])
    s_c = float(details["Sc"])
    s_bar = float(details["Sbar"])
    t1 = float(details["t1"])
    t2 = float(details["t2"])
    control_duration = t2 - t1

    exists = s_c < 2.0 * s_bar < s_star
    if not exists:
        raise RuntimeError(
            f"eta={eta:g}: 不满足 Sc < 2*Sbar < S_star，控制期内不存在所需拐点。"
        )

    k = params.c0 * eta / params.N
    tau_inflection = np.log((s_star - s_bar) / s_bar) / k
    t_inflection = t1 + tau_inflection

    def s_theory(t: float) -> float:
        return s_bar + (s_star - s_bar) * np.exp(-k * (t - t1))

    def q_second(t: float) -> float:
        s_t = s_theory(t)
        coefficient = params.gamma * params.c0 * eta**2 / (params.beta * params.N)
        return coefficient * (s_t - s_bar) * (2.0 * s_bar - s_t) / s_t**3

    s_at_inflection = s_theory(t_inflection)
    q_at_inflection = 1.0 - params.gamma * params.N / (
        params.beta * params.c0 * s_at_inflection
    )
    side_offset = max(1.0e-4, 1.0e-3 * control_duration)
    q_second_left = q_second(t_inflection - side_offset)
    q_second_right = q_second(t_inflection + side_offset)

    state_error = abs(s_at_inflection - 2.0 * s_bar)
    state_tolerance = 1.0e-9 * max(1.0, 2.0 * s_bar)
    if state_error > state_tolerance:
        raise RuntimeError(
            f"eta={eta:g}: S(t_bar)=2*Sbar 校验失败，误差为 {state_error:.3e}。"
        )
    if not (t1 < t_inflection < t2):
        raise RuntimeError(f"eta={eta:g}: t_bar 不在 (t1,t2) 内。")
    if not (q_second_left < 0.0 < q_second_right):
        raise RuntimeError(
            f"eta={eta:g}: q_c'' 在拐点两侧没有由负变正。"
        )

    return {
        "inflection_exists": exists,
        "t_inflection": float(t_inflection),
        "tau_inflection": float(tau_inflection),
        "S_at_inflection": float(s_at_inflection),
        "S_target_2Sbar": float(2.0 * s_bar),
        "S_inflection_error": float(state_error),
        "q_at_inflection": float(q_at_inflection),
        "q_second_left": float(q_second_left),
        "q_second_right": float(q_second_right),
    }


def build_plot_series(
    eta: float,
    params: tla.LandscapeParams,
    solution: pd.DataFrame,
    details: Dict[str, float | str],
    t_inflection: float,
    common_end: float,
) -> pd.DataFrame:
    """构造与最终图完全一致的高密度时间序列。"""

    t1 = float(details["t1"])
    t2 = float(details["t2"])
    clear_time = float(details["clear_time"])
    s_star = float(details["S_star"])
    s_bar = float(details["Sbar"])
    k = params.c0 * eta / params.N

    dense_grid = np.linspace(0.0, common_end, 3000)
    key_times = np.array([0.0, t1, t_inflection, t2, clear_time, common_end])
    time_grid = np.unique(np.r_[dense_grid, solution["t"].to_numpy(dtype=float), key_times])
    time_grid = time_grid[(time_grid >= 0.0) & (time_grid <= common_end)]

    solution_t = solution["t"].to_numpy(dtype=float)
    solution_i = solution["I"].to_numpy(dtype=float)
    i_values = np.interp(time_grid, solution_t, solution_i, left=solution_i[0], right=np.nan)

    q_values = np.full_like(time_grid, params.q0, dtype=float)
    control_mask = (time_grid >= t1) & (time_grid <= t2)
    s_control = s_bar + (s_star - s_bar) * np.exp(-k * (time_grid[control_mask] - t1))
    q_values[control_mask] = 1.0 - params.gamma * params.N / (
        params.beta * params.c0 * s_control
    )

    phase = np.full(time_grid.shape, "post-control", dtype=object)
    phase[time_grid < t1] = "pre-control"
    phase[control_mask] = "threshold-control"

    return pd.DataFrame(
        {
            "N_eff": params.N,
            "eta": eta,
            "eta_fraction": eta / params.N,
            "t": time_grid,
            "I": i_values,
            "q": q_values,
            "phase": phase,
        }
    )


def plot_trajectories(
    all_series: pd.DataFrame,
    summary: pd.DataFrame,
    params: tla.LandscapeParams,
) -> None:
    """绘制 I(t) 与 q(t) 双面板比较图。"""

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

    for eta in ETA_VALUES:
        sub = all_series[all_series["eta"].eq(eta)].sort_values("t")
        label = rf"$\eta={eta:g}$"
        color = COLORS[eta]
        linestyle = LINESTYLES[eta]
        ax_i.plot(sub["t"], sub["I"], color=color, linestyle=linestyle, lw=2.0, label=label)
        ax_q.plot(sub["t"], sub["q"], color=color, linestyle=linestyle, lw=2.0, label=label)

    ax_i.set_ylabel(r"$I(t)$")
    ax_i.set_title(r"(a) Community infections", loc="left", fontsize=10)
    ax_i.set_ylim(bottom=0.0)
    ax_i.legend(loc="upper right", ncol=3, columnspacing=1.2, handlelength=2.4)

    ax_q.axhline(
        params.q0,
        color="#555555",
        lw=1.0,
        linestyle=":",
        label=rf"$q_0={params.q0:g}$",
        zorder=1,
    )

    annotation_offsets = {80.0: (5, 12), 100.0: (5, -22), 150.0: (5, 12)}
    for eta in ETA_VALUES:
        row = summary[summary["eta"].eq(eta)].iloc[0]
        t_inflection = float(row["t_inflection"])
        q_inflection = float(row["q_at_inflection"])
        color = COLORS[eta]
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
            rf"$\bar{{t}}_{{{eta:g}}}={t_inflection:.2f}$ d",
            xy=(t_inflection, q_inflection),
            xytext=annotation_offsets[eta],
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

    fig.suptitle(r"Threshold trajectories at $N_{\rm eff}=50{,}000$", fontsize=11)
    fig.savefig(OUTPUT_DIR / f"{FIGURE_STEM}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{FIGURE_STEM}.png", dpi=400, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    observed = xcc.load_observed_data()
    params = tla.LandscapeParams(N=N_EFF)
    fit = eps.fit_initial_condition_for_N(observed, params)
    routine_df = tla.solve_time_control_param(
        "常规控制", fit, params, tla.c_const(params), tla.q_const(params)
    )

    solutions: List[Tuple[float, pd.DataFrame, Dict[str, float | str], Dict[str, float | bool]]] = []
    summary_rows: List[Dict[str, float | str | bool]] = []

    for eta in ETA_VALUES:
        solution, details = tla.solve_threshold_fast(fit, eta, params, routine_df)
        status = str(details.get("status", "unknown"))
        if status != "ok" or solution.empty:
            raise RuntimeError(f"eta={eta:g}: 阈值控制求解失败，status={status}。")

        inflection = compute_inflection(eta, params, details)
        plateau_error = float(details["plateau_max_error"])
        if not np.isfinite(plateau_error) or plateau_error > 1.0e-5:
            raise RuntimeError(
                f"eta={eta:g}: 平台误差 {plateau_error:.3e} 超过容差 1e-5。"
            )

        summary_rows.append(
            {
                "N_eff": params.N,
                "eta": eta,
                "eta_fraction": eta / params.N,
                "status": status,
                "I0_fit": fit.I0,
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
        solutions.append((eta, solution, details, inflection))

    summary = pd.DataFrame(summary_rows)
    common_end = 1.05 * float(summary["clear_time"].max())
    plot_frames = [
        build_plot_series(
            eta,
            params,
            solution,
            details,
            float(inflection["t_inflection"]),
            common_end,
        )
        for eta, solution, details, inflection in solutions
    ]
    all_series = pd.concat(plot_frames, ignore_index=True)

    all_series.to_csv(OUTPUT_DIR / TIMESERIES_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(OUTPUT_DIR / SUMMARY_NAME, index=False, encoding="utf-8-sig")
    plot_trajectories(all_series, summary, params)

    print(f"Generated: {OUTPUT_DIR / (FIGURE_STEM + '.pdf')}")
    print(f"Generated: {OUTPUT_DIR / (FIGURE_STEM + '.png')}")
    print(f"Generated: {OUTPUT_DIR / TIMESERIES_NAME}")
    print(f"Generated: {OUTPUT_DIR / SUMMARY_NAME}")
    print(summary[["eta", "t1", "t_inflection", "t2", "clear_time", "plateau_max_error"]].to_string(index=False))


if __name__ == "__main__":
    main()
