"""有效人口规模 N_eff 对情景一阈值控制的敏感性分析。

本脚本只生成探索性数值输出和 LaTeX 笔记。实验固定
He--Tang--Xiao 参数与 TDINN 控制函数，对每个 N_eff 重新拟合 I0，
再比较 eta=100、eta=520 和 eta=0.002 N_eff 三类阈值口径。
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
THRESHOLD_DIR = PARENT / "threshold_landscape_analysis"
for path in [str(PARENT), str(THRESHOLD_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import xian_control_comparison as xcc  # noqa: E402
import threshold_landscape_analysis as tla  # noqa: E402


OUT_DIR = HERE
FIG_DIR = OUT_DIR / "figures"

N_EFF_VALUES = [5.0e4, 1.0e5, 3.0e5, 1.0e6, 3.0e6, xcc.P.N]
ETA_SCENARIOS = ["eta100", "eta520", "eta_fraction_0p002"]
W_C = 1.0
W_Q = 2.0


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


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


def scenario_eta(name: str, params: tla.LandscapeParams) -> float:
    if name == "eta100":
        return 100.0
    if name == "eta520":
        return 520.0
    if name == "eta_fraction_0p002":
        return 0.002 * params.N
    raise ValueError(f"Unknown eta scenario: {name}")


def scenario_label(name: str) -> str:
    labels = {
        "eta100": r"$\eta=100$",
        "eta520": r"$\eta=520$",
        "eta_fraction_0p002": r"$\eta=0.002N_{\rm eff}$",
    }
    return labels[name]


def fit_initial_condition_for_N(
    observed: pd.DataFrame,
    params: tla.LandscapeParams,
    residual_type: str = "paper_mse",
) -> xcc.InitialFit:
    """在给定 N_eff 下只重新拟合 I0。

    固定 R(0)=0，令 S0=N_eff-I0。传播参数和 TDINN 控制函数保持不变。
    """

    obs_c = observed["community_new"].to_numpy(dtype=float)
    obs_q = observed["quarantine_new"].to_numpy(dtype=float)
    obs_c_cum = observed["community_cum"].to_numpy(dtype=float)
    obs_q_cum = observed["quarantine_cum"].to_numpy(dtype=float)
    n_days = len(observed)
    day_grid = np.arange(n_days + 1, dtype=float)

    def unpack(theta: np.ndarray) -> Tuple[float, float, float]:
        I0 = float(np.exp(theta[0]))
        S0 = params.N - I0
        return S0, I0, 0.0

    def model_predictions(theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Tuple[float, float, float]]:
        S0, I0, R0_initial = unpack(theta)
        if S0 <= 0.0 or I0 <= 0.0:
            raise ValueError("Infeasible initial state.")
        y0 = np.array([S0, I0, 0.0, 0.0, 0.0, 0.0])
        sol = solve_ivp(
            tla.rhs_with_controls(params, xcc.c_real, xcc.q_real),
            (0.0, float(n_days)),
            y0,
            t_eval=day_grid,
            dense_output=False,
            rtol=1.0e-7,
            atol=1.0e-5,
        )
        if not sol.success:
            raise RuntimeError(sol.message)
        pred_c_cum = sol.y[4, 1:]
        pred_q_cum = sol.y[5, 1:]
        return np.diff(sol.y[4]), np.diff(sol.y[5]), pred_c_cum, pred_q_cum, (S0, I0, R0_initial)

    def residual(theta: np.ndarray) -> np.ndarray:
        try:
            pred_c, pred_q, pred_c_cum, pred_q_cum, _ = model_predictions(theta)
        except Exception:
            size = 4 * n_days if residual_type == "paper_mse" else 2 * n_days
            return np.ones(size) * 1.0e6
        if residual_type == "paper_mse":
            scale = np.sqrt(float(n_days))
            return np.r_[
                (pred_c - obs_c) / scale,
                (pred_q - obs_q) / scale,
                (pred_c_cum - obs_c_cum) / scale,
                (pred_q_cum - obs_q_cum) / scale,
            ]
        return np.r_[pred_c - obs_c, pred_q - obs_q]

    start_values = [1.0e-4, 1.0e-3, 1.0e-2, 0.1, 1.0, 10.0, 100.0]
    upper_value = min(1.0e6, 0.95 * params.N)
    starts = [value for value in start_values if value < upper_value]
    theta_starts = [np.log([value]) for value in starts]
    lower = np.log([1.0e-8])
    upper = np.log([upper_value])

    best = None
    for theta0 in theta_starts:
        res = least_squares(
            residual,
            theta0,
            bounds=(lower, upper),
            max_nfev=160,
            xtol=1.0e-8,
            ftol=1.0e-8,
            gtol=1.0e-8,
        )
        value = float(np.sum(res.fun**2))
        if best is None or value < best[0]:
            best = (value, res.x)

    if best is None:
        raise RuntimeError("Initial-condition fitting did not run.")
    objective, theta_hat = best
    pred_c, pred_q, _, _, initial = model_predictions(theta_hat)
    raw_rmse = float(np.sqrt(np.mean(np.r_[pred_c - obs_c, pred_q - obs_q] ** 2)))
    return xcc.InitialFit(*initial, objective=objective, raw_rmse=raw_rmse, residual_type=residual_type)


def run_threshold_case(
    fit: xcc.InitialFit,
    params: tla.LandscapeParams,
    eta_name: str,
) -> Dict[str, float | str]:
    eta = scenario_eta(eta_name, params)
    try:
        routine_df = tla.solve_time_control_param("常规控制", fit, params, tla.c_const(params), tla.q_const(params))
        threshold_df, details = tla.solve_threshold_fast(fit, eta, params, routine_df)
        row = tla.summarize_threshold(threshold_df, eta, params, details, W_C, W_Q)
    except Exception as exc:
        row = {
            "eta": eta,
            "eta_fraction": eta / params.N,
            "c0": params.c0,
            "t1": np.nan,
            "t2": np.nan,
            "control_duration": np.nan,
            "clear_time": np.nan,
            "peak_I": np.nan,
            "cum_total_infections": np.nan,
            "q_start": np.nan,
            "q_mean_control": np.nan,
            "q_min_theory": np.nan,
            "q_max_theory": np.nan,
            "J_c": np.nan,
            "J_q": np.nan,
            "J": np.nan,
            "raw_c_cost": np.nan,
            "raw_q_cost": np.nan,
            "w_c": W_C,
            "w_q": W_Q,
            "plateau_max_error": np.nan,
            "q_was_clipped": np.nan,
            "status": "error",
            "error_message": str(exc),
        }
    row.update(
        {
            "N_eff": params.N,
            "eta_scenario": eta_name,
            "eta_scenario_label": scenario_label(eta_name),
            "I0_fit": fit.I0,
            "I0_fraction": fit.I0 / params.N,
            "S0_fit": fit.S0,
            "fit_objective": fit.objective,
            "fit_raw_rmse": fit.raw_rmse,
        }
    )
    row["cum_total_fraction"] = (
        float(row["cum_total_infections"]) / params.N
        if np.isfinite(float(row["cum_total_infections"]))
        else np.nan
    )
    row["clear_tail_duration"] = (
        float(row["clear_time"]) - float(row["t2"])
        if np.isfinite(float(row["clear_time"])) and np.isfinite(float(row["t2"]))
        else np.nan
    )
    return row


# 论文 §8 全程采用固定归一化初值的单一口径（见 xian_dom/caliber.py）：
# i0 = I0_city / N_city，跨 N_eff 不重新拟合。图 neff_time_metrics 由该口径生成。
CITY_N, CITY_I0 = 13_163_000.0, 0.00100662823352
FIXED_I0_FRACTION = CITY_I0 / CITY_N          # = 7.6474e-11


def fixed_initial_condition_for_N(params: tla.LandscapeParams) -> xcc.InitialFit:
    """按固定归一化初值构造 InitialFit（不拟合）。"""

    I0 = FIXED_I0_FRACTION * params.N
    return xcc.InitialFit(S0=params.N - I0, I0=I0, R0_initial=0.0,
                          objective=float("nan"), raw_rmse=float("nan"),
                          residual_type="fixed_i0")


def build_summary(observed: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """指标用固定归一化初值口径算；逐 N 重拟合结果仍写入 fit_rows 留档。

    重拟合已不进入论文（原局限 (3) 的 rmse 退化表随口径统一而删除），但保留其
    数值记录以便追溯该结论的来源。
    """

    fit_rows: List[Dict[str, float | str]] = []
    rows: List[Dict[str, float | str]] = []
    for N_eff in N_EFF_VALUES:
        params = tla.LandscapeParams(N=float(N_eff))
        refit = fit_initial_condition_for_N(observed, params)   # 仅留档
        fit_rows.append(
            {
                "N_eff": params.N,
                "I0_fit": refit.I0,
                "I0_fraction": refit.I0 / params.N,
                "S0_fit": refit.S0,
                "fit_objective": refit.objective,
                "fit_raw_rmse": refit.raw_rmse,
                "residual_type": refit.residual_type,
            }
        )
        fit = fixed_initial_condition_for_N(params)
        for eta_name in ETA_SCENARIOS:
            rows.append(run_threshold_case(fit, params, eta_name))
    return pd.DataFrame(rows), pd.DataFrame(fit_rows)


def plot_time_metrics(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), constrained_layout=True)
    metrics = [("t1", r"$t_1$"), ("control_duration", r"$\Delta t$"), ("clear_time", r"$T_{\rm clear}$")]
    for ax, (column, ylabel) in zip(axes, metrics):
        for eta_name, sub in summary.groupby("eta_scenario", sort=False):
            sub = sub.sort_values("N_eff")
            ax.plot(sub["N_eff"], sub[column], "o-", lw=1.8, ms=4.0, label=scenario_label(eta_name))
        ax.set_xscale("log")
        if column in {"control_duration", "clear_time"}:
            ax.set_yscale("log")
        ax.set_xlabel(r"$N_{\rm eff}$")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
    axes[0].legend(loc="best", fontsize=8)
    fig.savefig(FIG_DIR / "effective_population_time_metrics.pdf")
    fig.savefig(FIG_DIR / "effective_population_time_metrics.png", dpi=220)
    plt.close(fig)


def plot_cost_metrics(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), constrained_layout=True)
    metrics = [("cum_total_infections", r"$I_{t_{\rm cum}}$"), ("J_q", r"$J_q$"), ("J", r"$J$")]
    for ax, (column, ylabel) in zip(axes, metrics):
        for eta_name, sub in summary.groupby("eta_scenario", sort=False):
            sub = sub.sort_values("N_eff")
            ax.plot(sub["N_eff"], sub[column], "o-", lw=1.8, ms=4.0, label=scenario_label(eta_name))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"$N_{\rm eff}$")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
    axes[0].legend(loc="best", fontsize=8)
    fig.savefig(FIG_DIR / "effective_population_cost_metrics.pdf")
    fig.savefig(FIG_DIR / "effective_population_cost_metrics.png", dpi=220)
    plt.close(fig)


def plot_eta_fraction(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.4), constrained_layout=True)
    for eta_name, sub in summary.groupby("eta_scenario", sort=False):
        sub = sub.sort_values("N_eff")
        ax.plot(sub["N_eff"], sub["eta_fraction"], "o-", lw=1.8, ms=4.0, label=scenario_label(eta_name))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$N_{\rm eff}$")
    ax.set_ylabel(r"$\eta/N_{\rm eff}$")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.savefig(FIG_DIR / "effective_population_eta_fraction.pdf")
    fig.savefig(FIG_DIR / "effective_population_eta_fraction.png", dpi=220)
    plt.close(fig)


def latex_float(value: float, digits: int = 2) -> str:
    if not np.isfinite(value):
        return "--"
    if abs(value) >= 100000 or (0 < abs(value) < 0.01):
        return f"{value:.{digits}e}"
    return f"{value:.{digits}f}"


def write_latex_table(summary: pd.DataFrame) -> None:
    rows: List[str] = []
    for _, row in summary.sort_values(["eta_scenario", "N_eff"]).iterrows():
        rows.append(
            " & ".join(
                [
                    f"{float(row['N_eff']):,.0f}",
                    str(row["eta_scenario_label"]),
                    latex_float(float(row["eta"]), 0),
                    latex_float(float(row["I0_fit"]), 4),
                    latex_float(float(row["t1"]), 2),
                    latex_float(float(row["control_duration"]), 2),
                    latex_float(float(row["clear_time"]), 2),
                    latex_float(float(row["J"]), 2),
                ]
            )
            + r" \\"
        )
    content = "\n".join(
        [
            r"\noindent\resizebox{\textwidth}{!}{%",
            r"\begin{tabular}{cccccccc}",
            r"\toprule",
            r"$N_{\rm eff}$ & 阈值口径 & $\eta$ & $\hat I_0$ & $t_1$ & $\Delta t$ & $T_{\rm clear}$ & $J$ \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            "",
        ]
    )
    (OUT_DIR / "effective_population_summary_table.tex").write_text(content, encoding="utf-8")


def run_inflection_analyses() -> None:
    """重建两组局部拐点实验，供实验笔记引用。"""

    scripts = [
        HERE / "plot_eta_80_100_150_inflection.py",
        HERE / "plot_Neff_40000_50000_60000_inflection.py",
    ]
    for script in scripts:
        subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=HERE,
            check=True,
        )


def run_dimensionless_scaling_analysis() -> None:
    """重建固定无量纲初值的精确标度实验。"""

    subprocess.run(
        [sys.executable, "-B", str(HERE / "dimensionless_scaling_analysis.py")],
        cwd=HERE,
        check=True,
    )


def run_inflection_invariance_analysis() -> None:
    """重建拐点高度的 beta 扫描和 q0 存在边界扫描。"""

    subprocess.run(
        [sys.executable, "-B", str(HERE / "inflection_invariance_analysis.py")],
        cwd=HERE,
        check=True,
    )


def write_inflection_inverse_summary() -> pd.DataFrame:
    """合并两组拐点实验中的二阶差分定位和 beta 反演结果。"""

    representative_dir = OUT_DIR / "representative_panels"
    eta_frame = pd.read_csv(
        representative_dir / "inflection_summary_eta_80_100_150_Neff50000.csv"
    )
    eta_frame.insert(0, "scan", "vary_eta")
    neff_frame = pd.read_csv(
        representative_dir / "inflection_summary_Neff_40000_50000_60000_eta100.csv"
    )
    neff_frame.insert(0, "scan", "vary_N_eff")
    combined = pd.concat([eta_frame, neff_frame], ignore_index=True)
    columns = [
        "scan",
        "N_eff",
        "eta",
        "eta_fraction",
        "t_inflection",
        "t_inflection_numeric",
        "t_inflection_numeric_error",
        "q_inflection_theory",
        "q_inflection_numeric",
        "q_inflection_numeric_error",
        "beta_recovered_numeric",
        "beta_recovery_error",
    ]
    output = combined[columns].copy()
    if float(output["q_inflection_numeric_error"].abs().max()) > 2.0e-8:
        raise RuntimeError("二阶差分拐点高度误差超过 2e-8。")
    if float(output["beta_recovery_error"].abs().max()) > 2.0e-8:
        raise RuntimeError("由拐点高度反演 beta 的误差超过 2e-8。")
    safe_to_csv(output, OUT_DIR / "inflection_inverse_summary.csv")
    return output


def inflection_table_rows(
    frame: pd.DataFrame,
    parameter_column: str,
    parameter_digits: int = 0,
) -> str:
    """把局部拐点汇总表转换为 LaTeX 行。"""

    rows: List[str] = []
    for _, row in frame.sort_values(parameter_column).iterrows():
        if parameter_column == "N_eff":
            parameter_text = f"{float(row[parameter_column]):,.0f}"
        else:
            parameter_text = latex_float(float(row[parameter_column]), parameter_digits)
        rows.append(
            " & ".join(
                [
                    parameter_text,
                    f"{float(row['eta_fraction']):.4f}",
                    latex_float(float(row["t1"]), 2),
                    latex_float(float(row["t_inflection"]), 2),
                    latex_float(float(row["control_duration"]), 2),
                    latex_float(float(row["clear_time"]), 2),
                ]
            )
            + r" \\"
        )
    return "\n".join(rows)


def write_note(summary: pd.DataFrame) -> None:
    table_tex = (OUT_DIR / "effective_population_summary_table.tex").read_text(encoding="utf-8")
    representative_dir = OUT_DIR / "representative_panels"
    eta_inflection = pd.read_csv(
        representative_dir / "inflection_summary_eta_80_100_150_Neff50000.csv"
    )
    neff_inflection = pd.read_csv(
        representative_dir / "inflection_summary_Neff_40000_50000_60000_eta100.csv"
    )
    exact_scaling = pd.read_csv(OUT_DIR / "dimensionless_scaling_exact_summary.csv")
    refit_scaling = pd.read_csv(OUT_DIR / "dimensionless_scaling_refit_summary.csv")
    scaling_checks = pd.read_csv(OUT_DIR / "dimensionless_scaling_invariance_checks.csv")
    rho_sweep = pd.read_csv(OUT_DIR / "dimensionless_scaling_rho_sweep.csv")
    inverse_summary = pd.read_csv(OUT_DIR / "inflection_inverse_summary.csv")
    beta_sweep = pd.read_csv(OUT_DIR / "inflection_beta_sweep.csv")
    boundary_scan = pd.read_csv(OUT_DIR / "inflection_boundary_scan.csv")
    if not bool(scaling_checks["passed"].astype(bool).all()):
        raise RuntimeError("无量纲标度校验表中存在未通过的指标。")

    exact_scaling_rows = "\n".join(
        " & ".join(
            [
                f"{float(row['N_eff']):,.0f}",
                f"{float(row['t1']):.3f}",
                f"{float(row['control_duration']):.3f}",
                f"{float(row['clear_time_I_le_1']):.2f}",
                f"{float(row['clear_time_fractional']):.2f}",
                f"{float(row['cum_fraction_t2']):.6f}",
                f"{float(row['J']):.3f}",
            ]
        )
        + r" \\"
        for _, row in exact_scaling.sort_values("N_eff").iterrows()
    )
    refit_scaling_rows = "\n".join(
        " & ".join(
            [
                f"{float(row['N_eff']):,.0f}",
                f"{float(row['I0_fraction']):.2e}",
                f"{float(row['fit_raw_rmse']):.3f}",
                f"{float(row['t1']):.2f}",
                f"{float(row['control_duration']):.2f}",
                f"{float(row['cum_total_fraction']):.6f}",
                f"{float(row['clear_time']):.2f}",
            ]
        )
        + r" \\"
        for _, row in refit_scaling.sort_values("N_eff").iterrows()
    )
    inverse_rows = "\n".join(
        " & ".join(
            [
                "变 $\\eta$" if row["scan"] == "vary_eta" else "变 $N_{\\rm eff}$",
                f"{float(row['N_eff']):,.0f}",
                f"{float(row['eta']):.0f}",
                f"{float(row['t_inflection']):.5f}",
                f"{float(row['t_inflection_numeric']):.5f}",
                f"{float(row['q_inflection_numeric']):.8f}",
                f"{float(row['beta_recovered_numeric']):.8f}",
            ]
        )
        + r" \\"
        for _, row in inverse_summary.iterrows()
    )
    rho_sweep_rows = "\n".join(
        " & ".join(
            [
                f"{float(row['eta_fraction']):.4f}",
                f"{float(row['N_eff']):,.0f}",
                f"{float(row['eta']):,.1f}",
                f"{float(row['t1']):.3f}",
                f"{float(row['control_duration']):.3f}",
                f"{float(row['log_factor']):.4f}",
                f"{float(row['cum_fraction_t2']):.6f}",
                f"{float(row['clear_time_fractional']):.2f}",
                f"{float(row['clear_time_I_le_1']):.2f}",
            ]
        )
        + r" \\"
        for _, row in rho_sweep.iterrows()
    )
    beta_sweep_rows = "\n".join(
        " & ".join(
            [
                f"{float(row['beta']):.4f}",
                f"{float(row['q_inflection_theory']):.8f}",
                f"{float(row['q_inflection_numeric']):.8f}",
                f"{float(row['q_inflection_numeric_error']):.2e}",
                f"{float(row['beta_recovered_numeric']):.6f}",
            ]
        )
        + r" \\"
        for _, row in beta_sweep.iterrows()
    )
    boundary_rows = "\n".join(
        " & ".join(
            [
                f"{float(row['q0']):.4f}",
                f"{float(row['existence_product']):.6f}",
                "是" if bool(row["inflection_exists"]) else "否",
                "--" if not bool(row["inflection_exists"]) else f"{float(row['tau_inflection']):.3f}",
                f"{float(row['control_duration']):.3f}",
                "--" if not bool(row["inflection_exists"]) else f"{float(row['t2_minus_t_inflection']):.3f}",
            ]
        )
        + r" \\"
        for _, row in boundary_scan.iterrows()
    )
    eta_inflection_rows = inflection_table_rows(eta_inflection, "eta")
    neff_inflection_rows = inflection_table_rows(neff_inflection, "N_eff")

    all_inflection = pd.concat([eta_inflection, neff_inflection], ignore_index=True)
    q_inflection_min = float(all_inflection["q_at_inflection"].min())
    q_inflection_max = float(all_inflection["q_at_inflection"].max())
    if q_inflection_max - q_inflection_min > 1.0e-9:
        raise RuntimeError("拐点处 q_c 数值没有通过参数无关性校验。")
    max_i_collapse_error = float(exact_scaling["max_i_collapse_error"].max())
    max_q_collapse_error = float(exact_scaling["max_q_collapse_error"].max())
    max_q_numeric_error = float(inverse_summary["q_inflection_numeric_error"].abs().max())
    max_beta_recovery_error = float(inverse_summary["beta_recovery_error"].abs().max())

    rho_cross_n_spread = float(
        rho_sweep.groupby("eta_fraction")[
            ["t1", "control_duration", "q_max_theory", "cum_fraction_t2", "clear_time_fractional"]
        ]
        .agg(lambda column: float(column.max() - column.min()))
        .to_numpy(dtype=float)
        .max()
    )
    rho_dt_max = float(rho_sweep["control_duration"].max())
    rho_dt_min = float(rho_sweep["control_duration"].min())
    log_factor_max = float(rho_sweep["log_factor"].max())
    log_factor_min = float(rho_sweep["log_factor"].min())

    max_beta_sweep_error = float(beta_sweep["q_inflection_numeric_error"].abs().max())
    q_star_baseline = float(1.0 - 1.0 / (2.0 * (1.0 - xcc.P.beta)))
    baseline_beta_row = beta_sweep[np.isclose(beta_sweep["beta"], xcc.P.beta)].iloc[0]
    two_sbar_fraction = float(baseline_beta_row["two_Sbar"]) / float(baseline_beta_row["N_eff"])
    s_star_fraction = float(baseline_beta_row["S_star"]) / float(baseline_beta_row["N_eff"])
    beta_limit = float(1.0 - 1.0 / (2.0 * (1.0 - xcc.P.q0)))
    absent = boundary_scan[~boundary_scan["inflection_exists"].astype(bool)].iloc[0]
    absent_q0 = float(absent["q0"])
    absent_product = float(absent["existence_product"])
    closest = boundary_scan[boundary_scan["inflection_exists"].astype(bool)].iloc[-1]
    closest_q0 = float(closest["q0"])
    closest_gap = float(closest["t2_minus_t_inflection"])

    base_row = summary[
        (summary["N_eff"].sub(xcc.P.N).abs() < 1.0e-6) & (summary["eta_scenario"].eq("eta_fraction_0p002"))
    ].iloc[0]
    eta100_small = summary[(summary["N_eff"].eq(5.0e4)) & (summary["eta_scenario"].eq("eta100"))].iloc[0]
    eta100_base = summary[(summary["N_eff"].sub(xcc.P.N).abs() < 1.0e-6) & (summary["eta_scenario"].eq("eta100"))].iloc[0]

    tex = rf"""\documentclass[UTF8]{{ctexart}}
