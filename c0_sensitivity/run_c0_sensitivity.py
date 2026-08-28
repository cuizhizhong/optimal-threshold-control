#!/usr/bin/env python3
"""固定阈值比例、仅改变 c0 的西安阈值控制数值实验。

本脚本不会修改论文文件。它完成四件事：
1. 按现稿的四序列最小二乘口径，在 N_eff=20,000 下只拟合一次 I0；
2. 固定 N、theta、I0 与其余传播参数，仅改变 c0；
3. 计算触发、平台、拐点与清零指标，并做开环平台数值校验；
4. 输出主轨迹图、连续扫描图、CSV、JSON 与实验说明。
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq, minimize_scalar


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT.parent / "project_sources"
OUTPUT_DIR = ROOT / "outputs"
PACKAGED_OBSERVED_CSV = ROOT / "inputs" / "xian_observed_data_processed.csv"
OBSERVED_CSV = (
    PACKAGED_OBSERVED_CSV
    if PACKAGED_OBSERVED_CSV.exists()
    else SOURCE_DIR / "08-xian_observed_data_processed.csv"
)


@dataclass(frozen=True)
class Parameters:
    N: float = 20_000.0
    beta: float = 0.1498
    gamma: float = 0.2953
    delta_q: float = 0.3531
    q0: float = 0.3230
    theta: float = 2e-3
    full_city_N: float = 13_163_000.0
    full_city_I0_reference: float = 0.00100662823352

    @property
    def eta(self) -> float:
        return self.theta * self.N


@dataclass
class ScenarioMetrics:
    role: str
    c0: float
    initial_Re: float
    background_peak_fraction: float
    background_peak_I: float
    t1: float
    t2: float
    control_duration: float
    clear_time: float
    post_control_tail: float
    cumulative_community: float
    cumulative_quarantine: float
    cumulative_total: float
    s_star: float
    s_c: float
    s_bar: float
    q_max: float
    q_inf: float
    cost_J: float
    has_internal_inflection: bool
    t_inf: float | None
    lambda_inf: float | None
    t2_minus_tinf: float | None
    plateau_max_abs_error_I: float
    finite_difference_tinf: float | None
    finite_difference_qinf: float | None
    finite_difference_tinf_error: float | None
    finite_difference_qinf_error: float | None


@dataclass
class Scenario:
    metrics: ScenarioMetrics
    timeseries: pd.DataFrame
    platform_t: np.ndarray
    platform_q: np.ndarray
    platform_tau: np.ndarray


P = Parameters()

# 与图 19--21 的顺序蓝保持一致；这里按 c0 从低到高逐渐加深。
C0_COLORS = {
    "near-trigger": "#b6d9e9",
    "near-inflection": "#93c7df",
    "post-inflection": "#6fb4d6",
    "max-duration": "#2779b6",
    "baseline": "#08458a",
}
# 代表 c0 的图例标签按重算后的实际值动态生成，避免残留旧阈值下的硬编码数值。
C0_ROLE_ANNOTATIONS = {
    "near-trigger": " (near trigger)",
    "max-duration": r" (max. $\Delta t$)",
    "baseline": " (baseline)",
}


def c0_label(role: str, c0: float) -> str:
    value = f"{c0:.4f}" if role == "baseline" else f"{c0:.2f}"
    return rf"$c_0={value}$" + C0_ROLE_ANNOTATIONS.get(role, "")
C0_LINEWIDTHS = {
    "near-trigger": 1.6,
    "near-inflection": 1.6,
    "post-inflection": 1.6,
    "max-duration": 1.6,
    "baseline": 1.8,
}


def tdinn_controls(t: np.ndarray | float) -> tuple[np.ndarray | float, np.ndarray | float]:
    """论文所用西安 TDINN 控制函数，仅用于一次性 I0 标定。"""
    c = (12.8872 - 3.4625) * np.exp(-(0.0463 * np.asarray(t)) ** 2) + 3.4625
    q = (0.3230 - 0.9844) * np.exp(-(0.0452 * np.asarray(t)) ** 2) + 0.9844
    return c, q


def simulate_fit_series(N: float, I0: float, t_eval: np.ndarray) -> np.ndarray:
    """积分完整 SIQR 模型及两个累计仓室，用于复现现稿 I0 拟合口径。"""

    def rhs(t: float, y: np.ndarray) -> list[float]:
        S, I, S_q, I_q, C_c, C_q = y
        c, q = tdinn_controls(t)
        contact_flow = float(c) * S * I / N
        return [
            -(P.beta + (1.0 - P.beta) * float(q)) * contact_flow,
            P.beta * (1.0 - float(q)) * contact_flow - P.gamma * I,
            (1.0 - P.beta) * float(q) * contact_flow,
            P.beta * float(q) * contact_flow - P.delta_q * I_q,
            P.beta * (1.0 - float(q)) * contact_flow,
            P.beta * float(q) * contact_flow,
        ]

    sol = solve_ivp(
        rhs,
        (float(t_eval[0]), float(t_eval[-1])),
        [N - I0, I0, 0.0, 0.0, 0.0, 0.0],
        t_eval=t_eval,
        rtol=2e-9,
        atol=1e-11,
        max_step=0.1,
    )
    if not sol.success:
        raise RuntimeError(f"I0 标定积分失败: {sol.message}")
    return sol.y.T


def fit_initial_infection(N: float, observed: pd.DataFrame) -> tuple[float, float]:
    """按现稿口径拟合 I0。

    日新增量用累计仓室在相邻整数日之差表示；累计量取每个日区间右端点。
    该口径在全市人口下复现附件中的 I0 与目标函数值。
    """

    t_edges = np.arange(0.0, 41.0, 1.0)
    obs = [
        observed["community_new"].to_numpy(float),
        observed["quarantine_new"].to_numpy(float),
        observed["community_cum"].to_numpy(float),
        observed["quarantine_cum"].to_numpy(float),
    ]

    def objective(log_I0: float) -> float:
        I0 = math.exp(log_I0)
        sim = simulate_fit_series(N, I0, t_edges)
        C_c = sim[:, 4]
        C_q = sim[:, 5]
        predicted = [np.diff(C_c), np.diff(C_q), C_c[1:], C_q[1:]]
        return float(sum(np.mean((pred - data) ** 2) for pred, data in zip(predicted, obs)))

    result = minimize_scalar(
        objective,
        bounds=(-20.0, 2.0),
        method="bounded",
        options={"xatol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"I0 标定失败: {result.message}")
    return float(math.exp(result.x)), float(result.fun)


def baseline_constants(c0: float, I0: float) -> dict[str, float]:
    s0 = (P.N - I0) / P.N
    i0 = I0 / P.N
    A = P.beta + P.q0 * (1.0 - P.beta)
    k = P.beta * (1.0 - P.q0) / A
    rho = P.gamma / (c0 * A)
    s_c = P.gamma / (P.beta * c0 * (1.0 - P.q0))
    s_bar = P.gamma * (1.0 - P.beta) / (P.beta * c0)
    return {
        "s0": s0,
        "i0": i0,
        "A": A,
        "k": k,
        "rho": rho,
        "s_c": s_c,
        "s_bar": s_bar,
    }


def background_i_of_s(s: float | np.ndarray, c0: float, I0: float) -> float | np.ndarray:
    x = baseline_constants(c0, I0)
    return x["i0"] + x["k"] * (x["s0"] - s) + x["rho"] * np.log(s / x["s0"])


def background_peak_fraction(c0: float, I0: float) -> float:
    x = baseline_constants(c0, I0)
    if x["s_c"] >= x["s0"]:
        return x["i0"]
    return float(background_i_of_s(x["s_c"], c0, I0))


def solve_s_star(c0: float, I0: float, theta: float = P.theta) -> float:
    x = baseline_constants(c0, I0)
    i_peak = background_peak_fraction(c0, I0)
    if i_peak <= theta:
        raise ValueError(f"c0={c0:.8g} 下常规轨道不能触发阈值")
    return float(
        brentq(
            lambda s: float(background_i_of_s(s, c0, I0) - theta),
            x["s_c"] * (1.0 + 1e-13),
            x["s0"],
            xtol=5e-15,
            rtol=5e-15,
        )
    )


def solve_t1(c0: float, I0: float, s_star: float) -> float:
    x = baseline_constants(c0, I0)

    def integrand(s: float) -> float:
        i = float(background_i_of_s(s, c0, I0))
        return 1.0 / (c0 * x["A"] * s * i)

    value, _ = quad(
        integrand,
        s_star,
        x["s0"],
        epsabs=1e-10,
        epsrel=1e-10,
        limit=500,
    )
    return float(value)


def structural_metrics(
    c0: float, I0: float, theta: float = P.theta, compute_J: bool = True
) -> dict[str, float | bool | None]:
    x = baseline_constants(c0, I0)
    s_star = solve_s_star(c0, I0, theta)
    t1 = solve_t1(c0, I0, s_star)
    duration = math.log((s_star - x["s_bar"]) / (x["s_c"] - x["s_bar"])) / (
        c0 * theta
    )
    t2 = t1 + duration
    q_max = 1.0 - P.gamma / (P.beta * c0 * s_star)
    q_inf = 1.0 - 1.0 / (2.0 * (1.0 - P.beta))
    s_inf = 2.0 * x["s_bar"]
    has_inflection = bool(x["s_c"] < s_inf < s_star)

    if has_inflection:
        t_inf = t1 + math.log((s_star - x["s_bar"]) / x["s_bar"]) / (
            c0 * theta
        )
        lambda_inf = (t_inf - t1) / duration
        t2_minus_tinf = t2 - t_inf
    else:
        t_inf = None
        lambda_inf = None
        t2_minus_tinf = None

    # 二次加权综合成本 J（正文式 eq:dom:Jtheta）。情景一 c(t)≡c0 故 J_c=0，
    # 此处只积 J_q 的二次加权项，积分区间严格取平台段 [s_c, s_star]。
    if compute_J:
        def _cost_integrand(s: float) -> float:
            qc = 1.0 - P.gamma / (P.beta * c0 * s)
            return (qc - P.q0) ** 2 / (s - x["s_bar"])

        cost_integral, _ = quad(
            _cost_integrand,
            x["s_c"],
            s_star,
            epsabs=1e-11,
            epsrel=1e-11,
            limit=500,
        )
        cost_J: float | None = 2.0 / (c0 * theta * (1.0 - P.q0) ** 2) * cost_integral
    else:
        cost_J = None

    return {
        **x,
        "s_star": s_star,
        "t1": t1,
        "t2": t2,
        "duration": duration,
        "q_max": q_max,
        "q_inf": q_inf,
        "cost_J": cost_J,
        "has_inflection": has_inflection,
        "t_inf": t_inf,
        "lambda_inf": lambda_inf,
        "t2_minus_tinf": t2_minus_tinf,
    }


def normalized_rhs(c0: float, q_function: Callable[[float], float]) -> Callable:
    """归一化的 S-I 动力学及两个累计感染仓室。

    累计仓室以人口比例记录，并在输出指标中乘回 N。它们从 0 开始，
    与论文数值部分的累计感染口径一致，不把初始感染 I0 重复计入。
    """

    def rhs(t: float, y: np.ndarray) -> list[float]:
        s, i, z_community, z_quarantine = y
        q = q_function(t)
        contact_flow = c0 * s * i
        return [
            -(P.beta + q * (1.0 - P.beta)) * contact_flow,
            (P.beta * c0 * (1.0 - q) * s - P.gamma) * i,
            P.beta * (1.0 - q) * contact_flow,
            P.beta * q * contact_flow,
        ]

    return rhs


def sample_scenario(c0: float, role: str, I0: float) -> Scenario:
    m = structural_metrics(c0, I0)
    s0 = float(m["s0"])
    i0 = float(m["i0"])
    s_star = float(m["s_star"])
    s_c = float(m["s_c"])
    s_bar = float(m["s_bar"])
    t1 = float(m["t1"])
    t2 = float(m["t2"])

    q_baseline = lambda _t: P.q0
    pre_t = np.linspace(0.0, t1, max(500, int(6 * t1) + 1))
    pre = solve_ivp(
        normalized_rhs(c0, q_baseline),
        (0.0, t1),
        [s0, i0, 0.0, 0.0],
        t_eval=pre_t,
        rtol=2e-10,
        atol=2e-13,
        max_step=0.1,
    )
    if not pre.success:
        raise RuntimeError(f"c0={c0:g} 控制前积分失败: {pre.message}")

    platform_t = np.linspace(t1, t2, 4001)
    platform_s = s_bar + (s_star - s_bar) * np.exp(-c0 * P.theta * (platform_t - t1))
    platform_i = np.full_like(platform_t, P.theta)
    platform_q = 1.0 - P.gamma / (P.beta * c0 * platform_s)
    platform_tau = (platform_t - t1) / (t2 - t1)

    def q_open_loop(t: float) -> float:
        s_theory = s_bar + (s_star - s_bar) * math.exp(-c0 * P.theta * (t - t1))
        return 1.0 - P.gamma / (P.beta * c0 * s_theory)

    plateau_check = solve_ivp(
        normalized_rhs(c0, q_open_loop),
        (t1, t2),
        [
            s_star,
            P.theta,
            float(pre.y[2, -1]),
            float(pre.y[3, -1]),
        ],
        t_eval=platform_t,
        rtol=5e-11,
        atol=5e-14,
        max_step=max(0.01, (t2 - t1) / 2000.0),
    )
    if not plateau_check.success:
        raise RuntimeError(f"c0={c0:g} 平台校验积分失败: {plateau_check.message}")
    plateau_abs_error_I = float(np.max(np.abs(plateau_check.y[1] - P.theta)) * P.N)

    clear_level = 1.0 / P.N

    def clear_event(_t: float, y: np.ndarray) -> float:
        return float(y[1] - clear_level)

    clear_event.terminal = True
    clear_event.direction = -1
    post = solve_ivp(
        normalized_rhs(c0, q_baseline),
        (t2, t2 + 5000.0),
        [
            s_c,
            P.theta,
            float(plateau_check.y[2, -1]),
            float(plateau_check.y[3, -1]),
        ],
        events=clear_event,
        dense_output=True,
        rtol=2e-10,
        atol=2e-13,
        max_step=0.1,
    )
    if not post.success or len(post.t_events[0]) == 0:
        raise RuntimeError(f"c0={c0:g} 未在计算区间内达到 I=1")
    clear_time = float(post.t_events[0][0])
    post_t = np.linspace(t2, clear_time, max(500, int(5 * (clear_time - t2)) + 1))
    post_y = post.sol(post_t)

    q_second = np.gradient(np.gradient(platform_q, platform_t), platform_t)
    finite_tinf = None
    finite_qinf = None
    finite_tinf_error = None
    finite_qinf_error = None
    if bool(m["has_inflection"]):
        interior = slice(8, -8)
        local_index = int(np.argmin(np.abs(q_second[interior]))) + 8
        finite_tinf = float(platform_t[local_index])
        finite_qinf = float(platform_q[local_index])
        finite_tinf_error = abs(finite_tinf - float(m["t_inf"]))
        finite_qinf_error = abs(finite_qinf - float(m["q_inf"]))

    frames = [
        pd.DataFrame(
            {
                "role": role,
                "c0": c0,
                "t": pre_t[:-1],
                "I": pre.y[1, :-1] * P.N,
                "q": P.q0,
                "I_cum": pre.y[2, :-1] * P.N,
                "Iq_cum": pre.y[3, :-1] * P.N,
                "It_cum": (pre.y[2, :-1] + pre.y[3, :-1]) * P.N,
                "phase": "pre-control",
            }
        ),
        pd.DataFrame(
            {
                "role": role,
                "c0": c0,
                "t": platform_t,
                "I": platform_i * P.N,
                "q": platform_q,
                "I_cum": plateau_check.y[2] * P.N,
                "Iq_cum": plateau_check.y[3] * P.N,
                "It_cum": (plateau_check.y[2] + plateau_check.y[3]) * P.N,
                "phase": "threshold-control",
            }
        ),
        pd.DataFrame(
            {
                "role": role,
                "c0": c0,
                "t": post_t[1:],
                "I": post_y[1, 1:] * P.N,
                "q": P.q0,
                "I_cum": post_y[2, 1:] * P.N,
                "Iq_cum": post_y[3, 1:] * P.N,
                "It_cum": (post_y[2, 1:] + post_y[3, 1:]) * P.N,
                "phase": "post-control",
            }
        ),
    ]
    timeseries = pd.concat(frames, ignore_index=True)

    initial_Re = P.beta * c0 * (1.0 - P.q0) * s0 / P.gamma
    peak_fraction = background_peak_fraction(c0, I0)
    cumulative_community = float(post_y[2, -1] * P.N)
    cumulative_quarantine = float(post_y[3, -1] * P.N)
    metrics = ScenarioMetrics(
        role=role,
        c0=c0,
        initial_Re=initial_Re,
        background_peak_fraction=peak_fraction,
        background_peak_I=peak_fraction * P.N,
        t1=t1,
        t2=t2,
        control_duration=float(m["duration"]),
        clear_time=clear_time,
        post_control_tail=clear_time - t2,
        cumulative_community=cumulative_community,
        cumulative_quarantine=cumulative_quarantine,
        cumulative_total=cumulative_community + cumulative_quarantine,
        s_star=s_star,
        s_c=s_c,
        s_bar=s_bar,
        q_max=float(m["q_max"]),
        q_inf=float(m["q_inf"]),
        cost_J=float(m["cost_J"]),
        has_internal_inflection=bool(m["has_inflection"]),
        t_inf=float(m["t_inf"]) if m["t_inf"] is not None else None,
        lambda_inf=float(m["lambda_inf"]) if m["lambda_inf"] is not None else None,
        t2_minus_tinf=(
            float(m["t2_minus_tinf"]) if m["t2_minus_tinf"] is not None else None
        ),
        plateau_max_abs_error_I=plateau_abs_error_I,
        finite_difference_tinf=finite_tinf,
        finite_difference_qinf=finite_qinf,
        finite_difference_tinf_error=finite_tinf_error,
        finite_difference_qinf_error=finite_qinf_error,
    )
    return Scenario(metrics, timeseries, platform_t, platform_q, platform_tau)


def boundary_values(I0: float, theta: float = P.theta) -> dict[str, float]:
    # brentq 区间放宽以覆盖 theta in [5e-4, 8e-3] 的相图扫描：theta 升高使各边界右移。
    trigger = brentq(
        lambda c: background_peak_fraction(c, I0) - theta,
        2.5,
        10.0,
        xtol=1e-13,
        rtol=1e-13,
    )
    q_inf = 1.0 - 1.0 / (2.0 * (1.0 - P.beta))
    inflection = brentq(
        lambda c: float(structural_metrics(c, I0, theta, compute_J=False)["q_max"])
        - q_inf,
        trigger * (1.0 + 1e-7),
        14.0,
        xtol=1e-12,
        rtol=1e-12,
    )
    duration_opt = minimize_scalar(
        lambda c: -float(structural_metrics(c, I0, theta, compute_J=False)["duration"]),
        bounds=(trigger * (1.0 + 1e-7), 30.0),
        method="bounded",
        options={"xatol": 1e-11},
    )
    if not duration_opt.success:
        raise RuntimeError(f"控制时长极值搜索失败: {duration_opt.message}")
    return {
        "c0_trigger": float(trigger),
        "c0_inflection_onset": float(inflection),
        "c0_duration_max": float(duration_opt.x),
        "duration_max": float(-duration_opt.fun),
        "q_inf": q_inf,
    }


def build_continuous_scan(
    I0: float, boundaries: dict[str, float], rep_c0s: list[float]
) -> pd.DataFrame:
    c_min = boundaries["c0_trigger"] * (1.0 + 1e-6)
    # 左端的触发/拐点结构变化很快，采用更密的非均匀网格，并把边界与代表点显式纳入。
    c_values = np.unique(
        np.concatenate(
            [
                np.linspace(c_min, 4.5, 260),
                np.linspace(4.5, 22.0, 360),
                np.array(
                    [
                        boundaries["c0_inflection_onset"] * (1.0 + 1e-7),
                        boundaries["c0_duration_max"],
                    ]
                    + [float(c) for c in rep_c0s]
                ),
            ]
        )
    )
    rows: list[dict[str, float | bool | None]] = []
    for c0 in c_values:
        m = structural_metrics(float(c0), I0)
        rows.append(
            {
                "c0": c0,
                "t1": m["t1"],
                "t2": m["t2"],
                "control_duration": m["duration"],
                "q_max": m["q_max"],
                "cost_J": m["cost_J"],
                "has_internal_inflection": m["has_inflection"],
                "t_inf": m["t_inf"],
                "lambda_inf": m["lambda_inf"],
                "t2_minus_tinf": m["t2_minus_tinf"],
                "background_peak_fraction": background_peak_fraction(float(c0), I0),
            }
        )
    return pd.DataFrame(rows)


def configure_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Times",
                "STIXGeneral",
                "STIX",
                "DejaVu Serif",
            ],
            "mathtext.fontset": "stix",
            "axes.unicode_minus": False,
            "font.size": 9.0,
            "axes.labelsize": 10.0,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 7.3,
            "axes.linewidth": 0.9,
            "axes.edgecolor": "#444444",
            "xtick.color": "#555555",
            "ytick.color": "#555555",
            "xtick.labelcolor": "#222222",
            "ytick.labelcolor": "#222222",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "lines.solid_capstyle": "round",
            "lines.dash_capstyle": "round",
            "legend.frameon": False,
            "legend.handlelength": 2.1,
            "legend.handletextpad": 0.6,
            "legend.labelspacing": 0.30,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
            "savefig.pad_inches": 0.03,
        }
    )


def plot_main(
    scenarios: list[Scenario],
    *,
    y_scale: str = "log",
    inset_mode: str = "normalized",
) -> None:
    if y_scale not in {"log", "linear"}:
        raise ValueError(f"不支持的 I(t) 纵轴类型: {y_scale}")
    if inset_mode not in {"normalized", "cumulative"}:
        raise ValueError(f"不支持的 inset 类型: {inset_mode}")

    # 与现有 Panel A/B 一致：清零晚者先画，短轨迹后画并覆盖共同平台/q0 段。
    draw_scenarios = sorted(
        scenarios, key=lambda scenario: scenario.metrics.clear_time, reverse=True
    )
    max_clear = max(s.metrics.clear_time for s in scenarios)
    tend = 1.05 * max_clear
    fig, (ax_i, ax_q) = plt.subplots(
        2,
        1,
        figsize=(6.2911, 5.459),
        sharex=True,
        gridspec_kw={"height_ratios": [1.15, 1.0]},
        constrained_layout=True,
    )

    # ---- (a) I(t) ----
    ax_i.axhline(P.eta, color="#999999", lw=0.7, ls="--", alpha=0.55, zorder=1)
    role_handles = {}
    for scenario in draw_scenarios:
        role = scenario.metrics.role
        data = scenario.timeseries
        role_handles[role], = ax_i.plot(
            data["t"],
            data["I"],
            color=C0_COLORS[role],
            lw=C0_LINEWIDTHS[role],
            label=c0_label(role, scenario.metrics.c0),
            zorder=4,
        )
        if scenario.metrics.has_internal_inflection:
            ax_i.scatter(
                [scenario.metrics.t_inf],
                [P.eta],
                s=28,
                marker="o",
                facecolor=C0_COLORS[role],
                edgecolor="white",
                linewidth=0.6,
                zorder=6,
            )

    if y_scale == "log":
        ax_i.set_yscale("log")
        ax_i.set_ylim(1.0, 1.45 * P.eta)
    else:
        ax_i.set_yscale("linear")
        ax_i.set_ylim(0.0, 1.16 * P.eta)
    ax_i.set_xlim(0.0, tend)
    ax_i.set_ylabel(r"$I(t)$")
    ax_i.text(
        -0.008,
        1.02,
        "(a)",
        transform=ax_i.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color="#222222",
    )
    ax_i.text(
        tend * 0.995,
        P.eta * 1.012,
        rf"$\eta={P.eta:.2f}$",
        fontsize=7.6,
        color="#777777",
        ha="right",
        va="bottom",
    )
    ax_i.legend(
        handles=[role_handles[s.metrics.role] for s in scenarios],
        loc="upper center",
        ncol=3,
        columnspacing=1.0,
        borderaxespad=0.4,
    )
    ax_i.tick_params(length=3.5, width=0.8)

    # ---- (b) q(t), complete three-stage paths ----
    ax_q.axhline(P.q0, color="#999999", lw=0.7, ls="-", alpha=0.55, zorder=1)
    ax_q.axhline(
        scenarios[0].metrics.q_inf,
        color="#999999",
        lw=0.9,
        ls="--",
        zorder=1,
    )
    for scenario in draw_scenarios:
        role = scenario.metrics.role
        m = scenario.metrics
        color = C0_COLORS[role]
        lw = C0_LINEWIDTHS[role]
        ax_q.plot([0.0, m.t1], [P.q0, P.q0], color=color, lw=lw, zorder=3)
        ax_q.plot(
            [m.t1, m.t1],
            [P.q0, m.q_max],
            color=color,
            lw=1.0,
            ls="--",
            alpha=0.8,
            zorder=4,
        )
        ax_q.plot(
            scenario.platform_t,
            scenario.platform_q,
            color=color,
            lw=lw,
            zorder=5,
        )
        ax_q.plot(
            [m.t2, m.clear_time],
            [P.q0, P.q0],
            color=color,
            lw=lw,
            zorder=3,
        )
        ax_q.scatter(
            [m.clear_time],
            [P.q0],
            s=42,
            marker="|",
            color=color,
            linewidths=1.25,
            zorder=7,
        )
        if m.has_internal_inflection:
            ax_q.scatter(
                [m.t_inf],
                [m.q_inf],
                s=26,
                marker="o",
                facecolor="white",
                edgecolor=color,
                linewidth=1.1,
                zorder=6,
            )

    ax_q.set_xlim(0.0, tend)
    ax_q.set_ylim(0.29, 0.94)
    ax_q.set_xlabel(r"time $t$ (days)")
    ax_q.set_ylabel(r"$q(t)$")
    ax_q.text(
        -0.008,
        1.02,
        "(b)",
        transform=ax_q.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color="#222222",
    )
    ax_q.text(
        tend * 0.995,
        scenarios[0].metrics.q_inf + 0.012,
        r"$q_{\mathrm{inf}}$",
        fontsize=7.6,
        color="#888888",
        ha="right",
        va="bottom",
    )
    ax_q.text(
        tend * 0.995,
        P.q0 + 0.012,
        r"$q_0$",
        fontsize=7.6,
        color="#666666",
        ha="right",
        va="bottom",
    )
    ax_q.tick_params(length=3.5, width=0.8)

    inset = ax_q.inset_axes([0.55, 0.52, 0.43, 0.44], facecolor="white", zorder=8)
    inset.patch.set_alpha(0.94)
    if inset_mode == "normalized":
        for scenario in scenarios:
            role = scenario.metrics.role
            inset.plot(
                scenario.platform_tau,
                scenario.platform_q,
                color=C0_COLORS[role],
                lw=1.35 if role == "baseline" else 1.05,
            )
            if scenario.metrics.has_internal_inflection:
                inset.scatter(
                    [scenario.metrics.lambda_inf],
                    [scenario.metrics.q_inf],
                    s=20,
                    facecolor="white",
                    edgecolor=C0_COLORS[role],
                    linewidth=0.9,
                    zorder=6,
                )
        inset.axhline(
            scenarios[0].metrics.q_inf,
            color="#999999",
            lw=0.7,
            ls="--",
            zorder=1,
        )
        inset.set_xlim(0, 1)
        inset.set_ylim(0.30, 0.93)
        inset.set_xlabel(
            r"$\tau=(t-t_1)/(t_2-t_1)$",
            fontsize=7.0,
            labelpad=0.5,
        )
        inset.set_ylabel(r"$q_c$", fontsize=7.0, labelpad=1.0)
        inset.set_title("normalized platform time", fontsize=7.2, pad=2.0)
    else:
        positions = np.arange(len(scenarios))
        totals = np.array([s.metrics.cumulative_total for s in scenarios])
        bars = inset.bar(
            positions,
            totals / 1000.0,
            width=0.68,
            color=[C0_COLORS[s.metrics.role] for s in scenarios],
            edgecolor="white",
            linewidth=0.45,
            zorder=3,
        )
        inset.set_xticks(positions)
        inset.set_xticklabels(
            [
                f"{s.metrics.c0:.2f}".rstrip("0").rstrip(".")
                for s in scenarios
            ],
            fontsize=5.8,
        )
        inset.set_ylim(0.0, 1.22 * float(np.max(totals / 1000.0)))
        inset.set_xlabel(r"$c_0$", fontsize=7.0, labelpad=0.5)
        inset.set_ylabel(r"$I_{t\mathrm{cum}}$ ($10^3$)", fontsize=7.0, labelpad=1.0)
        inset.set_title("total infections by clearance", fontsize=7.2, pad=2.0)
        for bar, value in zip(bars, totals):
            inset.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.025 * float(np.max(totals / 1000.0)),
                f"{value / 1000.0:.2f}",
                ha="center",
                va="bottom",
                fontsize=5.3,
                color="#333333",
            )
    inset.tick_params(axis="both", labelsize=6.5, length=2.3, width=0.55, pad=1.0)
    inset.spines["top"].set_visible(False)
    inset.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        inset.spines[side].set_color("#777777")
        inset.spines[side].set_linewidth(0.55)

    output_stem = "c0_sensitivity_main" if y_scale == "log" else "c0_sensitivity_main_linear"
    if inset_mode == "cumulative":
        output_stem += "_cumulative"
    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT_DIR / f"{output_stem}.{suffix}", bbox_inches="tight")
    plt.close(fig)


def plot_scan(
    scan: pd.DataFrame,
    scenarios: list[Scenario],
    boundaries: dict[str, float],
    cum_curve: np.ndarray,
) -> None:
    # 2x4：上排为时间分解 t_end = t1 + Delta t + tail，下排为结构量与结局量。
    fig, axes = plt.subplots(
        2, 4, figsize=(6.2911, 3.55), sharex=True, constrained_layout=True
    )
    ax_t1, ax_dt, ax_tail, ax_tend, ax_q, ax_lam, ax_J, ax_cum = axes.flat
    c = scan["c0"]
    curve_color = "#3f5568"
    trigger = boundaries["c0_trigger"]
    inflection_onset = boundaries["c0_inflection_onset"]

    ax_t1.plot(c, scan["t1"], color=curve_color, lw=1.7)
    ax_t1.set_ylabel(r"$t_1$ (days)")

    ax_dt.plot(c, scan["control_duration"], color=curve_color, lw=1.7)
    ax_dt.axvline(
        boundaries["c0_duration_max"], color="#777777", ls=":", lw=0.9
    )
    ax_dt.scatter(
        [boundaries["c0_duration_max"]],
        [boundaries["duration_max"]],
        s=28,
        facecolor="white",
        edgecolor=C0_COLORS["max-duration"],
        linewidth=1.0,
        zorder=5,
    )
    ax_dt.annotate(
        rf"$c_0={boundaries['c0_duration_max']:.2f}$",
        (boundaries["c0_duration_max"], boundaries["duration_max"]),
        xytext=(boundaries["c0_duration_max"] + 1.2, boundaries["duration_max"] * 0.72),
        arrowprops={"arrowstyle": "->", "color": "#777777", "lw": 0.7},
        fontsize=7.0,
    )
    ax_dt.set_ylabel(r"$\Delta t$ (days)")

    ax_q.plot(c, scan["q_max"], color=curve_color, lw=1.7)
    ax_q.axhline(boundaries["q_inf"], color="#999999", ls="--", lw=0.9)
    ax_q.axvline(inflection_onset, color="#999999", ls=":", lw=0.9)
    ax_q.fill_between(
        c,
        scan["q_max"],
        boundaries["q_inf"],
        where=scan["q_max"] >= boundaries["q_inf"],
        color="#E7EDF4",
        alpha=1.0,
        zorder=0,
    )
    ax_q.set_ylabel(r"$q_{\max}$")
    ax_q.text(
        0.985,
        boundaries["q_inf"] + 0.015,
        r"$q_{\mathrm{inf}}$",
        transform=ax_q.get_yaxis_transform(),
        fontsize=7.2,
        color="#777777",
        ha="right",
        va="bottom",
    )

    valid = scan["has_internal_inflection"].astype(bool)
    ax_lam.plot(
        scan.loc[valid, "c0"],
        scan.loc[valid, "lambda_inf"],
        color=curve_color,
        lw=1.7,
    )
    ax_lam.axvline(inflection_onset, color="#999999", ls=":", lw=0.9)
    ax_lam.set_ylim(0, 1)
    ax_lam.set_ylabel(r"$\lambda$")

    # J：本池规模下的二次加权强度量（结构量），不叠加任何 TDINN 参照线。
    ax_J.plot(c, scan["cost_J"], color=curve_color, lw=1.7)
    ax_J.set_ylabel(r"$J$")

    # I_tcum：各 c0 到自身动态清零的总累计感染，"该池规模下的结果"，不画 TDINN 参照线。
    ax_cum.plot(cum_curve[:, 0], cum_curve[:, 1], color=curve_color, lw=1.7)
    ax_cum.set_ylabel(r"$I_{t\mathrm{cum}}$")

    # 尾段与清零时刻：需完整三段积分，故用较粗网格（见 compute_cumulative_curve）。
    ax_tail.plot(cum_curve[:, 0], cum_curve[:, 3], color=curve_color, lw=1.7)
    ax_tail.set_ylabel(r"tail (days)")

    ax_tend.plot(cum_curve[:, 0], cum_curve[:, 2], color=curve_color, lw=1.7)
    ax_tend.set_ylabel(r"$t_{\rm end}$ (days)")

    y_for_ax = {
        id(ax_t1): lambda s: s.metrics.t1,
        id(ax_dt): lambda s: s.metrics.control_duration,
        id(ax_q): lambda s: s.metrics.q_max,
        id(ax_lam): lambda s: s.metrics.lambda_inf,
        id(ax_J): lambda s: s.metrics.cost_J,
        id(ax_cum): lambda s: s.metrics.cumulative_total,
        id(ax_tail): lambda s: s.metrics.post_control_tail,
        id(ax_tend): lambda s: s.metrics.clear_time,
    }
    panel_labels = ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)", "(h)")
    for ax, panel_label in zip(axes.flat, panel_labels):
        ax.axvspan(3.0, trigger, color="#EEF1F4", alpha=1.0, zorder=-2)
        ax.axvline(trigger, color="#999999", ls="--", lw=0.8)
        for scenario in scenarios:
            role = scenario.metrics.role
            c0 = scenario.metrics.c0
            y = y_for_ax[id(ax)](scenario)
            if y is not None:
                ax.scatter(
                    [c0],
                    [y],
                    s=25,
                    color=C0_COLORS[role],
                    edgecolor="white",
                    linewidth=0.55,
                    zorder=6,
                )
        ax.set_xlim(3.0, 22.0)
        ax.text(
            -0.04,
            1.01,
            panel_label,
            transform=ax.transAxes,
            fontsize=10,
            fontweight="bold",
            ha="left",
            va="bottom",
            color="#222222",
        )
        ax.tick_params(length=3.2, width=0.75)

    #ax_t1.text(
    #    trigger + 0.16,
    #    0.96,
    #    "trigger",
    #    transform=ax_t1.get_xaxis_transform(),
    #    fontsize=6.8,
    #    color="#777777",
    #    ha="left",
    #    va="top",
    #)
    # ax_q.text(
    #    inflection_onset + 0.16,
    #    0.05,
    #    "inflection onset",
    #    transform=ax_q.get_xaxis_transform(),
    #   fontsize=6.8,
    #    color="#777777",
    #    ha="left",
    #    va="bottom",
    # )
    for ax in (ax_q, ax_lam, ax_J, ax_cum):
        ax.set_xlabel(r"$c_0$")

    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT_DIR / f"c0_sensitivity_scan.{suffix}", bbox_inches="tight")
    plt.close(fig)


def compute_cumulative_curve(
    I0: float, boundaries: dict[str, float], n: int = 48
) -> np.ndarray:
    """在较粗的 c0 网格上做完整积分，给出需要三段完整轨迹才能得到的量。

    返回形状 (n, 4) 的数组，列为 [c0, I_tcum, t_end, tail]，其中
    t_end 为到动态清零 I(t)=1 的时刻、tail 为解除控制后的尾段时长；
    与解析扫描表中的 t1、control_duration 合起来即 t_end = t1 + Delta t + tail。
    """
    c_lo = boundaries["c0_trigger"] * 1.01
    c_values = np.linspace(c_lo, 22.0, n)
    rows = []
    for c0 in c_values:
        sc = sample_scenario(float(c0), "scan", I0)
        rows.append((float(c0), sc.metrics.cumulative_total,
                     sc.metrics.clear_time, sc.metrics.post_control_tail))
    return np.array(rows)


def select_representatives(
    I0: float, boundaries: dict[str, float]
) -> tuple[list[tuple[str, float]], list[Scenario]]:
    """按新边界的相对间距布点：near-trigger 贴触发线上方 3%，两点以 ±5% 跨拐点边界，
    再取 Δt 脊与全市基准。自检两点确实分居拐点边界两侧；若相对间距因边界附近曲率
    过缓失效，则退回固定绝对间距 ±0.05 重试。"""
    trig = boundaries["c0_trigger"]
    inf = boundaries["c0_inflection_onset"]
    dur = boundaries["c0_duration_max"]

    def build(lo: float, hi: float) -> tuple[list[tuple[str, float]], list[Scenario]]:
        reps = [
            ("near-trigger", trig * 1.03),
            ("near-inflection", lo),
            ("post-inflection", hi),
            ("max-duration", dur),
            ("baseline", 12.8872),
        ]
        return reps, [sample_scenario(c0, role, I0) for role, c0 in reps]

    def checks_pass(scenarios: list[Scenario]) -> bool:
        m = {s.metrics.role: s.metrics for s in scenarios}
        # (1) 两点分居拐点边界两侧。
        straddle = (
            not m["near-inflection"].has_internal_inflection
            and m["post-inflection"].has_internal_inflection
        )
        # (2) near-trigger 最近临界：c0 最低且 t1 最高（陡升）。边界过近时 ×0.95 会把
        #     near-inflection 压到 near-trigger 之下，破坏该序，需退回绝对间距。
        lowest_c0 = m["near-trigger"].c0 == min(s.metrics.c0 for s in scenarios)
        highest_t1 = m["near-trigger"].t1 == max(s.metrics.t1 for s in scenarios)
        return straddle and lowest_c0 and highest_t1

    representatives, scenarios = build(inf * 0.95, inf * 1.05)
    if not checks_pass(scenarios):
        representatives, scenarios = build(inf - 0.05, inf + 0.05)

    assert checks_pass(scenarios), (
        "代表点自检未通过：需 near-inflection 全程凸、post-inflection 有拐点，"
        "且 near-trigger 为最低 c0、t1 最高"
    )
    return representatives, scenarios


def plot_phase(
    I0: float,
    boundaries: dict[str, float],
    scenarios: list[Scenario],
) -> None:
    """(θ, c0) 结构相图：三条结构边界（触发 / 拐点 s*=2s̄ / Δt 脊）叠 Δt 等值线，
    标出 θ=0.002 切片及其与三条边界的交点。全图只含结构量，绝不画 J 或 η=I^T_peak 参照线。"""
    theta_lo, theta_hi = 5e-4, 8e-3
    c_lo, c_hi = 3.0, 14.0

    theta_curve = np.logspace(math.log10(theta_lo), math.log10(theta_hi), 70)
    trig_c, inf_c, dur_c = [], [], []
    for th in theta_curve:
        b = boundary_values(I0, theta=float(th))
        trig_c.append(b["c0_trigger"])
        inf_c.append(b["c0_inflection_onset"])
        dur_c.append(b["c0_duration_max"])
    trig_c = np.array(trig_c)
    inf_c = np.array(inf_c)
    dur_c = np.array(dur_c)

    c_axis = np.linspace(c_lo, c_hi, 140)
    theta_axis = np.logspace(math.log10(theta_lo), math.log10(theta_hi), 120)
    C, TH = np.meshgrid(c_axis, theta_axis)
    DT = np.full_like(C, np.nan)
    for j, th in enumerate(theta_axis):
        for i, c0 in enumerate(c_axis):
            if background_peak_fraction(float(c0), I0) <= th:
                continue
            x = baseline_constants(float(c0), I0)
            try:
                s_star = solve_s_star(float(c0), I0, float(th))
            except ValueError:
                continue
            DT[j, i] = math.log(
                (s_star - x["s_bar"]) / (x["s_c"] - x["s_bar"])
            ) / (c0 * th)

    fig, ax = plt.subplots(figsize=(4.6, 3.7), constrained_layout=True)

    contour_levels = [20, 40, 60, 80, 100, 120]
    cs = ax.contour(
        C, TH, DT, levels=contour_levels, colors="#c2ccd4", linewidths=0.7, zorder=1
    )
    ax.clabel(cs, fmt="%d", fontsize=5.8, inline=True)

    ax.plot(
        trig_c, theta_curve, color="#8a8a8a", lw=1.6, ls="--",
        label="trigger boundary", zorder=3,
    )
    ax.plot(
        inf_c, theta_curve, color="#6fb4d6", lw=1.9,
        label=r"inflection onset ($s^*=2\bar s$)", zorder=3,
    )
    ax.plot(
        dur_c, theta_curve, color="#2779b6", lw=1.9,
        label=r"$\Delta t$ ridge ($\partial\Delta t/\partial c_0=0$)", zorder=3,
    )

    ax.axhline(P.theta, color="#333333", lw=0.9, ls=":", zorder=2)
    for role, c0 in (
        ("near-trigger", boundaries["c0_trigger"]),
        ("post-inflection", boundaries["c0_inflection_onset"]),
        ("max-duration", boundaries["c0_duration_max"]),
    ):
        ax.scatter(
            [c0], [P.theta], s=36, color=C0_COLORS[role],
            edgecolor="white", linewidth=0.8, zorder=6,
        )

    ax.set_yscale("log")
    ax.set_xlim(c_lo, c_hi)
    ax.set_ylim(theta_lo, theta_hi)
    ax.set_xlabel(r"$c_0$")
    ax.set_ylabel(r"$\theta=\eta/N$")
    ax.text(
        c_hi * 0.985, P.theta * 1.06, r"$\theta=0.002$",
        fontsize=7.0, color="#333333", ha="right", va="bottom",
    )
    ax.legend(loc="lower right", fontsize=6.6, borderaxespad=0.35)
    ax.tick_params(length=3.2, width=0.75)

    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT_DIR / f"c0_sensitivity_phase.{suffix}", bbox_inches="tight")
    plt.close(fig)


def inflection_state(
    c0: float, beta: float, I0: float, theta: float
) -> tuple[float, float, float] | None:
    """在显式 (c0, beta) 下（θ、q0、γ、归一化初值固定）返回 (s_star, s_bar, s_c)；
    若常规轨道触不到阈值则返回 None。刻意自足，不改动 §8.8 路径上冻结 P.beta 的函数。"""
    s0 = (P.N - I0) / P.N
    i0 = I0 / P.N
    A = beta + P.q0 * (1.0 - beta)
    k = beta * (1.0 - P.q0) / A
    rho = P.gamma / (c0 * A)
    s_c = P.gamma / (beta * c0 * (1.0 - P.q0))
    s_bar = P.gamma * (1.0 - beta) / (beta * c0)

    def i_no(s: float) -> float:
        return i0 + k * (s0 - s) + rho * math.log(s / s0)

    i_peak = i0 if s_c >= s0 else i_no(s_c)
    if i_peak <= theta:
        return None
    s_star = float(
        brentq(
            lambda s: i_no(s) - theta,
            s_c * (1.0 + 1e-13),
            s0,
            xtol=5e-15,
            rtol=5e-15,
        )
    )
    return s_star, s_bar, s_c


def plot_beta_existence(I0: float) -> None:
    """(c0, β) 平面上内部拐点的存在域（判据 s_c < 2 s̄ < s*）。β 为病原情景变量，
    θ、q0 固定；纯存在性结构图，无任何指标/成本/占优/TDINN。"""
    theta = P.theta
    beta_max = 1.0 - 1.0 / (2.0 * (1.0 - P.q0))

    c_axis = np.linspace(3.0, 14.0, 220)
    beta_axis = np.linspace(0.05, 0.30, 220)
    C, B = np.meshgrid(c_axis, beta_axis)
    Z = np.zeros_like(C)          # 1 = 存在内部拐点
    F = np.full_like(C, np.nan)   # s_star - 2 s_bar，其零集为上界 2 s̄ = s*
    for j, beta in enumerate(beta_axis):
        for i, c0 in enumerate(c_axis):
            st = inflection_state(float(c0), float(beta), I0, theta)
            if st is None:
                continue
            s_star, s_bar, s_c = st
            F[j, i] = s_star - 2.0 * s_bar
            if s_c < 2.0 * s_bar < s_star:
                Z[j, i] = 1.0

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(4.7, 3.7), constrained_layout=True)

    ax.contourf(C, B, Z, levels=[0.5, 1.5], colors=["#dbe7f3"], zorder=0)
    # 上界（t1 端）：2 s̄ = s*，随 c0、β 弯曲。
    ax.contour(C, B, F, levels=[0.0], colors=["#2779b6"], linewidths=1.9, zorder=3)
    # 下界（t2 端）：s_c = 2 s̄，等价 β = β_max，水平线，只由 β,q0 定。
    ax.axhline(beta_max, color="#8a8a8a", lw=1.7, ls="--", zorder=3)
    # 图24 的 c0 截面所在 β。
    ax.axhline(0.1498, color="#b8b8b8", lw=0.8, ls=":", zorder=1)
    # 西安点。
    ax.scatter(
        [12.8872], [0.1498], s=55, marker="o",
        facecolor="#08458a", edgecolor="white", linewidth=0.9, zorder=6,
    )
    ax.annotate(
        r"Xi'an $(12.89,\,0.1498)$", (12.8872, 0.1498),
        xytext=(9.4, 0.175), fontsize=6.8, color="#08458a",
        arrowprops={"arrowstyle": "->", "color": "#08458a", "lw": 0.7},
    )
    ax.text(
        3.15, beta_max + 0.006, r"$\beta_{\max}=0.2614$",
        fontsize=7.0, color="#666666", ha="left", va="bottom",
    )

    ax.set_xlim(3.0, 14.0)
    ax.set_ylim(0.05, 0.30)
    ax.set_xlabel(r"$c_0$")
    ax.set_ylabel(r"$\beta$")
    handles = [
        Patch(facecolor="#dbe7f3", edgecolor="none", label="internal inflection exists"),
        Line2D([0], [0], color="#2779b6", lw=1.9, label=r"$2\bar s=s^*$ (t$_1$ end)"),
        Line2D([0], [0], color="#8a8a8a", lw=1.7, ls="--", label=r"$\beta_{\max}$ (t$_2$ end)"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=6.6, borderaxespad=0.35)
    ax.tick_params(length=3.2, width=0.75)

    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT_DIR / f"c0_beta_existence.{suffix}", bbox_inches="tight")
    plt.close(fig)


def write_readme(
    I0: float,
    I0_objective: float,
    full_city_fit: float,
    full_city_objective: float,
    scenarios: list[Scenario],
    boundaries: dict[str, float],
) -> None:
    table_rows = []
    for s in scenarios:
        m = s.metrics
        inflection = (
            f"{m.t_inf:.2f} / {m.lambda_inf:.3f}"
            if m.has_internal_inflection
            else "无（全程凸）"
        )
        table_rows.append(
            f"| {m.c0:.5g} | {m.t1:.2f} | {m.control_duration:.2f} | "
            f"{m.t2:.2f} | {m.q_max:.4f} | {inflection} | {m.clear_time:.2f} | "
            f"{m.cumulative_total:.2f} |"
        )

    max_plateau_error = max(s.metrics.plateau_max_abs_error_I for s in scenarios)
    finite_t_errors = [
        s.metrics.finite_difference_tinf_error
        for s in scenarios
        if s.metrics.finite_difference_tinf_error is not None
    ]
    finite_q_errors = [
        s.metrics.finite_difference_qinf_error
        for s in scenarios
        if s.metrics.finite_difference_qinf_error is not None
    ]

    # 直接读图结论里的代表 c0 一律按重算后的实际值动态生成，避免残留旧阈值下的硬编码。
    reps = {s.metrics.role: s.metrics for s in scenarios}
    near_trio = "、".join(
        f"{reps[r].c0:.2f}"
        for r in ("near-trigger", "near-inflection", "post-inflection")
    )
    ordered = [s.metrics for s in scenarios]
    convex_c0 = "、".join(f"{m.c0:.2f}" for m in ordered if not m.has_internal_inflection)
    inflected_c0 = "、".join(f"{m.c0:.2f}" for m in ordered if m.has_internal_inflection)
    readme = f"""# 固定阈值比例下的 c0 数值实验

