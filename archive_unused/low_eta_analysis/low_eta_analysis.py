"""西安情景一阈值控制的低阈值压力测试。

本脚本刻意独立于主西安比较脚本，所有输出都写入 low_eta_analysis
文件夹，避免覆盖论文主结果。它只回答一个问题：

    如果为了让控制更早启动而降低医疗阈值 eta，
    控制时长、清零时间和控制成本会增加多少？

注意：这里的低阈值实验是补充分析，不是论文主基准。论文主基准仍是
eta = 0.002N = 26326。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))

import xian_control_comparison as xcc  # noqa: E402


OUT_DIR = HERE

# 单独绘制“图 2 风格”面板的代表性阈值。
# 100 是极端低阈值；520 和 1300 对应 ICU 床位数的低口径和扩容口径；
# 5000、13163 用于观察从极低阈值向主基准 26326 过渡时的变化。
PANEL_ETAS = [100.0, 520.0, 1300.0, 5000.0, 13163.0]

# 阈值敏感性扫描点。这里刻意在低阈值区域取点更密，
# 因为低阈值下控制时长变化最剧烈。
SCAN_ETAS = [
    100.0,
    300.0,
    520.0,
    1000.0,
    1300.0,
    2600.0,
    3200.0,
    5000.0,
    6500.0,
    10000.0,
    13163.0,
    15000.0,
    20000.0,
    26326.0,
]

# 面板主图只展示前 120 天，避免 eta 很低时两万多天的平台期压扁前期曲线。
PANEL_X_END = 120.0

# 内嵌小图只展示前 50 天，用来观察 TDINN、阈值控制和真实日报数据的早期差异。
ZOOM_X_END = 50.0


def solve_threshold_fast(fit: xcc.InitialFit, eta: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """使用解析平台段快速生成情景一阈值控制轨迹。

    主脚本中的 solve_flat_control 会在平台期用很小步长积分，用于主基准
    eta=26326 时没有问题。但低阈值（例如 eta=100）会导致平台期长达
    两万多天，如果仍按 0.02 天步长积分会非常慢。

    因此这里保留同一个理论控制律 q_c(t)，但平台期直接使用解析公式：

        S(t) = Sbar + (S_star - Sbar) exp[-c0 eta (t-t1)/N]
        I(t) = eta

    同时用解析积分得到累计社区感染 Cc 和累计隔离感染 Cq。
    这样既符合理论推导，又能高效生成低阈值压力测试图表。
    """

    details = xcc.compute_flat_thresholds(fit, eta)
    sbar = details["Sbar"]
    s_star = details["S_star"]
    y0 = np.array([fit.S0, fit.I0, 0.0, 0.0, 0.0, 0.0])

    # 第一阶段：常规控制，直到 I(t) 第一次达到 eta。
    def event_eta(t: float, y: np.ndarray) -> float:
        return y[1] - eta

    event_eta.terminal = True
    event_eta.direction = 1
    stage1 = solve_ivp(
        xcc.rhs_with_controls(xcc.c_background, xcc.q_background),
        (0.0, xcc.P.dynamic_horizon_limit),
        y0,
        events=event_eta,
        dense_output=True,
        rtol=1.0e-8,
        atol=1.0e-4,
    )
    if not stage1.success or len(stage1.t_events[0]) == 0:
        raise RuntimeError(f"Threshold eta={eta:g} was not reached.")

    t1 = float(stage1.t_events[0][0])
    y1 = stage1.sol(t1)
    t2 = t1 + details["Delta_t_formula"]
    k = xcc.P.c0 * eta / xcc.P.N
    a = s_star - sbar

    # 第二阶段：理论平台期。这里不再对完整 ODE 做密集积分，而是用解析式。
    def s_threshold(t: np.ndarray | float) -> np.ndarray:
        tau = np.asarray(t, dtype=float) - t1
        return sbar + a * np.exp(-k * tau)

    def q_threshold(t: np.ndarray | float) -> np.ndarray:
        # 开环控制律 q_c(t)，只依赖理论时间函数 S_threshold(t)，不是状态反馈。
        s_t = s_threshold(t)
        return 1.0 - xcc.P.gamma * xcc.P.N / (xcc.P.beta * xcc.P.c0 * s_t)

    def cc_stage2(t: np.ndarray | float) -> np.ndarray:
        # 平台期满足 dI/dt=0，因此每日新增社区感染率等于 gamma * eta。
        tau = np.asarray(t, dtype=float) - t1
        return y1[4] + xcc.P.gamma * eta * tau

    def cq_stage2(t: np.ndarray | float) -> np.ndarray:
        # 隔离区新增由 beta*c0*q(t)*S(t)*eta/N 给出。
        # 将 q_c(t) 和 S_threshold(t) 代入后可以直接积分。
        tau = np.asarray(t, dtype=float) - t1
        beta_c_integral = xcc.P.beta * xcc.P.c0 * eta / xcc.P.N * (
            sbar * tau + a * (1.0 - np.exp(-k * tau)) / k
        )
        return y1[5] + beta_c_integral - xcc.P.gamma * eta * tau

    y2 = np.array([float(s_threshold(t2)), eta, 0.0, 0.0, float(cc_stage2(t2)), float(cq_stage2(t2))])

    # 第三阶段：平台结束后回到常规控制，继续积分到 I(t)<=1。
    def event_clear(t: float, y: np.ndarray) -> float:
        return y[1] - 1.0

    event_clear.terminal = True
    event_clear.direction = -1
    stage3 = solve_ivp(
        xcc.rhs_with_controls(xcc.c_background, xcc.q_background),
        (t2, t2 + 50000.0),
        y2,
        events=event_clear,
        dense_output=True,
        rtol=1.0e-8,
        atol=1.0e-4,
    )
    if not stage3.success or len(stage3.t_events[0]) == 0:
        raise RuntimeError(f"Threshold eta={eta:g} did not clear within the fallback horizon.")

    t_clear = float(stage3.t_events[0][0])

    # 第一阶段较短，保留主脚本的细步长采样。
    t_stage1 = np.linspace(0.0, t1, max(4, int(np.ceil(t1 / xcc.P.dt)) + 1))
    y_stage1 = stage1.sol(t_stage1)

    # 平台期可能很长，只需日尺度采样即可支撑组会图和敏感性表。
    t_stage2_inner = np.arange(np.ceil(t1), np.floor(t2) + 1.0, 1.0)
    t_stage2_inner = t_stage2_inner[(t_stage2_inner > t1) & (t_stage2_inner < t2)]
    t_stage2 = np.r_[t1, t_stage2_inner, t2]
    s2 = s_threshold(t_stage2)
    i2 = np.full_like(t_stage2, eta, dtype=float)
    cc2 = cc_stage2(t_stage2)
    cq2 = cq_stage2(t_stage2)
    q2 = q_threshold(t_stage2)
    y_stage2 = np.vstack([s2, i2, np.full_like(t_stage2, np.nan), np.full_like(t_stage2, np.nan), cc2, cq2])

    # 第三阶段也用日尺度采样，减少输出文件体积。
    t_stage3_inner = np.arange(np.ceil(t2), np.floor(t_clear) + 1.0, 1.0)
    t_stage3_inner = t_stage3_inner[(t_stage3_inner > t2) & (t_stage3_inner < t_clear)]
    t_stage3 = np.r_[t2, t_stage3_inner, t_clear]
    y_stage3 = stage3.sol(t_stage3)

    def frame(strategy: str, t: np.ndarray, y: np.ndarray, c_values: np.ndarray, q_values: np.ndarray) -> pd.DataFrame:
        # 统一整理成和主脚本一致的长表结构，便于复用 summarize 和绘图逻辑。
        rt = xcc.P.beta * c_values * (1.0 - q_values) * y[0] / (xcc.P.gamma * xcc.P.N)
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
                "Rt": rt,
            }
        )

    df = pd.concat(
        [
            frame("情景一阈值控制", t_stage1, y_stage1, np.full_like(t_stage1, xcc.P.c0), np.full_like(t_stage1, xcc.P.q0)),
            frame("情景一阈值控制", t_stage2[1:], y_stage2[:, 1:], np.full_like(t_stage2[1:], xcc.P.c0), q2[1:]),
            frame("情景一阈值控制", t_stage3[1:], y_stage3[:, 1:], np.full_like(t_stage3[1:], xcc.P.c0), np.full_like(t_stage3[1:], xcc.P.q0)),
        ],
        ignore_index=True,
    )
    details.update(
        {
            "t1": t1,
            "t2_formula": t2,
            "t2_numeric": t2,
            "Delta_t_numeric": t2 - t1,
            "reaches_Sc_within_horizon": 1.0,
            "plateau_max_error": float(np.nanmax(np.abs(df.loc[(df["t"] >= t1) & (df["t"] <= t2), "I"] - eta))),
            "q_min_control": float(np.nanmin(q2)),
            "q_max_control": float(np.nanmax(q2)),
        }
    )
    return df, details


def daily_cases(sub: pd.DataFrame, column: str, day_edges: np.ndarray) -> np.ndarray:
    """由累计变量差分得到每日新增病例数。"""

    values = np.interp(day_edges, sub["t"].to_numpy(), sub[column].to_numpy())
    return np.maximum(np.diff(values), 0.0)


def plot_panel(
    eta: float,
    all_df: pd.DataFrame,
    observed: pd.DataFrame,
    threshold_summary: pd.Series,
    output_stem: str,
) -> None:
    """绘制一个阈值下的“图 2 风格”对比面板。

    该图只展示前 PANEL_X_END 天。完整的控制时长、清零时间和累计感染
    已经保存在表格中。这样做是为了避免低阈值超长平台期压缩前期曲线。
    """

    colors = {"TDINN控制": "#0068a9", "情景一阈值控制": "#c43c39", "常规控制": "#333333"}
    labels = {"TDINN控制": "TDINN control", "情景一阈值控制": "Threshold control", "常规控制": "Routine control"}
    styles = {"TDINN控制": "-", "情景一阈值控制": "--", "常规控制": ":"}
    day_edges = np.arange(0.0, np.ceil(PANEL_X_END) + 1.0)
    day_starts = day_edges[:-1]
    t1 = float(threshold_summary["control_start"])

    def add_markers(ax) -> None:
        # 灰色虚线是真实日报数据最后一天；红线是阈值控制启动时间 t1。
        # t2 对低阈值往往非常靠后，不画在截断主图中。
        ax.axvline(float(observed["t"].iloc[-1]), color="#999999", lw=1.0, linestyle=":", alpha=0.75)
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

        # 内嵌小图重点比较 TDINN 和阈值控制，并叠加真实日报点。
        # 常规控制峰值太高，放进 inset 会压扁低量级曲线。
        if strategy in {"TDINN控制", "情景一阈值控制"}:
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
    ax_i_zoom.axhline(eta, color="#777777", lw=1.0, linestyle="-.")

    for ax in [ax_i, ax_i_zoom, ax_new, ax_new_zoom, ax_qnew, ax_qnew_zoom, ax_c, ax_q]:
        add_markers(ax)
    for ax in [ax_i, ax_new, ax_qnew, ax_c, ax_q]:
        ax.set_xlim(0.0, PANEL_X_END)
    for ax in [ax_i_zoom, ax_new_zoom, ax_qnew_zoom]:
        ax.set_xlim(0.0, ZOOM_X_END)
        ax.set_title("zoom", fontsize=8, pad=2)
        ax.tick_params(labelsize=8)
    for ax in [ax_i, ax_new, ax_qnew]:
        ax.set_yscale("log")

    learned_peak = float(all_df.loc[all_df["strategy"].eq("TDINN控制"), "I"].max())
    visible_i_peak = float(all_df.loc[all_df["t"].le(PANEL_X_END), "I"].max())
    ax_i.set_ylim(1.0, max(1.08 * visible_i_peak, 1.35 * learned_peak, 1.25 * eta, 200.0))
    ax_i_zoom.set_ylim(0.0, max(200.0, 1.35 * learned_peak, 1.2 * eta))
    ax_new.set_ylim(1.0, max(80.0, 1.08 * max(new_all_values), 1.35 * max(new_low_values)))
    ax_qnew.set_ylim(1.0, max(180.0, 1.08 * max(qnew_all_values), 1.35 * max(qnew_low_values)))
    ax_new_zoom.set_ylim(0.0, max(10.0, 1.35 * max(new_low_values)))
    ax_qnew_zoom.set_ylim(0.0, max(10.0, 1.35 * max(qnew_low_values)))

    ax_i.set_title(f"Community infections, eta={eta:g}")
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

    fig.savefig(OUT_DIR / f"{output_stem}.pdf")
    fig.savefig(OUT_DIR / f"{output_stem}.png", dpi=220)
    plt.close(fig)


def write_summary_table(summary: pd.DataFrame) -> None:
    """写出低阈值扫描的 LaTeX 表格。"""

    rows = []
    for _, row in summary.iterrows():
        rows.append(
            f"{row['eta']:.0f} & {row['t1']:.2f} & {row['t2']:.2f} & "
            f"{row['control_duration']:.2f} & {row['clear_time']:.2f} & "
            f"{row['peak_I']:.0f} & {row['cum_total_infections']:.0f} & "
            f"{row['J_q']:.2f} & {row['J']:.2f} \\\\"
        )
    content = "\n".join(
        [
            "\\begin{tabular}{ccccccccc}",
            "\\toprule",
            "$\\eta$ & $t_1$ & $t_2$ & 控制时长 & 清零时间 & $\\max I$ & $I_{t_{cum}}$ & $J_q$ & $J$ \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    (OUT_DIR / "low_eta_summary_table.tex").write_text(content, encoding="utf-8")


def safe_to_csv(df: pd.DataFrame, path: Path) -> Path:
    """写出 CSV；若目标文件被占用，则写入带时间戳的副本。"""

    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
    except PermissionError:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        fallback = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        df.to_csv(fallback, index=False, encoding="utf-8-sig")
        print(f"Warning: {path.name} is locked; wrote {fallback.name} instead.")
        return fallback


def threshold_crossing_eta(summary: pd.DataFrame, column: str, target: float) -> float:
    """在 log10(eta) 尺度上插值得到指标降到 target 以下的近似阈值。"""

    data = summary.sort_values("eta")
    eta = data["eta"].to_numpy(dtype=float)
    values = data[column].to_numpy(dtype=float)
    for i in range(len(eta) - 1):
        y0 = values[i] - target
        y1 = values[i + 1] - target
        if y0 == 0:
            return float(eta[i])
        if y0 * y1 <= 0:
            log_eta0 = np.log10(eta[i])
            log_eta1 = np.log10(eta[i + 1])
            if values[i + 1] == values[i]:
                return float(eta[i])
            log_eta = log_eta0 + (target - values[i]) * (log_eta1 - log_eta0) / (values[i + 1] - values[i])
            return float(10.0**log_eta)
    if values[-1] <= target:
        return float(eta[-1])
    return float("nan")


def add_reasonable_region_background(summary: pd.DataFrame, axes: np.ndarray) -> None:
    """按控制时间和清零时间给低阈值敏感性图添加区间底色。"""

    eta_min = float(summary["eta"].min())
    eta_max = float(summary["eta"].max())
    acceptable_start = max(
        threshold_crossing_eta(summary, "control_duration", 1095.0),
        threshold_crossing_eta(summary, "clear_time", 1095.0),
    )
    preferred_start = max(
        threshold_crossing_eta(summary, "control_duration", 365.0),
        threshold_crossing_eta(summary, "clear_time", 365.0),
    )

    for ax in axes.ravel():
        ax.axvspan(eta_min, acceptable_start, color="#efefef", alpha=0.85, zorder=0)
        ax.axvspan(acceptable_start, preferred_start, color="#fff2bf", alpha=0.65, zorder=0)
        ax.axvspan(preferred_start, eta_max, color="#dcefd8", alpha=0.65, zorder=0)


def draw_sensitivity(summary: pd.DataFrame, output_stem: str, show_regions: bool) -> None:
    """绘制低阈值敏感性图。"""

    eta = summary["eta"].to_numpy()
    fig, axes = plt.subplots(2, 3, figsize=(14.0, 8.2), constrained_layout=True)
    ax_t1, ax_duration, ax_clear, ax_q, ax_cost, ax_cum = axes.ravel()

    if show_regions:
        add_reasonable_region_background(summary, axes)

    ax_t1.plot(eta, summary["t1"], "o-", color="#0068a9", lw=2.0)
    ax_t1.set_ylabel(r"$t_1$")

    ax_duration.plot(eta, summary["control_duration"], "o-", color="#c43c39", lw=2.0)
    ax_duration.set_ylabel("control duration")
    ax_duration.set_yscale("log")
    if show_regions:
        ax_duration.axhline(365.0, color="#777777", lw=1.0, linestyle=":", alpha=0.8)
        ax_duration.axhline(1095.0, color="#777777", lw=1.0, linestyle="--", alpha=0.8)

    ax_clear.plot(eta, summary["clear_time"], "o-", color="#7a7a7a", lw=2.0)
    ax_clear.set_ylabel("clear time")
    ax_clear.set_yscale("log")
    if show_regions:
        ax_clear.axhline(365.0, color="#777777", lw=1.0, linestyle=":", alpha=0.8)
        ax_clear.axhline(1095.0, color="#777777", lw=1.0, linestyle="--", alpha=0.8)

    ax_q.plot(eta, summary["q_start"], "o-", color="#c43c39", lw=2.0)
    ax_q.set_ylabel(r"$q_c(t_1)$")

    ax_cost.plot(eta, summary["J_q"], "o-", color="#c43c39", lw=2.0, label=r"$J_q$")
    ax_cost.plot(eta, summary["J"], "s--", color="#0068a9", lw=1.8, label=r"$J$")
    ax_cost.set_ylabel("control cost")
    ax_cost.set_yscale("log")
    ax_cost.legend(loc="best", fontsize=8)

    ax_cum.plot(eta, summary["cum_total_infections"], "o-", color="#444444", lw=2.0)
    ax_cum.set_ylabel(r"$I_{t_{cum}}$")

    for ax in axes.ravel():
        ax.set_xscale("log")
        ax.set_xlabel(r"$\eta$")
        # 520 和 1300 是 ICU 床位直接作为社区感染者阈值时的两个参考点；
        # 26326 是论文主基准 eta=0.002N。
        ax.axvline(520, color="#999999", lw=1.0, linestyle=":", alpha=0.8)
        ax.axvline(1300, color="#999999", lw=1.0, linestyle=":", alpha=0.8)
        ax.axvline(26326, color="#777777", lw=1.0, linestyle="--", alpha=0.7)
        ax.grid(False)
    fig.savefig(OUT_DIR / f"{output_stem}.pdf")
    fig.savefig(OUT_DIR / f"{output_stem}.png", dpi=220)
    plt.close(fig)


def plot_sensitivity(summary: pd.DataFrame) -> None:
    """绘制低阈值敏感性图。

    重点展示：eta 降低时，t1 只小幅提前，但控制时长、清零时间和控制成本
    会按数量级放大。
    """

    draw_sensitivity(summary, "low_eta_sensitivity", show_regions=False)
    draw_sensitivity(summary, "low_eta_sensitivity_regions", show_regions=True)


def write_notes(summary: pd.DataFrame) -> None:
    """写出组会展示用的简短说明。"""

    row100 = summary.loc[summary["eta"].eq(100.0)].iloc[0]
    row_base = summary.loc[summary["eta"].eq(26326.0)].iloc[0]
    text = f"""# Low-threshold stress-test notes