\usepackage{{amsmath,amssymb,booktabs,graphicx,geometry}}
\geometry{{a4paper,margin=2.4cm}}
\graphicspath{{{{figures/}}}}
\title{{有效人口规模 $N_{{\rm eff}}$ 下的单阈值控制敏感性实验}}
\author{{}}
\date{{\today}}

\begin{{document}}
\maketitle

\section{{问题和模型口径}}
原始西安实验取 $N=13,163,000$。这个口径对应全市人口下的均匀混合近似。
若传播主要发生在有限接触网络中，可以把 SIQR 方程中的归一化尺度解释为有效混合人口
$N_{{\rm eff}}$。本实验不改变控制律结构，只考察 $N_{{\rm eff}}$ 改变后，
阈值控制的启动时间和平台期长度如何变化。

感染项写为
\[
\frac{{\beta c(t)(1-q(t))S(t)I(t)}}{{N_{{\rm eff}}}}.
\]
对每个 $N_{{\rm eff}}$，固定 $\beta,\gamma,\delta_q,c(t),q(t)$，只重新拟合初始种子
$I_0$，并令 $S_0=N_{{\rm eff}}-I_0$、$R(0)=0$。这个设定是条件性敏感性分析，
不是重新估计全部传播参数。

\section{{实验设计}}
扫描
\[
N_{{\rm eff}}\in\{{5\times10^4,10^5,3\times10^5,10^6,3\times10^6,13,163,000\}}.
\]
阈值采用三种口径：
\[
\eta=100,\qquad \eta=520,\qquad \eta=0.002N_{{\rm eff}}.
\]
其中 $\eta=0.002N_{{\rm eff}}$ 用于观察同比例缩放；$\eta=100,520$ 用于观察固定绝对阈值时
$\eta/N_{{\rm eff}}$ 随 $N_{{\rm eff}}$ 下降而增大的影响。