## 实验口径

- 固定参数：`N_eff={P.N:.0f}`、`beta={P.beta}`、`gamma={P.gamma}`、`q0={P.q0}`。
- 固定阈值比例：`theta=eta/N={P.theta:.6g}`，所以共同平台为 `eta={P.eta:.2f}` 人。
- 在 `N_eff={P.N:.0f}` 下按现稿的四序列最小二乘口径只拟合一次初值，得到
  `I0={I0:.12g}`；所有 c0 情景共同使用该初值，不随 c0 重新拟合。
- 作为复现检查，同一程序在全市人口下得到 `I0={full_city_fit:.12g}`、
  目标函数 `{full_city_objective:.9f}`，附件记录值分别为
  `{P.full_city_I0_reference:.12g}`、`1036.76140515`。
- 不画 TDINN，也不画公共无控制轨迹；图中只比较阈值控制自身。

## 三个结构位置

- 阈值首次可达边界：`c0_trigger={boundaries['c0_trigger']:.8f}`。低于该值时无需启动阈值控制。
- 内部拐点出现边界：`c0_inf={boundaries['c0_inflection_onset']:.8f}`。在触发边界与此边界之间，
  q_c(t) 可构造但全程凸，不存在内部拐点。
- 控制时长极大点：`c0_duration_max={boundaries['c0_duration_max']:.8f}`，
  `Delta_t_max={boundaries['duration_max']:.8f}` 天。

