#!/usr/bin/env python3
"""生成两层理论相图；仅计算解析几何和标量方程，不调用优化器或 OCP。"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.optimize import brentq


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUT = ROOT / "validation/numerical_scenarios/scenario_inputs.json"
CHECKPOINT = ROOT / "validation/numerical_scenarios/analytic_checkpoints.json"
OUTPUT = ROOT / "figures/numerical_scenarios/FigN1_two_layers"
QBAR = 0.4


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root(fun, left, right):
    return brentq(fun, left, right, xtol=1e-14, rtol=9e-16)


class Geometry:
    """与 build_theory_geometry.m 相同的解析定义，独立用双精度求根。"""

    def __init__(self, parameters):
        self.beta, self.c, self.gamma, self.K = (
            float(parameters[key]) for key in ("beta", "c", "gamma", "K")
        )
        self.h = self.gamma / (self.beta * self.c)
        self.ell = self.gamma / self.c
        self.p = self.h - self.ell
        self.Phi_A = self.K + self.h - self.h * math.log(self.h)
        hi = max(1, 2 * self.h)
        while self.a(hi) > 0:
            hi *= 2
        self.s_A = root(self.a, self.h, hi)
        self.s_e = root(lambda s: self.a(s) - self.g(s), self.h, self.s_A)
        lo = (self.h + self.s_e) / 2
        while self.switch_point(lo)[1] < self.K:
            lo = self.h + (lo - self.h) / 10
        self.z_B = root(lambda z: self.switch_point(z)[1] - self.K, lo, self.s_e)
        self.s_B, _ = self.switch_point(self.z_B)
        self.Phi_B = self.phi(self.s_B, self.K)

    def a(self, s):
        return self.Phi_A - s + self.h * np.log(s)

    def g(self, s):
        return (s - self.h) * (s - self.p) / s

    def phi(self, s, i):
        return i + s - self.h * np.log(s)

    def switch_point(self, z):
        if z == self.s_e:
            return z, float(self.a(z))
        az = self.a(z)

        def equation(d):
            ratio = 1 / z if d == 0 else np.log1p(d / z) / d
            return az - (z - self.h) * (z + d - self.p) * ratio

        hi = max(self.s_e - z, 0.01)
        while equation(hi) > 0:
            hi *= 2
        d = root(equation, 0, hi)
        assert d > 0
        return z + d, float(az + self.ell * np.log1p(d / z))

    def envelope(self, s, qbar):
        """受限能力命题的包络，不延伸到其定义外的 qbar=1。"""
        assert 0 <= qbar < 1
        varpi = self.beta + (1 - self.beta) * qbar
        nu = self.beta * (1 - qbar) / varpi
        d = self.gamma / (self.c * varpi)
        hq = self.h / (1 - qbar)
        s = np.asarray(s, dtype=float)
        return np.where(s <= hq, self.K, self.K - nu * (s - hq) + d * np.log(s / hq))


def main():
    parameters = json.loads(INPUT.read_text(encoding="utf-8"))["parameters"]
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    assert parameters == checkpoint["parameters"]
    assert parameters == {"beta": 0.5, "c": 2.0, "gamma": 0.3, "K": 0.15}
    # 旧图及其 provenance 只取指纹，以运行前后不变作为边界检查。
    protected = sorted((ROOT / "figures/numerical_scenarios").glob("FigN1_regions*"))
    protected += sorted((ROOT / "figures/numerical_scenarios").glob("*provenance*"))
    protected += [ROOT / "data/numerical_scenarios/figure_provenance.json"]
    protected_before = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.is_file()}
    g = Geometry(parameters)
    names = ("h", "ell", "p", "s_A", "s_e", "z_B", "s_B", "Phi_A", "Phi_B")
    errors = {name: abs(getattr(g, name) - checkpoint["geometry"][name]) for name in names}
    assert max(errors.values()) < 2e-11
    z = np.linspace(g.z_B, g.s_e, 701)
    switch = np.array([g.switch_point(v) for v in z])
    sg, ig = switch.T
    assert np.all(np.diff(sg) < 0) and np.all(np.diff(ig) < 0)
    assert abs(ig[0] - g.K) < 2e-12
    assert abs(ig[-1] - g.a(g.s_e)) < 2e-12
    # 原始匹配条件核查；合并端点不是非平凡根。
    theta = lambda s, i: (s - g.h) / (i * (s - g.p))
    theta_errors = np.abs(theta(sg[:-1], ig[:-1]) - theta(z[:-1], g.a(z[:-1])))
    assert np.max(theta_errors) < 2e-10

    s = np.linspace(1e-6, 1, 1801)
    ceiling = np.minimum(g.K, 1 - s)
    safe = np.minimum(ceiling, np.maximum(0, g.envelope(s, 0)))
    limited = np.minimum(ceiling, np.maximum(0, g.envelope(s, QBAR)))
    assert np.all(safe <= limited + 1e-12) and np.all(limited <= ceiling + 1e-12)
    assert np.any(limited < ceiling - 0.01)
    assert np.max(np.abs(g.envelope(s[s >= g.h], 0) - g.a(s[s >= g.h]))) < 1e-12

    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["DejaVu Serif"],
        "font.size": 10, "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42,
        "axes.labelsize": 11, "axes.titlesize": 11, "axes.linewidth": 0.7,
        "xtick.labelsize": 9, "ytick.labelsize": 9,
    })
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.5), sharex=True, sharey=True)
    fig.subplots_adjust(left=.065, right=.985, bottom=.29, top=.84, wspace=.14)
    domain_color = "#edf1f6"
    limited_color = "#c9dce9"
    safe_color = "#d9e8d5"
    safe_line = "#376442"
    limited_line = "#246583"
    region_colors = [safe_color, "#d9e7f4", "#f4dfc5", "#e7d9ec"]
    capacity_color = "#a54c21"

    def common(ax):
        ax.set_xlim(0, 1.01)
        ax.set_ylim(0, .182)
        ax.set_xlabel(r"$s$")
        ax.set_xticks([0, .2, .4, .6, .8, 1])
        ax.set_yticks([0, .05, .10, .15])
        ax.plot([0, 1 - g.K], [g.K, g.K], color=".42", lw=.9)
        ax.plot([1 - g.K, 1], [g.K, 0], color=".4", lw=1.2, ls="--", zorder=6)
        ax.axvline(g.h, color=".45", lw=1.1, ls=":", ymin=0, ymax=g.K/.182, zorder=6)
        ax.text(.018, g.K+.006, r"$i=K$", fontsize=9, color=".35")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", length=3)
        ax.grid(False)
        curve_s = np.linspace(g.h, g.s_A, 501)
        ax.plot(curve_s, g.a(curve_s), color=safe_line, lw=1.6, zorder=7)

    left, right = axes
    left.fill_between(s, 0, ceiling, color=domain_color, linewidth=0)
    left.fill_between(s, 0, limited, color=limited_color, linewidth=0)
    left.fill_between(s, 0, safe, color=safe_color, linewidth=0)
    hq = g.h / (1 - QBAR)
    qs = np.linspace(hq, 1, 701)
    qi = g.envelope(qs, QBAR)
    valid = (qi > 0) & (qs + qi <= 1 + 1e-12)
    left.plot(qs[valid], qi[valid], color=limited_line, lw=1.7, zorder=7)
    left.text(.155, .064, r"$\mathcal{A}=\mathcal{A}^0$", color=safe_line, fontsize=12)
    left.text(.55, .112, r"$\mathcal{V}_{0.4}$", color=limited_line, fontsize=12)
    left.text(.76, .143, r"$\mathcal{D}\setminus\mathcal{V}_{0.4}$", fontsize=10, ha="center")
    left.text(.51, .158, r"$h_{0.4}=0.5$", fontsize=9, color=limited_line)
    left.plot([hq], [g.K], "o", color=limited_line, ms=3, zorder=8)
    left.set_title(r"(a) Constraint feasibility: $\mathcal{V}_1=\mathcal{D}$", pad=12)

    S, I = np.meshgrid(np.linspace(1e-5, 1, 1001), np.linspace(0, g.K, 401))
    gamma_i = np.interp(S, sg[::-1], ig[::-1], left=np.nan, right=np.inf)
    region = 3 * np.ones_like(S)
    region[(S > g.s_e) & (I < gamma_i)] = 1
    region[g.phi(S, I) > g.Phi_B] = 2
    region[(S <= g.h) | (g.phi(S, I) <= g.Phi_A)] = 0
    region = np.ma.masked_where(S + I > 1, region)
    right.contourf(S, I, region, levels=np.arange(-.5, 4.5), cmap=ListedColormap(region_colors), antialiased=False)
    right.plot(sg, ig, color="#222222", lw=1.8, zorder=8)
    boundary_s = np.linspace(g.s_B, 1, 501)
    boundary_i = g.Phi_B - boundary_s + g.h * np.log(boundary_s)
    valid = (boundary_i >= 0) & (boundary_s + boundary_i <= 1)
    right.plot(boundary_s[valid], boundary_i[valid], color=".28", lw=1.2, ls="-.", zorder=7)
    right.plot([g.s_B, 1-g.K], [g.K, g.K], color=capacity_color, lw=3, zorder=9)
    right.plot([g.s_B], [g.K], "o", color=capacity_color, ms=4, zorder=10)
    right.text(g.s_B+.006, g.K+.006, r"$s_B$", fontsize=9, color=capacity_color)
    right.text(.735, .157, r"$\mathcal{B}:\ q_B=1-h/s$", color=capacity_color, ha="center", fontsize=9)
    right.text(.18, .062, r"$\mathcal{A}$", color=safe_line, fontsize=13)
    right.text(.405, .137, r"$\mathcal{T}$", fontsize=12)
    right.text(.632, .065, r"$\mathcal{W}_\Gamma$", fontsize=12)
    right.text(.79, .10, r"$\mathcal{W}_K$", fontsize=12)
    right.set_title(r"(b) Minimum cost partition for $q\in[0,1]$", pad=12)
    for ax in axes:
        common(ax)
    left.set_ylabel(r"$i$")
    left.legend(handles=[
        Patch(fc=domain_color, label=r"$\mathcal{D}=\mathcal{V}_1$"),
        Patch(fc=limited_color, label=r"$\mathcal{V}_{0.4}\setminus\mathcal{A}$"),
        Patch(fc=safe_color, label=r"$\mathcal{A}=\mathcal{A}^0=\mathcal{V}_0$"),
        Line2D([], [], color=limited_line, lw=1.6, label=r"$i=\mathcal{I}_{0.4}(s)$"),
    ], loc="upper center", bbox_to_anchor=(.49, -.25), ncol=2, frameon=False, fontsize=9, handlelength=2)
    right.legend(handles=[
        Line2D([], [], color=safe_line, lw=1.6, label=r"$\partial\mathcal{A}$"),
        Line2D([], [], color="#222222", lw=1.8, label=r"$\Gamma_K$"),
        Line2D([], [], color=".28", ls="-.", lw=1.2, label=r"$\Phi=\Phi_B$"),
        Line2D([], [], color=capacity_color, lw=3, label=r"$\mathcal{B}$ (capacity arc)"),
    ], loc="upper center", bbox_to_anchor=(.5, -.25), ncol=2, frameon=False, fontsize=9, handlelength=2)
    fig.text(.5, .935, r"$\beta=0.5,\quad c=2,\quad\gamma=0.3,\quad K=0.15,\quad h=0.3$", ha="center", fontsize=11)
    fig.legend(handles=[
        Line2D([], [], color=".45", ls=":", lw=1.1, label=r"$s=h$"),
        Line2D([], [], color=".4", ls="--", lw=1.2, label=r"$s+i=1$"),
    ], loc="lower center", bbox_to_anchor=(.52, -.004), ncol=2, frameon=False, fontsize=9)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT.with_suffix(".pdf"), bbox_inches="tight", pad_inches=.06)
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=220, bbox_inches="tight", pad_inches=.06)
    plt.close(fig)

    # 只核对已有初值的解析分类；不读取、产生或重评任何 OCP 解。
    def classify(s0, i0):
        if s0 <= g.h or g.phi(s0, i0) <= g.Phi_A + 1e-12:
            return "A"
        if g.phi(s0, i0) > g.Phi_B + 1e-12:
            return "B" if abs(i0-g.K) < 1e-12 else "W_K"
        gamma = np.interp(s0, sg[::-1], ig[::-1], left=np.nan, right=np.inf)
        return "W_Gamma" if s0 > g.s_e and i0 < gamma else "T"

    classifications = []
    for case in json.loads(INPUT.read_text(encoding="utf-8"))["cases"]:
        actual = classify(case["s0"], case["i0"])
        assert actual == case["expected_region"], (case["case_id"], actual)
        classifications.append({"case_id": case["case_id"], "region": actual, "pass": True})
    assert protected_before == {str(p.relative_to(ROOT)): digest(p) for p in protected if p.is_file()}
    evidence = {
        "status": "theoretical_geometry_only", "optimizer_calls": 0, "OCP_solves": 0,
        "parameters": parameters, "restricted_qbar_left_panel": QBAR,
        "geometry": {name: getattr(g, name) for name in names},
        "checkpoint_max_absolute_error": max(errors.values()),
        "switch_original_theta_max_absolute_error": float(np.max(theta_errors)),
        "nested_feasibility_envelopes_verified": True,
        "physical_cutoff_verified": True,
        "classifications": classifications,
        "sources_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [INPUT, CHECKPOINT, Path(__file__).resolve(), ROOT / "matlab/numerical_scenarios/build_theory_geometry.m"]},
        "protected_files_unchanged": protected_before,
        "outputs_sha256": {str(OUTPUT.with_suffix(ext).relative_to(ROOT)): digest(OUTPUT.with_suffix(ext)) for ext in [".pdf", ".png"]},
        "visual_review": "recorded separately in two_layer_phase_visual_review.json; match its output SHA256 before relying on it",
    }
    (HERE / "two_layer_phase_checks.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"outputs": str(OUTPUT), "checks": "pass", "checkpoint_max_error": max(errors.values()), "optimizer_calls": 0, "OCP_solves": 0}))


if __name__ == "__main__":
    main()
