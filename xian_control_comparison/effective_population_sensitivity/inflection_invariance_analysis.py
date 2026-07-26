"""验证情景一平台期隔离率拐点高度的参数不变性及其存在边界。

本脚本包含两组结构性实验：

1. ``beta`` 扫描：固定 ``N_eff``、``eta``、``c0``、``q0``，只改变 ``beta``，
   用二阶差分独立定位 ``q_c(t)`` 的凹凸拐点，检验拐点高度是否等于
   ``1-1/(2(1-beta))``；
2. ``q0`` 边界扫描：固定 ``beta``，令 ``q0`` 逼近存在边界
   ``(1-beta)(1-q0)=1/2``，观察拐点时刻 ``t_bar`` 并入平台解除时刻 ``t2``
   并最终消失。

两组实验都固定无量纲初值 ``(s0,i0)``，不重新拟合日报数据。改变 ``beta``
或 ``q0`` 会破坏 He--Tang--Xiao 参数与 TDINN 控制函数的标定，因此这里只
验证控制律的结构恒等式，不能解释为参数估计。
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
for path in [str(PARENT), str(THRESHOLD_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import xian_control_comparison as xcc  # noqa: E402
import threshold_landscape_analysis as tla  # noqa: E402


FIG_DIR = HERE / "figures"
REFERENCE_N = 5.0e4
N_EFF = 5.0e4
ETA = 100.0
NUMERIC_SAMPLES = 20001
NUMERIC_EDGE_MARGIN = 10

BETA_VALUES = [0.06, 0.09, 0.12, 0.1498, 0.18, 0.21, 0.24]
Q0_VALUES = [0.3230, 0.3600, 0.3900, 0.4050, 0.4100, 0.4115, 0.4118, 0.4200]

BETA_SWEEP_NAME = "inflection_beta_sweep.csv"
BOUNDARY_SCAN_NAME = "inflection_boundary_scan.csv"
BETA_FIG_STEM = "inflection_height_beta_invariance"
BOUNDARY_FIG_STEM = "inflection_boundary_scan"

HEIGHT_TOLERANCE = 1.0e-6


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


def reference_i0_fraction() -> float:
    """取 N_eff=50,000 的拟合结果作为固定无量纲初值。"""

    fit_summary = pd.read_csv(HERE / "effective_population_fit_summary.csv")
    reference = fit_summary[np.isclose(fit_summary["N_eff"], REFERENCE_N)].iloc[0]
    return float(reference["I0_fit"]) / REFERENCE_N


def theory_height(beta: float) -> float:
    """拐点高度的解析值 q^star=1-1/(2(1-beta))。"""

    return float(1.0 - 1.0 / (2.0 * (1.0 - beta)))


def boundary_beta(q0: float) -> float:
    """给定 q0 时，拐点存在要求 beta 小于该临界值。"""

    return float(1.0 - 1.0 / (2.0 * (1.0 - q0)))


def solve_case(
    params: tla.LandscapeParams,
    eta: float,
    i0_fraction: float,
) -> Tuple[Dict[str, float | str], float]:
    """在固定无量纲初值下求阈值控制的理论量和启动时刻 t1。"""

    fit = xcc.InitialFit(
        S0=params.N * (1.0 - i0_fraction),
        I0=params.N * i0_fraction,
        R0_initial=0.0,
        objective=np.nan,
        raw_rmse=np.nan,
        residual_type="fixed_dimensionless_initial_state",
    )
    details = tla.compute_threshold_details(fit, eta, params)
    if str(details["status"]) == "threshold_not_reached":
        return details, float("nan")
    routine = tla.solve_time_control_param(
        "常规控制", fit, params, tla.c_const(params), tla.q_const(params)
    )
    return details, tla.first_crossing_time(routine, eta)


def plateau_control(
    params: tla.LandscapeParams,
    eta: float,
    details: Dict[str, float | str],
    t1: float,
    t_grid: np.ndarray,
) -> np.ndarray:
    """平台期理论隔离率 q_c(t)。"""

    s_star = float(details["S_star"])
    s_bar = float(details["Sbar"])
    k = params.c0 * eta / params.N
    s_grid = s_bar + (s_star - s_bar) * np.exp(-k * (t_grid - t1))
    return 1.0 - params.gamma * params.N / (params.beta * params.c0 * s_grid)


def locate_inflection_numerically(
    params: tla.LandscapeParams,
    eta: float,
    details: Dict[str, float | str],
    t1: float,
    t2: float,
) -> Tuple[float, float]:
    """对均匀采样的 q_c(t) 做二阶差分，独立定位负到正变号点。

    不使用解析条件 S=2*Sbar，避免用待验证的结论自我验证。若变号点落在
    采样边缘（拐点非常贴近 t2 时会出现），返回 NaN 而不是抛出异常。
    """

    t_grid = np.linspace(t1, t2, NUMERIC_SAMPLES)
    q_grid = plateau_control(params, eta, details, t1, t_grid)
    q_first = np.gradient(q_grid, t_grid, edge_order=2)
    q_second = np.gradient(q_first, t_grid, edge_order=2)
    interior = np.arange(NUMERIC_EDGE_MARGIN, len(t_grid) - NUMERIC_EDGE_MARGIN - 1)
    sign_change = interior[
        (q_second[interior] < 0.0) & (q_second[interior + 1] >= 0.0)
    ]
    if len(sign_change) != 1:
        return float("nan"), float("nan")
    index = int(sign_change[0])
    y_left = float(q_second[index])
    y_right = float(q_second[index + 1])
    zero_fraction = -y_left / (y_right - y_left)
    t_numeric = float(
        t_grid[index] + zero_fraction * (t_grid[index + 1] - t_grid[index])
    )
    return t_numeric, float(np.interp(t_numeric, t_grid, q_grid))


def inflection_row(
    params: tla.LandscapeParams,
    eta: float,
    details: Dict[str, float | str],
    t1: float,
) -> Dict[str, float | bool | str]:
    """汇总单个参数点的拐点解析量与数值定位结果。"""

    s_star = float(details["S_star"])
    s_c = float(details["Sc"])
    s_bar = float(details["Sbar"])
    control_duration = float(details["control_duration"])
    t2 = t1 + control_duration
    exists = bool(s_c < 2.0 * s_bar < s_star)
    q_theory = theory_height(params.beta)

    row: Dict[str, float | bool | str] = {
        "beta": params.beta,
        "q0": params.q0,
        "N_eff": params.N,
        "eta": eta,
        "eta_fraction": eta / params.N,
        "existence_product": (1.0 - params.beta) * (1.0 - params.q0),
        "Sc": s_c,
        "two_Sbar": 2.0 * s_bar,
        "S_star": s_star,
        "inflection_exists": exists,
        "t1": t1,
        "t2": t2,
        "control_duration": control_duration,
        "q_inflection_theory": q_theory,
        "status": str(details["status"]),
    }

    if not exists:
        row.update(
            {
                "t_inflection": float("nan"),
                "tau_inflection": float("nan"),
                "t2_minus_t_inflection": float("nan"),
                "t_inflection_numeric": float("nan"),
                "q_inflection_analytic": float("nan"),
                "q_inflection_numeric": float("nan"),
                "q_inflection_numeric_error": float("nan"),
                "beta_recovered_numeric": float("nan"),
                "beta_recovery_error": float("nan"),
            }
        )
        return row

    k = params.c0 * eta / params.N
    tau_inflection = float(np.log((s_star - s_bar) / s_bar) / k)
    t_inflection = t1 + tau_inflection
    s_at_inflection = s_bar + (s_star - s_bar) * np.exp(-k * tau_inflection)
    q_analytic = float(
        1.0 - params.gamma * params.N / (params.beta * params.c0 * s_at_inflection)
    )
    t_numeric, q_numeric = locate_inflection_numerically(params, eta, details, t1, t2)
    beta_recovered = (
        float(1.0 - 1.0 / (2.0 * (1.0 - q_numeric)))
        if np.isfinite(q_numeric)
        else float("nan")
    )

    row.update(
        {
            "t_inflection": t_inflection,
            "tau_inflection": tau_inflection,
            "t2_minus_t_inflection": t2 - t_inflection,
            "t_inflection_numeric": t_numeric,
            "q_inflection_analytic": q_analytic,
            "q_inflection_numeric": q_numeric,
            "q_inflection_numeric_error": q_numeric - q_theory,
            "beta_recovered_numeric": beta_recovered,
            "beta_recovery_error": beta_recovered - params.beta,
        }
    )
    return row


def sweep_beta(i0_fraction: float) -> pd.DataFrame:
    """固定 N_eff、eta、q0，扫描 beta 检验拐点高度只依赖 beta。"""

    rows: List[Dict[str, float | bool | str]] = []
    for beta in BETA_VALUES:
        params = tla.LandscapeParams(N=N_EFF, beta=float(beta))
        details, t1 = solve_case(params, ETA, i0_fraction)
        if not np.isfinite(t1):
            raise RuntimeError(f"beta={beta:g}: 常规控制未达到 eta={ETA:g}。")
        rows.append(inflection_row(params, ETA, details, t1))

    frame = pd.DataFrame(rows).sort_values("beta").reset_index(drop=True)
    if not bool(frame["inflection_exists"].all()):
        missing = frame.loc[~frame["inflection_exists"], "beta"].tolist()
        raise RuntimeError(f"beta 扫描中以下取值不存在拐点：{missing}。")
    height_error = float(frame["q_inflection_numeric_error"].abs().max())
    if not np.isfinite(height_error) or height_error > HEIGHT_TOLERANCE:
        raise RuntimeError(f"beta 扫描的拐点高度误差 {height_error:.3e} 超过容差。")
    return frame


def sweep_q0_boundary(i0_fraction: float) -> pd.DataFrame:
    """固定 beta，令 q0 逼近并越过存在边界 (1-beta)(1-q0)=1/2。"""

    rows: List[Dict[str, float | bool | str]] = []
    for q0 in Q0_VALUES:
        params = tla.LandscapeParams(N=N_EFF, q0=float(q0))
        details, t1 = solve_case(params, ETA, i0_fraction)
        if not np.isfinite(t1):
            raise RuntimeError(f"q0={q0:g}: 常规控制未达到 eta={ETA:g}。")
        rows.append(inflection_row(params, ETA, details, t1))

    frame = pd.DataFrame(rows).sort_values("q0").reset_index(drop=True)
    expected = frame["q0"] < frame["q_inflection_theory"]
    if not bool((frame["inflection_exists"] == expected).all()):
        raise RuntimeError("拐点存在性与判据 q0 < q^star 不一致。")
    if not bool(frame["inflection_exists"].any()):
        raise RuntimeError("q0 扫描中没有任何存在拐点的取值。")
    if not bool((~frame["inflection_exists"]).any()):
        raise RuntimeError("q0 扫描没有覆盖到拐点消失的一侧。")

    resolved = frame[frame["q_inflection_numeric"].notna()]
    height_error = float(resolved["q_inflection_numeric_error"].abs().max())
    if not np.isfinite(height_error) or height_error > HEIGHT_TOLERANCE:
        raise RuntimeError(f"q0 扫描的拐点高度误差 {height_error:.3e} 超过容差。")
    return frame


def plot_beta_invariance(frame: pd.DataFrame) -> None:
    """拐点高度对 beta 的理论曲线与数值散点，并标出存在边界。"""

    q0 = float(frame["q0"].iloc[0])
    beta_limit = boundary_beta(q0)
    dense_beta = np.linspace(0.02, 0.30, 500)
    dense_height = 1.0 - 1.0 / (2.0 * (1.0 - dense_beta))

    fig, (ax_curve, ax_error) = plt.subplots(
        2,
        1,
        figsize=(7.0, 6.4),
        sharex=True,
        gridspec_kw={"height_ratios": [1.35, 1.0]},
        constrained_layout=True,
    )

    ax_curve.axvspan(
        beta_limit,
        0.30,
        color="#BBBBBB",
        alpha=0.25,
        lw=0,
        label="no inflection",
    )
    ax_curve.plot(
        dense_beta,
        dense_height,
        color="#222222",
        lw=1.6,
        label=r"theory $q_{\mathrm{inf}}=1-\frac{1}{2(1-\beta)}$",
    )
    ax_curve.axhline(
        q0,
        color="#555555",
        lw=1.0,
        linestyle=":",
        label=rf"$q_0={q0:g}$",
    )
    ax_curve.axvline(beta_limit, color="#888888", lw=1.0, linestyle="--")
    ax_curve.scatter(
        frame["beta"],
        frame["q_inflection_numeric"],
        s=42,
        facecolor="white",
        edgecolor="#D55E00",
        linewidth=1.6,
        zorder=5,
        label="numeric inflection (2nd difference)",
    )
    baseline = frame[np.isclose(frame["beta"], xcc.P.beta)]
    if not baseline.empty:
        ax_curve.scatter(
            baseline["beta"],
            baseline["q_inflection_numeric"],
            s=42,
            color="#0072B2",
            zorder=6,
            label=rf"Xi'an $\beta={xcc.P.beta:g}$",
        )
    ax_curve.annotate(
        rf"$\beta_{{\max}}={beta_limit:.4f}$",
        xy=(beta_limit, q0),
        xytext=(-6, 26),
        textcoords="offset points",
        fontsize=8.2,
        ha="right",
        color="#555555",
    )
    ax_curve.set_ylabel(r"$q_c(2\bar S)$")
    ax_curve.set_ylim(0.26, 0.53)
    ax_curve.set_title(
        r"(a) Inflection height depends on $\beta$ only", loc="left", fontsize=10
    )
    ax_curve.legend(loc="lower left", fontsize=7.8)

    ax_error.semilogy(
        frame["beta"],
        np.abs(frame["q_inflection_numeric_error"]),
        "o-",
        color="#D55E00",
        lw=1.5,
        ms=4.5,
    )
    ax_error.axhline(
        HEIGHT_TOLERANCE,
        color="#555555",
        lw=1.0,
        linestyle="--",
        label=rf"tolerance ${HEIGHT_TOLERANCE:.0e}$",
    )
    ax_error.set_xlabel(r"$\beta$")
    ax_error.set_ylabel(r"$|q_{\mathrm{inf}}^{\rm numeric}-q_{\mathrm{inf}}^{\rm theory}|$")
    ax_error.set_title("(b) Numeric residual", loc="left", fontsize=10)
    ax_error.legend(loc="best", fontsize=8)

    for ax in (ax_curve, ax_error):
        ax.grid(axis="y", color="#D9D9D9", lw=0.6, alpha=0.6)
        ax.tick_params(direction="out", length=3.5, width=0.8)
    ax_curve.set_xlim(0.02, 0.30)

    fig.suptitle(
        rf"Inflection-height invariant at $N_{{\rm eff}}={N_EFF:,.0f}$, $\eta={ETA:g}$",
        fontsize=10.5,
    )
    fig.savefig(FIG_DIR / f"{BETA_FIG_STEM}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{BETA_FIG_STEM}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_boundary_scan(frame: pd.DataFrame, i0_fraction: float) -> None:
    """展示 q0 逼近边界时平台解除时刻如何滑到固定拐点上并使其消失。

    平台期控制律 q_c(tau) 几乎不随 q0 移动，因为 Sbar 和 k=c0*eta/N 都不含
    q0，S_star 对 q0 的依赖也很弱。改变 q0 主要改变平台解除时刻，即曲线在
    何处被截断；截断点的高度恰好是 q0 本身。
    """

    present = frame[frame["inflection_exists"]].sort_values("q0")
    colors = plt.cm.viridis(np.linspace(0.05, 0.85, len(present)))
    q_star = theory_height(xcc.P.beta)

    fig, (ax_q, ax_time) = plt.subplots(
        2,
        1,
        figsize=(7.0, 6.8),
        gridspec_kw={"height_ratios": [1.2, 1.0]},
        constrained_layout=True,
    )
    ax_zoom = ax_q.inset_axes([0.08, 0.14, 0.40, 0.44])

    for color, (_, row) in zip(colors, present.iterrows()):
        params = tla.LandscapeParams(N=N_EFF, q0=float(row["q0"]))
        details, t1 = solve_case(params, ETA, i0_fraction)
        duration = float(row["control_duration"])
        tau_grid = np.linspace(0.0, duration, 2000)
        q_grid = plateau_control(params, ETA, details, t1, t1 + tau_grid)
        for ax in (ax_q, ax_zoom):
            ax.plot(tau_grid, q_grid, color=color, lw=1.5)
            ax.scatter(
                [duration],
                [float(q_grid[-1])],
                s=30,
                color=color,
                marker="s",
                zorder=6,
            )
            ax.scatter(
                [float(row["tau_inflection"])],
                [float(row["q_inflection_analytic"])],
                s=40,
                facecolor="white",
                edgecolor="#222222",
                linewidth=1.2,
                zorder=7,
            )
        ax_q.plot([], [], color=color, lw=1.5, label=rf"$q_0={float(row['q0']):.4f}$")

    for ax in (ax_q, ax_zoom):
        ax.axhline(q_star, color="#222222", lw=1.1, linestyle="--")
    ax_q.plot(
        [],
        [],
        color="#222222",
        lw=1.1,
        linestyle="--",
        label=rf"$q^\star={q_star:.4f}$",
    )
    ax_q.scatter(
        [],
        [],
        s=30,
        color="#555555",
        marker="s",
        label=r"plateau release $(\Delta t,\,q_0)$",
    )
    ax_q.scatter(
        [],
        [],
        s=40,
        facecolor="white",
        edgecolor="#222222",
        linewidth=1.2,
        label=r"inflection $(\bar\tau,\,q^\star)$",
    )

    ax_zoom.set_xlim(72.0, 86.0)
    ax_zoom.set_ylim(0.315, 0.425)
    ax_zoom.tick_params(labelsize=7, direction="out", length=2.5)
    ax_zoom.set_title("zoom", fontsize=7.5, pad=2)
    ax_q.indicate_inset_zoom(ax_zoom, edgecolor="#999999")

    ax_q.set_xlabel(r"Time since control onset $\tau=t-t_1$ (days)")
    ax_q.set_ylabel(r"$q_c(\tau)$")
    ax_q.set_title(
        r"(a) Plateau release slides onto the fixed inflection as $q_0\uparrow q^\star$",
        loc="left",
        fontsize=10,
    )
    ax_q.legend(loc="upper right", fontsize=7.2, ncol=2, columnspacing=1.0)

    product = frame["existence_product"].to_numpy(dtype=float)
    ax_time.plot(
        product,
        frame["control_duration"],
        "s--",
        color="#0072B2",
        lw=1.6,
        ms=5.0,
        label=r"$\Delta t=t_2-t_1$",
    )
    ax_time.plot(
        product,
        frame["tau_inflection"],
        "o-",
        color="#D55E00",
        lw=1.6,
        ms=5.0,
        label=r"$\bar\tau=\bar t-t_1$",
    )
    ax_time.axvline(0.5, color="#222222", lw=1.1, linestyle="--")
    ax_time.axvspan(
        float(np.min(product)) - 0.005,
        0.5,
        color="#BBBBBB",
        alpha=0.25,
        lw=0,
        label="no inflection",
    )
    ax_time.set_xlabel(r"$(1-\beta)(1-q_0)$")
    ax_time.set_ylabel("Days since control onset")
    ax_time.set_title(
        r"(b) $\bar t\to t_2$ as $(1-\beta)(1-q_0)\to\frac{1}{2}^+$",
        loc="left",
        fontsize=10,
    )
    ax_time.set_xlim(float(np.min(product)) - 0.005, float(np.max(product)) + 0.005)
    ax_time.legend(loc="best", fontsize=8)

    for ax in (ax_q, ax_time):
        ax.grid(axis="y", color="#D9D9D9", lw=0.6, alpha=0.6)
        ax.tick_params(direction="out", length=3.5, width=0.8)

    fig.suptitle(
        rf"Existence boundary at $\beta={xcc.P.beta:g}$, "
        rf"$N_{{\rm eff}}={N_EFF:,.0f}$, $\eta={ETA:g}$",
        fontsize=10.5,
    )
    fig.savefig(FIG_DIR / f"{BOUNDARY_FIG_STEM}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{BOUNDARY_FIG_STEM}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_plotting()
    i0_fraction = reference_i0_fraction()

    beta_frame = sweep_beta(i0_fraction)
    boundary_frame = sweep_q0_boundary(i0_fraction)

    beta_frame.to_csv(HERE / BETA_SWEEP_NAME, index=False, encoding="utf-8-sig")
    boundary_frame.to_csv(HERE / BOUNDARY_SCAN_NAME, index=False, encoding="utf-8-sig")
    plot_beta_invariance(beta_frame)
    plot_boundary_scan(boundary_frame, i0_fraction)

    print(f"Generated: {HERE / BETA_SWEEP_NAME}")
    print(f"Generated: {HERE / BOUNDARY_SCAN_NAME}")
    print(f"Generated: {FIG_DIR / (BETA_FIG_STEM + '.pdf')}")
    print(f"Generated: {FIG_DIR / (BOUNDARY_FIG_STEM + '.pdf')}")
    print(
        beta_frame[
            [
                "beta",
                "q_inflection_theory",
                "q_inflection_numeric",
                "q_inflection_numeric_error",
                "beta_recovered_numeric",
            ]
        ].to_string(index=False)
    )
    print(
        boundary_frame[
            [
                "q0",
                "existence_product",
                "inflection_exists",
                "tau_inflection",
                "control_duration",
                "t2_minus_t_inflection",
                "q_inflection_analytic",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
