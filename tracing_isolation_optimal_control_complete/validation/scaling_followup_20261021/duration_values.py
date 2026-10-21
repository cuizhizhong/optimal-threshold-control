"""D 后续：80 位公共尾段时长核算及自包含数值宏。

从仓库根目录运行：
python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/duration_values.py

不读取历史数值 JSON，不执行历史脚本，不调用 MATLAB、ODE 或 OCP。
旧 D 宏从只读历史 TeX 原样复制，新增宏由本脚本的 80 位解析值舍入。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import mpmath as mp


mp.mp.dps = 80
OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[1]
OLD_MACROS = PROJECT / "validation/scaling_asymptotics_20261021/computed_values.tex"
NEW_MACROS = PROJECT / "latex/generated/scaling_values.tex"
TOL = mp.mpf("1e-65")


def dec(value):
    """输入均为十进制字符串；不经双精度浮点。"""
    return mp.mpf(str(value))


def serial(value):
    if isinstance(value, mp.mpf):
        return mp.nstr(value, 80)
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(item) for item in value]
    return value


def write_json(name, value):
    (OUT / name).write_text(json.dumps(serial(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixed(value, digits):
    """十进制四舍五入为展示字符串；绝不经 float。"""
    factor = mp.mpf(10) ** digits
    rounded = int(mp.floor(value * factor + mp.mpf(".5")))
    if digits == 0:
        return str(rounded)
    whole, fractional = divmod(rounded, 10 ** digits)
    return f"{whole}.{fractional:0{digits}d}"


def geometry(beta, c, gamma, K):
    """沿用 D 的标量端点方程；本文件独立复制，不执行旧脚本。"""
    beta, c, gamma, K = map(dec, (beta, c, gamma, K))
    h = gamma / (beta * c)
    ell, p, k = beta * h, (1 - beta) * h, K / h

    def reduced(x):
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

    # 时长差只取公共尾段，不能由两个总时长相减。
    T_boundary_tail = mp.log1p(u / beta) / (c * K)
    T_full = -mp.log1p(-h * A / K) / gamma
    Delta_T = T_boundary_tail - T_full
    # 同一公共尾段公式的原变量写法，仅作代数/舍入残差核对。
    Delta_T_unreduced = mp.log((s_B - p) / (h - p)) / (c * K) - mp.log(K / i_bar) / gamma
    tail_cost = beta / (K * (1 - beta)) * (mp.log1p(u) - beta * mp.log1p(u / beta))
    W = -mp.log1p(-h * A / K) / h
    Delta_J = tail_cost - W
    Theta = lambda s, i: (s - h) / (i * (s - p))
    residuals = {
        "scalar_relative": abs(reduced(x)) / k,
        "endpoint_relative": abs((i_bar - ell * mp.log(s_bar)) - (K - ell * mp.log(s_B))) / max(K, ell),
        "theta_relative": abs(Theta(s_bar, i_bar) / Theta(s_B, K) - 1),
        "direct_tail_formula_relative": abs(Delta_T_unreduced / Delta_T - 1),
    }
    assert all(value < TOL for value in residuals.values()), residuals
    assert Delta_T > 0 and Delta_J > 0
    return dict(beta=beta, c=c, gamma=gamma, K=K, h=h, ell=ell, p=p,
                x=x, u=u, s_B=s_B, s_bar=s_bar, i_bar=i_bar,
                T_boundary_tail=T_boundary_tail, T_full=T_full,
                Delta_T=Delta_T, Delta_T_limit=1 / (beta * gamma),
                scaled_Delta_T=beta * gamma * Delta_T,
                W=W, Delta_J=Delta_J, residuals=residuals)


def compare(beta, c, gamma, K, s0, i0):
    P = geometry(beta, c, gamma, K)
    s0, i0 = map(dec, (s0, i0))
    h, p, K, c, beta = (P[key] for key in ["h", "p", "K", "c", "beta"])
    assert 0 < i0 <= K and s0 > h and s0 + i0 <= 1
    f = lambda s: i0 + s0 - s + h * mp.log(s / s0) - K
    s1 = mp.findroot(f, (h, s0), solver="anderson", tol=mp.mpf("1e-72"), maxsteps=250)
    assert s1 >= P["s_B"], "公共容量入口条件失效"
    P["residuals"]["natural_entry_absolute"] = abs(f(s1))
    assert abs(f(s1)) < TOL
    T_fill = mp.log((s1 - p) / (h - p)) / (c * K)
    # 总时长各自求值；Delta_T 不从这里相减。
    T_star = mp.log((s1 - p) / (P["s_B"] - p)) / (c * K) + P["T_full"]
    J_fill = beta / (K * (1 - beta)) * (mp.log1p((s1 - h) / h) -
               beta * mp.log1p((s1 - h) / (h - p)))
    P.update(s0=s0, i0=i0, s1=s1, common_capacity_entry=True,
             T_fill=T_fill, T_star=T_star,
             time_reduction_pct=100 * P["Delta_T"] / T_fill,
             J_fill=J_fill, cost_saving_pct=100 * P["Delta_J"] / J_fill)
    return P


def main():
    e2 = compare(".5", "2", ".3", ".15", ".99", ".01")
    xian = compare(".13675", "10.1317", ".3004", ".01", ".9999", ".0001")
    xian["provenance"] = "Zhou 2024 Xi'an literature parameters; constructed constant-c no-return scenario, not a reproduction of the city fit"
    reference_points = [geometry(".5", "2", ".3", K) for K in [".01", ".001", ".0001"]]
    display = {
        "DtimeDeltaE": fixed(e2["Delta_T"], 6),
        "DtimeReductionE": fixed(e2["time_reduction_pct"], 2),
        "DtimeDeltaZ": fixed(xian["Delta_T"], 6),
        "DtimeReductionZ": fixed(xian["time_reduction_pct"], 2),
        "DtimeLimitZ": fixed(xian["Delta_T_limit"], 3),
        "DabstractSavingZ": fixed(xian["cost_saving_pct"], 2),
        "DabstractTimeFillZ": fixed(xian["T_fill"], 1),
        "DabstractTimeOptZ": fixed(xian["T_star"], 1),
        "DtimeDeltaZBrief": fixed(xian["Delta_T"], 2),
        "DtimeLimitZBrief": fixed(xian["Delta_T_limit"], 1),
    }
    expected = {
        "DtimeDeltaE": "2.536302", "DtimeReductionE": "53.17",
        "DtimeDeltaZ": "8.263905", "DtimeReductionZ": "25.41",
        "DtimeLimitZ": "24.343", "DabstractSavingZ": "0.34",
        "DabstractTimeFillZ": "32.5", "DabstractTimeOptZ": "24.3",
        "DtimeDeltaZBrief": "8.26", "DtimeLimitZBrief": "24.3",
    }
    numeric_checks = [{"quantity": key, "actual": value, "reference": expected[key],
                       "passed": value == expected[key]} for key, value in display.items()]
    assert all(check["passed"] for check in numeric_checks), numeric_checks
    reference_checks = []
    for P, expected_value in zip(reference_points, ["0.8667", "0.9838", "0.9983"]):
        actual = fixed(P["scaled_Delta_T"], 4)
        check = dict(beta=P["beta"], c=P["c"], gamma=P["gamma"], K=P["K"],
                     direct_tail_value=P["Delta_T"], scaled_value=P["scaled_Delta_T"],
                     actual_rounded=actual, reference_rounded=expected_value, passed=actual == expected_value)
        assert check["passed"], check
        reference_checks.append(check)

    old_bytes = OLD_MACROS.read_bytes()
    old_text = old_bytes.decode("utf-8")
    commands = re.findall(r"\\newcommand\{\\([^}]+)\}\{([^}]+)\}", old_text)
    assert len(commands) == 17 and len({name for name, _ in commands}) == 17
    new_text = ("% D 后续：旧 D 宏原样保留；新增时长宏使用 80 位解析值，详见 duration_values.py。\n" +
                "\n".join(line for line in old_text.splitlines() if line.startswith("\\newcommand")) + "\n" +
                "% 新增：时长差采用公共尾段公式，缩短百分比以纯容量填充总正控制时长为分母。\n" +
                "\n".join(f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in display.items()) + "\n")
    NEW_MACROS.parent.mkdir(parents=True, exist_ok=True)
    NEW_MACROS.write_text(new_text, encoding="utf-8")
    new_commands = dict(re.findall(r"\\newcommand\{\\([^}]+)\}\{([^}]+)\}", NEW_MACROS.read_text(encoding="utf-8")))
    preservation = [{"macro": name, "historical_value": value, "new_value": new_commands[name],
                     "passed": value == new_commands[name]} for name, value in commands]
    assert all(check["passed"] for check in preservation)
    assert OLD_MACROS.read_bytes() == old_bytes
    residual_maxima = {}
    for P in [e2, xian] + reference_points:
        for key, value in P["residuals"].items():
            residual_maxima[key] = max(residual_maxima.get(key, mp.mpf(0)), value)

    write_json("duration_values.json", dict(
        precision_decimal_digits=80, optimizer_calls=0, matlab_calls=0, new_ocp_solves=0, ode_solves=0,
        method="80-digit scalar endpoint root and closed-form public-tail evaluation; Delta_T is never formed from two total durations",
        formulas=dict(h="gamma/(beta*c)", p="(1-beta)*h", x="s_bar/h-1", A="x-log1p(x)",
            u="expm1(log1p(x)+A/beta)", scalar_equation="A*(beta+x)*u/(beta*(u-x))=K/h",
            T_boundary_tail="log1p(u/beta)/(c*K)=T_B(s_B,h)",
            T_full="-log1p(-h*A/K)/gamma=log(K/i_bar)/gamma",
            Delta_T="T_B(s_B,h)-log(K/i_bar)/gamma",
            T_fill="log((s1-p)/(h-p))/(c*K)",
            time_reduction_pct="100*Delta_T/T_fill", Delta_T_limit="1/(beta*gamma)",
            figure_d="beta*gamma*Delta_T"),
        E2=e2, Xian_constructed_no_return=xian, figure_d_reference_points=reference_points,
        new_macro_values=display))
    write_json("duration_checks.json", dict(
        status="passed", precision_decimal_digits=80, optimizer_calls=0, matlab_calls=0,
        new_ocp_solves=0, ode_solves=0, numeric_display_checks=numeric_checks,
        figure_d_reference_checks=reference_checks,
        old_macro_preservation=dict(count=len(preservation), checks=preservation,
            historical_file_unchanged=True, historical_sha256=hashlib.sha256(old_bytes).hexdigest()),
        high_precision_residual_maxima=residual_maxima,
        high_precision_residual_tolerance=TOL,
        check_count=len(numeric_checks) + len(reference_checks) + len(preservation),
        checks_passed=len(numeric_checks) + len(reference_checks) + len(preservation)))
    lines = ["# 公共尾段时长核算与数值宏", "",
        "运行：`python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/duration_values.py`。", "",
        "计算使用 80 位 mpmath 标量求根与封闭公式。MATLAB、优化器、新增 OCP、ODE 调用均为 0。", "",
        "时长差直接取 `log1p(u/beta)/(c*K) + log1p(-h*A/K)/gamma`，即式 `eq:common-capacity-comparison` 的公共容量尾段差。两方案的总正控制时长分别独立求值，只用于展示与百分比分母，未用于相减求时长差。", "",
        "E2 参数为 `beta=.5,c=2,gamma=.3,K=.15,s0=.99,i0=.01`；西安构造情景参数为 `beta=.13675,c=10.1317,gamma=.3004,K=.01,s0=.9999,i0=.0001`，不是城市拟合的复现。", "",
        "| 量 | E2 | 西安构造情景 |", "|---|---:|---:|"]
    for label, key in [("纯容量填充正控制时长", "T_fill"), ("成本最优正控制时长", "T_star"),
                       ("公共尾段时长差", "Delta_T"), ("缩短百分比", "time_reduction_pct"),
                       ("极限 1/(beta gamma)", "Delta_T_limit")]:
        lines.append(f"| {label} | {mp.nstr(e2[key], 25)} | {mp.nstr(xian[key], 25)} |")
    lines += ["", "西安参数极限为 24.343 日，而 K=.01 的实际差为 8.263905 日；小 beta 的有限 K 不应由极限值替代。正控制时长不是目标泛函，以上比较不等于时长最优性。", "",
        "图 2(d) 的三个独立参照点（beta=.5,c=2,gamma=.3）：", "",
        "| K | beta gamma Delta_T | 四位小数参照 |", "|---:|---:|---:|"]
    for check in reference_checks:
        lines.append(f"| {check['K']} | {mp.nstr(check['scaled_value'], 25)} | {check['reference_rounded']} |")
    lines += ["", f"新展示值核对 10/10；图 2(d) 参照点 3/3；旧 D 宏保护 17/17。共 30/30。最大高精度残差为 {mp.nstr(max(residual_maxima.values()), 8)}，阈值为 1e-65。", "",
        "`duration_values.json` 保存 80 位十进制字符串、公式和端点；`duration_checks.json` 保存参照核对、旧宏逐项保护与各类最大残差。十进制串是高精度计算的记录格式，并非对每一末位都经独立验证的宣称。", "",
        "旧 `validation/scaling_asymptotics_20261021/computed_values.tex` 未修改。新 `latex/generated/scaling_values.tex` 对旧宏的名字与展示数字逐项原样复制，新增时长宏与摘要独立舍入宏。", ""]
    (OUT / "duration_README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dict(status="passed", checks="30/30", macro_values=display,
                         maximum_residual=mp.nstr(max(residual_maxima.values()), 10)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