为检查平台期内隔离率曲线的形状，另做两组局部扫描：固定
$N_{{\rm eff}}=50,000$，取 $\eta\in\{{80,100,150\}}$；固定 $\eta=100$，取
$N_{{\rm eff}}\in\{{40,000,50,000,60,000\}}$。每个 $N_{{\rm eff}}$ 均重新拟合 $I_0$。

\section{{无量纲标度结构}}
令
\[
s=\frac{{S}}{{N_{{\rm eff}}}},\qquad
i=\frac{{I}}{{N_{{\rm eff}}}},\qquad
\rho=\frac{{\eta}}{{N_{{\rm eff}}}}.
\]
则社区易感者和社区感染者方程可写成
\[
\dot s=-c(t)\bigl[\beta+q(t)(1-\beta)\bigr]si,
\qquad
\dot i=\beta c(t)(1-q(t))si-\gamma i.
\]
方程中不再显含 $N_{{\rm eff}}$。因此，若传播参数、控制函数、无量纲初值
$(s_0,i_0)$ 和阈值比例 $\rho$ 同时固定，则无量纲状态轨迹唯一确定。此时
\[
R_0=\frac{{\beta c_0(1-q_0)}}{{\gamma}},
\qquad
\Delta t
=\frac{{1}}{{c_0\rho}}
\log\frac{{s^*-\bar s}}{{s_c-\bar s}},
\qquad
q_c(t)=1-\frac{{\gamma}}{{\beta c_0s_{{\rm th}}(t)}}
\]
均不显含 $N_{{\rm eff}}$。若终止时刻也由固定无量纲条件给出，则累计感染满足
$I_{{t_{{\rm cum}}}}=N_{{\rm eff}}h(\rho)$。这里的结论不使用 $s\approx1$；
它约束的是无量纲动力学和强度量，不表示绝对病例数与 $N_{{\rm eff}}$ 无关。

