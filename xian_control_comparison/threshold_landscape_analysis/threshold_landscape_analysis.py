"""西安情景一单阈值控制响应图谱分析。

本模块只生成探索性理论和数值输出，所有结果写入
threshold_landscape_analysis/ 子目录。它不覆盖西安主基准结果，
也不修改 low_eta_analysis/ 历史输出。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.colorbar import Colorbar
from matplotlib.colors import LogNorm, Normalize
import numpy as np
import pandas as pd
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq
from scipy.special import lambertw


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))

import xian_control_comparison as xcc  # noqa: E402
import paper_plot_style as pps  # noqa: E402


OUT_DIR = HERE
ETA_DIR = OUT_DIR / "eta_landscape"
ETA_PANEL_DIR = OUT_DIR / "representative_eta_panels"
COST_DIR = OUT_DIR / "cost_weight_analysis"
HEATMAP_DIR = OUT_DIR / "eta_c0_heatmap"
C0_PANEL_DIR = OUT_DIR / "representative_c0_panels"
HIGH_C0_STRESS_DIR = OUT_DIR / "high_c0_stress_test_panels"

REPRESENTATIVE_ETAS = [100.0, 151.90, 520.0, 1300.0, 3200.0, 6500.0, 15000.0, 26326.0]
REPRESENTATIVE_C0_ETAS = [100.0, 1300.0, 26326.0]
REPRESENTATIVE_C0_VALUES = [6.0, 9.0, 12.8872]
STRESS_C0_VALUES = [14.0, 18.0, 20.0]
DEFAULT_W_C = 1.0
DEFAULT_W_Q = 2.0
WQ_VALUES = [DEFAULT_W_Q]
PANEL_X_END = 120.0
ZOOM_X_END = 50.0
STATUS_COLORS = {
    "ok": "#2b8a3e",
    "q_below_q0": "#e67700",
    "q_out_of_bounds": "#c43c39",
    "threshold_not_reached": "#777777",
    "not_cleared": "#6f42c1",
    "error": "#111111",
}


@dataclass(frozen=True)
class LandscapeParams:
    """单阈值响应图谱使用的局部参数对象。"""

    N: float = xcc.P.N
    beta: float = xcc.P.beta
    gamma: float = xcc.P.gamma
    delta_q: float = xcc.P.delta_q
    c0: float = xcc.P.c0
    q0: float = xcc.P.q0
    dynamic_horizon_initial: float = 120.0
    dynamic_horizon_limit: float = 50000.0
    dt: float = xcc.P.dt


DEFAULT_PARAMS = LandscapeParams()


def ensure_dirs() -> None:
    for path in [OUT_DIR, ETA_DIR, ETA_PANEL_DIR, COST_DIR, HEATMAP_DIR, C0_PANEL_DIR, HIGH_C0_STRESS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


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


def merged_grid(base: Iterable[float], forced: Iterable[float]) -> np.ndarray:
    values = np.r_[np.asarray(list(base), dtype=float), np.asarray(list(forced), dtype=float)]
    return np.array(sorted(set(float(v) for v in values if np.isfinite(v))))


def c_const(params: LandscapeParams) -> Callable[[float], float]:
    return lambda t: params.c0


def q_const(params: LandscapeParams) -> Callable[[float], float]:
    return lambda t: params.q0


def rhs_with_controls(
    params: LandscapeParams,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
) -> Callable[[float, np.ndarray], np.ndarray]:
    """人口规模下 [S, I, Sq, Iq, Cc, Cq] 的参数化 ODE 右端项。"""

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        S, I, Sq, Iq, Cc, Cq = y
        c = float(c_fun(t))
        q = float(np.clip(q_fun(t), 0.0, 1.0))
        force = S * I / params.N
        community_infection = params.beta * c * (1.0 - q) * force
        quarantine_infection = params.beta * c * q * force
        quarantine_susceptible = (1.0 - params.beta) * c * q * force
        return np.array(
            [
                -(community_infection + quarantine_infection + quarantine_susceptible),
                community_infection - params.gamma * I,
                quarantine_susceptible,
                quarantine_infection - params.delta_q * Iq,
                community_infection,
                quarantine_infection,
            ]
        )

    return rhs


def frame_from_arrays(
    strategy: str,
    t: np.ndarray,
    y: np.ndarray,
    c_values: np.ndarray,
    q_values: np.ndarray,
    params: LandscapeParams,
) -> pd.DataFrame:
    Rt = params.beta * c_values * (1.0 - q_values) * y[0] / (params.gamma * params.N)
    return pd.DataFrame(
        {
            "strategy": strategy,
            "t": t,
            "S": y[0],
            "I": y[1],
            "Sq": y[2],
            "Iq": y[3],
            "Cc": y[4],
            "Cq": y[5],
            "c": c_values,
            "q": q_values,
            "Rt": Rt,
        }
    )


def sample_dense_interval(
    t_start: float,
    t_end: float,
    sol_fun: Callable[[np.ndarray], np.ndarray],
    dt: float,
) -> Tuple[np.ndarray, np.ndarray]:
    n = max(3, int(np.ceil((t_end - t_start) / dt)) + 1)
    t = np.linspace(t_start, t_end, n)
    return t, sol_fun(t)


def solve_event_stage_param(
    params: LandscapeParams,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
    y_start: np.ndarray,
    event_fun: Callable[[float, np.ndarray], float],
    event_name: str,
    t_start: float = 0.0,
    horizon_limit: float | None = None,
) -> Tuple[solve_ivp, float]:
    horizon_limit = params.dynamic_horizon_limit if horizon_limit is None else horizon_limit
    horizon = max(t_start + params.dynamic_horizon_initial, params.dynamic_horizon_initial)
    while horizon <= horizon_limit + 1.0e-9:
        sol = solve_ivp(
            rhs_with_controls(params, c_fun, q_fun),
            (t_start, horizon),
            y_start,
            events=event_fun,
            dense_output=True,
            rtol=1.0e-8,
            atol=1.0e-4,
        )
        if not sol.success:
            raise RuntimeError(sol.message)
        if len(sol.t_events[0]) > 0:
            return sol, float(sol.t_events[0][0])
        horizon *= 2.0
    raise RuntimeError(f"{event_name} was not reached by t={horizon_limit:.0f}.")


def solve_time_control_param(
    strategy: str,
    fit: xcc.InitialFit,
    params: LandscapeParams,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
) -> pd.DataFrame:
    """求解显式时间控制；用于固定 TDINN 参照线和可变 c0 常规控制。"""

    y0 = np.array([fit.S0, fit.I0, 0.0, 0.0, 0.0, 0.0])

    def event_first_case(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_first_case.terminal = True
    event_first_case.direction = 1

    def event_clear(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_clear.terminal = True
    event_clear.direction = -1

    stage1, t_first = solve_event_stage_param(params, c_fun, q_fun, y0, event_first_case, f"{strategy} first crossing")
    y_first = stage1.sol(t_first)
    stage2, t_clear = solve_event_stage_param(params, c_fun, q_fun, y_first, event_clear, f"{strategy} clearance", t_first)

    t1, y1 = sample_dense_interval(0.0, t_first, stage1.sol, params.dt)
    t2, y2 = sample_dense_interval(t_first, t_clear, stage2.sol, params.dt)
    t = np.r_[t1[:-1], t2]
    y = np.concatenate([y1[:, :-1], y2], axis=1)
    c_values = np.array([float(c_fun(float(tt))) for tt in t])
    q_values = np.array([float(np.clip(q_fun(float(tt)), 0.0, 1.0)) for tt in t])
    return frame_from_arrays(strategy, t, y, c_values, q_values, params)


def baseline_constants(params: LandscapeParams) -> Dict[str, float]:
    beta1 = params.c0 * (params.beta + params.q0 * (1.0 - params.beta))
    beta2 = params.beta * params.c0 * (1.0 - params.q0)
    rho1 = params.gamma * params.N / beta1
    Sc = params.gamma * params.N / beta2
    Sbar = params.gamma * params.N * (1.0 - params.beta) / (params.beta * params.c0)
    R0_eff = beta2 / params.gamma
    return {"beta1": beta1, "beta2": beta2, "rho1": rho1, "Sc": Sc, "Sbar": Sbar, "R0_eff": R0_eff}


def baseline_I_of_S(S: float, fit: xcc.InitialFit, params: LandscapeParams) -> float:
    const = baseline_constants(params)
    beta1 = const["beta1"]
    beta2 = const["beta2"]
    rho1 = const["rho1"]
    return fit.I0 - (beta2 / beta1) * (S - fit.S0) + rho1 * np.log(S / fit.S0)


def compute_threshold_details(fit: xcc.InitialFit, eta: float, params: LandscapeParams) -> Dict[str, float | str]:
    """计算单阈值控制理论量，不负责数值轨迹求解。"""

    details: Dict[str, float | str] = {**baseline_constants(params), "eta": eta, "c0": params.c0}
    Sc = float(details["Sc"])
    Sbar = float(details["Sbar"])
    if not (0.0 < Sc < fit.S0):
        details.update(
            {
                "Imax_background": np.nan,
                "S_star": np.nan,
                "t2": np.nan,
                "control_duration": np.nan,
                "q_start": np.nan,
                "q_end": np.nan,
                "q_min_theory": np.nan,
                "q_max_theory": np.nan,
                "status": "threshold_not_reached",
            }
        )
        return details

    Imax_background = baseline_I_of_S(Sc, fit, params)
    details["Imax_background"] = Imax_background
    if fit.I0 > eta or Imax_background <= eta:
        details.update(
            {
                "S_star": np.nan,
                "t2": np.nan,
                "control_duration": np.nan,
                "q_start": np.nan,
                "q_end": np.nan,
                "q_min_theory": np.nan,
                "q_max_theory": np.nan,
                "status": "threshold_not_reached",
            }
        )
        return details

    S_star = brentq(lambda S: baseline_I_of_S(S, fit, params) - eta, Sc, fit.S0)
    control_duration = (params.N / (params.c0 * eta)) * np.log((S_star - Sbar) / (Sc - Sbar))
    q_start = 1.0 - params.gamma * params.N / (params.beta * params.c0 * S_star)
    q_end = params.q0
    q_min = min(q_start, q_end)
    q_max = max(q_start, q_end)
    tol = 1.0e-9
    if q_min < -tol or q_max > 1.0 + tol:
        status = "q_out_of_bounds"
    elif q_min < params.q0 - tol:
        status = "q_below_q0"
    else:
        status = "ok"
    details.update(
        {
            "S_star": S_star,
            "control_duration": control_duration,
            "q_start": q_start,
            "q_end": q_end,
            "q_min_theory": q_min,
            "q_max_theory": q_max,
            "status": status,
        }
    )
    return details


def interpolate_row(df: pd.DataFrame, t_value: float) -> np.ndarray:
    columns = ["S", "I", "Sq", "Iq", "Cc", "Cq"]
    t = df["t"].to_numpy()
    return np.array([np.interp(t_value, t, df[col].to_numpy()) for col in columns], dtype=float)


def first_crossing_time(df: pd.DataFrame, eta: float) -> float:
    t = df["t"].to_numpy()
    I = df["I"].to_numpy()
    idx = np.where(I >= eta)[0]
    if len(idx) == 0:
        return np.nan
    i = int(idx[0])
    if i == 0:
        return float(t[0])
    if abs(I[i] - I[i - 1]) < 1.0e-12:
        return float(t[i])
    frac = (eta - I[i - 1]) / (I[i] - I[i - 1])
    return float(t[i - 1] + frac * (t[i] - t[i - 1]))


def daily_grid(start: float, end: float) -> np.ndarray:
    if end <= start:
        return np.array([start, end], dtype=float)
    inner = np.arange(np.ceil(start), np.floor(end) + 1.0, 1.0)
    inner = inner[(inner > start) & (inner < end)]
    return np.r_[start, inner, end]


def solve_stage3_after_platform(
    params: LandscapeParams,
    y2: np.ndarray,
    t2: float,
    eta: float,
    details: Dict[str, float | str],
) -> Tuple[pd.DataFrame, float, bool]:
    """平台结束后回到常规控制，清零终止时刻使用相平面公式计算。"""

    clear_time, S_end, C2 = formula_clear_time_after_platform(params, eta, t2, details)
    tau_end = clear_time - t2
    if not np.isfinite(tau_end) or tau_end <= 0.0 or tau_end > params.dynamic_horizon_limit:
        return pd.DataFrame(), np.nan, False

    tau = daily_grid(0.0, tau_end)
    sol = solve_ivp(
        rhs_with_controls(params, c_const(params), q_const(params)),
        (0.0, tau_end),
        y2,
        t_eval=tau,
        dense_output=True,
        rtol=1.0e-8,
        atol=1.0e-4,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    y = sol.y
    t_abs = t2 + tau
    df = frame_from_arrays(
        "情景一阈值控制",
        t_abs,
        y,
        np.full_like(t_abs, params.c0),
        np.full_like(t_abs, params.q0),
        params,
    )
    details.update({"S_end": S_end, "C2": C2, "clear_time_method": "phase_formula"})
    return df, clear_time, True


def formula_clear_time_after_platform(
    params: LandscapeParams,
    eta: float,
    t2: float,
    details: Dict[str, float | str],
) -> Tuple[float, float, float]:
    """使用主论文相平面公式计算情景一的清零终止时刻。"""

    beta1 = float(details["beta1"]) / params.N
    beta2 = float(details["beta2"]) / params.N
    rho1 = float(details["rho1"])
    Sc = float(details["Sc"])
    C2 = eta + (beta2 / beta1) * Sc - rho1 * np.log(Sc)

    def end_equation(S: float) -> float:
        return 1.0 + (beta2 / beta1) * S - rho1 * np.log(S) - C2

    S_end = np.nan
    try:
        arg = -(beta2 / (beta1 * rho1)) * np.exp((1.0 - C2) / rho1)
        W0 = lambertw(arg, k=0)
        if abs(float(np.imag(W0))) < 1.0e-7:
            candidate = float(-beta1 * rho1 * np.real(W0) / beta2)
            if 0.0 < candidate < Sc and abs(end_equation(candidate)) < 1.0e-3:
                S_end = candidate
    except (FloatingPointError, OverflowError, ValueError):
        S_end = np.nan

    if not np.isfinite(S_end):
        lower = max(1.0e-9, Sc * 1.0e-12)
        S_end = brentq(end_equation, lower, Sc * (1.0 - 1.0e-12), xtol=1.0e-8, rtol=1.0e-10)

    def integrand(S: float) -> float:
        denominator = S * (beta2 * S - beta1 * rho1 * np.log(S) - beta1 * C2)
        return 1.0 / denominator

    delta_t, _ = quad(integrand, Sc, S_end, epsabs=1.0e-7, epsrel=1.0e-9, limit=200)
    return float(t2 + delta_t), float(S_end), float(C2)


def solve_threshold_fast(
    fit: xcc.InitialFit,
    eta: float,
    params: LandscapeParams,
    routine_df: pd.DataFrame | None = None,
) -> Tuple[pd.DataFrame, Dict[str, float | str]]:
    """求解给定 eta 和 c0 下的情景一阈值控制轨迹。"""

    details = compute_threshold_details(fit, eta, params)
    if details["status"] == "threshold_not_reached":
        details.update({"t1": np.nan, "t2": np.nan, "q_was_clipped": 0.0, "plateau_max_error": np.nan})
        return pd.DataFrame(), details

    if routine_df is None:
        routine_df = solve_time_control_param("常规控制", fit, params, c_const(params), q_const(params))
    t1 = first_crossing_time(routine_df, eta)
    if not np.isfinite(t1):
        details.update({"t1": np.nan, "t2": np.nan, "q_was_clipped": 0.0, "plateau_max_error": np.nan, "status": "threshold_not_reached"})
        return pd.DataFrame(), details

    y1 = interpolate_row(routine_df, t1)
    y1[1] = eta
    Sbar = float(details["Sbar"])
    S_star = float(details["S_star"])
    control_duration = float(details["control_duration"])
    t2 = t1 + control_duration
    k = params.c0 * eta / params.N
    a = S_star - Sbar

    def s_threshold_abs(t_abs: np.ndarray | float) -> np.ndarray:
        tau = np.asarray(t_abs, dtype=float) - t1
        return Sbar + a * np.exp(-k * tau)

    def q_theory_abs(t_abs: np.ndarray | float) -> np.ndarray:
        s_t = s_threshold_abs(t_abs)
        return 1.0 - params.gamma * params.N / (params.beta * params.c0 * s_t)

    q_was_clipped = 1.0 if details["status"] == "q_out_of_bounds" else 0.0

    stage1 = routine_df[routine_df["t"] <= t1].copy()
    if len(stage1) == 0 or abs(float(stage1["t"].iloc[-1]) - t1) > 1.0e-8:
        y1_frame = frame_from_arrays(
            "情景一阈值控制",
            np.array([t1]),
            y1.reshape(6, 1),
            np.array([params.c0]),
            np.array([params.q0]),
            params,
        )
        stage1 = pd.concat([stage1, y1_frame], ignore_index=True)
    stage1["strategy"] = "情景一阈值控制"

    t_stage2 = daily_grid(t1, t2)
    if q_was_clipped:
        def q_clipped_tau(tau: float) -> float:
            return float(np.clip(q_theory_abs(t1 + tau), 0.0, 1.0))

        tau_eval = t_stage2 - t1
        sol2 = solve_ivp(
            rhs_with_controls(params, c_const(params), q_clipped_tau),
            (0.0, control_duration),
            y1,
            t_eval=tau_eval,
            dense_output=True,
            rtol=1.0e-8,
            atol=1.0e-4,
        )
        if not sol2.success:
            raise RuntimeError(sol2.message)
        y_stage2 = sol2.y
        q_stage2 = np.array([q_clipped_tau(float(tau)) for tau in tau_eval])
        y2 = y_stage2[:, -1]
    else:
        s2 = s_threshold_abs(t_stage2)
        tau = t_stage2 - t1
        cc2 = y1[4] + params.gamma * eta * tau
        beta_c_integral = params.beta * params.c0 * eta / params.N * (
            Sbar * tau + a * (1.0 - np.exp(-k * tau)) / k
        )
        cq2 = y1[5] + beta_c_integral - params.gamma * eta * tau
        y_stage2 = np.vstack(
            [
                s2,
                np.full_like(t_stage2, eta),
                np.full_like(t_stage2, np.nan),
                np.full_like(t_stage2, np.nan),
                cc2,
                cq2,
            ]
        )
        q_stage2 = np.asarray(q_theory_abs(t_stage2), dtype=float)
        y2 = np.array([float(s2[-1]), eta, 0.0, 0.0, float(cc2[-1]), float(cq2[-1])])

    stage2 = frame_from_arrays(
        "情景一阈值控制",
        t_stage2[1:],
        y_stage2[:, 1:],
        np.full_like(t_stage2[1:], params.c0),
        q_stage2[1:],
        params,
    )

    try:
        stage3, clear_time, cleared = solve_stage3_after_platform(params, y2, t2, eta, details)
        stage3 = stage3.iloc[1:].copy()
    except RuntimeError:
        stage3 = pd.DataFrame()
        clear_time = np.nan
        cleared = False

    df = pd.concat([stage1, stage2, stage3], ignore_index=True)
    if not cleared:
        details["status"] = "not_cleared" if details["status"] == "ok" else str(details["status"])
    plateau_mask = (df["t"] >= t1 - 1.0e-9) & (df["t"] <= t2 + 1.0e-9)
    plateau_error = float(np.nanmax(np.abs(df.loc[plateau_mask, "I"].to_numpy() - eta))) if plateau_mask.any() else np.nan
    details.update(
        {
            "t1": t1,
            "t2": t2,
            "clear_time": clear_time,
            "cleared": float(cleared),
            "q_was_clipped": q_was_clipped,
            "plateau_max_error": plateau_error,
        }
    )
    return df, details


def epidemic_clear_time(df: pd.DataFrame, threshold: float = 1.0) -> Tuple[float, bool]:
    if df.empty:
        return np.nan, False
    return xcc.epidemic_clear_time(df, threshold)


def compute_control_costs(
    df: pd.DataFrame,
    params: LandscapeParams,
    control_start: float,
    control_end: float,
    w_c: float,
    w_q: float,
    daily_denominator: float | None = None,
) -> Dict[str, float]:
    if df.empty or not np.isfinite(control_start) or not np.isfinite(control_end) or control_end <= control_start:
        return {"J_c": np.nan, "J_q": np.nan, "J": np.nan, "raw_c_cost": np.nan, "raw_q_cost": np.nan}
    t = df["t"].to_numpy()
    reduced_c = np.maximum(params.c0 - df["c"].to_numpy(), 0.0)
    enhanced_q = np.maximum(df["q"].to_numpy() - params.q0, 0.0)
    relative_c = reduced_c / params.c0
    relative_q = enhanced_q / (1.0 - params.q0)
    J_c = xcc.integrate_interval(t, relative_c, control_start, control_end)
    J_q = xcc.integrate_interval(t, relative_q, control_start, control_end)
    J = xcc.integrate_interval(t, w_c * relative_c**2 + w_q * relative_q**2, control_start, control_end)
    raw_c_cost = xcc.integrate_interval(t, reduced_c, control_start, control_end)
    raw_q_cost = xcc.integrate_interval(t, enhanced_q, control_start, control_end)
    return {"J_c": J_c, "J_q": J_q, "J": J, "raw_c_cost": raw_c_cost, "raw_q_cost": raw_q_cost}


def summarize_threshold(
    df: pd.DataFrame,
    eta: float,
    params: LandscapeParams,
    details: Dict[str, float | str],
    w_c: float = DEFAULT_W_C,
    w_q: float = DEFAULT_W_Q,
) -> Dict[str, float | str]:
    base: Dict[str, float | str] = {
        "eta": eta,
        "eta_fraction": eta / params.N,
        "c0": params.c0,
        "t1": details.get("t1", np.nan),
        "t2": details.get("t2", np.nan),
        "control_duration": details.get("control_duration", np.nan),
        "clear_time": np.nan,
        "peak_I": np.nan,
        "cum_total_infections": np.nan,
        "q_start": details.get("q_start", np.nan),
        "q_mean_control": np.nan,
        "q_min_theory": details.get("q_min_theory", np.nan),
        "q_max_theory": details.get("q_max_theory", np.nan),
        "J_c": np.nan,
        "J_q": np.nan,
        "J": np.nan,
        "raw_c_cost": np.nan,
        "raw_q_cost": np.nan,
        "w_c": w_c,
        "w_q": w_q,
        "plateau_max_error": details.get("plateau_max_error", np.nan),
        "q_was_clipped": details.get("q_was_clipped", 0.0),
        "status": details.get("status", "error"),
        "S_star": details.get("S_star", np.nan),
        "Sc": details.get("Sc", np.nan),
        "Sbar": details.get("Sbar", np.nan),
        "S_end": details.get("S_end", np.nan),
        "C2": details.get("C2", np.nan),
        "clear_time_method": details.get("clear_time_method", ""),
    }
    if df.empty:
        return base
    clear_time = float(details.get("clear_time", np.nan))
    cleared = bool(details.get("cleared", 0.0)) and np.isfinite(clear_time)
    if not cleared:
        clear_time, cleared = epidemic_clear_time(df)
    if not cleared:
        base["status"] = "not_cleared" if base["status"] == "ok" else base["status"]
    outcome_end = clear_time if cleared else float(df["t"].iloc[-1])
    active = df["t"].to_numpy() <= outcome_end + 1.0e-9
    peak_idx = int(np.argmax(np.where(active, df["I"].to_numpy(), -np.inf)))
    cum_community = xcc.interpolate_series(df["t"].to_numpy(), df["Cc"].to_numpy(), outcome_end)
    cum_quarantine = xcc.interpolate_series(df["t"].to_numpy(), df["Cq"].to_numpy(), outcome_end)
    costs = compute_control_costs(df, params, float(base["t1"]), float(base["t2"]), w_c, w_q)
    q_mean = np.nan
    if np.isfinite(float(base["t1"])) and np.isfinite(float(base["t2"])) and float(base["t2"]) > float(base["t1"]):
        q_mean = xcc.integrate_interval(df["t"].to_numpy(), df["q"].to_numpy(), float(base["t1"]), float(base["t2"])) / (
            float(base["t2"]) - float(base["t1"])
        )
    base.update(
        {
            "clear_time": clear_time if cleared else np.nan,
            "peak_I": float(df["I"].iloc[peak_idx]),
            "cum_total_infections": cum_community + cum_quarantine if cleared else np.nan,
            "q_mean_control": q_mean,
            "J_c": costs["J_c"],
            "J_q": costs["J_q"],
            "J": costs["J"],
            "raw_c_cost": costs["raw_c_cost"],
            "raw_q_cost": costs["raw_q_cost"],
        }
    )
    return base


def summarize_time_strategy(
    df: pd.DataFrame,
    params: LandscapeParams,
    eta: float,
    w_c: float,
    w_q: float,
    strategy: str,
) -> Dict[str, float | str]:
    clear_time, cleared = epidemic_clear_time(df)
    outcome_end = clear_time if cleared else float(df["t"].iloc[-1])
    active = df["t"].to_numpy() <= outcome_end + 1.0e-9
    peak_idx = int(np.argmax(np.where(active, df["I"].to_numpy(), -np.inf)))
    cum_total = xcc.interpolate_series(df["t"].to_numpy(), df["Cc"].to_numpy(), outcome_end) + xcc.interpolate_series(
        df["t"].to_numpy(), df["Cq"].to_numpy(), outcome_end
    )
    costs = compute_control_costs(df, params, 0.0, outcome_end, w_c, w_q, daily_denominator=outcome_end)
    return {
        "strategy": strategy,
        "eta": eta,
        "eta_fraction": eta / params.N,
        "c0": params.c0,
        "w_c": w_c,
        "w_q": w_q,
        "J": 0.0 if strategy == "常规控制" else costs["J"],
        "J_c": 0.0 if strategy == "常规控制" else costs["J_c"],
        "J_q": 0.0 if strategy == "常规控制" else costs["J_q"],
        "raw_c_cost": 0.0 if strategy == "常规控制" else costs["raw_c_cost"],
        "raw_q_cost": 0.0 if strategy == "常规控制" else costs["raw_q_cost"],
        "clear_time": clear_time if cleared else np.nan,
        "peak_I": float(df["I"].iloc[peak_idx]),
        "cum_total_infections": cum_total if cleared else np.nan,
        "status": "fixed_reference" if strategy == "TDINN控制" else "routine",
    }


def daily_cases(sub: pd.DataFrame, column: str, day_edges: np.ndarray) -> np.ndarray:
    values = np.interp(day_edges, sub["t"].to_numpy(), sub[column].to_numpy())
    return np.maximum(np.diff(values), 0.0)


def plot_panel(
    eta: float,
    c0: float,
    all_df: pd.DataFrame,
    observed: pd.DataFrame,
    threshold_summary: Dict[str, float | str],
    output_dir: Path,
    output_stem: str,
    linear_y_axis: bool = False,
) -> None:
    colors = {
        strategy: pps.STRATEGY_STYLES[strategy]["color"]
        for strategy in pps.STRATEGY_STYLES
    }
    labels = {
        strategy: pps.STRATEGY_STYLES[strategy]["label"]
        for strategy in pps.STRATEGY_STYLES
    }
    styles = {
        strategy: pps.STRATEGY_STYLES[strategy]["linestyle"]
        for strategy in pps.STRATEGY_STYLES
    }
    day_edges = np.arange(0.0, np.ceil(PANEL_X_END) + 1.0)
    day_starts = day_edges[:-1]
    t1 = float(threshold_summary.get("t1", np.nan))

    def add_markers(ax) -> None:
        ax.axvline(float(observed["t"].iloc[-1]), color="#999999", lw=1.0, linestyle=":", alpha=0.75)
        if np.isfinite(t1):
            ax.axvline(t1, color="#c43c39", lw=1.0, alpha=0.45)

    fig = plt.figure(figsize=(12.2, 11.8), constrained_layout=True)
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
    zoom_strategies = {"TDINN控制"} if eta > 1300.0 else {"TDINN控制", "情景一阈值控制"}
    high_eta_zoom = eta > 1300.0

    for strategy, sub_all in all_df.groupby("strategy", sort=False):
        color = colors[strategy]
        label = labels[strategy]
        style = styles[strategy]
        sub = sub_all[sub_all["t"] <= PANEL_X_END].copy()
        ax_i.plot(sub["t"], sub["I"], label=label, color=color, linestyle=style, lw=2.2)
        new = daily_cases(sub_all, "Cc", day_edges)
        qnew = daily_cases(sub_all, "Cq", day_edges)
        new_all_values.append(float(np.max(new)))
        qnew_all_values.append(float(np.max(qnew)))
        if strategy in zoom_strategies:
            new_low_values.append(float(np.max(new)))
            qnew_low_values.append(float(np.max(qnew)))
            ax_i_zoom.plot(sub_all["t"], sub_all["I"], label=label, color=color, linestyle=style, lw=1.9)
            ax_new_zoom.plot(day_starts, new, label=label, color=color, linestyle=style, lw=1.9)
            ax_qnew_zoom.plot(day_starts, qnew, label=label, color=color, linestyle=style, lw=1.9)
        ax_new.plot(day_starts, new, label=label, color=color, linestyle=style, lw=2.2)
        ax_qnew.plot(day_starts, qnew, label=label, color=color, linestyle=style, lw=2.2)
        ax_c.plot(sub["t"], sub["c"], label=label, color=color, linestyle=style, lw=2.2)
        ax_q.plot(sub["t"], sub["q"], label=label, color=color, linestyle=style, lw=2.2)

    ax_new_zoom.scatter(observed["t"], observed["community_new"], s=24, color="#d55e00", edgecolors="white", linewidths=0.5, label="Observed data", zorder=5)
    ax_qnew_zoom.scatter(observed["t"], observed["quarantine_new"], s=24, color="#d55e00", edgecolors="white", linewidths=0.5, label="Observed data", zorder=5)
    ax_i.axhline(eta, color="#777777", lw=1.2, linestyle="-.", label=rf"$\eta={eta:g}$")
    if not high_eta_zoom:
        ax_i_zoom.axhline(eta, color="#777777", lw=1.0, linestyle="-.")

    for ax in [ax_i, ax_i_zoom, ax_new, ax_new_zoom, ax_qnew, ax_qnew_zoom, ax_c, ax_q]:
        add_markers(ax)
    for ax in [ax_i, ax_new, ax_qnew, ax_c, ax_q]:
        ax.set_xlim(0.0, PANEL_X_END)
    for ax in [ax_i_zoom, ax_new_zoom, ax_qnew_zoom]:
        ax.set_xlim(0.0, ZOOM_X_END)
        ax.set_title("zoom", fontsize=8, pad=2)
        ax.tick_params(labelsize=8)
    if not linear_y_axis:
        for ax in [ax_i, ax_new, ax_qnew]:
            ax.set_yscale("log")

    learned_peak = float(all_df.loc[all_df["strategy"].eq("TDINN控制"), "I"].max())
    visible_i_peak = float(all_df.loc[all_df["t"].le(PANEL_X_END), "I"].max())
    y_min = 0.0 if linear_y_axis else 1.0
    ax_i.set_ylim(y_min, max(1.08 * visible_i_peak, 1.35 * learned_peak, 1.25 * eta, 200.0))
    ax_new.set_ylim(y_min, max(80.0, 1.08 * max(new_all_values), 1.35 * max(new_low_values)))
    ax_qnew.set_ylim(y_min, max(180.0, 1.08 * max(qnew_all_values), 1.35 * max(qnew_low_values)))
    if high_eta_zoom:
        learned_zoom = all_df.loc[
            all_df["strategy"].eq("TDINN控制") & all_df["t"].le(ZOOM_X_END)
        ]
        learned_zoom_peak = float(learned_zoom["I"].max()) if not learned_zoom.empty else learned_peak
        learned_all = all_df.loc[all_df["strategy"].eq("TDINN控制")]
        learned_new = daily_cases(learned_all, "Cc", day_edges)
        learned_qnew = daily_cases(learned_all, "Cq", day_edges)
        zoom_days = day_starts <= ZOOM_X_END + 1.0e-9
        observed_zoom = observed.loc[observed["t"].le(ZOOM_X_END)]
        observed_new_peak = float(observed_zoom["community_new"].max()) if not observed_zoom.empty else 0.0
        observed_qnew_peak = float(observed_zoom["quarantine_new"].max()) if not observed_zoom.empty else 0.0
        ax_i_zoom.set_ylim(0.0, max(10.0, 1.35 * learned_zoom_peak))
        ax_new_zoom.set_ylim(0.0, max(10.0, 1.35 * float(np.max(learned_new[zoom_days])), 1.25 * observed_new_peak))
        ax_qnew_zoom.set_ylim(0.0, max(10.0, 1.35 * float(np.max(learned_qnew[zoom_days])), 1.25 * observed_qnew_peak))
    else:
        ax_i_zoom.set_ylim(0.0, max(200.0, 1.35 * learned_peak, 1.2 * eta))
        ax_new_zoom.set_ylim(0.0, max(10.0, 1.35 * max(new_low_values)))
        ax_qnew_zoom.set_ylim(0.0, max(10.0, 1.35 * max(qnew_low_values)))

    title_suffix = " (linear y-axis)" if linear_y_axis else ""
    ax_i.set_title(f"Community infections, eta={eta:g}, c0={c0:g}{title_suffix}")
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
    for ax, fs in [(ax_i, 8.5), (ax_new, 8.0), (ax_qnew, 8.0), (ax_c, 8.0), (ax_q, 8.0)]:
        ax.legend(loc="lower right", fontsize=fs)
    for ax in [ax_i_zoom, ax_new_zoom, ax_qnew_zoom]:
        ax.legend(loc="upper right", fontsize=6.5, frameon=True)

    fig.savefig(output_dir / f"{output_stem}.pdf")
    fig.savefig(output_dir / f"{output_stem}.png", dpi=220)
    plt.close(fig)


def write_eta_table(summary: pd.DataFrame) -> None:
    rows = []
    subset = summary[summary["eta"].round(6).isin([round(v, 6) for v in REPRESENTATIVE_ETAS])].sort_values("eta")
    for _, row in subset.iterrows():
        rows.append(
            f"{row['eta']:.0f} & {row['t1']:.2f} & {row['t2']:.2f} & "
            f"{row['control_duration']:.2f} & {row['clear_time']:.2f} & "
            f"{row['q_max_theory']:.4f} & {row['J_q']:.2f} & {row['J']:.2f} & {row['status']} \\\\"
        )
    content = "\n".join(
        [
            "\\begin{tabular}{ccccccccc}",
            "\\toprule",
            "$\\eta$ & $t_1$ & $t_2$ & $\\Delta t$ & $t_{\\rm end}$ & $q_{\\max}$ & $J_q$ & $J$ & status \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (ETA_DIR / "eta_landscape_summary_table.tex").write_text(content, encoding="utf-8")


def plot_eta_landscape(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(12.0, 11.0), constrained_layout=True)
    pairs = [
        ("t1", r"$t_1$"),
        ("control_duration", r"$\Delta t$"),
        ("clear_time", r"$t_{\rm end}$"),
        ("q_max_theory", r"$q_{\max}$"),
        ("cum_total_infections", r"$I_{t_{\rm cum}}$"),
        ("J", r"$J$"),
    ]
    for ax, (col, ylabel) in zip(axes.ravel(), pairs):
        for status, sub in summary.groupby("status"):
            color = STATUS_COLORS.get(status, "#555555")
            ax.scatter(sub["eta"], sub[col], s=24, color=color, label=status, alpha=0.9)
        ok = summary[summary["status"].eq("ok")].sort_values("eta")
        if not ok.empty:
            ax.plot(ok["eta"], ok[col], color="#333333", lw=1.2, alpha=0.65)
        ax.set_xscale("log")
        if col in {"control_duration", "clear_time", "cum_total_infections", "J"}:
            ax.set_yscale("log")
        ax.axvline(26326.0, color="#777777", lw=1.0, linestyle=":")
        ax.set_xlabel(r"$\eta$")
        ax.set_ylabel(ylabel)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.savefig(ETA_DIR / "eta_landscape_sensitivity.pdf")
    fig.savefig(ETA_DIR / "eta_landscape_sensitivity.png", dpi=220)
    plt.close(fig)


def plot_cost_summary(cost_summary: pd.DataFrame) -> None:
    threshold = cost_summary[cost_summary["strategy"].eq("情景一阈值控制")].copy()
    fig, ax = plt.subplots(figsize=(6.8, 4.6), constrained_layout=True)
    for wq, sub in threshold.groupby("w_q"):
        sub = sub.sort_values("eta")
        ax.plot(sub["eta"], sub["J"], "o-", lw=1.8, ms=3.5, label=rf"$w_q={wq:g}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\eta$")
    ax.set_ylabel(r"$J$")
    ax.axvline(26326.0, color="#777777", lw=1.0, linestyle=":")
    ax.legend(loc="best", fontsize=8)
    fig.savefig(COST_DIR / "cost_summary_wq2.pdf")
    fig.savefig(COST_DIR / "cost_summary_wq2.png", dpi=220)
    plt.close(fig)


def make_contour_levels(values: np.ndarray, metric: str) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.array([])
    vmin = float(np.nanmin(finite))
    vmax = float(np.nanmax(finite))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        return np.array([])
    if metric in {"control_duration", "clear_time", "J"}:
        positive = finite[finite > 0.0]
        if positive.size == 0:
            return np.array([])
        lo = float(np.nanmin(positive))
        hi = float(np.nanmax(positive))
        # 几何等比档：以低端所在十进制档为基，逐级抬升；自动选比例（×2/×4/×8）
        # 使档数约为 4--8 条，避免小面板拥挤。
        base = 10.0 ** np.floor(np.log10(lo))
        seq = [base]
        for ratio in (2.0, 4.0, 8.0):
            seq, v = [], base
            while v < hi:
                seq.append(v)
                v *= ratio
            if len([x for x in seq if x > lo]) <= 8:
                break
        raw = np.array([x for x in seq if x > lo], dtype=float)
    else:
        raw = np.linspace(vmin, vmax, 6)
    levels = np.unique(np.round(raw, decimals=8))
    return levels[(levels > vmin) & (levels < vmax)]


def contour_label_format(metric: str) -> str:
    if metric == "cum_total_infections":
        return "%.3g"          # 累计跨度窄，用 3 位有效数字避免 7 位整数标签拥挤
    if metric in {"control_duration", "clear_time"}:
        return "%.0f"
    if metric == "J":
        return "%.0f"
    return "%.2g"


def heatmap_norm(values: np.ndarray, metric: str) -> Normalize:
    """为跨数量级指标使用对数颜色归一化，其余指标使用线性归一化。"""

    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return Normalize(vmin=0.0, vmax=1.0)
    if metric in {"control_duration", "clear_time", "J"}:
        positive = finite[finite > 0.0]
        if positive.size:
            return LogNorm(vmin=float(np.nanmin(positive)), vmax=float(np.nanmax(positive)))
    return Normalize(vmin=float(np.nanmin(finite)), vmax=float(np.nanmax(finite)))


def heatmap_style(metric: str):
    """返回颜色映射、等高线颜色和色条标签。"""

    labels = {
        "control_duration": r"$\Delta t$ (days)",
        "clear_time": r"$t_{\rm end}$ (days)",
        "cum_total_infections": r"$I_{t_{\rm cum}}$",
        "J": r"$J$",
    }
    symbols = {
        "control_duration": r"$\Delta t$",
        "clear_time": r"$t_{\rm end}$",
        "cum_total_infections": r"$I_{t_{\rm cum}}$",
        "J": r"$J$",
    }
    return pps.PARULA_CMAP, pps.COLORS["red"], labels[metric], symbols[metric]


def draw_heatmap(
    fig,
    ax,
    eta_vals: np.ndarray,
    c0_vals: np.ndarray,
    values: np.ndarray,
    metric: str,
    panel: str | None = None,
    show_contours: bool = True,
    show_xlabel: bool = True,
    show_ylabel: bool = True,
    cax=None,
):
    """在给定坐标轴上绘制一张论文热图。"""

    cmap, contour_color, colorbar_label, panel_symbol = heatmap_style(metric)
    masked = np.ma.masked_invalid(values)
    mesh = ax.pcolormesh(
        eta_vals,
        c0_vals,
        masked,
        shading="auto",
        cmap=cmap,
        norm=heatmap_norm(values, metric),
        edgecolors="face",
        linewidth=0.20,
        antialiased=False,
        snap=True,
        rasterized=False,
    )
    if show_contours:
        levels = make_contour_levels(values, metric)
        if levels.size:
            contours = ax.contour(
                eta_vals,
                c0_vals,
                values,
                levels=levels,
                colors=contour_color,
                linestyles="--",
                linewidths=0.9,
            )
            labels = ax.clabel(
                contours,
                inline=True,
                inline_spacing=3,
                fontsize=7.0,
                fmt=contour_label_format(metric),
                colors="black",
            )
            for label in labels:
                x_pos, y_pos = label.get_position()
                if (
                    y_pos < float(c0_vals.min()) + 0.35
                    or y_pos > float(c0_vals.max()) - 0.25
                    or x_pos < float(eta_vals.min()) * 1.12
                    or x_pos > float(eta_vals.max()) / 1.12
                ):
                    label.set_visible(False)
                    continue
                label.set_path_effects(
                    [patheffects.withStroke(linewidth=2.3, foreground="white")]
                )

    ax.set_xscale("log")
    tick_etas = np.array([100.0, 1000.0, 10000.0, 30000.0])
    tick_etas = tick_etas[(tick_etas >= eta_vals.min()) & (tick_etas <= eta_vals.max())]
    ax.set_xticks(tick_etas)
    ax.set_xticklabels([f"{v:g}" for v in tick_etas])
    ax.set_yticks([6.0, 8.0, 10.0, 12.0, 13.0])
    for x_eta, dash in [(151.90, (0, (4, 2))), (26326.0, (0, (1.2, 2.0)))]:
        ax.axvline(
            x_eta,
            color=pps.COLORS["routine"],
            lw=1.0,
            linestyle=dash,
            alpha=0.82,
            zorder=5,
        )
    if metric == "control_duration":
        y_lab = float(c0_vals.max()) * 0.985
        ax.text(
            151.90, y_lab, r"$I_{\mathrm{peak}}^{\mathrm{T}}$",
            rotation=90, ha="right", va="top", fontsize=6.6,
            color=pps.COLORS["routine"], clip_on=False,
        )
        ax.text(
            26326.0, y_lab, r"$\eta=0.002N$",
            rotation=90, ha="right", va="top", fontsize=6.6,
            color=pps.COLORS["routine"], clip_on=False,
        )
        ax.annotate(
            r"$\Delta t\approx1.48\times10^{4}\,$d $\approx$ 40 yr",
            xy=(151.90, 10.6), xytext=(1500.0, 7.4),
            fontsize=6.6, color="#111111",
            arrowprops=dict(arrowstyle="->", lw=0.7, color="#111111"),
        )
    if show_xlabel:
        ax.set_xlabel(r"$\eta$")
    if show_ylabel:
        ax.set_ylabel(r"$c_0$")
    pps.style_axis(ax, panel, panel_x=-0.08)
    ax.set_title(panel_symbol, fontsize=8.5, pad=3.0)
    previous_raster_threshold = Colorbar.n_rasterize
    Colorbar.n_rasterize = 512
    try:
        if cax is None:
            cbar = fig.colorbar(mesh, ax=ax, pad=0.025, fraction=0.050)
        else:
            cbar = fig.colorbar(mesh, cax=cax)
    finally:
        Colorbar.n_rasterize = previous_raster_threshold
    cbar.solids.set_edgecolor("face")
    cbar.solids.set_linewidth(0.20)
    cbar.solids.set_antialiased(False)
    cbar.set_label(colorbar_label, labelpad=2.0)
    cbar.ax.tick_params(labelsize=6.4, length=2.4, width=0.55, direction="in")
    cbar.outline.set_linewidth(0.65)
    if metric == "cum_total_infections":
        cbar.formatter.set_powerlimits((0, 0))
        cbar.update_ticks()
    return mesh


def plot_heatmap_with_contours(
    eta_vals: np.ndarray,
    c0_vals: np.ndarray,
    values: np.ndarray,
    metric: str,
    title: str,
) -> None:
    del title
    with pps.paper_style_context():
        fig = plt.figure(figsize=(0.48 * pps.TEXT_WIDTH_IN, 2.45))
        ax = fig.add_axes([0.16, 0.18, 0.64, 0.75])
        cax = fig.add_axes([0.83, 0.18, 0.035, 0.75])
        draw_heatmap(
            fig,
            ax,
            eta_vals,
            c0_vals,
            values,
            metric,
            show_contours=True,
            cax=cax,
        )
        pps.save_figure(fig, HEATMAP_DIR / f"heatmap_{metric}_contour")
        plt.close(fig)


def plot_combined_heatmaps(
    eta_vals: np.ndarray,
    c0_vals: np.ndarray,
    metric_values: Dict[str, np.ndarray],
) -> None:
    """生成主论文图 16 使用的统一 2x2 热图。"""

    metrics = [
        "control_duration",
        "clear_time",
        "cum_total_infections",
        "J",
    ]
    with pps.paper_style_context():
        fig = plt.figure(figsize=(0.98 * pps.TEXT_WIDTH_IN, 5.00))
        grid = fig.add_gridspec(
            2,
            4,
            width_ratios=[1.0, 0.045, 1.0, 0.045],
            left=0.085,
            right=0.910,
            bottom=0.105,
            top=0.955,
            wspace=0.38,
            hspace=0.14,
        )
        axes = np.empty((2, 2), dtype=object)
        colorbar_axes = np.empty((2, 2), dtype=object)
        axes[0, 0] = fig.add_subplot(grid[0, 0])
        axes[0, 1] = fig.add_subplot(grid[0, 2], sharex=axes[0, 0], sharey=axes[0, 0])
        axes[1, 0] = fig.add_subplot(grid[1, 0], sharex=axes[0, 0], sharey=axes[0, 0])
        axes[1, 1] = fig.add_subplot(grid[1, 2], sharex=axes[0, 0], sharey=axes[0, 0])
        colorbar_axes[0, 0] = fig.add_subplot(grid[0, 1])
        colorbar_axes[0, 1] = fig.add_subplot(grid[0, 3])
        colorbar_axes[1, 0] = fig.add_subplot(grid[1, 1])
        colorbar_axes[1, 1] = fig.add_subplot(grid[1, 3])
        for index, (ax, metric, panel) in enumerate(
            zip(
                axes.ravel(),
                metrics,
                ["(a)", "(b)", "(c)", "(d)"],
            )
        ):
            row, col = divmod(index, 2)
            draw_heatmap(
                fig,
                ax,
                eta_vals,
                c0_vals,
                metric_values[metric],
                metric,
                panel=panel,
                show_contours=True,
                show_xlabel=row == 1,
                show_ylabel=col == 0,
                cax=colorbar_axes[row, col],
            )
            if row == 0:
                ax.tick_params(labelbottom=False)
            if col == 1:
                ax.tick_params(labelleft=False)
        pps.save_figure(fig, HEATMAP_DIR / "xian_heatmaps")
        plt.close(fig)


def plot_heatmaps(heatmap: pd.DataFrame, paper_only: bool = False) -> None:
    metrics = [
        ("control_duration", r"$\Delta t$"),
        ("clear_time", r"$t_{\rm end}$"),
        ("cum_total_infections", r"$I_{t_{\rm cum}}$"),
        ("J", r"$J$"),
    ]
    eta_vals = np.array(sorted(heatmap["eta"].unique()))
    c0_vals = np.array(sorted(heatmap["c0"].unique()))
    metric_values: Dict[str, np.ndarray] = {}
    for col, title in metrics:
        pivot = heatmap.pivot(index="c0", columns="eta", values=col).reindex(index=c0_vals, columns=eta_vals)
        values = pivot.to_numpy(dtype=float)
        metric_values[col] = values
        with pps.paper_style_context():
            fig = plt.figure(figsize=(0.48 * pps.TEXT_WIDTH_IN, 2.45))
            ax = fig.add_axes([0.16, 0.18, 0.64, 0.75])
            cax = fig.add_axes([0.83, 0.18, 0.035, 0.75])
            draw_heatmap(
                fig,
                ax,
                eta_vals,
                c0_vals,
                values,
                col,
                show_contours=False,
                cax=cax,
            )
            pps.save_figure(fig, HEATMAP_DIR / f"heatmap_{col}")
            plt.close(fig)
        plot_heatmap_with_contours(eta_vals, c0_vals, values, col, title)

    plot_combined_heatmaps(eta_vals, c0_vals, metric_values)

    if paper_only:
        return

    status_map = {"ok": 0.0, "q_below_q0": 1.0, "q_out_of_bounds": 2.0, "threshold_not_reached": 3.0, "not_cleared": 4.0}
    status_values = heatmap.assign(status_code=heatmap["status"].map(status_map).fillna(5.0)).pivot(
        index="c0", columns="eta", values="status_code"
    )
    fig, ax = plt.subplots(figsize=(8.5, 5.6), constrained_layout=True)
    mesh = ax.pcolormesh(eta_vals, c0_vals, status_values.reindex(index=c0_vals, columns=eta_vals).to_numpy(), shading="auto", cmap="tab10", vmin=0, vmax=5)
    ax.set_xscale("log")
    ax.set_xlabel(r"$\eta$")
    ax.set_ylabel(r"$c_0$")
    ax.set_title("status code")
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_ticks(list(status_map.values()))
    cbar.set_ticklabels(list(status_map.keys()))
    fig.savefig(HEATMAP_DIR / "heatmap_status.pdf")
    fig.savefig(HEATMAP_DIR / "heatmap_status.png", dpi=220)
    plt.close(fig)


def make_notes() -> None:
    text = """# threshold_landscape_analysis notes

