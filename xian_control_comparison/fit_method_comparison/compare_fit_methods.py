"""Compare initial-condition fitting criteria for the Xi'an TDINN controls.

The model, parameters, learned c(t), learned q(t), and observed Excel data are
borrowed from the parent ``xian_control_comparison.py`` script.  This file only
changes the least-squares fitting objective for the effective initial seed I0.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import least_squares


OUT_DIR = Path(__file__).resolve().parent
PARENT_DIR = OUT_DIR.parent
sys.path.insert(0, str(PARENT_DIR))

import xian_control_comparison as xcc  # noqa: E402


@dataclass(frozen=True)
class FitResult:
    method: str
    label: str
    S0: float
    I0: float
    objective_mse: float
    daily_rmse_total: float
    daily_rmse_community: float
    daily_rmse_quarantine: float
    cumulative_rmse_total: float
    cumulative_rmse_community: float
    cumulative_rmse_quarantine: float
    predicted_total_cases: float
    observed_total_cases: float


def _observed_arrays(observed: pd.DataFrame) -> Dict[str, np.ndarray]:
    return {
        "community_new": observed["community_new"].to_numpy(dtype=float),
        "quarantine_new": observed["quarantine_new"].to_numpy(dtype=float),
        "community_cum": observed["community_cum"].to_numpy(dtype=float),
        "quarantine_cum": observed["quarantine_cum"].to_numpy(dtype=float),
        "t": observed["t"].to_numpy(dtype=float),
    }


def _simulate_from_log_i0(theta: np.ndarray, n_days: int) -> Tuple[float, float, Dict[str, np.ndarray]]:
    I0 = float(np.exp(theta[0]))
    S0 = xcc.P.N - I0
    if S0 <= 0.0:
        raise ValueError("S0 must remain positive.")

    day_grid = np.arange(n_days + 1, dtype=float)
    sol = xcc.solve_with_initials(S0, I0, float(n_days), xcc.c_real, xcc.q_real, t_eval=day_grid)
    community_cum = np.maximum(sol.y[4, 1:], 0.0)
    quarantine_cum = np.maximum(sol.y[5, 1:], 0.0)
    predicted = {
        "community_new": np.maximum(np.diff(sol.y[4]), 0.0),
        "quarantine_new": np.maximum(np.diff(sol.y[5]), 0.0),
        "community_cum": community_cum,
        "quarantine_cum": quarantine_cum,
        "I": sol.y[1, 1:],
        "Iq": sol.y[3, 1:],
    }
    return S0, I0, predicted


def _residual(theta: np.ndarray, observed_arrays: Dict[str, np.ndarray], method: str) -> np.ndarray:
    n_days = len(observed_arrays["community_new"])
    try:
        _, _, pred = _simulate_from_log_i0(theta, n_days)
    except Exception:
        if method == "paper_mse":
            return np.ones(4 * n_days) * 1.0e8
        return np.ones(2 * n_days) * 1.0e8

    obs_c_new = observed_arrays["community_new"]
    obs_q_new = observed_arrays["quarantine_new"]
    obs_c_cum = observed_arrays["community_cum"]
    obs_q_cum = observed_arrays["quarantine_cum"]

    if method == "sqrt_daily":
        return np.r_[
            np.sqrt(pred["community_new"] + 1.0) - np.sqrt(obs_c_new + 1.0),
            np.sqrt(pred["quarantine_new"] + 1.0) - np.sqrt(obs_q_new + 1.0),
        ]
    if method == "daily_mse":
        return np.r_[
            pred["community_new"] - obs_c_new,
            pred["quarantine_new"] - obs_q_new,
        ]
    if method == "paper_mse":
        return np.r_[
            pred["community_new"] - obs_c_new,
            pred["quarantine_new"] - obs_q_new,
            pred["community_cum"] - obs_c_cum,
            pred["quarantine_cum"] - obs_q_cum,
        ]
    raise ValueError(f"Unknown fitting method: {method}")


def fit_i0(observed: pd.DataFrame, method: str, label: str) -> Tuple[FitResult, pd.DataFrame]:
    observed_arrays = _observed_arrays(observed)
    n_days = len(observed)
    starts = [1.0e-8, 1.0e-6, 1.0e-4, 1.0e-3, 1.0e-2, 0.1, 1.0, 10.0, 100.0]
    lower = np.log([1.0e-12])
    upper = np.log([1.0e6])

    best = None
    for start in starts:
        res = least_squares(
            lambda theta: _residual(theta, observed_arrays, method),
            np.log([start]),
            bounds=(lower, upper),
            max_nfev=220,
            xtol=1.0e-9,
            ftol=1.0e-9,
            gtol=1.0e-9,
        )
        value = float(np.sum(res.fun**2))
        if best is None or value < best[0]:
            best = (value, res.x, res.fun)

    if best is None:
        raise RuntimeError(f"No fit was produced for method {method}.")

    objective_sum, theta_hat, residual_at_hat = best
    S0, I0, pred = _simulate_from_log_i0(theta_hat, n_days)
    obs = observed_arrays

    daily_res_c = pred["community_new"] - obs["community_new"]
    daily_res_q = pred["quarantine_new"] - obs["quarantine_new"]
    cum_res_c = pred["community_cum"] - obs["community_cum"]
    cum_res_q = pred["quarantine_cum"] - obs["quarantine_cum"]
    daily_all = np.r_[daily_res_c, daily_res_q]
    cum_all = np.r_[cum_res_c, cum_res_q]

    result = FitResult(
        method=method,
        label=label,
        S0=S0,
        I0=I0,
        objective_mse=float(objective_sum / residual_at_hat.size),
        daily_rmse_total=float(np.sqrt(np.mean(daily_all**2))),
        daily_rmse_community=float(np.sqrt(np.mean(daily_res_c**2))),
        daily_rmse_quarantine=float(np.sqrt(np.mean(daily_res_q**2))),
        cumulative_rmse_total=float(np.sqrt(np.mean(cum_all**2))),
        cumulative_rmse_community=float(np.sqrt(np.mean(cum_res_c**2))),
        cumulative_rmse_quarantine=float(np.sqrt(np.mean(cum_res_q**2))),
        predicted_total_cases=float(pred["community_cum"][-1] + pred["quarantine_cum"][-1]),
        observed_total_cases=float(obs["community_cum"][-1] + obs["quarantine_cum"][-1]),
    )

    frame = pd.DataFrame(
        {
            "method": method,
            "label": label,
            "t": observed["t"].to_numpy(dtype=float),
            "community_new_obs": obs["community_new"],
            "quarantine_new_obs": obs["quarantine_new"],
            "community_cum_obs": obs["community_cum"],
            "quarantine_cum_obs": obs["quarantine_cum"],
            "community_new_pred": pred["community_new"],
            "quarantine_new_pred": pred["quarantine_new"],
            "community_cum_pred": pred["community_cum"],
            "quarantine_cum_pred": pred["quarantine_cum"],
            "I_pred": pred["I"],
            "Iq_pred": pred["Iq"],
        }
    )
    return result, frame


def _write_latex_table(summary: pd.DataFrame) -> None:
    rows = []
    for _, row in summary.iterrows():
        rows.append(
            f"{row['label']} & {row['I0']:.6g} & {row['daily_rmse_total']:.3f} & "
            f"{row['cumulative_rmse_total']:.3f} & {row['predicted_total_cases']:.1f} \\\\"
        )

    content = "\n".join(
        [
            "\\begin{tabular}{lcccc}",
            "\\toprule",
            "拟合准则 & $I_0$ & 每日新增RMSE & 累计RMSE & 预测累计病例 \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "fit_method_summary_table.tex").write_text(content, encoding="utf-8")


def plot_fit_comparison(summary: pd.DataFrame, timeseries: pd.DataFrame) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
        }
    )
    colors = {
        "sqrt_daily": "#0068a9",
        "daily_mse": "#c43c39",
        "paper_mse": "#333333",
    }
    linestyles = {
        "sqrt_daily": "-",
        "daily_mse": "--",
        "paper_mse": ":",
    }

    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.4), constrained_layout=True)
    panels = [
        ("community_new_obs", "community_new_pred", "Daily community cases", "new cases"),
        ("quarantine_new_obs", "quarantine_new_pred", "Daily quarantine cases", "new cases"),
        ("community_cum_obs", "community_cum_pred", "Cumulative community cases", "cases"),
        ("quarantine_cum_obs", "quarantine_cum_pred", "Cumulative quarantine cases", "cases"),
    ]
    obs_color = "#d56b1b"
    for ax, (obs_col, pred_col, title, ylabel) in zip(axes.ravel(), panels):
        first = timeseries[timeseries["method"] == summary["method"].iloc[0]]
        ax.scatter(first["t"], first[obs_col], s=22, color=obs_color, label="observed", zorder=4)
        for _, row in summary.iterrows():
            sub = timeseries[timeseries["method"] == row["method"]]
            ax.plot(
                sub["t"],
                sub[pred_col],
                color=colors[row["method"]],
                linestyle=linestyles[row["method"]],
                linewidth=2.2,
                label=row["label"],
            )
        ax.set_title(title)
        ax.set_xlabel("t")
        ax.set_ylabel(ylabel)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(frameon=False, fontsize=8)

    fig.savefig(OUT_DIR / "fit_method_comparison_panels.png", dpi=300)
    fig.savefig(OUT_DIR / "fit_method_comparison_panels.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    x = np.arange(len(summary))
    width = 0.36
    ax.bar(x - width / 2, summary["daily_rmse_total"], width=width, label="daily new RMSE", color="#0068a9")
    ax.bar(x + width / 2, summary["cumulative_rmse_total"], width=width, label="cumulative RMSE", color="#c43c39")
    ax.set_xticks(x)
    ax.set_xticklabels(summary["label"], rotation=12, ha="right")
    ax.set_ylabel("RMSE")
    ax.set_title("Error metrics under different fitting criteria")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    fig.savefig(OUT_DIR / "fit_method_error_metrics.png", dpi=300)
    fig.savefig(OUT_DIR / "fit_method_error_metrics.pdf")
    plt.close(fig)


def run(methods: Iterable[Tuple[str, str]]) -> None:
    observed = xcc.load_observed_data()
    results = []
    frames = []
    for method, label in methods:
        result, frame = fit_i0(observed, method, label)
        results.append(result)
        frames.append(frame)

    summary = pd.DataFrame([result.__dict__ for result in results])
    timeseries = pd.concat(frames, ignore_index=True)

    summary.to_csv(OUT_DIR / "fit_method_summary.csv", index=False, encoding="utf-8-sig")
    timeseries.to_csv(OUT_DIR / "fit_method_timeseries.csv", index=False, encoding="utf-8-sig")
    _write_latex_table(summary)
    plot_fit_comparison(summary, timeseries)

    with (OUT_DIR / "fit_method_notes.md").open("w", encoding="utf-8") as f:
        f.write("# Initial-condition fitting method comparison\n\n")
        f.write("The fitted unknown is only the effective initial community infectious seed I0, with R(0)=0 and S0=N-I0.\n\n")
        f.write("- daily sqrt residual: fits daily new community/quarantine cases after a square-root variance-stabilizing transform.\n")
        f.write("- daily MSE: fits only daily new community/quarantine cases with ordinary residuals.\n")
        f.write("- paper-style MSE: fits daily new and cumulative community/quarantine cases with ordinary residuals, matching the structure of the He--Tang--Xiao data loss.\n")


def main() -> None:
    run(
        [
            ("sqrt_daily", "daily sqrt residual"),
            ("daily_mse", "daily MSE"),
            ("paper_mse", "paper-style MSE"),
        ]
    )


if __name__ == "__main__":
    main()
