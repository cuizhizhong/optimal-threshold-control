"""TDINN-q-only 消融对照实验。

本模块构造反事实对照

    c(t) = c0, q(t) = q_TDINN(t),

用于分离完整 TDINN 控制中接触率控制和隔离率控制的作用。该对照
不是重新训练得到的新 TDINN 控制。
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
EFFECTIVE_DIR = PARENT / "effective_population_sensitivity"
for path in [str(PARENT), str(THRESHOLD_DIR), str(EFFECTIVE_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import xian_control_comparison as xcc  # noqa: E402
import threshold_landscape_analysis as tla  # noqa: E402
import effective_population_sensitivity as eps  # noqa: E402


OUT_DIR = HERE
ZOOM_X_END = 50.0
W_C = 1.0
W_Q = 1.0

STRATEGY_ORDER = ["TDINN控制", "TDINN-q-only", "情景一阈值控制", "常规控制"]
COLORS = {
    "TDINN控制": "#0068a9",
    "TDINN-q-only": "#7b3294",
    "情景一阈值控制": "#c43c39",
    "常规控制": "#333333",
}
LABELS = {
    "TDINN控制": "TDINN control",
    "TDINN-q-only": "TDINN-q-only",
    "情景一阈值控制": "Threshold control",
    "常规控制": "Routine control",
}
STYLES = {
    "TDINN控制": "-",
    "TDINN-q-only": "-.",
    "情景一阈值控制": "--",
    "常规控制": ":",
}


def ensure_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_to_csv(df: pd.DataFrame, path: Path) -> Path:
    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
    except PermissionError:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        fallback = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        df.to_csv(fallback, index=False, encoding="utf-8-sig")
        print(f"Warning: {path.name} is locked; wrote {fallback.name} instead.")
        return fallback


def daily_cases(sub: pd.DataFrame, column: str, day_edges: np.ndarray) -> np.ndarray:
    values = np.interp(day_edges, sub["t"].to_numpy(), sub[column].to_numpy())
    return np.maximum(np.diff(values), 0.0)


def epidemic_clear_time(df: pd.DataFrame) -> Tuple[float, bool]:
    if df.empty:
        return np.nan, False
    return xcc.epidemic_clear_time(df)


def summarize_strategy(
    scenario: str,
    strategy: str,
    df: pd.DataFrame,
    params: tla.LandscapeParams,
    eta: float,
    control_start: float,
    control_end: float,
    control_duration: float,
    status: str = "ok",
) -> Dict[str, float | str]:
    clear_time, cleared = epidemic_clear_time(df)
    outcome_end = clear_time if cleared else float(df["t"].iloc[-1])
    t = df["t"].to_numpy()
    active = t <= outcome_end + 1.0e-9
    I = df["I"].to_numpy()
    peak_idx = int(np.argmax(np.where(active, I, -np.inf)))
    cum_total = xcc.interpolate_series(t, df["Cc"].to_numpy(), outcome_end) + xcc.interpolate_series(t, df["Cq"].to_numpy(), outcome_end)

    if strategy == "常规控制":
        J_c = J_q = J = 0.0
    else:
        reduced_c = np.maximum(params.c0 - df["c"].to_numpy(), 0.0)
        enhanced_q = np.maximum(df["q"].to_numpy() - params.q0, 0.0)
        relative_c = reduced_c / params.c0
        relative_q = enhanced_q / (1.0 - params.q0)
        J_c = xcc.integrate_interval(t, relative_c, control_start, control_end)
        J_q = xcc.integrate_interval(t, relative_q, control_start, control_end)
        J = xcc.integrate_interval(t, xcc.DEFAULT_W_C * relative_c**2 + xcc.DEFAULT_W_Q * relative_q**2, control_start, control_end)

    return {
        "scenario": scenario,
        "strategy": strategy,
        "N": params.N,
        "eta": eta,
        "eta_fraction": eta / params.N,
        "peak_I": float(I[peak_idx]),
        "peak_time": float(t[peak_idx]),
        "time_above_eta": xcc.integrate_interval(t, (I > eta + 1.0e-5).astype(float), 0.0, outcome_end),
        "clear_time": float(clear_time) if cleared else np.nan,
        "cum_total_infections": float(cum_total) if cleared else np.nan,
        "J_c": float(J_c),
        "J_q": float(J_q),
        "J": float(J),
        "q_max": float(df.loc[active, "q"].max()),
        "control_start": float(control_start),
        "control_end": float(control_end),
        "control_duration": float(control_duration),
        "status": status if cleared else "not_cleared",
    }


def plot_four_strategy_panel(
    scenario_title: str,
    eta: float,
    all_df: pd.DataFrame,
    observed: pd.DataFrame,
    t1: float,
    output_stem: str,
    display_x_end: float,
    truncated: bool,
) -> None:
    day_edges = np.arange(0.0, np.ceil(display_x_end) + 1.0)
    day_starts = day_edges[:-1]

    def add_markers(ax) -> None:
        ax.axvline(float(observed["t"].iloc[-1]), color="#999999", lw=1.0, linestyle=":", alpha=0.75)
        ax.axvline(t1, color="#c43c39", lw=1.0, alpha=0.45)

    fig = plt.figure(figsize=(12.6, 11.9), constrained_layout=True)
    gs = fig.add_gridspec(3, 2)
    ax_i = fig.add_subplot(gs[0, :])
    ax_new = fig.add_subplot(gs[1, 0])
    ax_qnew = fig.add_subplot(gs[1, 1])
    ax_c = fig.add_subplot(gs[2, 0])
    ax_q = fig.add_subplot(gs[2, 1])
    ax_i_zoom = ax_i.inset_axes([0.62, 0.60, 0.34, 0.33])
    ax_new_zoom = ax_new.inset_axes([0.54, 0.56, 0.40, 0.36])
    ax_qnew_zoom = ax_qnew.inset_axes([0.54, 0.56, 0.40, 0.36])

    new_low_values: List[float] = [float(observed["community_new"].max())]
    qnew_low_values: List[float] = [float(observed["quarantine_new"].max())]
    new_all_values: List[float] = []
    qnew_all_values: List[float] = []
    zoom_strategies = {"TDINN控制", "TDINN-q-only", "情景一阈值控制"}

    for strategy in STRATEGY_ORDER:
        sub_all = all_df[all_df["strategy"].eq(strategy)]
        if sub_all.empty:
            continue
        color = COLORS[strategy]
        label = LABELS[strategy]
        style = STYLES[strategy]
        sub = sub_all[sub_all["t"] <= display_x_end].copy()
        ax_i.plot(sub["t"], sub["I"], label=label, color=color, linestyle=style, lw=2.1)

        new = daily_cases(sub_all, "Cc", day_edges)
        qnew = daily_cases(sub_all, "Cq", day_edges)
        new_all_values.append(float(np.max(new)))
        qnew_all_values.append(float(np.max(qnew)))

        if strategy in zoom_strategies:
            new_low_values.append(float(np.max(new)))
            qnew_low_values.append(float(np.max(qnew)))
            ax_i_zoom.plot(sub_all["t"], sub_all["I"], label=label, color=color, linestyle=style, lw=1.7)
            ax_new_zoom.plot(day_starts, new, label=label, color=color, linestyle=style, lw=1.7)
            ax_qnew_zoom.plot(day_starts, qnew, label=label, color=color, linestyle=style, lw=1.7)

        ax_new.plot(day_starts, new, label=label, color=color, linestyle=style, lw=2.1)
        ax_qnew.plot(day_starts, qnew, label=label, color=color, linestyle=style, lw=2.1)
        ax_c.plot(sub["t"], sub["c"], label=label, color=color, linestyle=style, lw=2.1)
        ax_q.plot(sub["t"], sub["q"], label=label, color=color, linestyle=style, lw=2.1)

    ax_new_zoom.scatter(observed["t"], observed["community_new"], s=24, color="#d55e00", edgecolors="white", linewidths=0.5, label="Observed data", zorder=5)
    ax_qnew_zoom.scatter(observed["t"], observed["quarantine_new"], s=24, color="#d55e00", edgecolors="white", linewidths=0.5, label="Observed data", zorder=5)
    ax_i.axhline(eta, color="#777777", lw=1.2, linestyle="-.", label=rf"$\eta={eta:g}$")
    ax_i_zoom.axhline(eta, color="#777777", lw=1.0, linestyle="-.")

    for ax in [ax_i, ax_i_zoom, ax_new, ax_new_zoom, ax_qnew, ax_qnew_zoom, ax_c, ax_q]:
        add_markers(ax)
    for ax in [ax_i, ax_new, ax_qnew, ax_c, ax_q]:
        ax.set_xlim(0.0, display_x_end)
    for ax in [ax_i_zoom, ax_new_zoom, ax_qnew_zoom]:
        ax.set_xlim(0.0, ZOOM_X_END)
        ax.set_title("zoom", fontsize=8, pad=2)
        ax.tick_params(labelsize=8)
    for ax in [ax_i, ax_new, ax_qnew]:
        ax.set_yscale("log")

    visible_i_peak = float(all_df.loc[all_df["t"].le(display_x_end), "I"].max())
    low_peak = float(all_df.loc[all_df["strategy"].isin(["TDINN控制", "TDINN-q-only", "情景一阈值控制"]), "I"].max())
    ax_i.set_ylim(1.0, max(1.08 * visible_i_peak, 1.35 * low_peak, 1.25 * eta, 200.0))
    ax_i_zoom.set_ylim(0.0, max(200.0, 1.35 * low_peak, 1.2 * eta))
    ax_new.set_ylim(1.0, max(80.0, 1.08 * max(new_all_values), 1.35 * max(new_low_values)))
    ax_qnew.set_ylim(1.0, max(180.0, 1.08 * max(qnew_all_values), 1.35 * max(qnew_low_values)))
    ax_new_zoom.set_ylim(0.0, max(10.0, 1.35 * max(new_low_values)))
    ax_qnew_zoom.set_ylim(0.0, max(10.0, 1.35 * max(qnew_low_values)))

    suffix = " (display truncated)" if truncated else ""
    ax_i.set_title(f"{scenario_title}{suffix}")
    ax_i.set_ylabel(r"$I(t)$")
    ax_new.set_title("Daily new community infections")
    ax_new.set_ylabel(r"$I_{new}(t)$")
    ax_qnew.set_title("Daily new quarantined infections")
    ax_qnew.set_ylabel(r"$I_{q_{new}}(t)$")
    ax_c.set_title("Contact rate")
    ax_c.set_xlabel(r"$t$")
    ax_c.set_ylabel(r"$c(t)$")
    ax_q.set_title("Quarantine rate")
    ax_q.set_xlabel(r"$t$")
    ax_q.set_ylabel(r"$q(t)$")

    for ax, fs in [(ax_i, 8.1), (ax_new, 7.8), (ax_qnew, 7.8), (ax_c, 7.8), (ax_q, 7.8)]:
        ax.legend(loc="lower right", fontsize=fs)
    for ax in [ax_i_zoom, ax_new_zoom, ax_qnew_zoom]:
        ax.legend(loc="upper right", fontsize=6.2, frameon=True)

    fig.savefig(OUT_DIR / f"{output_stem}.pdf")
    fig.savefig(OUT_DIR / f"{output_stem}.png", dpi=220)
    plt.close(fig)


def build_scenario(
    scenario: str,
    title: str,
    output_stem: str,
    params: tla.LandscapeParams,
    fit: xcc.InitialFit,
    eta: float,
    observed: pd.DataFrame,
    display_limit: float | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    tdin_df = tla.solve_time_control_param("TDINN控制", fit, params, xcc.c_real, xcc.q_real)
    q_only_df = tla.solve_time_control_param("TDINN-q-only", fit, params, tla.c_const(params), xcc.q_real)
    routine_df = tla.solve_time_control_param("常规控制", fit, params, tla.c_const(params), tla.q_const(params))
    threshold_df, details = tla.solve_threshold_fast(fit, eta, params, routine_df)
    threshold_summary = tla.summarize_threshold(threshold_df, eta, params, details, W_C, W_Q)

    all_df = pd.concat([tdin_df, q_only_df, threshold_df, routine_df], ignore_index=True)
    safe_to_csv(all_df, OUT_DIR / f"timeseries_{output_stem.replace('panels_', '')}.csv")

    rows: List[Dict[str, float | str]] = []
    for strategy, df in [
        ("TDINN控制", tdin_df),
        ("TDINN-q-only", q_only_df),
        ("情景一阈值控制", threshold_df),
        ("常规控制", routine_df),
    ]:
        if strategy == "情景一阈值控制":
            control_start = float(threshold_summary["t1"])
            control_end = float(threshold_summary["t2"])
            control_duration = float(threshold_summary["control_duration"])
        elif strategy in {"TDINN控制", "TDINN-q-only"}:
            clear_time, _ = epidemic_clear_time(df)
            control_start = 0.0
            control_end = clear_time
            control_duration = clear_time
        else:
            control_start = 0.0
            control_end = 0.0
            control_duration = 0.0
        rows.append(summarize_strategy(scenario, strategy, df, params, eta, control_start, control_end, control_duration))

    summary = pd.DataFrame(rows)
    max_clear = float(np.nanmax(summary["clear_time"].to_numpy(dtype=float)))
    display_x_end = display_limit if display_limit is not None else max_clear
    truncated = display_limit is not None and display_limit < max_clear
    plot_four_strategy_panel(title, eta, all_df, observed, float(threshold_summary["t1"]), output_stem, display_x_end, truncated)
    return all_df, summary


def main() -> None:
    ensure_dir()
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False, "mathtext.fontset": "dejavusans"})
    observed = xcc.load_observed_data()

    city_params = tla.LandscapeParams(N=xcc.P.N)
    city_fit = xcc.fit_initial_conditions(observed)
    neff_params = tla.LandscapeParams(N=50_000.0)
    neff_fit = eps.fit_initial_condition_for_N(observed, neff_params)

    summaries: List[pd.DataFrame] = []
    _, summary = build_scenario(
        "city_eta002N",
        r"$N=13{,}163{,}000,\ \eta=0.002N$",
        "panels_city_eta002N",
        city_params,
        city_fit,
        0.002 * city_params.N,
        observed,
    )
    summaries.append(summary)

    _, summary = build_scenario(
        "city_eta100",
        r"$N=13{,}163{,}000,\ \eta=100$",
        "panels_city_eta100",
        city_params,
        city_fit,
        100.0,
        observed,
        display_limit=120.0,
    )
    summaries.append(summary)

    _, summary = build_scenario(
        "Neff50000_eta100",
        r"$N_{\rm eff}=50{,}000,\ \eta=100$",
        "panels_Neff50000_eta100",
        neff_params,
        neff_fit,
        100.0,
        observed,
    )
    summaries.append(summary)

    summary_df = pd.concat(summaries, ignore_index=True)
    safe_to_csv(summary_df, OUT_DIR / "tdinn_q_only_summary.csv")
    print("Generated TDINN-q-only comparison outputs in:")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
