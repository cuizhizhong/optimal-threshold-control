"""按实测正文宽度绘制解析两层几何；不积分 ODE，不调用 MATLAB、优化器或 OCP。"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.integrate import quad
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUTPUT = PROJECT / "figures/numerical_scenarios/FigN1_two_layers"
OLD_SCRIPT = PROJECT / "validation/geometry_proofs_20261021/make_two_layer_phase.py"
CHECKPOINT = PROJECT / "validation/numerical_scenarios/analytic_checkpoints.json"
INPUT = PROJECT / "validation/numerical_scenarios/scenario_inputs.json"
QVALUES = (0.0, 0.1, 0.2, 0.4)
COLORS = {"A": (.95, .95, .95), "WG": (.89, .94, .985),
          "WK": (1, .93, .85), "T": (.95, .90, .975),
          "safe": (.2, .45, .25), "physical": (.6, .6, .6),
          "trajectory": (.18, .39, .66)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def root(fun, lo, hi):
    # Brent 法只求解析标量方程的根，不进行控制优化。
    return brentq(fun, lo, hi, xtol=1e-14, rtol=9e-16)


def envelope(s, q, g):
    """C3 命题：全水平 K 段接常控制 q 的不变量包络。"""
    s = np.asarray(s)
    varpi = g.beta + (1 - g.beta) * q
    nu = g.beta * (1 - q) / varpi
    d = g.gamma / (g.c * varpi)
    hq = g.h / (1 - q)
    return np.where(s <= hq, g.K, g.K - nu * (s - hq) + d * np.log(s / hq))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    attempt = HERE / f"figure1_attempt{args.attempt}"
    attempt.mkdir(exist_ok=False)
    probe = (HERE / "measure_linewidth_console.log").read_text(encoding="utf-8", errors="replace")
    width_pt = float(re.search(r"FIGUREONE_LINEWIDTH_PT=([0-9.]+)pt", probe).group(1))
    width_in = width_pt / 72.27  # TeX 的 pt 与 PDF/Matplotlib 的 1/72 inch 不同。
    width_cm, height_cm = width_in * 2.54, 6.9
    spec = importlib.util.spec_from_file_location("unchanged_theoretical_geometry", OLD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parameters = json.loads(INPUT.read_text(encoding="utf-8"))["parameters"]
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    g = module.Geometry(parameters)
    names = ("h", "ell", "p", "s_A", "s_e", "z_B", "s_B", "Phi_A", "Phi_B")
    errors = {name: abs(getattr(g, name) - checkpoint["geometry"][name]) for name in names}
    assert max(errors.values()) < 2e-11
    zz = np.linspace(g.z_B, g.s_e, 1001)
    switch = np.array([g.switch_point(z) for z in zz])
    sg, ig = switch.T
    theta = lambda s, i: (s - g.h) / (i * (s - g.p))
    theta_residual = np.abs(theta(sg[:-1], ig[:-1]) - theta(zz[:-1], g.a(zz[:-1])))
    assert np.max(theta_residual) < 2e-10

    envelopes = []
    area_D = g.K - .5 * g.K ** 2
    for q in QVALUES:
        hq = g.h / (1 - q)
        varpi = g.beta + (1 - g.beta) * q
        nu, d = g.beta * (1 - q) / varpi, g.gamma / (g.c * varpi)
        zero = root(lambda s: envelope(s, q, g), hq, 2)
        physical = root(lambda s: envelope(s, q, g) + s - 1, hq, 1) if zero > 1 else None
        area, area_error = quad(lambda s: max(0., min(g.K, 1-s) - max(0., envelope(s, q, g))),
                                0, 1, points=sorted({hq, 1-g.K, min(zero, 1), *( [physical] if physical else [])}),
                                epsabs=2e-13, epsrel=2e-13)
        item = {"qbar": q, "h_qbar": hq, "envelope_at_h": float(envelope(hq, q, g)),
                "tangency_value_residual": float(envelope(hq, q, g) - g.K),
                "tangency_right_derivative": -nu + d/hq, "zero_s": zero,
                "physical_intersection_s": physical, "infeasible_area": area,
                "complete_D_area": area_D, "infeasible_fraction_complete_D": area / area_D,
                "area_quadrature_error": area_error}
        assert abs(item["tangency_value_residual"]) < 1e-13
        assert abs(item["tangency_right_derivative"]) < 1e-13
        envelopes.append(item)

    x0 = (.99, .01)
    phi0 = g.phi(*x0)
    s1 = root(lambda s: g.phi(s, g.K) - phi0, g.h, x0[0])
    s_release = root(lambda s: g.K + g.ell * np.log(s/g.s_B) - g.a(s), g.h, g.s_e)
    i_release = float(g.a(s_release))
    natural_s = np.linspace(x0[0], s1, 501)
    natural_i = phi0 - natural_s + g.h*np.log(natural_s)
    capacity_s = np.linspace(s1, g.s_B, 251)
    capacity_i = np.full_like(capacity_s, g.K)
    tracking_s = np.linspace(g.s_B, s_release, 301)
    tracking_i = g.K + g.ell*np.log(tracking_s/g.s_B)
    trajectory = [(natural_s, natural_i), (capacity_s, capacity_i), (tracking_s, tracking_i)]
    endpoint_errors = {
        "capacity_contact_Phi": abs(g.phi(s1, g.K)-phi0),
        "natural_starts_at_x0": float(max(abs(natural_s[0]-x0[0]), abs(natural_i[0]-x0[1]))),
        "natural_ends_at_capacity": abs(float(natural_i[-1])-g.K),
        "capacity_ends_at_s_B": abs(float(capacity_s[-1])-g.s_B),
        "tracking_starts_at_s_B_K": abs(float(tracking_i[0])-g.K),
        "tracking_ends_at_safety": abs(float(tracking_i[-1])-g.a(s_release)),
        "release_matches_z_B": abs(s_release-g.z_B),
        "full_tracking_Psi": float(np.max(np.abs(tracking_i-g.ell*np.log(tracking_s) - (g.K-g.ell*np.log(g.s_B))))),
    }
    assert max(endpoint_errors.values()) < 2e-11
    for ss, ii in trajectory:
        assert np.all(ii >= 0) and np.all(ii <= g.K+1e-12) and np.all(ss+ii <= 1+1e-12)

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
        "mathtext.fontset": "stix", "font.size": 9, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": .6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": None})
    fig = plt.figure(figsize=(width_in, height_cm/2.54))
    left = fig.add_axes([.065, .16, .405, .745])
    right = fig.add_axes([.575, .485, .412, .42])
    # 放大图在主坐标轴外，不覆盖主图任何曲线。
    inset = fig.add_axes([.665, .125, .305, .235])
    inset_xlim, inset_ylim = (.42, .60), (.10, .16)
    inset_gamma_span_cm = width_cm * .305 * (g.s_B-g.s_e)/(inset_xlim[1]-inset_xlim[0])
    assert inset_gamma_span_cm >= 2

    def common(ax, zoom=False):
        ax.set_xlim(inset_xlim if zoom else (.15, 1.01))
        ax.set_ylim(inset_ylim if zoom else (0, .17))
        ax.set_xlabel(r"$s$", labelpad=1)
        ax.set_ylabel(r"$i$", rotation=0, labelpad=5)
        ax.set_xticks([.42, .50, .60] if zoom else [.2, .4, .6, .8, 1.0])
        ax.set_yticks([.10, .15] if zoom else [0, .05, .10, .15])
        ax.tick_params(direction="out", length=2.5, width=.6, pad=2)
        ax.spines[["top", "right"]].set_visible(False)
        ax.plot([.15, 1-g.K], [g.K, g.K], "k--", lw=.8, zorder=5)
        ax.plot([1-g.K, 1], [g.K, 0], color=COLORS["physical"], ls="--", lw=.85, zorder=5)
        ax.plot([g.h, g.h], [0, g.K], color=COLORS["physical"], ls="-.", lw=.85, zorder=5)
        sa = np.linspace(g.h, g.s_A, 701)
        ax.plot(sa, g.a(sa), color=COLORS["safe"], lw=1.05, zorder=7)

    common(left)
    left.set_ylim(0, .19)
    ss = np.linspace(.15, 1, 4001)
    ceiling = np.minimum(g.K, 1-ss)
    safe = np.minimum(ceiling, np.maximum(0, envelope(ss, 0, g)))
    left.fill_between(ss, 0, safe, color=COLORS["A"], lw=0)
    qcolors = [COLORS["safe"], (.25, .43, .63), (.68, .43, .20), (.49, .34, .58)]
    label_s = [.53, .66, .78, .88]
    label_offsets = [(-26, -10), (-33, -23), (3, 5), (3, 5)]
    tangency_text = [(.254, .165), (.333, .182), (.425, .165), (.535, .180)]
    for idx, q in enumerate(QVALUES):
        hq = g.h/(1-q)
        high = envelopes[idx]["physical_intersection_s"] or envelopes[idx]["zero_s"]
        ssq = np.linspace(hq, min(high, 1), 1001)
        iiq = envelope(ssq, q, g)
        valid = (iiq >= -1e-12) & (iiq <= g.K+1e-12) & (ssq+iiq <= 1+1e-12)
        left.plot(ssq[valid], np.maximum(0, iiq[valid]), color=qcolors[idx], lw=1.05, zorder=7)
        sx = label_s[idx]
        left.annotate(r"$\bar q="+f"{q:g}"+"$", xy=(sx, envelope(sx,q,g)),
                      xytext=label_offsets[idx], textcoords="offset points", fontsize=9,
                      color=qcolors[idx], zorder=10,
                      arrowprops={"arrowstyle":"-", "lw":.5, "color":qcolors[idx]} if idx<2 else None)
        left.plot(hq, g.K, "o", ms=2.5, color=qcolors[idx], zorder=10)
        tx, ty = tangency_text[idx]
        left.annotate(f"${hq:.3f}$", xy=(hq,g.K), xytext=(tx,ty), ha="center", fontsize=8,
                      arrowprops={"arrowstyle":"-", "color":qcolors[idx], "lw":.5}, color=qcolors[idx])
    left.text(.22,.061,r"$\mathcal{A}=\mathcal{A}^0$",fontsize=10)
    left.text(.79,.173,r"$\mathcal{V}_1=\mathcal{D}$",fontsize=9,ha="center")

    def optimal_background(ax):
        grid = np.linspace(.15, 1, 5001)
        top = np.minimum(g.K, 1-grid)
        base = np.minimum(top, np.maximum(0, envelope(grid,0,g)))
        boundary_phi = np.clip(g.Phi_B-grid+g.h*np.log(grid), base, top)
        gamma = np.interp(grid, sg[::-1], ig[::-1], left=0, right=1e6)
        wg_top = np.maximum(base,np.minimum(boundary_phi,gamma))
        ax.fill_between(grid,0,base,color=COLORS["A"],lw=0)
        ax.fill_between(grid,base,wg_top,color=COLORS["WG"],lw=0)
        ax.fill_between(grid,wg_top,boundary_phi,color=COLORS["T"],lw=0)
        ax.fill_between(grid,boundary_phi,top,color=COLORS["WK"],lw=0)
        ax.plot(sg,ig,"k-",lw=1.1,zorder=8)
        ps = np.linspace(g.s_B,1,1001)
        pi = g.Phi_B-ps+g.h*np.log(ps)
        mask = (pi >= 0) & (ps+pi <= 1)
        ax.plot(ps[mask],pi[mask],"k:",lw=.95,zorder=7)
        common(ax,zoom=(ax is inset))

    def draw_trajectory(ax, arrows=True):
        for n, (sx, iy) in enumerate(trajectory):
            ax.plot(sx,iy,color=COLORS["trajectory"],lw=1.45,zorder=11)
            k = [220,105,130][n]
            if arrows:
                ax.annotate("",xy=(sx[k+30],iy[k+30]),xytext=(sx[k],iy[k]),
                    arrowprops={"arrowstyle":"-|>","color":COLORS["trajectory"],"lw":1,"mutation_scale":7},zorder=12)
        ax.plot([x0[0],s1,g.s_B,s_release],[x0[1],g.K,g.K,i_release],"o",
                color=COLORS["trajectory"],ms=2.4,zorder=12)

    optimal_background(right)
    optimal_background(inset)
    draw_trajectory(right)
    draw_trajectory(inset)
    right.text(.23,.050,r"$\mathcal{A}$",fontsize=10)
    right.text(.615,.073,r"$\mathcal{W}_\Gamma$",fontsize=9.5)
    right.text(.80,.065,r"$\mathcal{W}_K$",fontsize=9.5)
    right.text(.678,.158,r"$\mathcal{B}$",fontsize=9.5,ha="center")
    right.text(.97,.026,r"$x_0$",fontsize=9,ha="right")
    # h 与 s_B 使用独立的刻线/标号，避开邻近的数值刻度。
    for value, label in [(g.h,r"$h$"),(g.s_B,r"$s_B$")]:
        right.plot([value,value],[-.007,0],transform=right.get_xaxis_transform(),color="k",lw=.6,clip_on=False)
        right.text(value,-.105,label,transform=right.get_xaxis_transform(),ha="center",va="top",fontsize=8)
    inset.text(.437,.109,r"$\mathcal{A}$",fontsize=9)
    inset.text(.478,.134,r"$\mathcal{T}$",fontsize=10)
    inset.text(.558,.112,r"$\mathcal{W}_\Gamma$",fontsize=9)
    inset.annotate(r"$\Gamma_K$",xy=(.516,float(np.interp(.516,sg[::-1],ig[::-1]))),
                   xytext=(.552,.132),fontsize=9,arrowprops={"arrowstyle":"-","lw":.5,"color":"k"})
    right.add_patch(Rectangle((.42,.10),.18,.06,fill=False,lw=.55,edgecolor=".45",ls="--",zorder=13))
    fig.text(.065,.955,"(a)",fontsize=9,ha="left",va="top")
    fig.text(.575,.955,"(b)",fontsize=9,ha="left",va="top")
    fig.canvas.draw()
    before_current = {ext:sha(OUTPUT.with_suffix(ext)) for ext in (".pdf",".png")}
    # 先完整生成到本次记录目录，再原子替换，避免图形检查短暂读取时留下半文件。
    for ext in (".pdf", ".png"):
        rendered = attempt / ("FigN1_two_layers"+ext)
        kwargs = {"metadata":{"Title":"Two-layer analytical phase geometry","Creator":"make_figure1.py"}} if ext == ".pdf" else {"dpi":300}
        fig.savefig(rendered, **kwargs)
        temporary = OUTPUT.with_name(OUTPUT.name+"_replacement").with_suffix(ext)
        shutil.copyfile(rendered, temporary)
        os.replace(temporary, OUTPUT.with_suffix(ext))
    plt.close(fig)
    # Matplotlib 的 MediaBox 为未压缩页字典；直接读取可避免混用 Python 环境。
    media = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", OUTPUT.with_suffix(".pdf").read_bytes())
    assert media is not None
    pdf_width = float(media.group(1))
    expected_pdf_width = width_pt * 72/72.27
    assert abs(pdf_width-expected_pdf_width)<1e-6
    baseline = {ext:sha(HERE/f"baseline_FigN1_two_layers{ext}") for ext in (".pdf",".png")}
    evidence={"status":"analytical_geometry_only", "attempt":args.attempt,"optimizer_calls":0,"ocp_solves":0,
        "ode_integrations":0,"matlab_calls":0,"parameters":parameters,
        "measurement":{"linewidth_tex_pt":width_pt,"width_cm":width_cm,"height_cm":height_cm,
                       "pdf_width_big_pt":pdf_width,"insertion_scale":expected_pdf_width/pdf_width,
                       "tick_font_pt":8,"axis_label_font_pt":9,"region_font_pt":[9,10],
                       "inset_xlim":inset_xlim,"inset_ylim":inset_ylim,
                       "inset_width_cm":width_cm*.305,"inset_Gamma_horizontal_span_cm":inset_gamma_span_cm,
                       "inset_does_not_overlap_main_axes":True},
        "geometry":{name:getattr(g,name) for name in names},"checkpoint_errors":errors,
        "checkpoint_max_absolute_error":max(errors.values()),
        "theta_max_absolute_residual":float(np.max(theta_residual)),"envelopes":envelopes,
        "trajectory":{"x0":x0,"capacity_contact":[s1,g.K],"capacity_end":[g.s_B,g.K],
                      "release":[s_release,i_release],"endpoint_residuals":endpoint_errors,
                      "all_sampled_points_in_D":True},
        "optional_hold_until_h_segment":"omitted_for_legibility",
        "sources_sha256":{str(p.relative_to(PROJECT)):sha(p) for p in [Path(__file__),OLD_SCRIPT,INPUT,CHECKPOINT]},
        "baseline_outputs_sha256":baseline,"immediately_before_outputs_sha256":before_current,
        "outputs_sha256":{str(OUTPUT.with_suffix(ext).relative_to(PROJECT)):sha(OUTPUT.with_suffix(ext)) for ext in (".pdf",".png")}}
    write_json(attempt/"analytic_checks.json",evidence)
    write_json(HERE/"analytic_checks.json",evidence)
    print(json.dumps({"attempt":args.attempt,"geometry_max_error":max(errors.values()),
        "theta_max_residual":float(np.max(theta_residual)),"inset_Gamma_span_cm":inset_gamma_span_cm,
        "size_cm":[width_cm,height_cm],"optimizer_calls":0,"ocp_solves":0},ensure_ascii=False))


if __name__ == "__main__":
    main()