\subsection{{固定无量纲初值的精确结构实验}}
为检验上述条件，取 $N_{{\rm eff}}=50,000$ 的拟合结果作为参考，固定
$i_0=I_0/50,000$，再令 $I_0=i_0N_{{\rm eff}}$、$\rho=0.002$。
表中 $T_{{\rm clear}}^{{(1)}}$ 使用绝对判据 $I\leq1$，
$T_{{\rm clear}}^{{(\varepsilon)}}$ 使用固定分数判据
$i\leq\varepsilon$，其中 $\varepsilon=10^{{-7}}$。

\noindent\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{rrrrrrr}}
\toprule
$N_{{\rm eff}}$ & $t_1$ & $\Delta t$ & $T_{{\rm clear}}^{{(1)}}$ &
$T_{{\rm clear}}^{{(\varepsilon)}}$ & $I_{{t_2,\rm cum}}/N_{{\rm eff}}$ & $J$ \\
\midrule
{exact_scaling_rows}
\bottomrule
\end{{tabular}}
}}

六个 $N_{{\rm eff}}$ 下，$t_1$、$\Delta t$、$t_2$、$J$、平台结束时累计感染分数和
$T_{{\rm clear}}^{{(\varepsilon)}}$ 均通过预设数值容差。
公共时间区间内，$i(t)$ 的最大折叠误差为
${max_i_collapse_error:.2e}$，$q(t)$ 的最大折叠误差为 ${max_q_collapse_error:.2e}$。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.82\linewidth]{{dimensionless_scaling_collapse.pdf}}
\caption{{固定 $(s_0,i_0)$ 和 $\rho=0.002$ 时的无量纲感染轨迹与隔离率轨迹折叠。
白心圆表示各 $N_{{\rm eff}}$ 下绝对判据 $I=1$ 对应的不同终点。}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.72\linewidth]{{clearance_tail_decomposition.pdf}}
\caption{{固定 $(s_0,i_0,\rho)$ 时的清零尾段。绝对判据 $I\leq1$ 等价于
$i\leq1/N_{{\rm eff}}$，因而随 $N_{{\rm eff}}$ 移动；固定分数判据给出相同尾段时长。}}
\end{{figure}}