本目录保存情景一单阈值控制的探索性响应图谱。控制律保持为时间开环：

```tex
q_c(t)=1-\\frac{\\gamma N}{\\beta c_0 S_{\\rm th}(t)}.
```

本模块只记录理论量、数值轨迹、成本指标和可行性状态，不写策略优劣结论。

状态字段说明：

- `ok`：理论隔离率满足可行范围，数值轨迹使用原始 `q_c(t)`。
- `q_below_q0`：理论所需隔离率低于常规隔离率，但仍在 `[0,1]` 内。
- `q_out_of_bounds`：理论隔离率超出 `[0,1]`，ODE 轨迹使用截断后的隔离率；这类轨迹不再严格等同于原始理论开环控制。
- `threshold_not_reached`：常规控制轨道未达到给定阈值。
- `not_cleared`：在设定时间上限内未达到 `I(t)<=1`。

CSV 中控制时长字段为 `control_duration`；图表和 LaTeX 表头记为
`\\Delta t=t_2-t_1`。

CSV 中清零终止时刻字段为 `clear_time`；图表和 LaTeX 表头记为
`t_{\\rm end}`。该时间由主论文中的相平面公式计算：先由
`I(t_{\\rm end})=1` 求 `S_{\\rm end}`，再从 `S_c` 积分到 `S_{\\rm end}`。
隔离率强度指标使用 `q_{\\max}`。在当前情景一平台段中 `q_c(t)`
随时间下降，因此最大值在启动端点取得，但图表中不把最大值指标
直接写成控制函数取值。