隔离率拐点高度在所有存在内部拐点的情景中均为
`q_inf={boundaries['q_inf']:.12f}`，与 c0 无关。

## 五个代表情景

| c0 | t1 (d) | Delta t (d) | t2 (d) | q_max | t_inf / lambda | clear time (d) | total cumulative |
|---:|---:|---:|---:|---:|:---:|---:|---:|
{chr(10).join(table_rows)}

## 直接读图结论

1. c0 增大时，阈值平台高度始终等于 eta，变化的是到达平台的速度、平台长度和所需隔离强度。
2. t1 严格提前，q_max 严格增大；c0={near_trio}
   加密展示了触发边界到控制时长极大点之间的近临界过渡。
3. Delta t 在整个可行域上不是单调量：从触发边界的 0 上升，在 c0≈{boundaries['c0_duration_max']:.2f} 达到约 {boundaries['duration_max']:.2f} 天，
   随后随 c0 增大而下降；基准情景展示这一回落阶段。
4. c0={convex_c0} 虽能触发阈值控制，但 q_max<q_inf，因此 q_c(t) 全程凸、无内部拐点。
   c0={inflected_c0} 均超过约 {boundaries['c0_inflection_onset']:.4f}，存在唯一内部拐点。
5. 内部拐点存在时，q_inf 不变，但 lambda 随 c0 增大而增大：
   拐点在归一化平台时间中向 t2 端移动；绝对 t_inf 则因整条轨迹提前而提前。