\subsection{{逐个 $N_{{\rm eff}}$ 重拟合绝对初值的实验}}
现有数据校准对每个 $N_{{\rm eff}}$ 单独拟合绝对 $I_0$，因此
$i_0=I_0/N_{{\rm eff}}$ 随 $N_{{\rm eff}}$ 改变，严格标度命题的初值条件不再满足。
这解释了同比例阈值组中 $\Delta t$ 近似不变，而 $t_1$ 从约 $11.13$ 天增至 $16.90$ 天。

\noindent\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{rrrrrrr}}
\toprule
$N_{{\rm eff}}$ & $\hat I_0/N_{{\rm eff}}$ & 拟合 RMSE & $t_1$ & $\Delta t$ &
$I_{{t_{{\rm cum}}}}/N_{{\rm eff}}$ & $T_{{\rm clear}}$ \\
\midrule
{refit_scaling_rows}
\bottomrule
\end{{tabular}}
}}

表中拟合 RMSE 处于相近量级，但这只说明在固定
$\beta,\gamma,\delta_q,c_{{\rm TDINN}}(t),q_{{\rm TDINN}}(t)$ 并重拟合 $I_0$ 的条件下，
当前日报拟合没有明显退化；它不构成 $N_{{\rm eff}}$ 的识别结果。

