"""比较西安 TDINN控制、情景一阈值控制和常规控制。

本脚本使用人口规模下的 SIQR 模型。总人口固定为西安市 2021 年末常住人口，
beta、gamma 和 delta_q 固定为 He--Tang--Xiao (2023) 表 1 中的参数，
初始移除类设为 R(0)=0。因此 N=S0+I0，拟合时只用观测到的每日社区病例和
隔离病例估计 I0。

情景一阈值控制实现为时间域上的 q_c(t)。在控制阶段，先由常规控制轨道
计算 t1 和 S_star，然后 q_c(t) 只依赖时间 t，不使用数值积分中的当前 S(t)
作为反馈。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, least_squares

import paper_plot_style as pps


OUT_DIR = Path(__file__).resolve().parent
ROOT_DIR = OUT_DIR.parent
DATA_PATH = ROOT_DIR / "真实数据" / "Xianguankong.xlsx"
DEFAULT_W_C = 1.0
DEFAULT_W_Q = 2.0


@dataclass(frozen=True)
class Parameters:
    """模型、拟合和作图共用的固定参数。

    这里集中放参数是为了保证三种策略使用同一组人口规模、传播参数、
    常规控制强度和阈值设定，避免在不同函数里手工重复常数。
    """

    # 西安人口规模 SIQR 模型参数。
    N: float = 13_163_000.0
    beta: float = 0.1498
    gamma: float = 0.2953
    delta_q: float = 0.3531
    c0: float = 12.8872
    q0: float = 0.3230

    # 主分析中的医疗容量阈值：eta = 0.002N。
    eta_fraction: float = 0.002

    # 仅用于敏感性分析的额外阈值。
    eta_fraction_values: Tuple[float, ...] = (
        0.0001,
        0.0002,
        0.0005,
        0.001,
        0.0015,
        0.002,
        0.003,
        0.004,
        0.005,
        0.0075,
        0.01,
    )

    # 事件驱动积分从该时间长度开始；若未找到事件则逐步翻倍，
    # 但不超过 dynamic_horizon_limit。
    dynamic_horizon_initial: float = 120.0
    dynamic_horizon_limit: float = 5000.0

    # 对 ODE 稠密解采样并输出轨道时使用的时间步长。
    dt: float = 0.025

    # 当前主分析固定 R(0)=0，只拟合 I0。
    fit_removed_initial: bool = False

    @property
    def eta(self) -> float:
        """返回人口规模单位下的主阈值 eta。"""
        return self.eta_fraction * self.N

    @property
    def eta_values(self) -> Tuple[float, ...]:
        """返回人口规模单位下的敏感性分析阈值。"""
        return tuple(self.N * value for value in self.eta_fraction_values)


@dataclass(frozen=True)
class InitialFit:
    """TDINN 数据校准得到的初始条件和拟合诊断量。"""

    S0: float
    I0: float
    R0_initial: float
    objective: float
    raw_rmse: float
    residual_type: str


P = Parameters()


def c_real(t: np.ndarray | float) -> np.ndarray | float:
    """西安案例中学习得到的接触率函数 c_2(t)。"""
    x = np.asarray(t)
    return (12.8872 - 3.4625) * np.exp(-((0.0463 * x) ** 2)) + 3.4625


def q_real(t: np.ndarray | float) -> np.ndarray | float:
    """西安案例中学习得到的隔离率函数 q_2(t)。"""
    x = np.asarray(t)
    return (0.3230 - 0.9844) * np.exp(-((0.0452 * x) ** 2)) + 0.9844


def c_background(t: float) -> float:
    """常规控制和情景一阈值控制使用的常规接触率 c0。"""
    return P.c0


def q_background(t: float) -> float:
    """阈值控制窗口之外使用的常规隔离率 q0。"""
    return P.q0


def load_observed_data() -> pd.DataFrame:
    """读取西安报告数据，并添加拟合和作图需要的每日/累计病例列。"""

    raw = pd.read_excel(DATA_PATH)
    df = raw.rename(columns={"Date": "date", "I_new": "community_new", "Iq_new": "quarantine_new"}).copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["t"] = (df["date"] - df["date"].iloc[0]).dt.days.astype(float)
    df["total_new"] = df["community_new"] + df["quarantine_new"]
    df["community_cum"] = df["community_new"].cumsum()
    df["quarantine_cum"] = df["quarantine_new"].cumsum()
    df["total_cum"] = df["total_new"].cumsum()
    return df


def rhs_with_controls(
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
) -> Callable[[float, np.ndarray], np.ndarray]:
    """人口规模下 [S, I, Sq, Iq, Cc, Cq] 的 ODE 右端项。"""

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        S, I, Sq, Iq, Cc, Cq = y
        c = float(c_fun(t))
        # ODE 求解器在插值或步长试探时可能查询到预期范围外的值；
        # 这里截断 q，确保隔离率始终是合法概率。
        q = float(np.clip(q_fun(t), 0.0, 1.0))

        # 人口规模下的质量作用感染项。
        force = S * I / P.N

        # 新感染被拆分为社区感染流和隔离感染流。
        community_infection = P.beta * c * (1.0 - q) * force
        quarantine_infection = P.beta * c * q * force

        # 进入隔离的易感者记入 Sq；在这个简化系统中，
        # 他们之后不再贡献社区感染。
        quarantine_susceptible = (1.0 - P.beta) * c * q * force

        dS = -(community_infection + quarantine_infection + quarantine_susceptible)
        dI = community_infection - P.gamma * I
        dSq = quarantine_susceptible
        dIq = quarantine_infection - P.delta_q * Iq
        dCc = community_infection
        dCq = quarantine_infection
        return np.array([dS, dI, dSq, dIq, dCc, dCq])

    return rhs


def solve_with_initials(
    S0: float,
    I0: float,
    horizon: float,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
    t_eval: np.ndarray | None = None,
    dense_output: bool = False,
) -> solve_ivp:
    """在给定 S0/I0 和控制函数 c(t)、q(t) 下求解 SIQR 系统。"""

    y0 = np.array([S0, I0, 0.0, 0.0, 0.0, 0.0])
    sol = solve_ivp(
        rhs_with_controls(c_fun, q_fun),
        (0.0, horizon),
        y0,
        t_eval=t_eval,
        dense_output=dense_output,
        rtol=1e-7,
        atol=1e-5,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol


def fit_initial_conditions(observed: pd.DataFrame, residual_type: str = "paper_mse") -> InitialFit:
    """用观测到的每日和累计报告病例拟合初始状态。

    主分析中 P.fit_removed_initial=False，因此优化器只搜索 I0，
    并设置 S0=N-I0、R(0)=0。优化变量取为 log(I0)，这样既能保证
    I0>0，也能改善数值稳定性。
    """

    obs_c = observed["community_new"].to_numpy(dtype=float)
    obs_q = observed["quarantine_new"].to_numpy(dtype=float)
    obs_c_cum = observed["community_cum"].to_numpy(dtype=float)
    obs_q_cum = observed["quarantine_cum"].to_numpy(dtype=float)
    n_days = len(observed)
    day_grid = np.arange(n_days + 1, dtype=float)

    def unpack(theta: np.ndarray) -> Tuple[float, float, float]:
        """把对数参数还原为人口数量。"""

        if P.fit_removed_initial:
            S0 = float(np.exp(theta[0]))
            I0 = float(np.exp(theta[1]))
            R0_initial = P.N - S0 - I0
            return S0, I0, R0_initial
        I0 = float(np.exp(theta[0]))
        S0 = P.N - I0
        return S0, I0, 0.0

    def model_predictions(theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Tuple[float, float, float]]:
        """运行 TDINN控制模型，返回每日和累计模型输出。"""

        S0, I0, R0_initial = unpack(theta)
        if S0 <= 0.0 or I0 <= 0.0 or R0_initial < 0.0:
            raise ValueError("Infeasible initial state.")
        sol = solve_with_initials(S0, I0, float(n_days), c_real, q_real, t_eval=day_grid)
        pred_c_cum = sol.y[4, 1:]
        pred_q_cum = sol.y[5, 1:]
        return np.diff(sol.y[4]), np.diff(sol.y[5]), pred_c_cum, pred_q_cum, (S0, I0, R0_initial)

    def residual(theta: np.ndarray) -> np.ndarray:
        """传给 scipy.optimize.least_squares 的残差向量。"""

        try:
            pred_c, pred_q, pred_c_cum, pred_q_cum, _ = model_predictions(theta)
        except Exception:
            size = 4 * n_days if residual_type == "paper_mse" else 2 * n_days
            return np.ones(size) * 1.0e6
        if residual_type == "raw":
            return np.r_[pred_c - obs_c, pred_q - obs_q]
        if residual_type == "paper_mse":
            # 同时匹配每日新增和累计轨道；除以 sqrt(n_days)
            # 使目标函数保持在类似 MSE 的尺度。
            scale = np.sqrt(float(n_days))
            return np.r_[
                (pred_c - obs_c) / scale,
                (pred_q - obs_q) / scale,
                (pred_c_cum - obs_c_cum) / scale,
                (pred_q_cum - obs_q_cum) / scale,
            ]
        if residual_type == "weighted":
            return np.r_[(pred_c - obs_c) / np.sqrt(obs_c + 1.0), (pred_q - obs_q) / np.sqrt(obs_q + 1.0)]
        return np.r_[np.sqrt(pred_c + 1.0) - np.sqrt(obs_c + 1.0), np.sqrt(pred_q + 1.0) - np.sqrt(obs_q + 1.0)]

    if P.fit_removed_initial:
        # 历史选项：同时拟合 S0 和 I0，并令 R(0)=N-S0-I0。
        starts = [
            (P.N - 1.0e-3, 1.0e-3),
            (P.N - 1.0, 1.0),
            (1.0e6, 1.0),
            (5.0e5, 5.0),
            (1.0e5, 20.0),
            (5.0e4, 50.0),
            (1.0e4, 500.0),
        ]
        lower = np.log([1.0e-6, 1.0e-8])
        upper = np.log([P.N, 1.0e6])
        theta_starts = [np.log(start) for start in starts if start[0] + start[1] < P.N]
    else:
        # 主分析：对 I0 使用多个初始猜测，以降低陷入局部极小值的风险。
        theta_starts = [np.log([v]) for v in [1.0e-4, 1.0e-3, 1.0e-2, 0.1, 1.0, 10.0, 100.0]]
        lower = np.log([1.0e-8])
        upper = np.log([1.0e6])

    best = None
    for theta0 in theta_starts:
        res = least_squares(
            residual,
            theta0,
            bounds=(lower, upper),
            max_nfev=160,
            xtol=1e-8,
            ftol=1e-8,
            gtol=1e-8,
        )
        value = float(np.sum(res.fun**2))
        if best is None or value < best[0]:
            best = (value, res.x)

    if best is None:
        raise RuntimeError("Initial-condition fitting did not run.")
    objective, theta_hat = best
    pred_c, pred_q, _, _, initial = model_predictions(theta_hat)
    raw_rmse = float(np.sqrt(np.mean(np.r_[pred_c - obs_c, pred_q - obs_q] ** 2)))
    return InitialFit(*initial, objective=objective, raw_rmse=raw_rmse, residual_type=residual_type)


def baseline_constants() -> Dict[str, float]:
    """常规控制理论相平面公式中使用的常数。"""

    beta1 = P.c0 * (P.beta + P.q0 * (1.0 - P.beta))
    beta2 = P.beta * P.c0 * (1.0 - P.q0)
    rho1 = P.gamma * P.N / beta1
    Sc = P.gamma * P.N / beta2
    Sbar = P.gamma * P.N * (1.0 - P.beta) / (P.beta * P.c0)
    R0_eff = beta2 / P.gamma
    return {"beta1": beta1, "beta2": beta2, "rho1": rho1, "Sc": Sc, "Sbar": Sbar, "R0_eff": R0_eff}


def baseline_I_of_S(S: float, fit: InitialFit) -> float:
    """计算常规控制相平面关系 I(S)。

    这条理论曲线用于寻找 S_star，也就是常规控制轨道首次达到
    I=eta 时对应的易感者数量。
    """

    const = baseline_constants()
    beta1 = const["beta1"]
    beta2 = const["beta2"]
    rho1 = const["rho1"]
    return fit.I0 - (beta2 / beta1) * (S - fit.S0) + rho1 * np.log(S / fit.S0)


def frame_from_solution(
    strategy: str,
    t: np.ndarray,
    y: np.ndarray,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
) -> pd.DataFrame:
    """把 ODE 数组整理为包含状态、控制和 R_e(t) 的长表。"""

    c_values = np.array([float(c_fun(float(tt))) for tt in t])
    q_values = np.array([float(np.clip(q_fun(float(tt)), 0.0, 1.0)) for tt in t])
    Rt_values = P.beta * c_values * (1.0 - q_values) * y[0] / (P.gamma * P.N)
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
            "Rt": Rt_values,
        }
    )


def interpolate_series(t: np.ndarray, y: np.ndarray, x: float) -> float:
    """用线性插值读取任意时间 x 上的轨道值。"""

    if x <= t[0]:
        return float(y[0])
    if x >= t[-1]:
        return float(y[-1])
    return float(np.interp(x, t, y))


def integrate_interval(t: np.ndarray, y: np.ndarray, start: float, end: float) -> float:
    """在任意子区间 [start, end] 上做梯形积分。"""

    if end <= start:
        return 0.0
    start = max(float(start), float(t[0]))
    end = min(float(end), float(t[-1]))
    if end <= start:
        return 0.0
    mask = (t > start) & (t < end)
    tt = np.r_[start, t[mask], end]
    yy = np.r_[np.interp(start, t, y), y[mask], np.interp(end, t, y)]
    return float(np.trapz(yy, tt))


def epidemic_clear_time(df: pd.DataFrame, threshold: float = 1.0) -> Tuple[float, bool]:
    """返回疫情发生后 I(t) 首次降到 threshold 以下的时间。

    代码会先等待 I 向上穿过 threshold，再寻找之后的向下穿越点。
    这样可以避免在拟合 I0 小于 1 人时把 t=0 误判为清零时刻。
    """

    t = df["t"].to_numpy()
    I = df["I"].to_numpy()
    tol = 1.0e-8
    above = I >= threshold
    if not np.any(above):
        return float(t[0]), True
    first_above = int(np.argmax(above))
    below_after = np.where((np.arange(len(I)) > first_above) & (I <= threshold + tol))[0]
    if len(below_after) == 0:
        return float(t[-1]), False
    idx = int(below_after[0])
    t0, t1 = t[idx - 1], t[idx]
    I0, I1 = I[idx - 1], I[idx]
    if abs(I1 - I0) < 1.0e-12:
        return float(t1), True
    frac = (threshold - I0) / (I1 - I0)
    return float(t0 + frac * (t1 - t0)), True


def solve_event_stage(
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
    t_start: float,
    y_start: np.ndarray,
    event_fun: Callable[[float, np.ndarray], float],
    event_name: str,
) -> Tuple[solve_ivp, float]:
    """积分到终止事件发生；若当前时间范围内未发生事件，则延长积分范围。"""

    horizon = max(t_start + P.dynamic_horizon_initial, P.dynamic_horizon_initial)
    while horizon <= P.dynamic_horizon_limit + 1.0e-9:
        sol = solve_ivp(
            rhs_with_controls(c_fun, q_fun),
            (t_start, horizon),
            y_start,
            events=event_fun,
            dense_output=True,
            rtol=1e-8,
            atol=1e-4,
        )
        if not sol.success:
            raise RuntimeError(sol.message)
        if len(sol.t_events[0]) > 0:
            return sol, float(sol.t_events[0][0])
        horizon *= 2.0
    raise RuntimeError(f"{event_name} was not reached by t={P.dynamic_horizon_limit:.0f}.")


def sample_solution_stages(stages: List[Tuple[float, float, Callable[[np.ndarray], np.ndarray]]]) -> Tuple[np.ndarray, np.ndarray]:
    """把多个稠密输出阶段采样并拼接为一条连续时间网格。"""

    t_parts: List[np.ndarray] = []
    y_parts: List[np.ndarray] = []
    for t_start, t_end, sol in stages:
        if t_end <= t_start:
            continue
        n = max(3, int(np.ceil((t_end - t_start) / P.dt)) + 1)
        ts = np.linspace(t_start, t_end, n)
        t_parts.append(ts)
        y_parts.append(sol(ts))
    if not t_parts:
        raise RuntimeError("No solution stages were available for sampling.")
    # 拼接前去掉相邻阶段重复的端点。
    t = np.concatenate([part[:-1] for part in t_parts[:-1]] + [t_parts[-1]])
    y = np.concatenate([part[:, :-1] for part in y_parts[:-1]] + [y_parts[-1]], axis=1)
    return t, y


def solve_time_control(
    strategy: str,
    fit: InitialFit,
    c_fun: Callable[[float], float],
    q_fun: Callable[[float], float],
) -> pd.DataFrame:
    """求解 c(t)、q(t) 均为显式时间函数的策略。

    该函数用于 TDINN控制 和 常规控制。积分按 I=1 分段：
    先找到疫情开始穿越点，再继续积分到后续清零穿越点，
    因此每种策略都有自己的有限输出时间范围。
    """

    y0 = np.array([fit.S0, fit.I0, 0.0, 0.0, 0.0, 0.0])

    def event_first_case(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_first_case.terminal = True
    event_first_case.direction = 1

    def event_clear(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_clear.terminal = True
    event_clear.direction = -1

    stage1, t_first = solve_event_stage(c_fun, q_fun, 0.0, y0, event_first_case, f"{strategy} first crossing")
    y_first = stage1.sol(t_first)
    stage2, t_clear = solve_event_stage(c_fun, q_fun, t_first, y_first, event_clear, f"{strategy} clearance")
    t, y = sample_solution_stages([(0.0, t_first, stage1.sol), (t_first, t_clear, stage2.sol)])
    return frame_from_solution(strategy, t, y, c_fun, q_fun)


def compute_flat_thresholds(fit: InitialFit, eta: float) -> Dict[str, float]:
    """计算情景一阈值控制所需的理论量。

    关键输出包括 S_star 和 Delta_t：S_star 是常规控制轨道首次达到
    I=eta 时的易感者数量；Delta_t 是在 I(t)=eta 平台期内，
    S(t) 从 S_star 下降到 S_c 所需的解析持续时间。
    """

    const = baseline_constants()
    Sc = const["Sc"]
    Sbar = const["Sbar"]
    if not (0.0 < Sc < fit.S0):
        raise ValueError("The baseline critical susceptible level is outside the fitted interval.")
    Imax_background = baseline_I_of_S(Sc, fit)
    if fit.I0 > eta:
        raise ValueError("Initial I0 already exceeds eta.")
    if Imax_background <= eta:
        raise ValueError("The no-control trajectory never reaches eta.")

    # 在常规控制相平面曲线上求解 I(S_star)=eta。
    S_star = brentq(lambda S: baseline_I_of_S(S, fit) - eta, Sc, fit.S0)

    # 阈值平台期推导得到的持续时间公式。
    Delta_t = (P.N / (P.c0 * eta)) * np.log((S_star - Sbar) / (Sc - Sbar))
    q_start = 1.0 - P.gamma * P.N / (P.beta * P.c0 * S_star)
    return {
        **const,
        "eta": eta,
        "Imax_background": Imax_background,
        "S_star": S_star,
        "Delta_t_formula": Delta_t,
        "q_start": q_start,
        "q_end": P.q0,
    }


def solve_flat_control(fit: InitialFit, eta: float | None = None) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """按三段理论过程求解情景一阈值控制。

    第一段：常规控制，直到 I(t)=eta。
    第二段：使用开环 q_c(t)，理论上维持 I(t)=eta 的平台期。
    第三段：S 到达 S_c 后回到常规控制，并继续求解到清零。
    """

    if eta is None:
        eta = P.eta
    details = compute_flat_thresholds(fit, eta)
    Sc = details["Sc"]
    Sbar = details["Sbar"]
    S_star = details["S_star"]

    y0 = np.array([fit.S0, fit.I0, 0.0, 0.0, 0.0, 0.0])

    def event_eta(t: float, y: np.ndarray) -> float:
        return y[1] - eta

    event_eta.terminal = True
    event_eta.direction = 1

    stage1 = solve_ivp(
        rhs_with_controls(c_background, q_background),
        (0.0, P.dynamic_horizon_limit),
        y0,
        events=event_eta,
        dense_output=True,
        rtol=1e-8,
        atol=1e-4,
    )
    if not stage1.success or len(stage1.t_events[0]) == 0:
        raise RuntimeError("Threshold-control stage 1 did not reach eta.")

    t1 = float(stage1.t_events[0][0])
    t2 = t1 + details["Delta_t_formula"]
    y1 = stage1.sol(t1)

    def S_threshold(t: float) -> float:
        """平台期内的理论易感者路径。"""

        return Sbar + (S_star - Sbar) * np.exp(-P.c0 * eta * (t - t1) / P.N)

    def q_control_time(t: float) -> float:
        """开环阈值控制律 q_c(t)。

        注意：这里使用的是预先计算好的时间函数 S_threshold(t)，
        而不是数值积分中的当前状态 y[0]。这样才能保持情景一
        理论推导中的开环控制结构。
        """

        if t < t1 or t > t2:
            return P.q0
        S_t = S_threshold(t)
        return 1.0 - P.gamma * P.N / (P.beta * P.c0 * S_t)

    def event_Sc(t: float, y: np.ndarray) -> float:
        return y[0] - Sc

    event_Sc.terminal = True
    event_Sc.direction = -1

    stage2 = solve_ivp(
        rhs_with_controls(c_background, q_control_time),
        (t1, t2),
        y1,
        events=event_Sc,
        dense_output=True,
        max_step=0.02,
        rtol=1e-8,
        atol=1e-4,
    )
    if not stage2.success:
        raise RuntimeError("Threshold-control stage 2 did not reach Sc.")

    reaches_Sc = len(stage2.t_events[0]) > 0
    t2_numeric = float(stage2.t_events[0][0]) if reaches_Sc else np.nan
    if not reaches_Sc:
        # 精确计算中 t2 应当与 S=Sc 重合；若事件定位器因舍入误差
        # 错过端点，则用解析 t2 作为后备值，保证流程继续运行。
        reaches_Sc = True
        t2_numeric = t2

    y2 = stage2.sol(t2_numeric)

    def event_clear(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_clear.terminal = True
    event_clear.direction = -1

    stage3, t_clear = solve_event_stage(
        c_background,
        q_background,
        t2_numeric,
        y2,
        event_clear,
        "Threshold-control clearance",
    )

    t, y = sample_solution_stages(
        [(0.0, t1, stage1.sol), (t1, t2_numeric, stage2.sol), (t2_numeric, t_clear, stage3.sol)]
    )

    df = frame_from_solution("情景一阈值控制", t, y, c_background, q_control_time)
    control_end_for_window = t2_numeric
    mask = (df["t"] >= t1) & (df["t"] <= control_end_for_window)
    details = {
        **details,
        "t1": t1,
        "t2_formula": t2,
        "t2_numeric": t2_numeric,
        "Delta_t_numeric": t2_numeric - t1,
        "reaches_Sc_within_horizon": float(reaches_Sc),
        "plateau_max_error": float(np.max(np.abs(df.loc[mask, "I"] - eta))),
        "q_min_control": float(df.loc[mask, "q"].min()),
        "q_max_control": float(df.loc[mask, "q"].max()),
    }
    return df, details


def summarize(
    df: pd.DataFrame,
    eta: float | None = None,
    control_start: float = 0.0,
    control_end: float = 0.0,
) -> Dict[str, float | str]:
    """计算论文中报告的一种策略的性能指标。"""

    if eta is None:
        eta = P.eta
    strategy = str(df["strategy"].iloc[0])
    t = df["t"].to_numpy()
    I = df["I"].to_numpy()
    Rt = df["Rt"].to_numpy()
    clear_time, cleared = epidemic_clear_time(df)
    outcome_end = clear_time
    active = t <= outcome_end + 1.0e-9
    crossing = np.where((Rt < 1.0) & active)[0]

    reduced_c = np.maximum(P.c0 - df["c"].to_numpy(), 0.0)
    enhanced_q = np.maximum(df["q"].to_numpy() - P.q0, 0.0)
    relative_c = reduced_c / P.c0
    relative_q = enhanced_q / (1.0 - P.q0)
    Cc = df["Cc"].to_numpy()
    Cq = df["Cq"].to_numpy()
    cum_community = interpolate_series(t, Cc, outcome_end)
    cum_quarantine = interpolate_series(t, Cq, outcome_end)
    cum_total = cum_community + cum_quarantine
    I_end = interpolate_series(t, I, outcome_end)
    S_end = interpolate_series(t, df["S"].to_numpy(), outcome_end)
    peak_idx = int(np.argmax(np.where(active, I, -np.inf)))
    return {
        "strategy": strategy,
        "peak_I": float(I[peak_idx]),
        "peak_time": float(t[peak_idx]),
        "time_above_eta": integrate_interval(t, (I > eta + 1.0e-5).astype(float), 0.0, outcome_end),
        "clear_time": float(clear_time),
        "cleared": float(cleared),
        "final_I": float(I_end),
        "final_S": float(S_end),
        "cum_community_infections": float(cum_community),
        "cum_quarantined_infections": float(cum_quarantine),
        "cum_total_infections": float(cum_total),
        "control_start": float(control_start),
        "control_end": float(control_end),
        "control_duration": float(max(control_end - control_start, 0.0)),
        "J_c": integrate_interval(t, relative_c, control_start, control_end),
        "J_q": integrate_interval(t, relative_q, control_start, control_end),
        "J": integrate_interval(t, DEFAULT_W_C * relative_c**2 + DEFAULT_W_Q * relative_q**2, control_start, control_end),
        "raw_c_cost": integrate_interval(t, reduced_c, control_start, control_end),
        "raw_q_cost": integrate_interval(t, enhanced_q, control_start, control_end),
        "first_Rt_below_1": float(t[crossing[0]]) if len(crossing) else np.nan,
    }


def write_latex_table(summary: pd.DataFrame) -> None:
    """写出西安对比文档中使用的主结果 LaTeX 表格。"""

    rows = []
    for _, row in summary.iterrows():
        rows.append(
            (
                f"{row['strategy']} & "
                f"{row['peak_I']:.0f} & "
                f"{row['control_start']:.2f} & "
                f"{row['control_end']:.2f} & "
                f"{row['control_duration']:.2f} & "
                f"{row['clear_time']:.2f} & "
                f"{row['cum_total_infections']:.0f} & "
                f"{row['J_c']:.2f} & "
                f"{row['J_q']:.2f} & "
                f"{row['J']:.2f} \\\\"
            )
        )
    content = "\n".join(
        [
            "\\begin{tabular}{lccccccccc}",
            "\\toprule",
            "控制策略 & $\\max I$ & $t_1$ & $t_2$ & 控制时长 & 清零时间 & $I_{t_{cum}}$ & $J_c$ & $J_q$ & $J$ \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "xian_control_comparison_results_table.tex").write_text(content, encoding="utf-8")


def write_fit_table(fit: InitialFit) -> None:
    """写出记录初始条件拟合结果的小型 LaTeX 表格。"""

    residual_labels = {
        "sqrt": "sqrt daily residual",
        "raw": "daily MSE",
        "weighted": "weighted daily MSE",
        "paper_mse": "MSE",
    }
    residual_label = residual_labels.get(fit.residual_type, fit.residual_type.replace("_", r"\_"))
    content = "\n".join(
        [
            "\\begin{tabular}{lc}",
            "\\toprule",
            "参数 & 估计值 \\\\",
            "\\midrule",
            f"$N$ & {P.N:.0f} \\\\",
            f"$S_0$ & {fit.S0:.4f} \\\\",
            f"$I_0$（有效感染种子） & {fit.I0:.6f} \\\\",
            f"$R(0)=N-S_0-I_0$ & {fit.R0_initial:.4f} \\\\",
            f"残差准则 & {residual_label} \\\\",
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "xian_initial_fit_table.tex").write_text(content, encoding="utf-8")


def plot_results(
    all_df: pd.DataFrame,
    observed: pd.DataFrame,
    flat_details: Dict[str, float],
    fit: InitialFit,
    eta: float | None = None,
) -> None:
    """生成观测数据和策略对比所需的主图组。"""

    if eta is None:
        eta = P.eta
    x_end = max(epidemic_clear_time(sub)[0] for _, sub in all_df.groupby("strategy", sort=False))
    x_end = max(x_end, float(observed["t"].iloc[-1]))

    def daily_cases_from_cumulative(sub: pd.DataFrame, cumulative_column: str, day_edges: np.ndarray) -> np.ndarray:
        """把连续累计感染量转换为按日新增量。"""

        values = np.interp(day_edges, sub["t"].to_numpy(), sub[cumulative_column].to_numpy())
        return np.maximum(np.diff(values), 0.0)

    def add_policy_markers(ax) -> None:
        """标记观测数据结束日、阈值控制开始时刻和阈值控制结束时刻。"""

        ax.axvline(
            observed["t"].iloc[-1],
            color=pps.COLORS["light_gray"],
            lw=0.8,
            linestyle=(0, (1.2, 2.0)),
            alpha=0.72,
            zorder=0,
        )
        ax.axvline(
            flat_details["t1"],
            color=pps.COLORS["dark_red"],
            lw=0.9,
            linestyle=(0, (3.0, 2.0)),
            alpha=0.32,
            zorder=0,
        )
        if np.isfinite(flat_details["t2_numeric"]):
            ax.axvline(
                flat_details["t2_numeric"],
                color=pps.COLORS["dark_red"],
                lw=0.9,
                linestyle=(0, (3.0, 2.0)),
                alpha=0.32,
                zorder=0,
            )

    def plot_strategy(
        ax,
        sub: pd.DataFrame,
        y_values: np.ndarray | pd.Series,
        x_values: np.ndarray | pd.Series | None = None,
        inset: bool = False,
    ) -> None:
        """按固定策略样式画一条曲线。"""

        strategy = str(sub["strategy"].iloc[0])
        spec = pps.STRATEGY_STYLES[strategy]
        linewidth = max(1.7, float(spec["linewidth"]) - 0.4) if inset else spec["linewidth"]
        if x_values is None:
            x_values = sub["t"]
        ax.plot(
            x_values,
            y_values,
            color=spec["color"],
            linestyle=spec["linestyle"],
            lw=linewidth,
            zorder=3,
        )

    def style_inset(ax) -> None:
        """用完整细边框区分线性插图与主面板。"""

        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.65)
            spine.set_color("#555555")
        ax.tick_params(which="both", labelsize=6.0, length=2.4, width=0.55, pad=1.5)

    with pps.paper_style_context():
        # 图 11：观测到的每日报告病例。
        fig_obs, ax_obs = plt.subplots(
            figsize=(0.78 * pps.TEXT_WIDTH_IN, 2.75),
            constrained_layout=True,
        )
        ax_obs.bar(
            observed["t"],
            observed["community_new"],
            color=pps.COLORS["coral"],
            width=0.86,
            edgecolor="white",
            linewidth=0.25,
            label=r"$I_{\rm new}(t)$",
            zorder=2,
        )
        ax_obs.bar(
            observed["t"],
            observed["quarantine_new"],
            bottom=observed["community_new"],
            color=pps.COLORS["sky"],
            width=0.86,
            edgecolor="white",
            linewidth=0.25,
            label=r"$I_{q_{\rm new}}(t)$",
            zorder=2,
        )
        pps.style_axis(ax_obs)
        ax_obs.set_xlabel(r"time $t$ (days)")
        ax_obs.set_ylabel("daily reported cases")
        ax_obs.set_xlim(-0.8, observed["t"].iloc[-1] + 0.8)
        ax_obs.set_ylim(0.0, 1.08 * float(observed["total_new"].max()))
        ax_obs.legend(loc="upper left", ncol=2, columnspacing=1.1)
        pps.save_figure(fig_obs, OUT_DIR / "xian_observed_daily_cases")
        plt.close(fig_obs)

        # 图 12：社区感染轨道、每日新增和控制函数。
        day_edges = np.arange(0.0, np.ceil(x_end) + 1.0)
        day_starts = day_edges[:-1]

        fig = plt.figure(
            figsize=(0.98 * pps.TEXT_WIDTH_IN, 6.10),
            constrained_layout=True,
        )
        gs = fig.add_gridspec(4, 2, height_ratios=[0.10, 1.12, 1.0, 1.0])
        ax_legend = fig.add_subplot(gs[0, :])
        ax_legend.axis("off")
        ax_legend.legend(
            handles=pps.strategy_handles(include_observed=True),
            loc="center",
            ncol=4,
            columnspacing=1.0,
            borderaxespad=0.0,
        )
        ax_I = fig.add_subplot(gs[1, :])
        ax_new = fig.add_subplot(gs[2, 0])
        ax_qnew = fig.add_subplot(gs[2, 1])
        ax_c = fig.add_subplot(gs[3, 0])
        ax_q = fig.add_subplot(gs[3, 1])

        # 线性插图保留 TDINN 与真实日报的低量级细节。
        ax_I_zoom = ax_I.inset_axes([0.665, 0.585, 0.305, 0.355])
        ax_new_zoom = ax_new.inset_axes([0.535, 0.535, 0.435, 0.405])
        ax_qnew_zoom = ax_qnew.inset_axes([0.535, 0.535, 0.435, 0.405])

        new_low_values: List[float] = [float(observed["community_new"].max())]
        qnew_low_values: List[float] = [float(observed["quarantine_new"].max())]
        new_all_values: List[float] = []
        qnew_all_values: List[float] = []

        for strategy, sub in all_df.groupby("strategy", sort=False):
            daily_new = daily_cases_from_cumulative(sub, "Cc", day_edges)
            daily_qnew = daily_cases_from_cumulative(sub, "Cq", day_edges)
            plot_strategy(ax_I, sub, sub["I"])
            plot_strategy(ax_new, sub, daily_new, x_values=day_starts)
            plot_strategy(ax_qnew, sub, daily_qnew, x_values=day_starts)
            plot_strategy(ax_c, sub, sub["c"])
            plot_strategy(ax_q, sub, sub["q"])

            new_all_values.append(float(np.max(daily_new)))
            qnew_all_values.append(float(np.max(daily_qnew)))
            if strategy == "TDINN控制":
                new_low_values.append(float(np.max(daily_new)))
                qnew_low_values.append(float(np.max(daily_qnew)))
                plot_strategy(ax_I_zoom, sub, sub["I"], inset=True)
                plot_strategy(ax_new_zoom, sub, daily_new, x_values=day_starts, inset=True)
                plot_strategy(ax_qnew_zoom, sub, daily_qnew, x_values=day_starts, inset=True)

        ax_new_zoom.scatter(
            observed["t"],
            observed["community_new"],
            s=18,
            color=pps.COLORS["coral"],
            edgecolors="white",
            linewidths=0.55,
            zorder=6,
        )
        ax_qnew_zoom.scatter(
            observed["t"],
            observed["quarantine_new"],
            s=18,
            color=pps.COLORS["coral"],
            edgecolors="white",
            linewidths=0.55,
            zorder=6,
        )

        ax_I.axhline(
            eta,
            color=pps.COLORS["gray"],
            lw=1.2,
            linestyle=(0, (4.5, 2.0, 1.2, 2.0)),
            zorder=1,
        )
        ax_I.text(
            0.985,
            1.10 * eta,
            r"$\eta$",
            transform=ax_I.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=7.4,
            color=pps.COLORS["gray"],
        )
        for ax in [ax_I, ax_I_zoom, ax_new, ax_new_zoom, ax_qnew, ax_qnew_zoom, ax_c, ax_q]:
            add_policy_markers(ax)
        for ax in [ax_I, ax_new, ax_qnew, ax_c, ax_q]:
            ax.set_xlim(0.0, x_end)
        for ax in [ax_I_zoom, ax_new_zoom, ax_qnew_zoom]:
            ax.set_xlim(0.0, min(x_end, 50.0))

        learned_peak = float(all_df.loc[all_df["strategy"] == "TDINN控制", "I"].max())
        I_full_peak = float(all_df["I"].max())
        for ax in [ax_I, ax_new, ax_qnew]:
            ax.set_yscale("log")
        ax_I.set_ylim(1.0, max(1.08 * I_full_peak, 1.25 * eta, 1.35 * learned_peak, 200.0))
        ax_new.set_ylim(1.0, max(80.0, 1.08 * max(new_all_values), 1.35 * max(new_low_values)))
        ax_qnew.set_ylim(1.0, max(180.0, 1.08 * max(qnew_all_values), 1.35 * max(qnew_low_values)))
        ax_I_zoom.set_ylim(0.0, max(200.0, 1.35 * learned_peak))
        ax_new_zoom.set_ylim(0.0, max(10.0, 1.35 * max(new_low_values)))
        ax_qnew_zoom.set_ylim(0.0, max(10.0, 1.35 * max(qnew_low_values)))

        for ax in [ax_I_zoom, ax_new_zoom, ax_qnew_zoom]:
            style_inset(ax)
        for ax, panel in zip([ax_I, ax_new, ax_qnew, ax_c, ax_q], ["(a)", "(b)", "(c)", "(d)", "(e)"]):
            pps.style_axis(ax, panel)
        for ax in [ax_I, ax_new, ax_qnew]:
            ax.tick_params(labelbottom=False)

        ax_I.set_ylabel(r"$I(t)$")
        ax_new.set_ylabel(r"$I_{\rm new}(t)$")
        ax_qnew.set_ylabel(r"$I_{q_{\rm new}}(t)$")
        ax_c.set_xlabel(r"time $t$ (days)")
        ax_c.set_ylabel(r"$c(t)$")
        ax_q.set_xlabel(r"time $t$ (days)")
        ax_q.set_ylabel(r"$q(t)$")
        pps.save_figure(fig, OUT_DIR / "xian_control_comparison_panels")
        plt.close(fig)

        # 图 13：累计感染。
        fig2 = plt.figure(
            figsize=(0.82 * pps.TEXT_WIDTH_IN, 5.40),
            constrained_layout=True,
        )
        gs2 = fig2.add_gridspec(4, 1, height_ratios=[0.10, 1.0, 1.0, 1.0])
        ax2_legend = fig2.add_subplot(gs2[0, 0])
        ax2_legend.axis("off")
        ax2_legend.legend(
            handles=pps.strategy_handles(include_observed=True),
            loc="center",
            ncol=4,
            columnspacing=0.9,
            borderaxespad=0.0,
        )
        axes = [
            fig2.add_subplot(gs2[1, 0]),
            fig2.add_subplot(gs2[2, 0]),
            fig2.add_subplot(gs2[3, 0]),
        ]
        cumulative_specs = [
            ("Cc", "community_cum", r"$I_{\rm cum}(t)$"),
            ("Cq", "quarantine_cum", r"$I_{q_{\rm cum}}(t)$"),
            (None, "total_cum", r"$I_{t_{\rm cum}}(t)$"),
        ]
        for ax, (model_col, observed_col, ylabel), panel in zip(
            axes,
            cumulative_specs,
            ["(a)", "(b)", "(c)"],
        ):
            y_max_values: List[float] = [float(observed[observed_col].max())]
            for _, sub in all_df.groupby("strategy", sort=False):
                y_values = sub["Cc"] + sub["Cq"] if model_col is None else sub[model_col]
                y_max_values.append(float(np.max(y_values)))
                plot_strategy(ax, sub, y_values)
            ax.scatter(
                observed["t"],
                observed[observed_col],
                s=14,
                color=pps.COLORS["coral"],
                edgecolors="white",
                linewidths=0.5,
                zorder=6,
            )
            ax.axvline(
                observed["t"].iloc[-1],
                color=pps.COLORS["light_gray"],
                lw=0.8,
                linestyle=(0, (1.2, 2.0)),
                alpha=0.72,
                zorder=0,
            )
            ax.set_xlim(0.0, x_end)
            ax.set_yscale("symlog", linthresh=100.0)
            ax.set_ylim(0.0, 1.15 * max(y_max_values))
            ax.set_ylabel(ylabel)
            pps.style_axis(ax, panel)
        axes[0].tick_params(labelbottom=False)
        axes[1].tick_params(labelbottom=False)
        axes[-1].set_xlabel(r"time $t$ (days)")
        pps.save_figure(fig2, OUT_DIR / "xian_control_cumulative")
        plt.close(fig2)

        # 图 14：有效再生数。
        fig_rt, ax_rt = plt.subplots(
            figsize=(0.82 * pps.TEXT_WIDTH_IN, 2.60),
            constrained_layout=True,
        )
        rt_max_values: List[float] = []
        for _, sub in all_df.groupby("strategy", sort=False):
            rt_max_values.append(float(np.max(sub["Rt"])))
            plot_strategy(ax_rt, sub, sub["Rt"])
        ax_rt.axhline(
            1.0,
            color=pps.COLORS["dark_red"],
            lw=1.25,
            linestyle=(0, (4.0, 2.0)),
            alpha=0.82,
            zorder=1,
        )
        ax_rt.text(
            0.985,
            1.05,
            r"$R_e(t)=1$",
            transform=ax_rt.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=7.4,
            color=pps.COLORS["dark_red"],
        )
        add_policy_markers(ax_rt)
        ax_rt.set_xlim(0.0, x_end)
        ax_rt.set_ylim(0.0, max(1.2, 1.08 * max(rt_max_values)))
        ax_rt.set_xlabel(r"time $t$ (days)")
        ax_rt.set_ylabel(r"$R_e(t)$")
        pps.style_axis(ax_rt)
        ax_rt.legend(
            handles=pps.strategy_handles(),
            loc="upper center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=3,
            columnspacing=1.1,
        )
        pps.save_figure(fig_rt, OUT_DIR / "xian_effective_reproduction_number")
        plt.close(fig_rt)


def write_eta_sensitivity_table(scan: pd.DataFrame) -> None:
    """写出 eta 敏感性分析的 LaTeX 表格。"""

    rows = []

    def eta_fraction_text(value: float) -> str:
        return f"{value:.4f}".rstrip("0").rstrip(".")

    for _, row in scan.iterrows():
        rows.append(
            f"{row['eta']:.0f} & {eta_fraction_text(row['eta_fraction'])} & "
            f"{row['t1']:.2f} & {row['t2_numeric']:.2f} & {row['flat_control_duration']:.2f} & "
            f"{row['q_start']:.4f} & {row['flat_J']:.2f} & "
            f"{row['flat_cum_total']:.0f} & {row['flat_clear_time']:.2f} \\\\"
        )
    content = "\n".join(
        [
            "\\begin{tabular}{ccccccccc}",
            "\\toprule",
            "$\\eta$ & $\\eta/N$ & $t_1$ & $t_2$ & 控制时长 & $q_c(t_1)$ & "
            "$J$ & $I_{t_{cum}}$ & 清零时间 \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "xian_eta_sensitivity_table.tex").write_text(content, encoding="utf-8")


def plot_eta_sensitivity(scan: pd.DataFrame, learned_summary: Dict[str, float | str]) -> None:
    """绘制情景一阈值控制随 eta 变化的敏感性结果。"""

    eta_percent = 100.0 * scan["eta_fraction"].to_numpy()
    threshold_color = pps.STRATEGY_STYLES["情景一阈值控制"]["color"]

    def set_eta_axis(ax) -> None:
        """统一使用 eta/N 的百分比对数轴，只标三个主要数量级。"""

        ax.set_xscale("log")
        ax.set_xlim(float(eta_percent.min() * 0.84), float(eta_percent.max() * 1.18))
        ax.set_xticks([0.01, 0.1, 1.0])
        ax.set_xticklabels(["0.01", "0.1", "1"])
        ax.set_xlabel(r"$\eta/N$ (%)")

    def label_tdinn_reference(ax, value: float) -> None:
        ax.text(
            0.97,
            1.06 * value,
            "TDINN",
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=6.8,
            color=pps.COLORS["navy"],
        )

    with pps.paper_style_context():
        fig, axes = plt.subplots(
            2,
            2,
            figsize=(0.95 * pps.TEXT_WIDTH_IN, 4.35),
            constrained_layout=True,
        )
        ax_q, ax_j, ax_cum, ax_time = axes.ravel()

        ax_q.plot(
            eta_percent,
            scan["q_start"],
            marker="o",
            color=threshold_color,
            lw=2.2,
            ms=3.8,
            markeredgewidth=0.0,
        )
        ax_q.set_ylabel(r"$q_c(t_1)$")

        actual_j = float(learned_summary["J"])
        ax_j.plot(
            eta_percent,
            scan["flat_J"],
            marker="o",
            color=threshold_color,
            lw=2.2,
            ms=3.8,
            markeredgewidth=0.0,
        )
        ax_j.axhline(
            actual_j,
            color=pps.COLORS["navy"],
            lw=1.3,
            linestyle=(0, (4.2, 2.0)),
        )
        ax_j.set_yscale("log")
        ax_j.set_ylabel(r"$J$")
        label_tdinn_reference(ax_j, actual_j)

        actual_cum = float(learned_summary["cum_total_infections"])
        ax_cum.plot(
            eta_percent,
            scan["flat_cum_total"],
            marker="o",
            color=threshold_color,
            lw=2.2,
            ms=3.8,
            markeredgewidth=0.0,
        )
        ax_cum.axhline(
            actual_cum,
            color=pps.COLORS["navy"],
            lw=1.3,
            linestyle=(0, (4.2, 2.0)),
        )
        ax_cum.set_yscale("log")
        ax_cum.set_ylabel(r"$I_{t_{\rm cum}}$")
        label_tdinn_reference(ax_cum, actual_cum)

        ax_time.plot(
            eta_percent,
            scan["flat_control_duration"],
            marker="o",
            color=threshold_color,
            lw=2.2,
            ms=3.8,
            markeredgewidth=0.0,
            label=r"$\Delta t$",
        )
        ax_time.plot(
            eta_percent,
            scan["flat_clear_time"],
            marker="s",
            color=pps.COLORS["blue"],
            lw=2.0,
            ms=3.5,
            markeredgewidth=0.0,
            label=r"$t_{\rm end}$",
        )
        actual_time = float(learned_summary["clear_time"])
        ax_time.axhline(
            actual_time,
            color=pps.COLORS["navy"],
            lw=1.3,
            linestyle=(0, (4.2, 2.0)),
        )
        not_cleared = scan["flat_cleared"].to_numpy() < 0.5
        if np.any(not_cleared):
            ax_time.scatter(
                eta_percent[not_cleared],
                scan.loc[not_cleared, "flat_clear_time"],
                marker="o",
                s=46,
                facecolors="none",
                edgecolors=pps.COLORS["blue"],
                linewidths=1.2,
                label="not cleared",
            )
        ax_time.set_yscale("log")
        ax_time.set_ylabel("time (days)")
        label_tdinn_reference(ax_time, actual_time)
        ax_time.legend(loc="upper right")

        for ax, panel in zip(axes.ravel(), ["(a)", "(b)", "(c)", "(d)"]):
            set_eta_axis(ax)
            pps.style_axis(ax, panel)
        pps.save_figure(fig, OUT_DIR / "xian_eta_sensitivity")
        plt.close(fig)


def run_eta_sensitivity(
    fit: InitialFit,
    learned_df: pd.DataFrame,
    fixed_df: pd.DataFrame,
) -> pd.DataFrame:
    """对 Parameters 中列出的所有 eta 值运行阈值控制敏感性分析。"""

    learned_clear_time, _ = epidemic_clear_time(learned_df)
    fixed_clear_time, _ = epidemic_clear_time(fixed_df)

    # TDINN控制和常规控制本身不随 eta 改变；
    #这里只重新计算它们相对于每个候选阈值的指标。
    learned_rows = {eta: summarize(learned_df, eta, 0.0, learned_clear_time) for eta in P.eta_values}
    fixed_rows = {eta: summarize(fixed_df, eta, 0.0, 0.0) for eta in P.eta_values}
    rows: List[Dict[str, float]] = []
    for eta_fraction, eta in zip(P.eta_fraction_values, P.eta_values):
        # 情景一阈值控制必须重新求解，因为 t1、平台期长度和
        # q_c(t) 都依赖 eta。
        flat_df, details = solve_flat_control(fit, eta)
        flat_clear_time, flat_cleared = epidemic_clear_time(flat_df)
        flat_control_end = details["t2_numeric"] if np.isfinite(details["t2_numeric"]) else flat_clear_time
        flat_summary = summarize(flat_df, eta, details["t1"], flat_control_end)
        rows.append(
            {
                "eta_fraction": eta_fraction,
                "eta": eta,
                "t1": details["t1"],
                "t2_formula": details["t2_formula"],
                "t2_numeric": details["t2_numeric"],
                "reaches_Sc_within_horizon": details["reaches_Sc_within_horizon"],
                "q_start": details["q_start"],
                "q_end_window": float(flat_df["q"].iloc[-1]),
                "q_max_window": float(flat_df["q"].max()),
                "plateau_max_error": details["plateau_max_error"],
                "flat_peak_I": float(flat_summary["peak_I"]),
                "flat_time_above_eta": float(flat_summary["time_above_eta"]),
                "flat_clear_time": float(flat_summary["clear_time"]),
                "flat_cleared": float(flat_cleared),
                "flat_control_duration": float(flat_summary["control_duration"]),
                "flat_cum_total": float(flat_summary["cum_total_infections"]),
                "flat_J_q": float(flat_summary["J_q"]),
                "flat_J": float(flat_summary["J"]),
                "real_peak_I": float(learned_rows[eta]["peak_I"]),
                "real_time_above_eta": float(learned_rows[eta]["time_above_eta"]),
                "real_clear_time": float(learned_rows[eta]["clear_time"]),
                "real_control_duration": float(learned_rows[eta]["control_duration"]),
                "real_cum_total": float(learned_rows[eta]["cum_total_infections"]),
                "real_J_q": float(learned_rows[eta]["J_q"]),
                "real_J": float(learned_rows[eta]["J"]),
                "fixed_peak_I": float(fixed_rows[eta]["peak_I"]),
                "fixed_time_above_eta": float(fixed_rows[eta]["time_above_eta"]),
                "fixed_clear_time": float(fixed_rows[eta]["clear_time"]),
                "fixed_cum_total": float(fixed_rows[eta]["cum_total_infections"]),
            }
        )
    scan = pd.DataFrame(rows)
    scan.to_csv(OUT_DIR / "xian_eta_sensitivity.csv", index=False, encoding="utf-8-sig")
    write_eta_sensitivity_table(scan)
    plot_eta_sensitivity(scan, summarize(learned_df, P.eta, 0.0, learned_clear_time))
    return scan


def main() -> None:
    """西安对比结果的主生成流程。"""

    # 1. 数据准备和单参数初始条件校准。
    observed = load_observed_data()
    fit = fit_initial_conditions(observed, residual_type="paper_mse")

    # 2. 求解三种对比策略。
    learned_df = solve_time_control("TDINN控制", fit, lambda t: float(c_real(t)), lambda t: float(q_real(t)))
    flat_df, flat_details = solve_flat_control(fit)
    fixed_df = solve_time_control("常规控制", fit, c_background, q_background)
    learned_clear_time, learned_cleared = epidemic_clear_time(learned_df)
    flat_control_end = flat_details["t2_numeric"]

    # 3. 生成辅助 eta 敏感性分析输出。
    eta_scan = run_eta_sensitivity(fit, learned_df, fixed_df)

    # 4. 保存可复用的数值轨道和处理后的观测数据。
    all_df = pd.concat([learned_df, flat_df, fixed_df], ignore_index=True)
    all_df.to_csv(OUT_DIR / "xian_control_comparison_timeseries.csv", index=False, encoding="utf-8-sig")
    observed.to_csv(OUT_DIR / "xian_observed_data_processed.csv", index=False, encoding="utf-8-sig")

    # 5. 保存汇总指标、LaTeX 表格和图。
    summary = pd.DataFrame(
        [
            summarize(learned_df, P.eta, 0.0, learned_clear_time),
            summarize(flat_df, P.eta, flat_details["t1"], flat_control_end),
            summarize(fixed_df, P.eta, 0.0, 0.0),
        ]
    )
    summary.to_csv(OUT_DIR / "xian_control_comparison_summary.csv", index=False, encoding="utf-8-sig")
    write_latex_table(summary)
    write_fit_table(fit)
    plot_results(all_df, observed, flat_details, fit)

    # 6. 记录详细标量诊断量，方便后续核查。
    details: Dict[str, float | str] = {
        "N": P.N,
        "beta": P.beta,
        "gamma": P.gamma,
        "delta_q": P.delta_q,
        "c0": P.c0,
        "q0": P.q0,
        "eta": P.eta,
        "eta_fraction": P.eta_fraction,
        "learned_clear_time": learned_clear_time,
        "learned_cleared": float(learned_cleared),
        "fit_removed_initial": str(P.fit_removed_initial),
        "S0_fit": fit.S0,
        "I0_fit": fit.I0,
        "R0_initial_fit": fit.R0_initial,
        "fit_objective": fit.objective,
        **flat_details,
        "data_start": observed["date"].iloc[0].strftime("%Y-%m-%d"),
        "data_end": observed["date"].iloc[-1].strftime("%Y-%m-%d"),
        "data_days": len(observed),
        "observed_community_cases": float(observed["community_new"].sum()),
        "observed_quarantine_cases": float(observed["quarantine_new"].sum()),
        "observed_total_cases": float(observed["total_new"].sum()),
        "eta_scan_min": float(eta_scan["eta"].min()),
        "eta_scan_max": float(eta_scan["eta"].max()),
    }
    details_lines = []
    for key, value in details.items():
        if isinstance(value, str):
            details_lines.append(f"{key},{value}")
        else:
            details_lines.append(f"{key},{float(value):.12g}")
    (OUT_DIR / "xian_flat_control_details.csv").write_text(
        "metric,value\n" + "\n".join(details_lines) + "\n",
        encoding="utf-8",
    )

    print("Generated:")
    for name in [
        "xian_control_comparison_timeseries.csv",
        "xian_observed_data_processed.csv",
        "xian_control_comparison_summary.csv",
        "xian_flat_control_details.csv",
        "xian_initial_fit_table.tex",
        "xian_control_comparison_results_table.tex",
        "xian_eta_sensitivity.csv",
        "xian_eta_sensitivity_table.tex",
        "xian_eta_sensitivity.pdf",
        "xian_observed_daily_cases.pdf",
        "xian_control_comparison_panels.pdf",
        "xian_control_cumulative.pdf",
        "xian_effective_reproduction_number.pdf",
    ]:
        print(f"  {OUT_DIR / name}")


if __name__ == "__main__":
    main()