`representative_c0_panels/` 中，TDINN 控制固定为文献函数参照线；
情景一阈值控制和常规控制均使用文件名中的 `c0` 重新计算。

`high_c0_stress_test_panels/` 使用 `c0=14,18,20` 做高接触率压力测试。
该目录不属于主分析的 `c0 in [6,13]` 图谱。
"""
    (OUT_DIR / "notes.md").write_text(text, encoding="utf-8")


def run_eta_landscape(
    fit: xcc.InitialFit,
    observed: pd.DataFrame,
    learned_df: pd.DataFrame,
    default_routine_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[float, pd.DataFrame], Dict[float, Dict[str, float | str]]]:
    eta_grid = merged_grid(np.geomspace(100.0, 30000.0, 50), REPRESENTATIVE_ETAS)
    rows: List[Dict[str, float | str]] = []
    panel_cache: Dict[float, pd.DataFrame] = {}
    panel_details: Dict[float, Dict[str, float | str]] = {}
    for eta in eta_grid:
        df, details = solve_threshold_fast(fit, eta, DEFAULT_PARAMS, default_routine_df)
        row = summarize_threshold(df, eta, DEFAULT_PARAMS, details, DEFAULT_W_C, DEFAULT_W_Q)
        rows.append(row)
        if any(abs(eta - rep) < 1.0e-6 for rep in REPRESENTATIVE_ETAS) and not df.empty:
            panel_cache[float(eta)] = df
            panel_details[float(eta)] = row
    summary = pd.DataFrame(rows)
    safe_to_csv(summary, ETA_DIR / "eta_landscape_summary.csv")
    write_eta_table(summary)
    plot_eta_landscape(summary)

    for eta, threshold_df in panel_cache.items():
        all_df = pd.concat([learned_df, threshold_df, default_routine_df], ignore_index=True)
        safe_to_csv(all_df, ETA_PANEL_DIR / f"timeseries_eta{int(round(eta))}.csv")
        plot_panel(
            eta,
            DEFAULT_PARAMS.c0,
            all_df,
            observed,
            panel_details[eta],
            ETA_PANEL_DIR,
            f"panels_eta{int(round(eta))}",
        )
    return summary, panel_cache, panel_details


def run_cost_analysis(
    eta_summary: pd.DataFrame,
    panel_cache: Dict[float, pd.DataFrame],
    fit: xcc.InitialFit,
    learned_df: pd.DataFrame,
    routine_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, float | str]] = []
    eta_values = eta_summary["eta"].to_numpy(dtype=float)
    threshold_cache = dict(panel_cache)
    routine_clear = epidemic_clear_time(routine_df)[0]
    for eta in eta_values:
        if eta not in threshold_cache:
            threshold_df, details = solve_threshold_fast(fit, float(eta), DEFAULT_PARAMS, routine_df)
            threshold_cache[float(eta)] = threshold_df
        else:
            threshold_df = threshold_cache[float(eta)]
            _, details = solve_threshold_fast(fit, float(eta), DEFAULT_PARAMS, routine_df)
        for wq in WQ_VALUES:
            rows.append(
                {
                    **summarize_threshold(threshold_df, float(eta), DEFAULT_PARAMS, details, DEFAULT_W_C, wq),
                    "strategy": "情景一阈值控制",
                }
            )
            rows.append(summarize_time_strategy(learned_df, DEFAULT_PARAMS, float(eta), DEFAULT_W_C, wq, "TDINN控制"))
            rows.append(
                {
                    "strategy": "常规控制",
                    "eta": float(eta),
                    "eta_fraction": float(eta) / DEFAULT_PARAMS.N,
                    "c0": DEFAULT_PARAMS.c0,
                    "w_c": DEFAULT_W_C,
                    "w_q": wq,
                    "J": 0.0,
                    "J_c": 0.0,
                    "J_q": 0.0,
                    "raw_c_cost": 0.0,
                    "raw_q_cost": 0.0,
                    "clear_time": routine_clear,
                    "peak_I": float(routine_df["I"].max()),
                    "cum_total_infections": np.nan,
                    "status": "routine",
                }
            )
    cost_summary = pd.DataFrame(rows)
    safe_to_csv(cost_summary, COST_DIR / "cost_summary_wq2.csv")
    plot_cost_summary(cost_summary)
    return cost_summary


def run_eta_c0_heatmap(fit: xcc.InitialFit) -> pd.DataFrame:
    eta_grid = merged_grid(np.geomspace(50.0, 40000.0, 90), REPRESENTATIVE_ETAS)
    c0_grid = merged_grid(np.linspace(6.0, 13.0, 45), REPRESENTATIVE_C0_VALUES)
    rows: List[Dict[str, float | str]] = []
    for c0 in c0_grid:
        params = LandscapeParams(c0=float(c0))
        try:
            routine_df = solve_time_control_param("常规控制", fit, params, c_const(params), q_const(params))
        except RuntimeError:
            routine_df = pd.DataFrame()
        for eta in eta_grid:
            if routine_df.empty:
                details = compute_threshold_details(fit, float(eta), params)
                details.update({"status": "threshold_not_reached", "t1": np.nan, "t2": np.nan})
                rows.append(summarize_threshold(pd.DataFrame(), float(eta), params, details, DEFAULT_W_C, DEFAULT_W_Q))
                continue
            try:
                df, details = solve_threshold_fast(fit, float(eta), params, routine_df)
                rows.append(summarize_threshold(df, float(eta), params, details, DEFAULT_W_C, DEFAULT_W_Q))
            except Exception as exc:  # 保留扫描，不让单点失败中断整体图谱。
                details = compute_threshold_details(fit, float(eta), params)
                details.update({"status": "error", "error_message": str(exc), "t1": np.nan, "t2": np.nan})
                rows.append(summarize_threshold(pd.DataFrame(), float(eta), params, details, DEFAULT_W_C, DEFAULT_W_Q))
    heatmap = pd.DataFrame(rows)
    safe_to_csv(heatmap, HEATMAP_DIR / "eta_c0_heatmap_summary.csv")
    plot_heatmaps(heatmap)
    return heatmap


def run_representative_c0_panels(
    fit: xcc.InitialFit,
    observed: pd.DataFrame,
    learned_df: pd.DataFrame,
) -> None:
    for c0 in REPRESENTATIVE_C0_VALUES:
        params = LandscapeParams(c0=float(c0))
        threshold_background_df = solve_time_control_param("常规控制", fit, params, c_const(params), q_const(params))
        for eta in REPRESENTATIVE_C0_ETAS:
            threshold_df, details = solve_threshold_fast(fit, eta, params, threshold_background_df)
            if threshold_df.empty:
                continue
            summary = summarize_threshold(threshold_df, eta, params, details, DEFAULT_W_C, DEFAULT_W_Q)
            all_df = pd.concat([learned_df, threshold_df, threshold_background_df], ignore_index=True)
            stem = f"panels_eta{int(round(eta))}_c0_{str(c0).replace('.', 'p')}"
            safe_to_csv(all_df, C0_PANEL_DIR / f"timeseries_eta{int(round(eta))}_c0_{str(c0).replace('.', 'p')}.csv")
            plot_panel(
                eta,
                c0,
                all_df,
                observed,
                summary,
                C0_PANEL_DIR,
                stem,
            )
            if abs(eta - 100.0) < 1.0e-9 and abs(c0 - 6.0) < 1.0e-9:
                plot_panel(
                    eta,
                    c0,
                    all_df,
                    observed,
                    summary,
                    C0_PANEL_DIR,
                    f"{stem}_linear",
                    linear_y_axis=True,
                )


def run_high_c0_stress_test_panels(
    fit: xcc.InitialFit,
    observed: pd.DataFrame,
    learned_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, float | str]] = []
    for c0 in STRESS_C0_VALUES:
        params = LandscapeParams(c0=float(c0))
        threshold_background_df = solve_time_control_param("常规控制", fit, params, c_const(params), q_const(params))
        for eta in REPRESENTATIVE_C0_ETAS:
            threshold_df, details = solve_threshold_fast(fit, eta, params, threshold_background_df)
            summary = summarize_threshold(threshold_df, eta, params, details, DEFAULT_W_C, DEFAULT_W_Q)
            rows.append(summary)
            if threshold_df.empty:
                continue
            all_df = pd.concat([learned_df, threshold_df, threshold_background_df], ignore_index=True)
            c0_text = f"{c0:g}".replace(".", "p")
            eta_text = int(round(eta))
            safe_to_csv(all_df, HIGH_C0_STRESS_DIR / f"stress_timeseries_eta{eta_text}_c0_{c0_text}.csv")
            plot_panel(
                eta,
                c0,
                all_df,
                observed,
                summary,
                HIGH_C0_STRESS_DIR,
                f"stress_panels_eta{eta_text}_c0_{c0_text}",
            )
    summary_df = pd.DataFrame(rows)
    safe_to_csv(summary_df, HIGH_C0_STRESS_DIR / "high_c0_stress_test_summary.csv")
    return summary_df


def main() -> None:
    ensure_dirs()
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False, "mathtext.fontset": "dejavusans"})
    observed = xcc.load_observed_data()
    fit = xcc.fit_initial_conditions(observed)
    learned_df = solve_time_control_param("TDINN控制", fit, DEFAULT_PARAMS, xcc.c_real, xcc.q_real)
    default_routine_df = solve_time_control_param("常规控制", fit, DEFAULT_PARAMS, c_const(DEFAULT_PARAMS), q_const(DEFAULT_PARAMS))

    eta_summary, panel_cache, panel_details = run_eta_landscape(fit, observed, learned_df, default_routine_df)
    run_cost_analysis(eta_summary, panel_cache, fit, learned_df, default_routine_df)
    run_eta_c0_heatmap(fit)
    run_representative_c0_panels(fit, observed, learned_df)
    run_high_c0_stress_test_panels(fit, observed, learned_df)
    make_notes()

    print("Generated threshold landscape analysis outputs in:")
    for path in [ETA_DIR, ETA_PANEL_DIR, COST_DIR, HEATMAP_DIR, C0_PANEL_DIR, HIGH_C0_STRESS_DIR]:
        print(f"  {path}")


def regenerate_paper_heatmaps() -> None:
    """从既有二维扫描 CSV 重绘论文热图，不重复运行 ODE 扫描。"""

    ensure_dirs()
    summary_path = HEATMAP_DIR / "eta_c0_heatmap_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Missing {summary_path}; run the full threshold landscape analysis first."
        )
    heatmap = pd.read_csv(summary_path)
    required = {
        "eta",
        "c0",
        "control_duration",
        "clear_time",
        "cum_total_infections",
        "J",
    }
    missing = sorted(required - set(heatmap.columns))
    if missing:
        raise ValueError(f"Heatmap summary is missing columns: {missing}")
    plot_heatmaps(heatmap, paper_only=True)
    print(f"Generated paper heatmaps from: {summary_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-plots-only",
        action="store_true",
        help="read the existing eta-c0 summary CSV and only redraw Section 7 heatmaps",
    )
    cli_args = parser.parse_args()
    if cli_args.paper_plots_only:
        regenerate_paper_heatmaps()
    else:
        main()