\subsection{{阈值比例扫描}}
上一组固定 $\rho=0.002$ 只改变 $N_{{\rm eff}}$，说明这些指标不随 $N_{{\rm eff}}$ 变。
但要说明它们\emph{{只}}通过 $\rho=\eta/N_{{\rm eff}}$ 进入，还需要说明它们确实随 $\rho$
变化。为此固定同一组无量纲初值，在
\[
\rho\in\{{5\times10^{{-4}},10^{{-3}},2\times10^{{-3}},4\times10^{{-3}},8\times10^{{-3}}\}}
\]
上重复实验，并在 $N_{{\rm eff}}=50,000$ 和 $N_{{\rm eff}}=13,163,000$
（相差约 $263$ 倍）两个尺度上各算一遍。

\noindent\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{rrrrrrrrr}}
\toprule
$\rho$ & $N_{{\rm eff}}$ & $\eta$ & $t_1$ & $\Delta t$ & $c_0\rho\Delta t$ &
$I_{{t_2,\rm cum}}/N_{{\rm eff}}$ & $T_{{\rm clear}}^{{(\varepsilon)}}$ &
$T_{{\rm clear}}^{{(1)}}$ \\
\midrule
{rho_sweep_rows}
\bottomrule
\end{{tabular}}
}}

同一 $\rho$ 下，两个 $N_{{\rm eff}}$ 的 $t_1$、$\Delta t$、$q_{{\max}}$、
$I_{{t_2,\rm cum}}/N_{{\rm eff}}$ 和 $T_{{\rm clear}}^{{(\varepsilon)}}$ 的最大差异为
${rho_cross_n_spread:.2e}$；而沿 $\rho$ 方向 $\Delta t$ 从
${rho_dt_max:.2f}$ 天降到 ${rho_dt_min:.2f}$ 天。对数因子
$c_0\rho\Delta t=\log[(s^*-\bar s)/(s_c-\bar s)]$ 在整个扫描区间只从
${log_factor_max:.4f}$ 变到 ${log_factor_min:.4f}$，因此
$\Delta t\approx\text{{const}}/(c_0\rho)$ 是好的近似。与此对照，绝对判据
$T_{{\rm clear}}^{{(1)}}$ 在同一 $\rho$ 下仍随 $N_{{\rm eff}}$ 改变，
这与上一节关于清零地板的结论一致。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\linewidth]{{dimensionless_rho_dependence.pdf}}
\caption{{组二：$\Delta t$ 和 $I_{{t_2,\rm cum}}/N_{{\rm eff}}=h(\rho)$ 随 $\rho$ 变化，
且两个相差约 $263$ 倍的 $N_{{\rm eff}}$ 给出重合的曲线。}}
\end{{figure}}

\clearpage
\section{{平台期控制律及其凹凸拐点}}
记 $\tau=t-t_1$。平台期内 $I(t)=\eta$，理论易感者轨迹和隔离率控制为
\[
S_{{\rm th}}(t)=\bar S+(S^*-\bar S)e^{{-k\tau}},\qquad
q_c(t)=1-\frac{{\gamma N_{{\rm eff}}}}{{\beta c_0S_{{\rm th}}(t)}},
\]
其中
\[
k=\frac{{c_0\eta}}{{N_{{\rm eff}}}},\qquad
\bar S=\frac{{\gamma N_{{\rm eff}}(1-\beta)}}{{\beta c_0}}.
\]
对 $q_c(t)$ 求二阶导数得到
\[
q_c''(t)
=
\frac{{\gamma c_0\eta^2}}{{\beta N_{{\rm eff}}}}
\frac{{\bigl(S_{{\rm th}}(t)-\bar S\bigr)
\bigl(2\bar S-S_{{\rm th}}(t)\bigr)}}{{S_{{\rm th}}(t)^3}}.
\]
由于控制期内 $S_{{\rm th}}(t)>\bar S$，二阶导数的符号由
$2\bar S-S_{{\rm th}}(t)$ 决定。因此，若
\[
S_c<2\bar S<S^*,
\]
则控制期内存在唯一凹凸拐点 $\bar t$，且
\[
\bar t
=t_1+\frac{{N_{{\rm eff}}}}{{c_0\eta}}
\log\frac{{S^*-\bar S}}{{\bar S}}.
\]
拐点处 $S_{{\rm th}}(\bar t)=2\bar S$，从而
\[
q_c(\bar t)
=1-\frac{{1}}{{2(1-\beta)}}
\approx {0.5 * (q_inflection_min + q_inflection_max):.4f}.
\]
在固定 $\beta$ 的条件下，这个纵坐标不依赖 $N_{{\rm eff}}$ 和 $\eta$。这里的
$\bar t$ 只描述 $q_c(t)$ 的曲率变化，不是新的控制启动时刻或解除时刻。

记 $q^\star=1-1/(2(1-\beta))$。存在条件的左端不等式可以等价改写为
\[
S_c<2\bar S
\iff
(1-\beta)(1-q_0)>\frac{{1}}{{2}}
\iff
q_0<q^\star,
\]
因为 $S_c=\gamma N_{{\rm eff}}/[\beta c_0(1-q_0)]$、
$2\bar S=2\gamma N_{{\rm eff}}(1-\beta)/(\beta c_0)$。也就是说，拐点存在的条件
恰好是常规隔离率低于拐点高度本身：$\beta$ 和 $q_0$ 都不能太大。西安参数下
$q_0={xcc.P.q0:g}<q^\star\approx{q_star_baseline:.4f}$，条件成立；等价地，给定
$q_0$ 时要求 $\beta<1-1/(2(1-q_0))\approx{beta_limit:.4f}$。右端不等式
$2\bar S<S^*$ 在当前参数下不起约束作用（$2\bar S/N_{{\rm eff}}\approx
{two_sbar_fraction:.3f}$，而 $S^*/N_{{\rm eff}}\approx{s_star_fraction:.3f}$）。