6. I(t) 平台上的实心圆只是 q_c(t) 拐点时刻的投影，不是 I(t) 自身的拐点。
7. 总累计感染按各情景自身的清零时刻 I(t)=1 截止，定义为
   I_tcum=I_cum+Iq_cum；累计仓室从 0 开始，不重复计入共同的初始感染 I0。

## 数值校验

- 五个开环平台的最大绝对平台误差（换算为人数）为 `{max_plateau_error:.3e}`。
- 对存在拐点的三条曲线，用均匀时间网格二阶差分独立定位：
  最大时刻误差 `{max(finite_t_errors):.3e}` 天，最大高度误差 `{max(finite_q_errors):.3e}`。

## 文件

- `c0_sensitivity_main.png/.pdf`：I(t) 与 q(t) 的两面板主图。
- `c0_sensitivity_main_linear.png/.pdf`：仅将主图 I(t) 纵轴改为线性坐标的对照版。
- `c0_sensitivity_main_linear_cumulative.png/.pdf`：线性主图；用清零时总累计感染柱状图替代相对时间 inset。

## 到论文图的映射（复制到 ../figures/ 时务必按此对应）

主图有三个变体，**正文图 23 用的是 `main_linear_cumulative`**（线性纵轴 + 总累计感染柱图 inset），
不是 `main`（对数纵轴 + 相对时间 inset）。三者版式相近，容易复制错。

