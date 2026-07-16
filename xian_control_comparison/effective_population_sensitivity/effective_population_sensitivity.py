"""有效人口规模 N_eff 对情景一阈值控制的敏感性分析。

本脚本只生成探索性数值输出和 LaTeX 笔记。实验固定
He--Tang--Xiao 参数与 TDINN 控制函数，对每个 N_eff 重新拟合 I0，
再比较 eta=100、eta=520 和 eta=0.002 N_eff 三类阈值口径。
"""

from __future__ import annotations

import sys
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
    return row


def build_summary(observed: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fit_rows: List[Dict[str, float | str]] = []
    rows: List[Dict[str, float | str]] = []
    for N_eff in N_EFF_VALUES:
        params = tla.LandscapeParams(N=float(N_eff))
        fit = fit_initial_condition_for_N(observed, params)
        fit_rows.append(
            {
                "N_eff": params.N,
                "I0_fit": fit.I0,
                "I0_fraction": fit.I0 / params.N,
                "S0_fit": fit.S0,
                "fit_objective": fit.objective,
                "fit_raw_rmse": fit.raw_rmse,
                "residual_type": fit.residual_type,
            }
        )
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
                    latex_float(float(row["N_eff"]), 0),
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
            r"\begin{tabular}{cccccccc}",
            r"\toprule",
            r"$N_{\rm eff}$ & 阈值口径 & $\eta$ & $\hat I_0$ & $t_1$ & $\Delta t$ & $T_{\rm clear}$ & $J$ \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "effective_population_summary_table.tex").write_text(content, encoding="utf-8")


def write_note(summary: pd.DataFrame) -> None:
    table_tex = (OUT_DIR / "effective_population_summary_table.tex").read_text(encoding="utf-8")
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

\section{{限制}}
本实验固定 $\beta,\gamma,\delta_q,c(t),q(t)$，只重新拟合 $I_0$。因此结果只能解释为：
在给定传播参数和控制函数下，$N_{{\rm eff}}$ 作为有效混合人口尺度如何影响阈值控制指标。
若要把某个 $N_{{\rm eff}}$ 解释为真实传播网络规模，还需要空间活动、接触网络或分区病例数据支持，
并可能需要重新估计 $\beta$ 或控制函数。

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
    write_note(summary)
    print("Generated effective population sensitivity outputs in:")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