Purpose: answer whether simply lowering the threshold solves the late-start problem.

Main finding: lowering eta starts control earlier and lowers the peak, but the gain in start time is small compared with the increase in control duration and clearance time.

Key comparison:

- eta=26326: t1={row_base['t1']:.2f}, control duration={row_base['control_duration']:.2f}, clear time={row_base['clear_time']:.2f}.
- eta=100: t1={row100['t1']:.2f}, control duration={row100['control_duration']:.2f}, clear time={row100['clear_time']:.2f}.

Interpretation:

- Lower eta means the threshold is reached earlier, so t1 decreases.
- But the platform phase holds I(t)=eta. When eta is very low, S(t) is depleted very slowly.
- The theoretical duration contains a leading 1/eta factor, so low eta quickly creates unrealistic control times.
- Therefore lowering the capacity threshold is not a sufficient fix. A better extension is to keep a capacity threshold eta_cap and introduce an earlier warning threshold eta_warn < eta_cap.
"""
    (OUT_DIR / "notes.md").write_text(text, encoding="utf-8")


def main() -> None:
    """生成全部低阈值分析输出。"""

    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False, "mathtext.fontset": "dejavusans"})

    observed = xcc.load_observed_data()
    fit = xcc.fit_initial_conditions(observed)
    learned_df = xcc.solve_time_control("TDINN控制", fit, xcc.c_real, xcc.q_real)
    routine_df = xcc.solve_time_control("常规控制", fit, xcc.c_background, xcc.q_background)
    learned_clear = xcc.epidemic_clear_time(learned_df)[0]

    scan_rows = []
    panel_cache: Dict[float, pd.DataFrame] = {}
    panel_summary: Dict[float, pd.DataFrame] = {}
    # 逐个阈值求解情景一，并收集敏感性表格指标。
    for eta in SCAN_ETAS:
        flat_df, details = solve_threshold_fast(fit, eta)
        flat_summary = xcc.summarize(flat_df, eta, details["t1"], details["t2_numeric"])
        scan_rows.append(
            {
                "eta": eta,
                "eta_fraction": eta / xcc.P.N,
                "t1": details["t1"],
                "t2": details["t2_numeric"],
                "control_duration": flat_summary["control_duration"],
                "clear_time": flat_summary["clear_time"],
                "peak_I": flat_summary["peak_I"],
                "cum_total_infections": flat_summary["cum_total_infections"],
                "J_q": flat_summary["J_q"],
                "J": flat_summary["J"],
                "q_start": details["q_start"],
                "q_min_control": details["q_min_control"],
                "q_max_control": details["q_max_control"],
            }
        )
        # 只对代表性阈值保存完整轨迹和图 2 风格面板，避免输出过多。
        if eta in PANEL_ETAS:
            panel_cache[eta] = flat_df
            panel_summary[eta] = pd.DataFrame(
                [
                    xcc.summarize(learned_df, eta, 0.0, learned_clear),
                    flat_summary,
                    xcc.summarize(routine_df, eta, 0.0, 0.0),
                ]
            )

    summary = pd.DataFrame(scan_rows)
    safe_to_csv(summary, OUT_DIR / "low_eta_summary.csv")
    write_summary_table(summary)
    plot_sensitivity(summary)
    write_notes(summary)

    for eta in PANEL_ETAS:
        all_df = pd.concat([learned_df, panel_cache[eta], routine_df], ignore_index=True)
        safe_to_csv(all_df, OUT_DIR / f"timeseries_eta{int(eta)}.csv")
        safe_to_csv(panel_summary[eta], OUT_DIR / f"summary_eta{int(eta)}.csv")
        plot_panel(eta, all_df, observed, panel_summary[eta].loc[panel_summary[eta]["strategy"].eq("情景一阈值控制")].iloc[0], f"panels_eta{int(eta)}")

    print("Generated low-threshold analysis outputs in:")
    print(OUT_DIR)
    for name in [
        "low_eta_summary.csv",
        "low_eta_summary_table.tex",
        "low_eta_sensitivity.pdf",
        "low_eta_sensitivity.png",
        "low_eta_sensitivity_regions.pdf",
        "low_eta_sensitivity_regions.png",
        "notes.md",
    ]:
        print(f"  {OUT_DIR / name}")


if __name__ == "__main__":
    main()
