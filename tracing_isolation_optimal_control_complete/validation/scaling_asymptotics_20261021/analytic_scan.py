"""D4：无回流模型的 80 位解析量级扫描；不求解 ODE 或 OCP。

运行：python validation/scaling_asymptotics_20261021/analytic_scan.py
从项目目录运行，或使用脚本绝对路径。输出始终写在脚本所在目录。
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


mp.mp.dps = 80
OUT = Path(__file__).resolve().parent
TOL = mp.mpf("1e-65")
COUNTS = {"geometry_cases": 0, "comparable_cases": 0, "masked_cases": 0}
RESIDUALS = {"scalar_relative": mp.mpf(0), "endpoint_relative": mp.mpf(0),
             "theta_relative": mp.mpf(0), "cost_difference_relative": mp.mpf(0)}


def dec(value):
    """精确输入和保留精度的 JSON；不得先转成二进制浮点输入。"""
    return mp.mpf(str(value))


def serial(value):
    if isinstance(value, mp.mpf):
        return mp.nstr(value, 72)
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(item) for item in value]
    return value


def write_json(name, value):
    (OUT / name).write_text(json.dumps(serial(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def geometry(beta, c, gamma, K):
    beta, c, gamma, K = map(dec, (beta, c, gamma, K))
    h = gamma / (beta * c)
    ell, p, k = beta * h, (1 - beta) * h, K / h

    def reduced(x):
        # z=h(1+x)，A=x-ln(1+x)，u=s_B/h-1。
        A = x - mp.log1p(x)
        u = mp.expm1(mp.log1p(x) + A / beta)
        return A * (beta + x) * u / (beta * (u - x)) - k

    x = mp.findroot(reduced, (k * beta / 10, k / beta), solver="anderson",
                    tol=mp.mpf("1e-78"), maxsteps=300)
    A = x - mp.log1p(x)
    u = mp.expm1(mp.log1p(x) + A / beta)
    s_B, s_bar, i_bar = h * (1 + u), h * (1 + x), K - h * A
    if not (h < s_bar < s_B and 0 < i_bar < K):
        raise AssertionError("安全端点或切换次序失效")

    def boundary_cost(hi, lo):
        return beta / (K * (1 - beta)) * (mp.log1p((hi - lo) / lo) -
                                           beta * mp.log1p((hi - lo) / (lo - p)))

    def boundary_time(hi, lo):
        return mp.log((hi - p) / (lo - p)) / (c * K)

    log_infection_ratio = -mp.log1p(-h * A / K)
    W = log_infection_ratio / h
    T_full = log_infection_ratio / gamma
    # 只减去公共容量尾段，且整个消去过程均在 80 位进行。
    tail_cost = beta / (K * (1 - beta)) * (mp.log1p(u) - beta * mp.log1p(u / beta))
    Delta_J = tail_cost - W
    Delta_T = mp.log1p(u / beta) / (c * K) - T_full
    Theta = lambda s, i: (s - h) / (i * (s - p))
    endpoint_res = (i_bar - ell * mp.log(s_bar)) - (K - ell * mp.log(s_B))
    residuals = {
        "scalar_relative": abs(reduced(x)) / k,
        "endpoint_relative": abs(endpoint_res) / max(K, ell),
        "theta_relative": abs(Theta(s_bar, i_bar) / Theta(s_B, K) - 1),
    }
    for key, value in residuals.items():
        RESIDUALS[key] = max(RESIDUALS[key], value)
        assert value < TOL, (key, value)
    assert Delta_J > 0 and Delta_T > 0
    COUNTS["geometry_cases"] += 1
    return dict(beta=beta, c=c, gamma=gamma, K=K, h=h, ell=ell, p=p,
                s_B=s_B, s_bar=s_bar, i_bar=i_bar, exit_gap=s_B - h,
                Delta_J=Delta_J, Delta_T=Delta_T, W=W, T_full=T_full,
                boundary_cost=boundary_cost, boundary_time=boundary_time,
                residuals=residuals)


def natural_entry(P, s0, i0):
    s0, i0 = map(dec, (s0, i0))
    h, K = P["h"], P["K"]
    if not (0 < i0 <= K and 0 < s0 and s0 + i0 <= 1):
        raise ValueError("初值不满足 0<i0<=K、物理总量约束")
    if i0 == K and s0 > h:
        return s0
    peak = i0 + s0 - h + h * mp.log(h / s0) if s0 > h else i0
    if peak <= K:
        return None
    f = lambda s: i0 + s0 - s + h * mp.log(s / s0) - K
    return mp.findroot(f, (h, s0), solver="anderson", tol=mp.mpf("1e-72"), maxsteps=250)


def compare(beta, c, gamma, K, s0, i0):
    P = geometry(beta, c, gamma, K)
    s0, i0 = map(dec, (s0, i0))
    s1 = natural_entry(P, s0, i0)
    public = {key: value for key, value in P.items() if not callable(value)}
    public.update(s0=s0, i0=i0, s1=s1)
    if s1 is None or s1 < P["s_B"]:
        # 无公共容量尾段时，不把尾段差冒充从该初值出发的最优成本差。
        COUNTS["masked_cases"] += 1
        public.update(comparable=False, mask_reason="natural_entry_before_s_B" if s1 else "initial_state_safe",
                      Delta_J=None, Delta_T=None, J_fill=None, J_star=None,
                      relative_saving=None, T_fill=None, T_star=None, time_ratio=None)
        return public
    J_fill = P["boundary_cost"](s1, P["h"])
    J_star = P["boundary_cost"](s1, P["s_B"]) + P["W"]
    T_fill = P["boundary_time"](s1, P["h"])
    T_star = P["boundary_time"](s1, P["s_B"]) + P["T_full"]
    # 总成本可达 O(1/K)，其差为 O(K^2)；仅此独立恒等式核对加到
    # 110 位，避免核对过程本身损失约 -3log10(K) 位有效数字。
    with mp.workdps(110):
        residual = abs((P["boundary_cost"](s1, P["h"]) -
                        P["boundary_cost"](s1, P["s_B"]) - P["W"]) /
                       P["Delta_J"] - 1)
    RESIDUALS["cost_difference_relative"] = max(RESIDUALS["cost_difference_relative"], residual)
    assert residual < mp.mpf("1e-60")
    assert 0 < J_star < J_fill and 0 < T_star < T_fill
    COUNTS["comparable_cases"] += 1
    public.update(comparable=True, mask_reason="", J_fill=J_fill, J_star=J_star,
                  relative_saving=P["Delta_J"] / J_fill, T_fill=T_fill, T_star=T_star,
                  time_ratio=T_star / T_fill)
    return public


def asymptotic_case(beta, K, b0="1", gamma=".3"):
    beta, K, b0, gamma = map(dec, (beta, K, b0, gamma))
    R = compare(beta, b0 / beta, gamma, K, 1 - K / 2, K / 2)
    assert R["comparable"]
    h, p = R["h"], R["p"]
    exit_first = K / beta
    exit_second = exit_first - (1 - beta) * K**2 / (beta**3 * h)
    C_J = 1 / (24 * beta**4 * h**3)
    C_T = 1 / (beta * gamma)
    # 此独立初值族的 s1^circ=1，J_fill~A_fill/K。
    A_fill = beta / (1 - beta) * (mp.log(1 / h) - beta * mp.log((1 - p) / (h - p)))
    C_relative = C_J / A_fill
    R["asymptotics"] = dict(
        s1_limit=mp.mpf(1), exit_first=exit_first, exit_second=exit_second,
        exit_first_error_pct=100 * abs(exit_first / R["exit_gap"] - 1),
        exit_second_error_pct=100 * abs(exit_second / R["exit_gap"] - 1),
        exit_second_remainder_over_K3=(R["exit_gap"] - exit_second) / K**3,
        Delta_J_over_K2=R["Delta_J"] / K**2, Delta_J_limit=C_J,
        Delta_J_error_pct=100 * abs(R["Delta_J"] / (C_J * K**2) - 1),
        Delta_T_limit=C_T, Delta_T_error_pct=100 * abs(R["Delta_T"] / C_T - 1),
        relative_saving_over_K3=R["relative_saving"] / K**3,
        relative_saving_limit=C_relative,
        relative_saving_error_pct=100 * abs(R["relative_saving"] / (C_relative * K**3) - 1),
        A_fill=A_fill)
    return R


def accuracy_threshold(beta, b0, gamma, metric, pct):
    beta, b0, gamma, pct = map(dec, (beta, b0, gamma, pct))

    def error(logK):
        K = mp.exp(logK)
        P = geometry(beta, b0 / beta, gamma, K)
        if metric == "exit_first":
            return 100 * abs((K / beta) / P["exit_gap"] - 1) - pct
        if metric == "Delta_J":
            leading = K**2 / (24 * beta**4 * P["h"]**3)
            return 100 * abs(P["Delta_J"] / leading - 1) - pct
        if metric == "Delta_T":
            return 100 * abs(P["Delta_T"] * beta * gamma - 1) - pct
        raise ValueError(metric)

    # 对数 K 的标量求根，与最优控制优化无关。
    lo, hi = mp.log(mp.mpf("1e-10")), mp.log(mp.mpf("1e-2"))
    assert error(lo) < 0 < error(hi)
    root = mp.findroot(error, (lo, hi), solver="anderson", tol=mp.mpf("1e-58"), maxsteps=250)
    return dict(metric=metric, relative_error_pct=pct, K_at_threshold=mp.exp(root),
                threshold_equation_residual_pct=abs(error(root)))


def make_figure(scan):
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#262626"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.labelsize": 9, "legend.fontsize": 7.2,
                         "axes.linewidth": .7, "pdf.fonttype": 42,
                         "xtick.direction": "in", "ytick.direction": "in",
                         "savefig.dpi": 300})
    fig, axes = plt.subplots(2, 2, figsize=(16.5 / 2.54, 12.8 / 2.54))
    fields = ["exit_gap", "Delta_J", "relative_saving", "time_ratio"]
    labels = [r"$s_B-h$", r"$\Delta J$", r"$\Delta J/J_{\rm fill}$", r"$T_+^*/T_{+,\rm fill}$"]
    figure_data = {"width_cm": 16.5, "height_cm": 12.8, "curve_data": [],
                   "mask": "all panels omit natural_entry_before_s_B cases",
                   "fixed": {"b0": 1, "gamma": .3, "s0": .9999, "i0": .0001}}
    for beta, color in zip([".13", ".155", ".25", ".5", ".8"], colors):
        records = [r for r in scan if r["beta"] == dec(beta)]
        x = [float(r["K"]) for r in records]
        curve = {"beta": beta, "K": x, "comparable": [r["comparable"] for r in records]}
        for ax, key, ylabel in zip(axes.flat, fields, labels):
            y = [float(r[key]) if r["comparable"] else math.nan for r in records]
            curve[key] = [v if math.isfinite(v) else None for v in y]
            ax.plot(x, y, color=color, lw=1.35, label=rf"$\beta={float(beta):g}$")
            ax.set(xscale="log", xlabel=r"$K$", ylabel=ylabel, xlim=(1e-4, .15))
            if key != "time_ratio":
                ax.set_yscale("log")
            ax.grid(which="major", color=".89", lw=.45)
            ax.tick_params(which="both", top=True, right=True)
        figure_data["curve_data"].append(curve)
    for ax, letter in zip(axes.flat, "abcd"):
        ax.text(.04, .96, f"({letter})", transform=ax.transAxes, va="top", fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1))
    axes[0, 0].legend(loc="lower right", frameon=False, ncol=1)
    axes[1, 1].set_ylim(.20, 1.025)
    fig.subplots_adjust(left=.12, bottom=.145, right=.985, top=.98, wspace=.33, hspace=.36)
    fig.text(.52, .018,
             r"Common-tail comparison ($s_1\geq s_B$); masked: $\beta=0.13,\ K=0.15$.",
             ha="center", va="center", fontsize=7)
    fig.savefig(OUT / "magnitude.pdf")
    fig.savefig(OUT / "magnitude.png")
    plt.close(fig)
    write_json("figure_data.json", figure_data)


def main():
    e2 = compare(".5", "2", ".3", ".15", ".99", ".01")
    zhou = compare(".13675", "10.1317", ".3004", ".01", ".9999", ".0001")
    zhou["provenance"] = "Zhou 2024 Xi'an literature parameters, constructed constant-c no-return scenario; not city-fit reproduction"
    # 定点补入便于阅读的 K，不用二进制浮点值作高精度输入。
    K_grid = sorted({mp.mpf(mp.nstr(mp.power(mp.mpf("1500"), mp.mpf(j) / 120) / 10000, 40))
                     for j in range(121)} | {dec(v) for v in [".0001", ".001", ".01", ".05", ".15"]})
    scan = [compare(beta, 1 / dec(beta), ".3", K, ".9999", ".0001")
            for beta in [".13", ".155", ".25", ".5", ".8"] for K in K_grid]
    small = [asymptotic_case(beta, f"1e-{power}")
             for beta in [".13", ".155", ".25", ".5", ".8"] for power in range(3, 10)]
    thresholds = [accuracy_threshold(".155", "1", ".3", metric, pct)
                  for metric in ["exit_first", "Delta_J", "Delta_T"] for pct in ["1", "5", "10"]]
    # 旧核算脚本使用的参数另列，不与固定 b0=1 的新扫描混在一起。
    historical = [asymptotic_case(".155", f"1e-{power}", b0="1.55", gamma=".3504")
                  for power in range(3, 7)]
    historical_thresholds = [accuracy_threshold(".155", "1.55", ".3504", metric, pct)
                             for metric in ["exit_first", "Delta_J", "Delta_T"] for pct in ["1", "5", "10"]]

    quadrature = []
    for beta, K in [(".5", ".15"), (".155", "1e-8")]:
        P = geometry(beta, 1 / dec(beta), ".3", K)
        integrand = lambda s: P["beta"] * (s - P["h"]) / (P["K"] * s * (s - P["p"]))
        integrated = mp.quad(integrand, [P["h"], P["s_B"]])
        closed = P["boundary_cost"](P["s_B"], P["h"])
        residual = abs(integrated / closed - 1)
        assert residual < mp.mpf("1e-60")
        quadrature.append(dict(beta=P["beta"], K=P["K"], relative_residual=residual))

    asymptotic_checks = []
    for beta in [dec(v) for v in [".13", ".155", ".25", ".5", ".8"]]:
        family = [r for r in small if r["beta"] == beta]
        last = family[-1]["asymptotics"]
        first = family[0]["asymptotics"]
        for metric in ["exit_second_error_pct", "Delta_J_error_pct", "Delta_T_error_pct", "relative_saving_error_pct"]:
            assert last[metric] < first[metric]
            assert last[metric] < mp.mpf(".01")
        # 在最末三个点检验相对节省的 K^3 幂次。
        local_slopes = [mp.log(family[j + 1]["relative_saving"] / family[j]["relative_saving"]) /
                        mp.log(family[j + 1]["K"] / family[j]["K"]) for j in [-3, -2]]
        assert max(abs(slope - 3) for slope in local_slopes) < mp.mpf("1e-4")
        asymptotic_checks.append(dict(beta=beta, final_relative_errors_pct=last,
                                      last_local_log_slopes=local_slopes))

    fields = ["beta", "c", "gamma", "K", "s0", "i0", "s1", "s_B", "s_bar", "i_bar", "exit_gap",
              "comparable", "mask_reason", "J_fill", "J_star", "Delta_J", "relative_saving",
              "T_fill", "T_star", "Delta_T", "time_ratio"]
    with (OUT / "scan.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: serial(r.get(key)) for key in fields} for r in scan)
    make_figure(scan)
    write_json("analytic_results.json", dict(precision_decimal_digits=80, optimizer_calls=0,
        new_ocp_solves=0, ode_solves=0, E2=e2, Zhou_constructed_no_return=zhou,
        scan=dict(fixed_b0=1, fixed_gamma=".3", s0=".9999", i0=".0001", rows=len(scan),
                  K_points_per_beta=len(K_grid), masks=sum(not r["comparable"] for r in scan),
                  masked_rows=[r for r in scan if not r["comparable"]]),
        small_K_family=small, beta_0155_accuracy_thresholds=thresholds,
        precision_scenarios=dict(
            fixed_b0_beta_0155_K_1e_4=next(r for r in small if r["beta"] == dec(".155") and r["K"] == dec("1e-4")),
            historical_beta_0155_c10_gamma_03504_K_1e_4=next(r for r in historical if r["K"] == dec("1e-4"))),
        historical_check=dict(beta=".155", c="10", b0="1.55", gamma=".3504",
                              source="historical asymptotics_and_feasibility.py parameters; analytical recomputation, not fit",
                              cases=historical, accuracy_thresholds=historical_thresholds)))
    write_json("analytic_checks.json", dict(status="passed", precision_decimal_digits=80,
        optimizer_calls=0, new_ocp_solves=0, ode_solves=0, case_counts=COUNTS,
        scan_case_count=len(scan), small_K_case_count=len(small),
        high_precision_residual_maxima=RESIDUALS, independent_quadrature_checks=quadrature,
        asymptotic_family_checks=asymptotic_checks))
    report = ["# D4 解析核算与量级图", "", "本目录计算使用 80 位 mpmath 标量求根、封闭公式与独立标量积分；只有独立总成本差恒等式核对提高到 110 位，以覆盖 O(1/K) 总成本之差为 O(K^2) 的消去。优化器调用、新增 OCP 求解、ODE 求解均为 0。", "",
              "运行命令：`python tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/analytic_scan.py`（仓库根目录）。", "",
              "当前符号为 `beta`、`p=(1-beta)h`、`ell=beta*h`。历史脚本中输入参数 `p` 表示 beta；本脚本未调用旧脚本。", "",
              "## 比较口径", "", "纯容量填充：从给定初值免费自然等待到首次容量触点 `(s1,K)`，用 `q_B=1-h/s` 维持 `i=K` 直到 `(h,K)`，再置 `q=0`。当 `s1>=s_B` 时，两方案共享前段；最优方案于 `(s_B,K)` 转为 `q=1`，在安全边界 `(s_bar,i_bar)` 停止付费。`T_fill`、`T_star` 仅计算正控制集合的时间测度，不包括免费等待和安全集内延拓。", "",
              "固定正初值扫描设 `s0=.9999,i0=.0001`，只取 `K>=i0`。`s1<s_B` 时，公共容量尾段比较不适用，CSV 明确标记 mask；总成本、成本差、时长等比较字段留空。图的四个面板均屏蔽这些点，避免把辅助几何上的尾段差当作该初值的最优节省。", "",
              "高精度 JSON/CSV 数字以十进制字符串输出最多 72 位数字；这只是存储格式，并非对全部 72 位均准确的承诺，实际残差见检查文件。作图数据最后才转换为双精度。DeltaJ 先在 80 位使用 log1p、expm1 与公共尾段成本差计算，不由两个双精度总成本相减。", "",
              "## E2 本轮解析重算", ""]
    for key in ["s1", "s_B", "s_bar", "i_bar", "J_fill", "J_star", "Delta_J", "relative_saving", "T_fill", "T_star", "Delta_T", "time_ratio"]:
        report.append(f"- `{key} = {mp.nstr(e2[key], 25)}`")
    report += ["", "E2 为计划所列示例参数的解析重算，不是新的优化求解。", "", "## 扫描与图", "",
               f"固定 `b0=beta*c=1,gamma=.3`；beta 为 `.13,.155,.25,.5,.8`；每条曲线 {len(K_grid)} 个 K 点，共 {len(scan)} 条记录；其中 {sum(not r['comparable'] for r in scan)} 条被 mask。",
               "`magnitude.pdf` 是 16.5 cm × 12.8 cm 的四面板矢量曲线图；PNG 为对应 300 dpi 预览。前三图采用双对数坐标，最后一图为对数 K 与线性时长比。`figure_data.json` 保存实际图形数据与 mask。", "",
               "## 小容量族与误差", "", "独立初值族采用 `s0=1-K/2,i0=K/2`，因此 `s1(K)->s1^circ=1>h`，允许 K 降至 1e-9，不违反正感染初值与容量约束。全部五个 beta 均重算 K=1e-3,...,1e-9。JSON 记录三条展开的误差、二阶退出位置余项/K^3、DeltaJ/K^2、相对节省/K^3 及其极限系数。", "",
               "以下误差按精确解析量作分母（退出位置首项），或按渐近极限/首项作分母（DeltaJ、DeltaT）；百分比字段名给出具体口径。beta=.155、固定 b0=1,gamma=.3 的阈值为：", "",
               "| 展开 | 误差百分比 | K 阈值 |", "|---|---:|---:|"]
    for threshold in thresholds:
        report.append(f"| {threshold['metric']} | {mp.nstr(threshold['relative_error_pct'], 4)}% | {mp.nstr(threshold['K_at_threshold'], 10)} |")
    report += ["", "在这些阈值以下，所定义的相对误差低于对应百分比；阈值由对数 K 的解析标量根求得。`small_K_family` 另保留实际网格值，尤其可直接查看 K=1e-4 时的误差，不能将“约 1e-4”理解为统一的 1% 精度保证。", "",
               "历史脚本的 beta=.155,c=10,gamma=.3504 对应 b0=1.55、h=.2260645...，与新图固定 b0=1,gamma=.3 的参数不同；JSON 的 `historical_check` 独立保留其解析复核及阈值，不混写来源。", "",
               "## 文献参数构造情景", "", "Zhou 2024 西安常参数取 beta=.13675,c=10.1317,gamma=.1998+.1006=.3004；此处再取 K=.01,s0=.9999,i0=.0001。这仅以文献参数构造无回流、常 c 情景，不是城市拟合复现，不采用文献基线跟踪 q0 代替本文 q=0 的无控制定义。参数出处由稿件来源核对负责；本脚本不产生作者新拟合参数。", ""]
    for key in ["h", "s_B", "J_fill", "J_star", "Delta_J", "relative_saving", "T_fill", "T_star"]:
        report.append(f"- `{key} = {mp.nstr(zhou[key], 22)}`")
    report += ["", "## 核对", "", "`analytic_checks.json` 保存一元根残差、端点不变量残差、Theta 匹配残差、公共尾段与总成本差的一致性，以及两个独立容量成本积分核对。五个小容量族均检查末点误差收敛与末三个点的相对节省对数斜率趋近 3。", "",
               f"本轮检查通过：扫描 {len(scan)} 个参数组合；小容量族 {len(small)} 个组合；独立积分 2 个；阈值 18 个（当前与历史来源各 9 个）。完整过程含标量求根迭代，不属于优化器调用或 OCP 求解。", ""]
    (OUT / "analytic_README.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"status": "passed", "scan_rows": len(scan), "masked_rows": sum(not r["comparable"] for r in scan),
                      "small_K_cases": len(small), "optimizer_calls": 0, "new_ocp_solves": 0,
                      "E2": {key: mp.nstr(e2[key], 20) for key in ["J_fill", "J_star", "Delta_J", "relative_saving", "T_fill", "T_star"]}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