反过来，若从隔离率曲线读取凹凸拐点高度 $q^\star$，则可形式上反演
\[
\widehat\beta
=1-\frac{{1}}{{2(1-q^\star)}}.
\]
为避免用解析条件自我验证，数值实验在每条控制曲线上均匀取 $20,001$ 个点，
通过二阶差分的负到正变号独立定位拐点，再计算 $q^\star$ 和 $\widehat\beta$。

\noindent\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{lrrrrrr}}
\toprule
扫描 & $N_{{\rm eff}}$ & $\eta$ & $\bar t_{{\rm analytic}}$ &
$\bar t_{{\rm numeric}}$ & $q^\star_{{\rm numeric}}$ & $\widehat\beta$ \\
\midrule
{inverse_rows}
\bottomrule
\end{{tabular}}
}}

六个校验点中，数值拐点高度相对理论值的最大绝对误差为
${max_q_numeric_error:.2e}$，反演 $\beta$ 的最大绝对误差为
${max_beta_recovery_error:.2e}$。该反演目前只是给定解析控制律下的一致性检查；
若应用于实际估计，还需要处理观测噪声、控制函数平滑和二阶导数的不稳定性。

\subsection{{拐点高度对 $\beta$ 的依赖}}
上表固定 $\beta={xcc.P.beta:g}$，只说明拐点高度不随 $\eta$ 和 $N_{{\rm eff}}$ 改变。
要验证它确实按 $q^\star=1-1/(2(1-\beta))$ 随 $\beta$ 变化，固定
$N_{{\rm eff}}=50,000$、$\eta=100$、$c_0$ 和 $q_0$，只改变 $\beta$ 并重复同样的
二阶差分定位。

\begin{{center}}
\small
\begin{{tabular}}{{rrrrr}}
\toprule
$\beta$ & $q^\star_{{\rm theory}}$ & $q^\star_{{\rm numeric}}$ &
误差 & $\widehat\beta$ \\
\midrule
{beta_sweep_rows}
\bottomrule
\end{{tabular}}
\end{{center}}

数值拐点高度与理论曲线的最大绝对误差为 ${max_beta_sweep_error:.2e}$，
且 $\widehat\beta$ 逐行还原出输入的 $\beta$。改变 $\beta$ 会破坏 He--Tang--Xiao
参数与 TDINN 控制函数的标定，因此这组扫描是结构性实验，只验证控制律的恒等式，
不是 $\beta$ 的替代估计。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.80\linewidth]{{inflection_height_beta_invariance.pdf}}
\caption{{拐点高度只由 $\beta$ 决定。理论曲线 $q^\star=1-1/(2(1-\beta))$ 与二阶差分
数值拐点吻合；曲线与 $q_0$ 的交点给出存在边界
$\beta_{{\max}}\approx{beta_limit:.4f}$，其右侧控制期内不再存在拐点。}}
\end{{figure}}

\subsection{{存在边界}}
固定 $\beta={xcc.P.beta:g}$（此时 $q^\star\approx{q_star_baseline:.4f}$），令 $q_0$
逐步逼近 $q^\star$。由于 $\bar S$ 和 $k=c_0\eta/N_{{\rm eff}}$ 都不含 $q_0$、
$S^*$ 对 $q_0$ 的依赖也很弱，平台期控制曲线 $q_c(\tau)$ 几乎不随 $q_0$ 移动；
改变 $q_0$ 主要改变平台何时解除，即曲线在何处被截断，而截断点的高度恰好是 $q_0$。
因此当 $q_0\uparrow q^\star$ 时，是平台解除时刻 $t_2$ 向固定的拐点 $\bar t$ 靠拢，
最终把拐点挤出控制区间。

\begin{{center}}
\small
\begin{{tabular}}{{rrcrrr}}
\toprule
$q_0$ & $(1-\beta)(1-q_0)$ & 存在拐点 & $\bar\tau=\bar t-t_1$ & $\Delta t$ &
$t_2-\bar t$ \\
\midrule
{boundary_rows}
\bottomrule
\end{{tabular}}
\end{{center}}

表中 $\bar\tau$ 几乎不动，而 $\Delta t$ 随 $q_0$ 下降并与之合拢：
$q_0={closest_q0:.4f}$ 时 $t_2-\bar t$ 已降到 ${closest_gap:.4f}$ 天。当
$q_0={absent_q0:.4f}$ 时 $(1-\beta)(1-q_0)={absent_product:.4f}<1/2$，
控制期内不再存在拐点，与判据 $q_0<q^\star$ 一致。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.80\linewidth]{{inflection_boundary_scan.pdf}}
\caption{{存在边界。$q_c(\tau)$ 几乎不随 $q_0$ 移动，方块表示平台解除点
$(\Delta t,q_0)$，白心圆表示固定的拐点 $(\bar\tau,q^\star)$；
$q_0\uparrow q^\star$ 时方块沿同一条曲线滑到圆上。}}
\end{{figure}}

\clearpage
\section{{数值结果}}
表中 $\Delta t=t_2-t_1$ 表示平台控制时长，主成本 $J$ 使用 $w_c=1,w_q=2$。

{table_tex}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\linewidth]{{effective_population_time_metrics.pdf}}
\caption{{不同 $N_{{\rm eff}}$ 下的 $t_1$、$\Delta t$ 和 $T_{{\rm clear}}$。}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\linewidth]{{effective_population_cost_metrics.pdf}}
\caption{{不同 $N_{{\rm eff}}$ 下的累计感染和控制成本指标。}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.68\linewidth]{{effective_population_eta_fraction.pdf}}
\caption{{三类阈值口径对应的 $\eta/N_{{\rm eff}}$。}}
\end{{figure}}

