"""验证情景一阈值控制的无量纲标度结构。

本脚本区分两类实验：

1. 精确结构实验：固定无量纲初值 ``s0, i0`` 和阈值比例
   ``rho_eta = eta / N_eff``，只改变 ``N_eff``；
2. 数据重拟合实验：沿用 ``effective_population_sensitivity.py`` 对每个
   ``N_eff`` 重新拟合绝对初值 ``I0`` 的结果。

第一类用于验证解析标度律，第二类用于说明当前数据校准会通过
``i0 = I0 / N_eff`` 改变启动时间，因此不能把所有指标都写成无条件不变量。
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
from scipy.integrate import solve_ivp


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
THRESHOLD_DIR = PARENT / "threshold_landscape_analysis"
for path in [str(PARENT), str(THRESHOLD_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import xian_control_comparison as xcc  # noqa: E402
import threshold_landscape_analysis as tla  # noqa: E402


FIG_DIR = HERE / "figures"
N_EFF_VALUES = [5.0e4, 1.0e5, 3.0e5, 1.0e6, 3.0e6, xcc.P.N]
REFERENCE_N = 5.0e4
ETA_FRACTION = 0.002
FRACTIONAL_CLEAR_EPSILON = 1.0e-7
W_C = 1.0
W_Q = 2.0

# 组二：固定 N_eff、改变阈值比例 rho，用两端相差约 263 倍的 N_eff 交叉验证
# 「指标只通过 rho 进入」。
RHO_VALUES = [0.0005, 0.001, 0.002, 0.004, 0.008]
RHO_SWEEP_N_VALUES = [5.0e4, xcc.P.N]
RHO_CROSS_N_TOLERANCE = 1.0e-5

EXACT_SUMMARY_NAME = "dimensionless_scaling_exact_summary.csv"
REFIT_SUMMARY_NAME = "dimensionless_scaling_refit_summary.csv"
CHECKS_NAME = "dimensionless_scaling_invariance_checks.csv"
TIMESERIES_NAME = "dimensionless_scaling_exact_timeseries.csv"
RHO_SWEEP_NAME = "dimensionless_scaling_rho_sweep.csv"
COLLAPSE_STEM = "dimensionless_scaling_collapse"
TAIL_STEM = "clearance_tail_decomposition"
RHO_STEM = "dimensionless_rho_dependence"


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
            "pdf.fonttype": 42,
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def stage3_tail_duration(
    params: tla.LandscapeParams,
    eta_fraction: float,
    target_fraction: float,
) -> float:
    """在平台解除后，以无量纲 SI 子系统计算到目标感染分数的尾段时长。"""

    if not 0.0 < target_fraction < eta_fraction:
        raise ValueError("target_fraction 必须位于 (0, eta_fraction) 内。")

    alpha_s = params.c0 * (params.beta + params.q0 * (1.0 - params.beta))
    alpha_i = params.beta * params.c0 * (1.0 - params.q0)
    s_c = params.gamma / alpha_i

    def rhs(_t: float, y: np.ndarray) -> np.ndarray:
        s, i = y
        return np.array(
            [
                -alpha_s * s * i,
                alpha_i * s * i - params.gamma * i,
            ]
        )

    def target_event(_t: float, y: np.ndarray) -> float:
        return float(y[1] - target_fraction)

    target_event.terminal = True  # type: ignore[attr-defined]
    target_event.direction = -1.0  # type: ignore[attr-defined]

    solution = solve_ivp(
        rhs,
        (0.0, params.dynamic_horizon_limit),
        np.array([s_c, eta_fraction], dtype=float),
        events=target_event,
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.25,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    if len(solution.t_events[0]) == 0:
        raise RuntimeError("平台后轨迹未到达指定的无量纲清零阈值。")
    return float(solution.t_events[0][0])


def interpolate_at(frame: pd.DataFrame, column: str, t_value: float) -> float:
    return float(
        np.interp(
            t_value,
            frame["t"].to_numpy(dtype=float),
            frame[column].to_numpy(dtype=float),
        )
    )


def solve_normalized_routine_until_threshold(
    params: tla.LandscapeParams,
    i0_fraction: float,
    eta_fraction: float,
) -> pd.DataFrame:
    """用高精度无量纲方程求常规阶段，消除固定绝对容差造成的尺度误差。"""

    def rhs(_t: float, y: np.ndarray) -> np.ndarray:
        s, i, sq, iq, cc, cq = y
        force = s * i
        community_infection = params.beta * params.c0 * (1.0 - params.q0) * force
        quarantine_infection = params.beta * params.c0 * params.q0 * force
        quarantine_susceptible = (1.0 - params.beta) * params.c0 * params.q0 * force
        return np.array(
            [
                -(community_infection + quarantine_infection + quarantine_susceptible),
                community_infection - params.gamma * i,
                quarantine_susceptible,
                quarantine_infection - params.delta_q * iq,
                community_infection,
                quarantine_infection,
            ]
        )

    def threshold_event(_t: float, y: np.ndarray) -> float:
        return float(y[1] - eta_fraction)

    threshold_event.terminal = True  # type: ignore[attr-defined]
    threshold_event.direction = 1.0  # type: ignore[attr-defined]

    solution = solve_ivp(
        rhs,
        (0.0, params.dynamic_horizon_initial),
        np.array([1.0 - i0_fraction, i0_fraction, 0.0, 0.0, 0.0, 0.0]),
        events=threshold_event,
        dense_output=True,
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=0.05,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    if len(solution.t_events[0]) == 0:
        raise RuntimeError("高精度无量纲常规阶段未到达阈值。")

    t1 = float(solution.t_events[0][0])
    inner = np.arange(0.0, t1, params.dt)
    time_grid = np.unique(np.r_[inner, t1])
    normalized = solution.sol(time_grid)
    population_states = normalized * params.N
    population_states[1, -1] = eta_fraction * params.N
    return tla.frame_from_arrays(
        "常规控制",
        time_grid,
        population_states,
        np.full_like(time_grid, params.c0),
        np.full_like(time_grid, params.q0),
        params,
    )


CITY_N = 13_163_000.0
CITY_I0 = 0.00100662823352


def reference_i0_fraction() -> float:
    """全节单一口径的固定归一化初值 i0 = I0_city / N_city = 7.6474e-11。

    此前取 N_eff=50,000 的重拟合结果（i0 = 2.617e-8），这是一个与第 7 节全市
    标定不一致的任意选择，且使折叠实验报出 t1 = 11.13 d 而正文其余处为 16.90 d。
    统一到全市标定值后，折叠曲线整体右移约 5.8 d，t1 = 16.90 d 与第 7 节一致。
    见 xian_dom/caliber.py 与正文 §8 开头的口径声明。
    """

    return CITY_I0 / CITY_N


def solve_exact_case(
    params: tla.LandscapeParams,
    i0_fraction: float,
    eta_fraction: float,
) -> Tuple[Dict[str, float | str], pd.DataFrame]:
    """在固定无量纲初值和阈值比例下求解单个 (N_eff, rho) 点。"""

    fit = xcc.InitialFit(
        S0=params.N * (1.0 - i0_fraction),
        I0=params.N * i0_fraction,
        R0_initial=0.0,
        objective=np.nan,
        raw_rmse=np.nan,
        residual_type="fixed_dimensionless_initial_state",
    )
    eta = eta_fraction * params.N
    routine = solve_normalized_routine_until_threshold(params, i0_fraction, eta_fraction)
    threshold, details = tla.solve_threshold_fast(fit, eta, params, routine)
    if str(details.get("status", "")) != "ok" or threshold.empty:
        raise RuntimeError(
            f"精确标度实验失败：N_eff={params.N:g}, rho={eta_fraction:g}, "
            f"status={details.get('status')}。"
        )
    metric = tla.summarize_threshold(threshold, eta, params, details, W_C, W_Q)
    t1 = float(details["t1"])
    t2 = float(details["t2"])
    clear_time = float(metric["clear_time"])
    tail_abs_ode = stage3_tail_duration(params, eta_fraction, 1.0 / params.N)
    tail_fraction = stage3_tail_duration(params, eta_fraction, FRACTIONAL_CLEAR_EPSILON)
    cum_t2 = interpolate_at(threshold, "Cc", t2) + interpolate_at(threshold, "Cq", t2)

    row: Dict[str, float | str] = {
        "N_eff": params.N,
        "eta": eta,
        "eta_fraction": eta_fraction,
        "I0_scaled": fit.I0,
        "I0_fraction": i0_fraction,
        "t1": t1,
        "t2": t2,
        "control_duration": float(metric["control_duration"]),
        "clear_time_I_le_1": clear_time,
        "tail_duration_I_le_1": clear_time - t2,
        "tail_duration_I_le_1_ode": tail_abs_ode,
        "tail_formula_ode_error": (clear_time - t2) - tail_abs_ode,
        "fractional_clear_epsilon": FRACTIONAL_CLEAR_EPSILON,
        "clear_time_fractional": t2 + tail_fraction,
        "tail_duration_fractional": tail_fraction,
        "cum_fraction_t2": cum_t2 / params.N,
        "cum_total_infections_I_le_1": float(metric["cum_total_infections"]),
        "cum_fraction_I_le_1": float(metric["cum_total_infections"]) / params.N,
        "J": float(metric["J"]),
        "q_start": float(metric["q_start"]),
        "q_max_theory": float(metric["q_max_theory"]),
        "plateau_max_error": float(metric["plateau_max_error"]),
        "status": str(metric["status"]),
    }

    series = pd.DataFrame(
        {
            "N_eff": params.N,
            "eta": eta,
            "eta_fraction": eta_fraction,
            "t": threshold["t"].to_numpy(dtype=float),
            "i": threshold["I"].to_numpy(dtype=float) / params.N,
            "q": threshold["q"].to_numpy(dtype=float),
        }
    )
    series["phase"] = np.where(
        series["t"] < t1,
        "pre-control",
        np.where(series["t"] <= t2, "threshold-control", "post-control"),
    )
    return row, series


def build_exact_scaling(i0_fraction: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """组一：固定无量纲初值和 rho=0.002，只改变 N_eff。"""

    rows: List[Dict[str, float | str]] = []
    trajectories: List[pd.DataFrame] = []
    solutions: Dict[float, pd.DataFrame] = {}

    for n_eff in N_EFF_VALUES:
        params = tla.LandscapeParams(N=float(n_eff))
        row, series = solve_exact_case(params, i0_fraction, ETA_FRACTION)
        rows.append(row)
        trajectories.append(series)
        solutions[params.N] = series

    summary = pd.DataFrame(rows).sort_values("N_eff").reset_index(drop=True)
    all_series = pd.concat(trajectories, ignore_index=True)

    common_end = float(summary["clear_time_I_le_1"].min())
    common_grid = np.linspace(0.0, common_end, 6000)
    reference_series = solutions[REFERENCE_N]
    reference_i = np.interp(common_grid, reference_series["t"], reference_series["i"])
    reference_q = np.interp(common_grid, reference_series["t"], reference_series["q"])
    for n_eff, series in solutions.items():
        i_values = np.interp(common_grid, series["t"], series["i"])
        q_values = np.interp(common_grid, series["t"], series["q"])
        mask = summary["N_eff"].eq(n_eff)
        summary.loc[mask, "max_i_collapse_error"] = float(
            np.max(np.abs(i_values - reference_i))
        )
        summary.loc[mask, "max_q_collapse_error"] = float(
            np.max(np.abs(q_values - reference_q))
        )

    return summary, all_series


def build_refit_summary() -> pd.DataFrame:
    """整理逐个 N_eff 重拟合绝对 I0 的现有同比例阈值结果。"""

    base = pd.read_csv(HERE / "effective_population_summary.csv")
    frame = base[base["eta_scenario"].eq("eta_fraction_0p002")].copy()
    frame["clear_tail_duration"] = frame["clear_time"] - frame["t2"]
    frame["cum_total_fraction"] = frame["cum_total_infections"] / frame["N_eff"]
    columns = [
        "N_eff",
        "eta",
        "eta_fraction",
        "I0_fit",
        "I0_fraction",
        "fit_raw_rmse",
        "t1",
        "t2",
        "control_duration",
        "clear_time",
        "clear_tail_duration",
        "cum_total_infections",
        "cum_total_fraction",
        "J",
        "q_max_theory",
        "plateau_max_error",
        "status",
    ]
    return frame[columns].sort_values("N_eff").reset_index(drop=True)


def build_rho_sweep(i0_fraction: float) -> pd.DataFrame:
    """组二：固定 N_eff 改变 rho，并在两个 N_eff 上交叉验证。

    组一说明「固定 rho 时指标不随 N_eff 变」，本组说明这些指标确实随 rho
    变，且同一 rho 下两个相差约 263 倍的 N_eff 给出同一组无量纲指标。两组
    合起来才构成「指标只通过 rho=eta/N_eff 进入」的依赖分离证据。
    """

    rows: List[Dict[str, float | str]] = []
    for n_eff in RHO_SWEEP_N_VALUES:
        for rho in RHO_VALUES:
            params = tla.LandscapeParams(N=float(n_eff))
            row, _ = solve_exact_case(params, i0_fraction, float(rho))
            rows.append(row)

    frame = pd.DataFrame(rows)
    frame["log_factor"] = frame["control_duration"] * xcc.P.c0 * frame["eta_fraction"]
    frame = frame.sort_values(["eta_fraction", "N_eff"]).reset_index(drop=True)

    invariant_columns = [
        "t1",
        "control_duration",
        "q_max_theory",
        "cum_fraction_t2",
        "clear_time_fractional",
    ]
    spread = frame.groupby("eta_fraction")[invariant_columns].agg(
        lambda column: float(column.max() - column.min())
    )
    worst = float(np.nanmax(spread.to_numpy(dtype=float)))
    if worst > RHO_CROSS_N_TOLERANCE:
        raise RuntimeError(
            f"固定 rho 时无量纲指标在不同 N_eff 之间的最大差异 {worst:.3e} 超过容差。"
        )
    if float(frame["control_duration"].max() - frame["control_duration"].min()) < 1.0:
        raise RuntimeError("rho 扫描没有产生可分辨的 control_duration 变化。")
    return frame


def build_invariance_checks(exact: pd.DataFrame) -> pd.DataFrame:
    """汇总精确结构实验中的数值不变量误差。"""

    definitions = [
        ("t1", "invariant", 1.0e-5),
        ("t2", "invariant", 1.0e-5),
        ("control_duration", "invariant", 1.0e-5),
        ("J", "invariant", 1.0e-5),
        ("q_start", "invariant", 1.0e-10),
        ("q_max_theory", "invariant", 1.0e-10),
        ("cum_fraction_t2", "invariant", 1.0e-8),
        ("clear_time_fractional", "invariant", 1.0e-5),
        ("max_i_collapse_error", "zero", 1.0e-7),
        ("max_q_collapse_error", "zero", 1.0e-7),
    ]
    rows: List[Dict[str, float | str | bool]] = []
    for metric, expectation, tolerance in definitions:
        values = exact[metric].to_numpy(dtype=float)
        value_range = float(np.nanmax(values) - np.nanmin(values))
        check_value = float(np.nanmax(np.abs(values))) if expectation == "zero" else value_range
        rows.append(
            {
                "metric": metric,
                "expectation": expectation,
                "minimum": float(np.nanmin(values)),
                "maximum": float(np.nanmax(values)),
                "range_or_max_abs": check_value,
                "tolerance": tolerance,
                "passed": bool(check_value <= tolerance),
            }
        )
    return pd.DataFrame(rows)


def plot_collapse(exact: pd.DataFrame, series: pd.DataFrame) -> None:
    colors = plt.cm.viridis(np.linspace(0.05, 0.9, len(N_EFF_VALUES)))
    linestyles = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1))]
    fig, (ax_i, ax_q) = plt.subplots(
        2,
        1,
        figsize=(7.3, 6.8),
        sharex=True,
        gridspec_kw={"height_ratios": [1.1, 1.0]},
        constrained_layout=True,
    )

    for color, linestyle, n_eff in zip(colors, linestyles, N_EFF_VALUES):
        sub = series[series["N_eff"].eq(n_eff)].sort_values("t")
        label = rf"$N_{{\rm eff}}={n_eff:,.0f}$"
        ax_i.plot(sub["t"], sub["i"], color=color, linestyle=linestyle, lw=1.8, label=label)
        ax_q.plot(sub["t"], sub["q"], color=color, linestyle=linestyle, lw=1.8, label=label)
        row = exact[exact["N_eff"].eq(n_eff)].iloc[0]
        ax_i.scatter(
            [float(row["clear_time_I_le_1"])],
            [1.0 / n_eff],
            s=25,
            facecolor="white",
            edgecolor=color,
            linewidth=1.2,
            zorder=5,
        )

    ax_i.axhline(ETA_FRACTION, color="#555555", lw=0.9, linestyle=":", label=r"$\theta=0.002$")
    ax_i.set_yscale("log")
    ax_i.set_ylabel(r"$i(t)=I(t)/N_{\rm eff}$")
    ax_i.set_title("(a) Normalized infection trajectories", loc="left", fontsize=10)
    ax_i.legend(loc="best", ncol=2, fontsize=7.5, columnspacing=1.0)

    ax_q.set_xlabel(r"Time $t$ (days)")
    ax_q.set_ylabel(r"$q(t)$")
    ax_q.set_title("(b) Quarantine-control collapse", loc="left", fontsize=10)
    ax_q.set_ylim(0.29, 0.88)
    ax_q.legend(loc="best", ncol=2, fontsize=7.5, columnspacing=1.0)

    max_time = float(exact["clear_time_I_le_1"].max())
    ax_q.set_xlim(0.0, 1.03 * max_time)
    for ax in (ax_i, ax_q):
        ax.grid(axis="y", color="#D9D9D9", lw=0.6, alpha=0.6)
        ax.tick_params(direction="out", length=3.5, width=0.8)

    fig.suptitle(
        r"Exact scaling at fixed $(s_0,i_0)$ and $\theta=\eta/N_{\rm eff}=0.002$",
        fontsize=10.5,
    )
    fig.savefig(FIG_DIR / f"{COLLAPSE_STEM}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{COLLAPSE_STEM}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_clearance_tail(exact: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.7, 4.4), constrained_layout=True)
    ax.plot(
        exact["N_eff"],
        exact["tail_duration_I_le_1_ode"],
        "o-",
        color="#0072B2",
        lw=1.8,
        label=r"absolute criterion $I\leq1$",
    )
    ax.plot(
        exact["N_eff"],
        exact["tail_duration_fractional"],
        "s--",
        color="#D55E00",
        lw=1.8,
        label=rf"fractional criterion $i\leq {FRACTIONAL_CLEAR_EPSILON:.0e}$",
    )
    ax.set_xscale("log")
    ax.set_xlabel(r"$N_{\rm eff}$")
    ax.set_ylabel(r"Post-control tail $T_{\rm clear}-t_2$ (days)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    ax.set_title(r"Clearance-floor contribution at fixed $\rho=0.002$", fontsize=10.5)
    fig.savefig(FIG_DIR / f"{TAIL_STEM}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{TAIL_STEM}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_rho_dependence(frame: pd.DataFrame) -> None:
    """组二：指标随 rho 变化，且两个 N_eff 的曲线完全重合。"""

    styles = [
        (RHO_SWEEP_N_VALUES[0], "o-", "#0072B2"),
        (RHO_SWEEP_N_VALUES[1], "s--", "#D55E00"),
    ]
    fig, (ax_dt, ax_cum) = plt.subplots(
        1, 2, figsize=(9.6, 4.2), constrained_layout=True
    )

    rho_grid = np.geomspace(min(RHO_VALUES) * 0.8, max(RHO_VALUES) * 1.25, 100)
    log_factor = float(frame["log_factor"].mean())
    ax_dt.plot(
        rho_grid,
        log_factor / (xcc.P.c0 * rho_grid),
        color="#888888",
        lw=1.2,
        linestyle=":",
        label=r"$\Delta t\propto1/\rho$",
    )
    for n_eff, style, color in styles:
        sub = frame[frame["N_eff"].eq(n_eff)].sort_values("eta_fraction")
        label = rf"$N_{{\rm eff}}={n_eff:,.0f}$"
        ax_dt.plot(
            sub["eta_fraction"],
            sub["control_duration"],
            style,
            color=color,
            lw=1.6,
            ms=7.0,
            mfc="none",
            label=label,
        )
        ax_cum.plot(
            sub["eta_fraction"],
            sub["cum_fraction_t2"],
            style,
            color=color,
            lw=1.6,
            ms=7.0,
            mfc="none",
            label=label,
        )

    ax_dt.set_xscale("log")
    ax_dt.set_yscale("log")
    ax_dt.set_xlabel(r"$\rho=\eta/N_{\rm eff}$")
    ax_dt.set_ylabel(r"$\Delta t$ (days)")
    ax_dt.set_title("(a) Plateau duration", loc="left", fontsize=10)
    ax_dt.legend(loc="best", fontsize=8)

    ax_cum.set_xscale("log")
    ax_cum.set_xlabel(r"$\rho=\eta/N_{\rm eff}$")
    ax_cum.set_ylabel(r"$I_{t_2,\rm cum}/N_{\rm eff}=h(\rho)$")
    ax_cum.set_title("(b) Cumulative infection fraction", loc="left", fontsize=10)
    ax_cum.legend(loc="best", fontsize=8)

    for ax in (ax_dt, ax_cum):
        ax.grid(True, color="#D9D9D9", lw=0.6, alpha=0.6)
        ax.tick_params(direction="out", length=3.5, width=0.8)

    fig.suptitle(
        r"Group 2: metrics vary with $\rho$ and coincide across $N_{\rm eff}$",
        fontsize=10.5,
    )
    fig.savefig(FIG_DIR / f"{RHO_STEM}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{RHO_STEM}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_plotting()
    i0_fraction = reference_i0_fraction()
    exact, series = build_exact_scaling(i0_fraction)
    refit = build_refit_summary()
    rho_sweep = build_rho_sweep(i0_fraction)
    checks = build_invariance_checks(exact)
    if not bool(checks["passed"].all()):
        failed = checks[~checks["passed"]]
        raise RuntimeError(f"无量纲标度数值校验失败：\n{failed.to_string(index=False)}")

    exact.to_csv(HERE / EXACT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    refit.to_csv(HERE / REFIT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    checks.to_csv(HERE / CHECKS_NAME, index=False, encoding="utf-8-sig")
    series.to_csv(HERE / TIMESERIES_NAME, index=False, encoding="utf-8-sig")
    rho_sweep.to_csv(HERE / RHO_SWEEP_NAME, index=False, encoding="utf-8-sig")
    plot_collapse(exact, series)
    plot_clearance_tail(exact)
    plot_rho_dependence(rho_sweep)

    print(f"Generated: {HERE / EXACT_SUMMARY_NAME}")
    print(f"Generated: {HERE / REFIT_SUMMARY_NAME}")
    print(f"Generated: {HERE / CHECKS_NAME}")
    print(f"Generated: {HERE / RHO_SWEEP_NAME}")
    print(f"Generated: {FIG_DIR / (COLLAPSE_STEM + '.pdf')}")
    print(f"Generated: {FIG_DIR / (TAIL_STEM + '.pdf')}")
    print(f"Generated: {FIG_DIR / (RHO_STEM + '.pdf')}")
    print(
        exact[
            [
                "N_eff",
                "t1",
                "control_duration",
                "clear_time_I_le_1",
                "clear_time_fractional",
                "max_i_collapse_error",
                "max_q_collapse_error",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