| 本目录输出 | ../figures/ 目标名 | 正文 |
|---|---|---|
| `c0_sensitivity_main_linear_cumulative.pdf` | `c0_sensitivity_panel.pdf` | 图 23（`fig:c0-panel`） |
| `c0_sensitivity_phase.pdf` | `c0_sensitivity_phase.pdf` | 图 24（`fig:c0-phase`） |
| `c0_sensitivity_scan.pdf` | `c0_sensitivity_scan.pdf` | 附录（`fig:c0-scan`） |
| `c0_beta_existence.pdf` | `c0_beta_existence.pdf` | 附录（`fig:c0-beta-existence`） |

`c0_sensitivity_main.pdf` 与 `c0_sensitivity_main_linear.pdf` 仅作对照，不进论文。
- `c0_sensitivity_scan.png/.pdf`：c0 连续扫描的八指标图，上排 t1、Δt、tail、t_end
  （三者相加即 t_end），下排 q_max、λ、J、I_tcum。
- `c0_sensitivity_phase.png/.pdf`：(θ,c0) 结构相图（三条结构边界叠 Δt 等值线）。
- `c0_beta_existence.png/.pdf`：(c0,β) 平面内部拐点存在域（β 为病原情景变量，θ、q0 固定）。
- `c0_representative_summary.csv`：五个代表情景的指标表。
- `c0_representative_timeseries.csv`：五条轨迹的逐时点数据。
- `c0_continuous_scan.csv`：连续 c0 扫描数据。
- `experiment_parameters.json`：参数、边界与一次性初值标定结果。
- `run_c0_sensitivity.py`：可复现实验脚本。
- `inputs/xian_observed_data_processed.csv`：脚本的一次性初值标定输入。
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    observed = pd.read_csv(OBSERVED_CSV, encoding="utf-8-sig")

    # 论文 §8 全程采用固定**绝对**初值的单一口径：I0 = 1.0066e-3 人（全市标定值），
    # 跨 N_eff 与跨 c0 均不重新拟合（见 xian_dom/caliber.py 与正文 §8 开头）。
    # 此前本节在 N_eff=20,000 上单独拟合一次 I0，与全市标定不一致。
    # 全市重拟合仍执行一次，仅用于复现性检查与 README 记录。
    full_city_fit, full_city_objective = fit_initial_infection(P.full_city_N, observed)
    I0 = P.full_city_I0_reference
    I0_objective = float("nan")
    boundaries = boundary_values(I0)

    # stale/bracket 双重保险：三边界须均大于各自 θ=1.656e-3 旧值，且严格有序。
    old_boundaries = (3.2916453650218696, 3.51266848657926, 6.579743617539404)
    new_boundaries = (
        boundaries["c0_trigger"],
        boundaries["c0_inflection_onset"],
        boundaries["c0_duration_max"],
    )
    assert all(new > old for new, old in zip(new_boundaries, old_boundaries)), (
        f"θ=0.002 下三边界应大于 θ=1.656e-3 旧值 {old_boundaries}，实得 {new_boundaries}"
    )
    assert new_boundaries[0] < new_boundaries[1] < new_boundaries[2], (
        f"三边界应严格有序 trigger<inflection<duration，实得 {new_boundaries}"
    )

    # 方向一自检：Δt 脊（c0_duration_max）须落在命题 prop:s1:sensitivity 的解析零集
    # ln(s0/s*)=Θ 上，才可在正文断言"脊是解析判据的零集，而非仅数值极值"。
    xr = baseline_constants(boundaries["c0_duration_max"], I0)
    s_star_r = solve_s_star(boundaries["c0_duration_max"], I0)
    theta_disc = (s_star_r - xr["s_c"]) / xr["s_c"] * (
        (s_star_r - xr["s_bar"]) / s_star_r
        * math.log((s_star_r - xr["s_bar"]) / (xr["s_c"] - xr["s_bar"]))
        - 1.0
    )
    ridge_residual = abs(math.log(xr["s0"] / s_star_r) - theta_disc)
    assert ridge_residual < 1e-6, (
        f"Δt 脊未落在解析零集 ln(s0/s*)=Θ 上：残差 {ridge_residual:.3e}"
    )

    representatives, scenarios = select_representatives(I0, boundaries)
    rep_c0s = [c0 for _role, c0 in representatives]
    scan = build_continuous_scan(I0, boundaries, rep_c0s)
    cum_curve = compute_cumulative_curve(I0, boundaries)

    configure_plot_style()
    plot_main(scenarios, y_scale="log")
    plot_main(scenarios, y_scale="linear")
    plot_main(scenarios, y_scale="linear", inset_mode="cumulative")
    plot_scan(scan, scenarios, boundaries, cum_curve)
    plot_phase(I0, boundaries, scenarios)
    plot_beta_existence(I0)

    summary = pd.DataFrame([asdict(s.metrics) for s in scenarios])
    summary.to_csv(OUTPUT_DIR / "c0_representative_summary.csv", index=False, encoding="utf-8-sig")
    pd.concat([s.timeseries for s in scenarios], ignore_index=True).to_csv(
        OUTPUT_DIR / "c0_representative_timeseries.csv",
        index=False,
        encoding="utf-8-sig",
    )
    scan.to_csv(OUTPUT_DIR / "c0_continuous_scan.csv", index=False, encoding="utf-8-sig")

    parameters = {
        "parameters": asdict(P),
        "derived": {
            "eta": P.eta,
            "I0_refit_at_N_eff": I0,
            "I0_refit_objective": I0_objective,
            "full_city_I0_reproduction": full_city_fit,
            "full_city_objective_reproduction": full_city_objective,
            "ridge_discriminant_residual": ridge_residual,
            **boundaries,
        },
        "representative_c0": [
            {"role": role, "c0": float(c0)} for role, c0 in representatives
        ],
    }
    (OUTPUT_DIR / "experiment_parameters.json").write_text(
        json.dumps(parameters, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_readme(
        I0,
        I0_objective,
        full_city_fit,
        full_city_objective,
        scenarios,
        boundaries,
    )

    print(json.dumps(parameters["derived"], ensure_ascii=False, indent=2))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