\clearpage
\subsection{{固定 $N_{{\rm eff}}=50,000$ 改变阈值}}
\begin{{center}}
\small
\begin{{tabular}}{{rrrrrr}}
\toprule
$\eta$ & $\eta/N_{{\rm eff}}$ & $t_1$ & $\bar t$ & $\Delta t$ & $T_{{\rm clear}}$ \\
\midrule
{eta_inflection_rows}
\bottomrule
\end{{tabular}}
\end{{center}}

数值结果中，$\eta$ 从 $80$ 增至 $150$ 时，$\bar t$ 由约
${float(eta_inflection.loc[eta_inflection['eta'].idxmin(), 't_inflection']):.2f}$ 天提前到
${float(eta_inflection.loc[eta_inflection['eta'].idxmax(), 't_inflection']):.2f}$ 天，平台控制时长和清零时间也随之缩短。
该变化主要来自 $N_{{\rm eff}}/(c_0\eta)$，但对数项仍通过 $S^*$ 依赖阈值。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.78\linewidth]{{representative_panels/eta_80_100_150_inflection_Neff50000.pdf}}
\caption{{固定 $N_{{\rm eff}}=50,000$ 时，不同阈值下的 $I(t)$、$q(t)$ 与隔离率曲线拐点。}}
\end{{figure}}

\clearpage
\subsection{{固定 $\eta=100$ 改变有效人口规模}}
\begin{{center}}
\small
\begin{{tabular}}{{rrrrrr}}
\toprule
$N_{{\rm eff}}$ & $\eta/N_{{\rm eff}}$ & $t_1$ & $\bar t$ & $\Delta t$ & $T_{{\rm clear}}$ \\
\midrule
{neff_inflection_rows}
\bottomrule
\end{{tabular}}
\end{{center}}

固定 $\eta=100$ 时，$N_{{\rm eff}}$ 从 $40,000$ 增至 $60,000$，$\bar t$ 由约
${float(neff_inflection.loc[neff_inflection['N_eff'].idxmin(), 't_inflection']):.2f}$ 天推迟到
${float(neff_inflection.loc[neff_inflection['N_eff'].idxmax(), 't_inflection']):.2f}$ 天。
与此同时，$\eta/N_{{\rm eff}}$ 下降，平台控制时长由约
${float(neff_inflection.loc[neff_inflection['N_eff'].idxmin(), 'control_duration']):.2f}$ 天增至
${float(neff_inflection.loc[neff_inflection['N_eff'].idxmax(), 'control_duration']):.2f}$ 天。

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.78\linewidth]{{representative_panels/Neff_40000_50000_60000_inflection_eta100.pdf}}
\caption{{固定 $\eta=100$ 时，不同 $N_{{\rm eff}}$ 下的 $I(t)$、$q(t)$ 与隔离率曲线拐点。}}
\end{{figure}}

\clearpage
\section{{初步观察}}
在当前固定传播参数的设定下，$N_{{\rm eff}}=13,163,000$ 且
$\eta=0.002N_{{\rm eff}}$ 时，计算得到
\[
t_1\approx {float(base_row['t1']):.2f},\qquad
\Delta t\approx {float(base_row['control_duration']):.2f},\qquad
T_{{\rm clear}}\approx {float(base_row['clear_time']):.2f}.
\]
这与原西安主基准属于同一数量级。

当固定绝对阈值 $\eta=100$ 时，若从 $N_{{\rm eff}}=13,163,000$ 降到
$N_{{\rm eff}}=50,000$，$\eta/N_{{\rm eff}}$ 增大，平台期由
\[
\Delta t\approx {float(eta100_base['control_duration']):.2f}
\]
变为
\[
\Delta t\approx {float(eta100_small['control_duration']):.2f}.
\]
这一变化对应的是阈值相对有效人口比例的改变，而不是阈值控制律本身的改变。

令 $s=S/N_{{\rm eff}}$、$\rho=\eta/N_{{\rm eff}}$，平台控制时长可写成
\[
\Delta t
=\frac{{1}}{{c_0\rho}}
\log\frac{{s^*-\bar s}}{{s_c-\bar s}}.
\]
因此，在逐个 $N_{{\rm eff}}$ 重拟合绝对 $I_0$ 的口径下，当归一化启动点
$s^*$ 变化较小时，$\rho$ 是平台时长的主导尺度。
这解释了同比例阈值 $\rho=0.002$ 下 $\Delta t$ 基本保持在 $85$ 天量级，
也解释了固定绝对阈值下 $N_{{\rm eff}}$ 增大时平台期近似按比例延长。
不过 $s^*$ 仍通过重新拟合的初值和阈值到达条件变化，因此该缩放关系不是无条件恒等式。

\section{{限制}}
本实验固定 $\beta,\gamma,\delta_q,c(t),q(t)$，只重新拟合 $I_0$。因此结果只能解释为：
在给定传播参数和控制函数下，$N_{{\rm eff}}$ 作为有效混合人口尺度如何影响阈值控制指标。
若要把某个 $N_{{\rm eff}}$ 解释为真实传播网络规模，还需要空间活动、接触网络或分区病例数据支持，
并可能需要重新估计 $\beta$ 或控制函数。
固定 $(s_0,i_0,\rho)$ 的结构实验用于验证方程标度，不是对每个 $N_{{\rm eff}}$ 的数据拟合；
固定分数清零阈值 $10^{{-7}}$ 也只是用于分离终止判据效应的数值参照，不能替代动态清零定义。
此外，$\bar t$ 是给定解析控制律下的曲率标记，不对应目标泛函的最优切换条件，
也不能据此单独判断控制强度是否现实可行。

\end{{document}}
"""
    (OUT_DIR / "effective_population_sensitivity_note.tex").write_text(tex, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False, "mathtext.fontset": "dejavusans"})
    observed = xcc.load_observed_data()
    summary, fit_summary = build_summary(observed)
    safe_to_csv(summary, OUT_DIR / "effective_population_summary.csv")
    safe_to_csv(fit_summary, OUT_DIR / "effective_population_fit_summary.csv")
    plot_time_metrics(summary)
    plot_cost_metrics(summary)
    plot_eta_fraction(summary)
    write_latex_table(summary)
    run_dimensionless_scaling_analysis()
    run_inflection_analyses()
    run_inflection_invariance_analysis()
    write_inflection_inverse_summary()
    write_note(summary)
    print("Generated effective population sensitivity outputs in:")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
