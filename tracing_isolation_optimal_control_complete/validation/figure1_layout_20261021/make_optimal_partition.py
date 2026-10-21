"""按实测正文宽度绘制单幅成本分区；只求解析标量方程，不积分 ODE。"""
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
from matplotlib.patches import ConnectionPatch, Rectangle
import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUTPUT = PROJECT / "figures/numerical_scenarios/FigN1_optimal_partition"
BASE_SCRIPT = PROJECT / "validation/mainline_focus_20261021/make_optimal_partition.py"
GEOMETRY_SCRIPT = PROJECT / "validation/geometry_proofs_20261021/make_two_layer_phase.py"
CHECKPOINT = PROJECT / "validation/numerical_scenarios/analytic_checkpoints.json"
INPUT = PROJECT / "validation/numerical_scenarios/scenario_inputs.json"
WIDTH_PROBE = PROJECT / "validation/figure1_revision_20261021/measure_linewidth_console.log"
COLORS = {"A": (.95, .95, .95), "WG": (.89, .94, .985),
          "WK": (1, .93, .85), "T": (.95, .90, .975),
          "safe": (.2, .45, .25), "physical": (.6, .6, .6),
          "E1": (.12, .40, .68), "E2": (.82, .36, .10)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def root(fun, lo, hi):
    # Brent 法只求解析标量方程的根，不进行控制优化。
    return brentq(fun, lo, hi, xtol=1e-14, rtol=9e-16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    attempt = HERE / f"figure_attempt{args.attempt}"
    attempt.mkdir(exist_ok=False)
    protected = [p for stem in ("FigN1_regions", "FigN2_waiting", "FigN3_boundary_tracking")
                 for p in (PROJECT / "figures/numerical_scenarios").glob(stem + ".*")]
    before = {str(p.relative_to(PROJECT)): sha(p) for p in protected}
    width_pt = float(re.search(r"FIGUREONE_LINEWIDTH_PT=([0-9.]+)pt",
                              WIDTH_PROBE.read_text(encoding="utf-8")).group(1))
    width_in, height_cm = width_pt / 72.27, 8.0
    spec = importlib.util.spec_from_file_location("unchanged_theoretical_geometry", GEOMETRY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parameters = json.loads(INPUT.read_text(encoding="utf-8"))["parameters"]
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    g = module.Geometry(parameters)
    names = ("h", "ell", "p", "s_A", "s_e", "z_B", "s_B", "Phi_A", "Phi_B")
    errors = {name: abs(getattr(g, name) - checkpoint["geometry"][name]) for name in names}
    assert max(errors.values()) < 2e-11
    zz = np.linspace(g.z_B, g.s_e, 1201)
    switch = np.array([g.switch_point(z) for z in zz])
    sg, ig = switch.T
    theta = lambda s, i: (s - g.h) / (i * (s - g.p))
    theta_residual = np.abs(theta(sg[:-1], ig[:-1]) - theta(zz[:-1], g.a(zz[:-1])))
    assert np.max(theta_residual) < 2e-10

    trajectories, endpoint_evidence = {}, {}
    source = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    macros = {name: float(re.search(r"\\providecommand\{\\" + name + r"\}\{([0-9.]+)\}", source).group(1))
              for name in ("NumSwitchSEOneRef", "NumSwitchIEOneRef")}
    for name, initial in (("E1", (.75, .01)), ("E2", (.99, .01))):
        phi0 = g.phi(*initial)
        if name == "E1":
            release = root(lambda z: g.phi(*g.switch_point(z)) - phi0, g.z_B, g.s_e)
            start_s, start_i = g.switch_point(release)
            contact = None
            natural_s = np.linspace(initial[0], start_s, 601)
            natural_i = phi0 - natural_s + g.h * np.log(natural_s)
            segments = [(natural_s, natural_i)]
        else:
            contact = root(lambda s: g.phi(s, g.K) - phi0, g.h, initial[0])
            start_s, start_i = g.s_B, g.K
            release = root(lambda s: g.K + g.ell * np.log(s / g.s_B) - g.a(s), g.h, g.s_e)
            natural_s = np.linspace(initial[0], contact, 601)
            natural_i = phi0 - natural_s + g.h * np.log(natural_s)
            segments = [(natural_s, natural_i), (np.linspace(contact, g.s_B, 401), np.full(401, g.K))]
        full_s = np.linspace(start_s, release, 401)
        full_i = start_i + g.ell * np.log(full_s / start_s)
        segments.append((full_s, full_i))
        trajectories[name] = segments
        residuals = {
            "natural_initial_point": max(abs(natural_s[0] - initial[0]), abs(natural_i[0] - initial[1])),
            "natural_Phi_conservation": float(np.max(np.abs(g.phi(natural_s, natural_i) - phi0))),
            "natural_end_i": abs(float(natural_i[-1]) - (start_i if contact is None else g.K)),
            "tracking_Psi_conservation": float(np.max(np.abs(full_i - g.ell * np.log(full_s) - (start_i - g.ell * np.log(start_s))))),
            "tracking_end_on_safe_boundary": abs(float(full_i[-1]) - g.a(release)),
        }
        if name == "E1":
            residuals.update({"switch_on_Gamma_K": max(abs(g.switch_point(release)[0] - start_s), abs(g.switch_point(release)[1] - start_i)),
                              "switch_Theta_matching": abs(theta(start_s, start_i) - theta(release, g.a(release)))})
            macro_errors = {"s": abs(start_s - macros["NumSwitchSEOneRef"]), "i": abs(start_i - macros["NumSwitchIEOneRef"])}
            assert max(macro_errors.values()) < 5e-9
        else:
            residuals.update({"capacity_contact_Phi_conservation": abs(g.phi(contact, g.K) - phi0),
                              "capacity_end_s_B": abs(float(segments[1][0][-1]) - g.s_B),
                              "capacity_i_K": float(np.max(np.abs(segments[1][1] - g.K))),
                              "release_matches_z_B": abs(release - g.z_B)})
            macro_errors = None
        assert max(residuals.values()) < 2e-11
        assert all(np.all(ii >= 0) and np.all(ii <= g.K + 1e-12) and np.all(ss + ii <= 1 + 1e-12) for ss, ii in segments)
        expected = next(item for item in checkpoint["cases"] if item["case_id"] == name)
        point_errors = {"s_full": abs(start_s - expected["s_full"]), "i_full": abs(start_i - expected["i_full"]),
                        "s_release": abs(release - expected["s_release"]), "i_release": abs(float(full_i[-1]) - expected["i_release"])}
        assert max(point_errors.values()) < 2e-11
        endpoint_evidence[name] = {"initial": initial, "capacity_contact": None if contact is None else [contact, g.K],
                                  "full_tracking_start": [start_s, start_i], "release": [release, float(full_i[-1])],
                                  "endpoint_residuals": residuals, "checkpoint_errors": point_errors,
                                  "main_tex_rounded_macro_errors": macro_errors, "all_sampled_points_in_D": True}

    def capacity_cost(high, low):
        return g.beta / (g.K * (1 - g.beta)) * (math.log(high / low) - g.beta * math.log((high - g.p) / (low - g.p)))

    contact = endpoint_evidence["E2"]["capacity_contact"][0]
    full_final_i = endpoint_evidence["E2"]["release"][1]
    boundary_cost, tracking_cost = capacity_cost(contact, g.s_B), math.log(g.K / full_final_i) / g.h
    optimal_cost = boundary_cost + tracking_cost
    hold_cost = capacity_cost(contact, g.h)
    saving_percent = 100 * (hold_cost - optimal_cost) / hold_cost
    excess_percent = 100 * (hold_cost - optimal_cost) / optimal_cost
    assert f"{saving_percent:.2f}" == "3.10"
    assert "3.10\\%" in source
    expected_E2 = next(item for item in checkpoint["cases"] if item["case_id"] == "E2")
    assert abs(optimal_cost - expected_E2["J_reference"]) < 2e-12

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
        "mathtext.fontset": "stix", "font.size": 9, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": .6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": None})
    fig = plt.figure(figsize=(width_in, height_cm / 2.54))
    main_ax = fig.add_axes([.075, .145, .905, .80])
    inset = fig.add_axes([.107, .205, .270, .3033])
    inset_xlim, inset_ylim = (.42, .60), (.10, .166)

    def background(ax, zoom=False):
        grid = np.linspace(.15, 1, 6001)
        top = np.minimum(g.K, 1 - grid)
        safe_raw = np.where(grid <= g.h, g.K, g.a(grid))
        safe = np.minimum(top, np.maximum(0, safe_raw))
        boundary_phi = np.clip(g.Phi_B - grid + g.h * np.log(grid), safe, top)
        gamma = np.interp(grid, sg[::-1], ig[::-1], left=0, right=1e6)
        wg_top = np.maximum(safe, np.minimum(boundary_phi, gamma))
        ax.fill_between(grid, 0, safe, color=COLORS["A"], lw=0)
        ax.fill_between(grid, safe, wg_top, color=COLORS["WG"], lw=0)
        ax.fill_between(grid, wg_top, boundary_phi, color=COLORS["T"], lw=0)
        ax.fill_between(grid, boundary_phi, top, color=COLORS["WK"], lw=0)
        sa = np.linspace(g.h, g.s_A, 901)
        ax.plot(sa, g.a(sa), color=COLORS["safe"], lw=1.15, zorder=5)
        ax.plot(sg, ig, "k-", lw=1.05, zorder=6)
        ps = np.linspace(g.s_B, 1, 1201)
        pi = g.Phi_B - ps + g.h * np.log(ps)
        mask = (pi >= 0) & (ps + pi <= 1)
        ax.plot(ps[mask], pi[mask], "k:", lw=1.0, zorder=5)
        ax.plot([.15, 1 - g.K], [g.K, g.K], "k--", lw=.75, zorder=4)
        ax.plot([1 - g.K, 1], [g.K, 0], color=COLORS["physical"], ls="--", lw=.85, zorder=4)
        ax.plot([g.h, g.h], [0, g.K], color=COLORS["physical"], ls="-.", lw=.85, zorder=4)
        ax.set_xlim(inset_xlim if zoom else (.15, 1.01))
        ax.set_ylim(inset_ylim if zoom else (0, .17))
        ax.set_xticks([.42, .50, .60] if zoom else [.2, .4, .6, .8, 1.0])
        ax.set_yticks([.10, .125, .15] if zoom else [0, .05, .10, .15])
        ax.tick_params(direction="out", length=2.5, width=.6, pad=2)
        if not zoom:
            ax.set_xlabel(r"$s$", labelpad=1)
            ax.set_ylabel(r"$i$", rotation=0, labelpad=4)
            ax.spines[["top", "right"]].set_visible(False)
        else:
            ax.patch.set_alpha(1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.tick_params(left=False, right=False, bottom=False, top=False,
                           labelleft=False, labelright=False, labelbottom=False, labeltop=False)
            for spine in ax.spines.values():
                spine.set_color(".4")
                spine.set_linewidth(.6)

    background(main_ax)
    background(inset, zoom=True)
    for ax in (main_ax, inset):
        for name, segments in trajectories.items():
            for sx, iy in segments:
                ax.plot(sx, iy, color=COLORS[name], lw=1.55, zorder=9)
                # 两个坐标系中分别放置箭头，保持可读的物理长度。
                idx = 260 if len(sx) == 601 else 170
                step = 30 if ax is main_ax else 20
                ax.annotate("", xy=(sx[idx + step], iy[idx + step]), xytext=(sx[idx], iy[idx]),
                    arrowprops={"arrowstyle": "-|>", "color": COLORS[name], "lw": 1.05, "mutation_scale": 7}, zorder=10)
        ax.plot([g.h, g.s_B], [g.K, g.K], "o", ms=3.1, mfc="white", mec="k", mew=.8, zorder=12)
    for name in ("E1", "E2"):
        initial = endpoint_evidence[name]["initial"]
        main_ax.plot(*initial, "o", ms=2.6, color=COLORS[name], zorder=11)
    main_ax.text(.762, .014, r"$E_1$", fontsize=9, color=COLORS["E1"])
    main_ax.text(.961, .012, r"$E_2$", fontsize=9, color=COLORS["E2"], ha="right")
    main_ax.text(.224, .111, r"$\mathcal{A}$", fontsize=9)
    main_ax.text(.635, .081, r"$\mathcal{W}_{\Gamma}$", fontsize=9)
    main_ax.text(.785, .109, r"$\mathcal{W}_{K}$", fontsize=9)
    main_ax.text(.660, .156, r"$\mathcal{B}$", fontsize=9, ha="center")
    main_ax.text(g.h, .154, r"$h$", fontsize=9, ha="center")
    main_ax.text(g.s_B, .154, r"$s_B$", fontsize=9, ha="center")
    main_ax.text(.452, .139, r"$\mathcal{T}$", fontsize=9, ha="center", va="center")
    main_ax.annotate(r"$\partial\mathcal{A}$", xy=(.610, float(g.a(.610))), xytext=(.560, .025),
                     fontsize=9, color=COLORS["safe"], arrowprops={"arrowstyle": "-", "lw": .5, "color": COLORS["safe"]})
    main_ax.annotate(r"$\Gamma_K$", xy=(.528, float(np.interp(.528, sg[::-1], ig[::-1]))),
                     xytext=(.560, .120), fontsize=9, arrowprops={"arrowstyle": "-", "lw": .5, "color": "k"})
    main_ax.annotate(r"$\Phi=\Phi_B$", xy=(.744, float(g.Phi_B - .744 + g.h * np.log(.744))),
                     xytext=(.790, .055), fontsize=9, arrowprops={"arrowstyle": "-", "lw": .5, "color": "k"})
    main_ax.text(.943, .104, r"$s+i=1$", fontsize=9, rotation=-61, ha="center", color=".4")
    main_ax.text(.625, .050, r"$q=0$", fontsize=9, color=COLORS["E1"])
    main_ax.text(.935, .077, r"$q=0$", fontsize=9, color=COLORS["E2"])
    main_ax.text(.710, .137, r"$q=q_B$", fontsize=9, color=COLORS["E2"])
    # 完全跟踪段的两条标签移至放大图，避免压在主图的短曲线上。
    inset.text(.475, .139, r"$\mathcal{T}$", fontsize=9, ha="center", va="center")
    inset.text(.598, .110, r"$\mathcal{W}_{\Gamma}$", fontsize=9, ha="right")
    e1_s, e1_i = endpoint_evidence["E1"]["full_tracking_start"]
    inset.annotate(r"$q=1$", xy=(.491, e1_i + g.ell * np.log(.491 / e1_s)),
                   xytext=(.503, .107), fontsize=9, color=COLORS["E1"],
                   arrowprops={"arrowstyle": "-", "lw": .5, "color": COLORS["E1"]})
    inset.annotate(r"$q=1$", xy=(.516, g.K + g.ell * np.log(.516 / g.s_B)),
                   xytext=(.548, .123), fontsize=9, color=COLORS["E2"],
                   arrowprops={"arrowstyle": "-", "lw": .5, "color": COLORS["E2"]})
    # 连接线只经过 A 内的空白处；目标框不以填色覆盖轨道。
    zoom_box = Rectangle((inset_xlim[0], inset_ylim[0]), inset_xlim[1] - inset_xlim[0],
                         inset_ylim[1] - inset_ylim[0], fill=False, edgecolor=".5", ls="--", lw=.55, zorder=13)
    main_ax.add_patch(zoom_box)
    for point, target in [((.42, .10), (0, 1)), ((.60, .10), (1, 1))]:
        fig.add_artist(ConnectionPatch(point, target, coordsA=main_ax.transData, coordsB=inset.transAxes,
                                      color=".55", lw=.5, zorder=1))
    fig.canvas.draw()
    # 标注的实际文本框与密采样曲线核查；引线不属于标签本身。
    renderer = fig.canvas.get_renderer()
    label_intersections, label_pair_intersections, text_boxes = [], [], []
    for axis_name, ax in (("main", main_ax), ("inset", inset)):
        candidates = [*ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels(), ax.xaxis.label, ax.yaxis.label]
        for text_item in candidates:
            if not text_item.get_text() or not text_item.get_visible():
                continue
            bbox = text_item.get_window_extent(renderer)
            # Annotation.get_window_extent 包含引线；只用其 Text 基类的文字框。
            if isinstance(text_item, matplotlib.text.Annotation):
                bbox = matplotlib.text.Text.get_window_extent(text_item, renderer)
            text_boxes.append((axis_name, text_item.get_text(), bbox))
            for line_index, line in enumerate(ax.lines):
                xdata, ydata = np.asarray(line.get_xdata()), np.asarray(line.get_ydata())
                if len(xdata) < 2:
                    continue
                dense_x, dense_y = [], []
                for xa, xb, ya, yb in zip(xdata[:-1], xdata[1:], ydata[:-1], ydata[1:]):
                    count = 2001 if len(xdata) <= 3 else 9
                    dense_x.extend(np.linspace(xa, xb, count))
                    dense_y.extend(np.linspace(ya, yb, count))
                points = np.column_stack((dense_x, dense_y))
                valid = ((points[:, 0] >= ax.get_xlim()[0]) & (points[:, 0] <= ax.get_xlim()[1]) &
                         (points[:, 1] >= ax.get_ylim()[0]) & (points[:, 1] <= ax.get_ylim()[1]))
                screen = ax.transData.transform(points[valid])
                hit = ((screen[:, 0] >= bbox.x0) & (screen[:, 0] <= bbox.x1) &
                       (screen[:, 1] >= bbox.y0) & (screen[:, 1] <= bbox.y1))
                if np.any(hit):
                    label_intersections.append({"axis": axis_name, "label": text_item.get_text(), "line_index": line_index,
                                                "line_color": str(line.get_color()), "line_style": line.get_linestyle()})
    for n, (axis_a, text_a, box_a) in enumerate(text_boxes):
        for axis_b, text_b, box_b in text_boxes[n + 1:]:
            if box_a.overlaps(box_b):
                label_pair_intersections.append({"axis_a": axis_a, "axis_b": axis_b, "label_a": text_a, "label_b": text_b})
    label_checks = {"label_curve_intersections": label_intersections,
                    "label_pair_intersections": label_pair_intersections,
                    "method": "all visible annotation, tick and axis-label text boxes; own-axis dense visible Line2D samples and all cross-axis text pairs; annotation leaders excluded",
                    "visible_text_boxes_checked": len(text_boxes), "inset_coordinate_ticks": "hidden"}
    write_json(attempt / "label_collision_checks.json", label_checks)
    write_json(HERE / "label_collision_checks.json", label_checks)
    assert not label_intersections and not label_pair_intersections, label_checks
    immediately_before = {ext: sha(OUTPUT.with_suffix(ext)) if OUTPUT.with_suffix(ext).exists() else None for ext in (".pdf", ".png")}
    for ext in (".pdf", ".png"):
        rendered = attempt / (OUTPUT.name + ext)
        kwargs = {"metadata": {"Title": "Analytical optimal partition", "Creator": "make_optimal_partition.py"}} if ext == ".pdf" else {"dpi": 300}
        fig.savefig(rendered, **kwargs)
        temporary = OUTPUT.with_name(OUTPUT.name + "_replacement").with_suffix(ext)
        shutil.copyfile(rendered, temporary)
        os.replace(temporary, OUTPUT.with_suffix(ext))
    plt.close(fig)
    media = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", OUTPUT.with_suffix(".pdf").read_bytes())
    assert media is not None
    pdf_width, pdf_height = map(float, media.groups())
    expected_pdf_width = width_pt * 72 / 72.27
    assert abs(pdf_width - expected_pdf_width) < 1e-6
    assert abs(pdf_height - height_cm / 2.54 * 72) < 1e-6
    assert before == {str(p.relative_to(PROJECT)): sha(p) for p in protected}
    evidence = {"status": "analytical_geometry_only", "attempt": args.attempt,
        "optimizer_calls": 0, "ocp_solves": 0, "ode_integrations": 0, "matlab_calls": 0,
        "parameters": parameters, "measurement": {"linewidth_tex_pt": width_pt, "width_cm": width_in * 2.54,
            "height_cm": height_cm, "pdf_width_big_pt": pdf_width, "pdf_height_big_pt": pdf_height,
            "insertion_scale": expected_pdf_width / pdf_width, "tick_font_pt": 8, "label_font_pt": 9,
            "inset_xlim": inset_xlim, "inset_ylim": inset_ylim,
            "inset_main_data_bbox": [.15 + (.107 - .075) / .905 * .86, .15 + (.377 - .075) / .905 * .86,
                                     (.205 - .145) / .80 * .17, (.5083 - .145) / .80 * .17],
            "inset_linear_size_relative_to_previous": .9,
            "inset_coordinate_ticks_visible": False,
            "T_main_anchor": [.452, .139], "T_main_has_leader": False,
            "comparison_path_visible": False,
            "zoom_box_top": .166},
        "geometry": {name: getattr(g, name) for name in names}, "checkpoint_errors": errors,
        "checkpoint_max_absolute_error": max(errors.values()), "theta_max_absolute_residual": float(np.max(theta_residual)),
        "trajectories": endpoint_evidence,
        "E2_analytic_cost": {"boundary_cost_to_s_B": boundary_cost, "full_tracking_cost": tracking_cost,
            "optimal_total": optimal_cost, "capacity_until_h_total": hold_cost,
            "checkpoint_optimal_cost_error": abs(optimal_cost - expected_E2["J_reference"]),
            "saving_percent_relative_to_comparison": saving_percent, "saving_percent_rounded": f"{saving_percent:.2f}",
            "comparison_excess_percent_relative_to_optimal": excess_percent,
            "denominator_note": "正文3.10%以纯容量对照成本为分母；若用最优成本作分母则为3.20%，不能混用。",
            "main_tex_3_10_percent_present": True},
        "style": {"colors": COLORS, "s_h_linestyle": "-.", "s_plus_i_one_linestyle": "--", "no_legend": True},
        "label_collision_checks": label_checks,
        "protected_outputs_unchanged": before,
        "sources_sha256": {str(p.relative_to(PROJECT)): sha(p) for p in [Path(__file__), BASE_SCRIPT, GEOMETRY_SCRIPT, INPUT, CHECKPOINT, WIDTH_PROBE]},
        "immediately_before_outputs_sha256": immediately_before,
        "outputs_sha256": {str(OUTPUT.with_suffix(ext).relative_to(PROJECT)): sha(OUTPUT.with_suffix(ext)) for ext in (".pdf", ".png")}}
    write_json(attempt / "analytic_checks.json", evidence)
    write_json(HERE / "analytic_checks.json", evidence)
    print(json.dumps({"attempt": args.attempt, "geometry_max_error": max(errors.values()),
        "theta_max_residual": float(np.max(theta_residual)), "E2_saving_percent": saving_percent,
        "size_cm": [width_in * 2.54, height_cm], "optimizer_calls": 0, "ocp_solves": 0, "matlab_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
