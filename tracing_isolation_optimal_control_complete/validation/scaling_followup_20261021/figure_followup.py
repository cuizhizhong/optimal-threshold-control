"""D 后续：80 位公共尾段解析量与按正文实测宽度绘制的量级图。

底稿：validation/scaling_asymptotics_20261021/analytic_scan.py。
本脚本复制其解析函数，不导入或调用旧脚本，不改写旧验证记录。
运行：python validation/scaling_followup_20261021/figure_followup.py --attempt 1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

import mpmath as mp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

mp.mp.dps = 80
OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[1]
OUTPUT = PROJECT / "figures/scaling/FigD_magnitude"
BASE = PROJECT / "validation/scaling_asymptotics_20261021/analytic_scan.py"
OLD_DATA = BASE.with_name("figure_data.json")
WIDTH_PROBE = PROJECT / "validation/figure1_revision_20261021/measure_linewidth_console.log"
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dense_display_curve(ax, line):
    """采用图 1 的逐段密采样标准，只保留坐标窗内的可见曲线。"""
    xdata, ydata = np.asarray(line.get_xdata()), np.asarray(line.get_ydata())
    dense_x, dense_y = [], []
    for xa, xb, ya, yb in zip(xdata[:-1], xdata[1:], ydata[:-1], ydata[1:]):
        if not np.all(np.isfinite((xa, xb, ya, yb))):
            continue
        count = 2001 if len(xdata) <= 3 else 9
        dense_x.extend(np.linspace(xa, xb, count))
        dense_y.extend(np.linspace(ya, yb, count))
    if not dense_x:
        return np.empty((0, 2))
    points = np.column_stack((dense_x, dense_y))
    valid = ((points[:, 0] >= ax.get_xlim()[0]) & (points[:, 0] <= ax.get_xlim()[1]) &
             (points[:, 1] >= ax.get_ylim()[0]) & (points[:, 1] <= ax.get_ylim()[1]))
    return ax.transData.transform(points[valid])


def collision_checks(fig, axes, legend):
    """核查可见文字框、所有跨子图文字对，以及全局图例外框。"""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    text_boxes, all_curves = [], []
    for letter, ax in zip("abcd", axes.flat):
        # LogLocator 还返回坐标窗之外的 tick；Axis 实际绘制时会过滤它们。
        # 因此这里按 tick 坐标筛选，核查真正绘制的文字。
        xticks = [item for item in ax.get_xticklabels()
                  if ax.get_xlim()[0] <= item.get_position()[0] <= ax.get_xlim()[1]]
        yticks = [item for item in ax.get_yticklabels()
                  if ax.get_ylim()[0] <= item.get_position()[1] <= ax.get_ylim()[1]]
        items = [*ax.texts, *xticks, *yticks,
                 ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()]
        for item in items:
            if item.get_visible() and item.get_text():
                text_boxes.append((letter, item.get_text(), item.get_window_extent(renderer)))
        all_curves.extend((letter, n, dense_display_curve(ax, line)) for n, line in enumerate(ax.lines))
    for item in legend.get_texts():
        text_boxes.append(("legend", item.get_text(), item.get_window_extent(renderer)))
    hits, pairs, legend_hits = [], [], []
    for location, text, bbox in text_boxes:
        for panel, n, points in all_curves:
            # 图 1 标准核查本图文字与本图曲线；图例与所有曲线比对。
            if location not in (panel, "legend"):
                continue
            hit = ((points[:, 0] >= bbox.x0) & (points[:, 0] <= bbox.x1) &
                   (points[:, 1] >= bbox.y0) & (points[:, 1] <= bbox.y1))
            if np.any(hit):
                hits.append(dict(panel=panel, label=text, line_index=n))
    for n, (loc_a, text_a, box_a) in enumerate(text_boxes):
        for loc_b, text_b, box_b in text_boxes[n + 1:]:
            if box_a.overlaps(box_b):
                pairs.append(dict(location_a=loc_a, location_b=loc_b, label_a=text_a, label_b=text_b))
    bbox = legend.get_window_extent(renderer)
    for panel, n, points in all_curves:
        hit = ((points[:, 0] >= bbox.x0) & (points[:, 0] <= bbox.x1) &
               (points[:, 1] >= bbox.y0) & (points[:, 1] <= bbox.y1))
        if np.any(hit):
            legend_hits.append(dict(panel=panel, line_index=n))
    checks = dict(
        status="passed" if not hits and not pairs and not legend_hits else "failed",
        label_curve_intersections=hits, label_pair_intersections=pairs,
        legend_box_curve_intersections=legend_hits, visible_text_boxes_checked=len(text_boxes),
        method="Figure 1 standard: visible annotation/tick/axis-label text boxes versus own-axis visible Line2D curves; 2001 samples/segment for <=3-point lines, otherwise 9; all cross-axis text pairs; additionally all global-legend texts and its outer box versus all curves",
        subpanel_labels="outside upper-left of each plotting window", global_legend_count=1)
    return checks


def make_figure(scan, attempt):
    width_pt = float(re.search(r"FIGUREONE_LINEWIDTH_PT=([0-9.]+)pt",
                              WIDTH_PROBE.read_text(encoding="utf-8")).group(1))
    width_in, height_cm = width_pt / 72.27, 12.8
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#262626"]
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
        "mathtext.fontset": "stix", "font.size": 9, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": .6,
        "legend.fontsize": 8, "pdf.fonttype": 42, "xtick.direction": "in", "ytick.direction": "in",
        "savefig.dpi": 300})
    fig, axes = plt.subplots(2, 2, figsize=(width_in, height_cm / 2.54))
    fields = ["exit_gap", "Delta_J", "relative_saving", "normalized_time_difference"]
    labels = [r"$s_B-h$", r"$\Delta J$", r"$\Delta J/J_{\rm fill}$",
              r"$\beta\gamma\,(T_{+,\rm fill}-T_+^*)$"]
    data = dict(width_cm=width_in * 2.54, height_cm=height_cm, curve_data=[],
        mask="all panels omit natural_entry_before_s_B cases",
        fixed=dict(b0=1, gamma=.3, s0=.9999, i0=.0001),
        duration_difference_formula="log1p(u/beta)/(c*K) - (-log1p(-h*A/K))/gamma; u=s_B/h-1, A=(s_bar/h-1)-log1p(s_bar/h-1)",
        duration_difference_source="80-digit direct common capacity tail; never a subtraction of two total durations")
    for beta, color in zip([".13", ".155", ".25", ".5", ".8"], colors):
        rows = [r for r in scan if r["beta"] == dec(beta)]
        xs = [float(r["K"]) for r in rows]
        curve = dict(beta=beta, K=xs, comparable=[r["comparable"] for r in rows])
        curve["Delta_T_high_precision"] = [mp.nstr(r["Delta_T"], 72) if r["comparable"] else None for r in rows]
        for ax, key, label in zip(axes.flat, fields, labels):
            ys = [float(r[key]) if r["comparable"] else math.nan for r in rows]
            curve[key] = [y if math.isfinite(y) else None for y in ys]
            ax.plot(xs, ys, color=color, lw=1.35, label=rf"$\beta={float(beta):g}$")
            ax.set(xscale="log", xlabel=r"$K$", ylabel=label, xlim=(1e-4, .15))
            if key != "normalized_time_difference":
                ax.set_yscale("log")
            ax.grid(which="major", color=".89", lw=.45)
            ax.tick_params(which="both", top=True, right=True)
            ax.tick_params(axis="x", pad=7)
        data["curve_data"].append(curve)
    for ax, letter in zip(axes.flat, "abcd"):
        ax.text(0, 1.045, f"({letter})", transform=ax.transAxes, va="bottom", ha="left", fontsize=9,
                fontweight="bold", clip_on=False)
    axes[1, 1].axhline(1, color=".45", lw=.8, ls="--", zorder=0)
    axes[1, 1].set_ylim(0, 1.045)
    axes[1, 1].set_yticks([0, .2, .4, .6, .8, 1.0])
    fig.subplots_adjust(left=.13, bottom=.105, right=.98, top=.88, wspace=.40, hspace=.52)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    legend = fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.55, .99),
                        ncol=5, frameon=False, handlelength=1.6, columnspacing=1.7)
    label_checks = collision_checks(fig, axes, legend)
    plain_json(attempt / "label_collision_checks.json", label_checks)
    plain_json(OUT / "label_collision_checks.json", label_checks)
    fig.savefig(attempt / "layout_preview.png", dpi=150)
    assert label_checks["status"] == "passed", label_checks
    # 不用 bbox_inches='tight'，从而保留实测正文宽度与 8/9 pt 字号。
    for ext in (".pdf", ".png"):
        fig.savefig(attempt / (OUTPUT.name + ext))
    plt.close(fig)
    pdf = attempt / (OUTPUT.name + ".pdf")
    media = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", pdf.read_bytes())
    assert media
    pdf_width, pdf_height = map(float, media.groups())
    assert abs(pdf_width - width_pt * 72 / 72.27) < 1e-6
    assert abs(pdf_height - height_cm / 2.54 * 72) < 1e-6
    measurement = dict(linewidth_tex_pt=width_pt, width_cm=width_in * 2.54, height_cm=height_cm,
        pdf_width_big_pt=pdf_width, pdf_height_big_pt=pdf_height, insertion_scale=1,
        tick_font_pt=8, label_font_pt=9, font_family="Times New Roman / STIXGeneral",
        math_font="stix", global_legend_count=1, reference_line_y=1,
        english_footnote_present=False)
    return data, label_checks, measurement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    attempt = OUT / f"figure_attempt{args.attempt}"
    attempt.mkdir(exist_ok=False)
    protected = [BASE, OLD_DATA, BASE.with_name("magnitude.pdf"), BASE.with_name("magnitude.png")]
    protected += [p for p in (PROJECT / "figures/numerical_scenarios").iterdir()
                  if p.stem.startswith(("FigN1_regions", "FigN2", "FigN3", "FigN1_optimal_partition"))]
    before = {str(p.relative_to(PROJECT)): sha(p) for p in protected}
    K_grid = sorted({mp.mpf(mp.nstr(mp.power(mp.mpf("1500"), mp.mpf(j) / 120) / 10000, 40))
                     for j in range(121)} | {dec(v) for v in [".0001", ".001", ".01", ".05", ".15"]})
    scan = [compare(beta, 1 / dec(beta), ".3", K, ".9999", ".0001")
            for beta in [".13", ".155", ".25", ".5", ".8"] for K in K_grid]
    for row in scan:
        row["normalized_time_difference"] = row["beta"] * row["gamma"] * row["Delta_T"] if row["comparable"] else None
    data, label_checks, measurement = make_figure(scan, attempt)
    old = json.loads(OLD_DATA.read_text(encoding="utf-8"))
    unchanged = []
    for previous, current in zip(old["curve_data"], data["curve_data"]):
        for field in ["beta", "K", "comparable", "exit_gap", "Delta_J", "relative_saving"]:
            unchanged.append(dict(beta=current["beta"], field=field, identical=current[field] == previous[field]))
    assert all(r["identical"] for r in unchanged)
    refs = []
    for K, expected in [(".01", ".8667"), (".001", ".9838"), (".0001", ".9983")]:
        row = next(r for r in scan if r["beta"] == dec(".5") and r["K"] == dec(K))
        got = row["normalized_time_difference"]
        rounded = f"{float(got):.4f}"
        assert rounded == f"{float(dec(expected)):.4f}"
        refs.append(dict(beta=".5", c="2", gamma=".3", K=K,
            direct_common_tail_Delta_T=mp.nstr(row["Delta_T"], 72),
            normalized_time_difference=mp.nstr(got, 72), expected_rounded_4dp=f"{float(dec(expected)):.4f}",
            actual_rounded_4dp=rounded, passed=True))
    masks = [dict(beta=mp.nstr(r["beta"], 8), K=mp.nstr(r["K"], 8), reason=r["mask_reason"])
             for r in scan if not r["comparable"]]
    assert len(scan) == 620 and len(masks) == 1 and masks[0]["beta"] == "0.13" and masks[0]["K"] == "0.15"
    assert before == {str(p.relative_to(PROJECT)): sha(p) for p in protected}
    checks = dict(status="passed", precision_decimal_digits=80, matlab_calls=0, optimizer_calls=0,
        new_ocp_solves=0, ode_solves=0, attempt=args.attempt, scan_rows=len(scan), masks=masks,
        all_duration_differences="direct 80-digit common-capacity-tail formula; no subtraction of total durations",
        original_abc_grid_mask_data_checks=unchanged, normalized_duration_reference_checks=refs,
        high_precision_residual_maxima=serial(RESIDUALS), measurement=measurement,
        label_collision_checks=label_checks, protected_files_sha256=before,
        sources_sha256={str(p.relative_to(PROJECT)): sha(p) for p in [Path(__file__), BASE, OLD_DATA, WIDTH_PROBE]})
    plain_json(attempt / "figure_checks.json", checks)
    plain_json(attempt / "figure_data.json", data)
    plain_json(OUT / "figure_checks.json", checks)
    plain_json(OUT / "figure_data.json", data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    for ext in (".pdf", ".png"):
        shutil.copyfile(attempt / (OUTPUT.name + ext), OUTPUT.with_suffix(ext))
    report = ["# 图 2 后续解析核查", "",
        f"实际成功运行：`python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/figure_followup.py --attempt {args.attempt}`。",
        "以旧 D 脚本为底稿复制纯解析函数；不导入旧脚本，不写入旧验证目录。mpmath 80 位标量根与闭式公式，无 MATLAB、优化器、OCP 或 ODE 调用。", "",
        "扫描固定 beta*c=1、gamma=0.3、s0=0.9999、i0=0.0001；与旧图完全相同的 620 个点。前三面板、K 网格与 mask 均逐项相同（30 项通过）；唯一排除点为 beta=0.13,K=0.15，因共同容量入口条件不成立。", "",
        "第四面板逐点使用公共尾段公式 Delta_T=T_B(s_B,h)-log(K/i_bar)/gamma，再计算 beta*gamma*Delta_T；不由两个总时长相减。横轴为对数 K，y=1 虚线给出固定 beta 时的 K→0 极限。", "",
        "| beta=0.5 的 K | beta*gamma*Delta_T | 四位小数参照 |", "|---|---:|---:|"]
    for ref in refs:
        report.append(f"| {ref['K']} | {ref['normalized_time_difference'][:25]} | {ref['expected_rounded_4dp']} |")
    report += ["", f"正文实测宽度 {measurement['linewidth_tex_pt']} TeX pt，PDF 实际宽度 {measurement['pdf_width_big_pt']} bp；插图不缩放。刻度 8 pt、标签 9 pt，Times New Roman/STIXGeneral 与 stix 数学字体。", "",
        "外置子图字母和单次顶部图例；去掉英文脚注。沿用图 1 的实际文字框与密曲线核查，并加入全局图例外框与所有曲线核查；所有文字框对亦检查，结果均零相交。", "",
        "`figure_checks.json` 为主核查，`figure_data.json` 存全部作图数据，`label_collision_checks.json` 存文字碰撞检查；每次尝试单独存入 figure_attemptN。最终图输出到 figures/scaling/FigD_magnitude.pdf 与 .png。旧 D 图、旧脚本及 FigN1_regions/FigN2/FigN3/FigN1_optimal_partition 均经 SHA-256 核对未变。", "",
        "首次尝试保留了文字框相交失败记录：LogLocator 返回实际窗外刻度，以及左下角刻度间距不足。第二次采用 Axis 实际绘制时的坐标窗筛选并增大 x 刻度间距，检查通过；此后只修正本说明中实际命令的 attempt 编号并保留新的核查。", ""]
    (OUT / "figure_README.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({k: checks[k] for k in ["status", "scan_rows", "masks", "measurement", "normalized_duration_reference_checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
