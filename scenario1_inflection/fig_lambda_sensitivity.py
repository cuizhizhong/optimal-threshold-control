"""绘制拐点归一化位置 lambda 的四参数响应图。"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Patch
import numpy as np

from inflection_analysis import find_q0_stationary_points, solve


rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Liberation Serif', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 9,
    'axes.linewidth': 0.7,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.normpath(os.path.join(HERE, '..', 'figures'))
OUT = os.path.join(FIG_DIR, 'scenario1_inflection_lambda_sensitivity.pdf')

BASE = dict(beta=0.155, gamma=0.3504, c0=10.0, q0=0.01526,
            eta=0.05 * 763, N=763.0, S0=762.0, I0=1.0)

COLORS = ['#9ecae1', '#4292c6', '#08519c']
C_MAIN = '#08519c'
C_INFEASIBLE = '#f0f0f0'
C_NO_INFLECTION = '#c7c7c7'


def solve_scan(param, values, base=BASE):
    rows = []
    # 扫到 0 时 c0=0/beta=0/eta=0 会触发 inf/nan（solve 据此返回不可行状态），屏蔽告警即可
    with np.errstate(divide='ignore', invalid='ignore'):
        for value in values:
            p = dict(base)
            p[param] = value * p['N'] if param == 'eta' else value
            rows.append(solve(**p))
    return rows


def region_codes(rows):
    codes = np.zeros(len(rows), dtype=int)  # 0=不可行, 1=无内部拐点, 2=内部拐点
    for i, r in enumerate(rows):
        if r.get('status') == 'ok':
            codes[i] = 2 if r.get('has_inflection', False) else 1
    return codes


def contiguous_runs(mask):
    start = None
    for i, flag in enumerate(mask):
        if flag and start is None:
            start = i
        if start is not None and (not flag or i == len(mask) - 1):
            end = i if flag and i == len(mask) - 1 else i - 1
            yield start, end
            start = None


def shade_full_height(ax, x, codes):
    for code, color in [(0, C_INFEASIBLE), (1, C_NO_INFLECTION)]:
        for i0, i1 in contiguous_runs(codes == code):
            ax.axvspan(x[i0], x[i1], color=color, zorder=0, lw=0)


def plot_internal_curve(ax, x, rows, color, label=None, lw=1.6):
    y = np.array([
        r.get('lam', np.nan)
        if r.get('status') == 'ok' and r.get('has_inflection', False)
        else np.nan
        for r in rows
    ], dtype=float)
    ax.plot(x, y, color=color, lw=lw, label=label, zorder=3)


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.5), sharey=True)

    # 各面板扫描下探到 0，令不可行阴影贴到左边、不呈现虚假左边界
    specs = [
        ('eta', np.linspace(0.0, 0.05, 700), r'$\eta/N$', (0.0, 0.05)),
        ('c0', np.linspace(0.0, 16.0, 900), r'$c_0$', (0.0, 16.0)),
        ('beta', np.linspace(0.0, 0.50, 800), r'$\beta$', (0.0, 0.50)),
    ]
    for ax, (param, x, xlabel, xlim) in zip(axes.ravel()[:3], specs):
        rows = solve_scan(param, x)
        codes = region_codes(rows)
        shade_full_height(ax, x, codes)
        plot_internal_curve(ax, x, rows, C_MAIN)
        ax.set_xlabel(xlabel); ax.set_xlim(*xlim)

    ax = axes.ravel()[3]
    # q0 面板：只用基准 beta=0.155 的可行性上底色（不可行区 q0>0.398），扫到 0.45 露出该区
    q0_grid = np.linspace(0.0, 0.45, 2400)
    shade_full_height(ax, q0_grid, region_codes(solve_scan('q0', q0_grid, BASE)))
    betas = [0.10, 0.12, 0.155]
    for beta, color in zip(betas, COLORS):
        p = dict(BASE); p['beta'] = beta
        rows = solve_scan('q0', q0_grid, p)
        plot_internal_curve(ax, q0_grid, rows, color, label=rf'$\beta={beta:g}$')

        found = find_q0_stationary_points(p, q0_bounds=(0.0, 0.39), n=2001)
        for root in found['roots']:
            pr = dict(p); pr['q0'] = root
            rr = solve(**pr)
            ax.plot(root, rr['lam'], 'o', ms=5.2, mfc='white', mec=color,
                    mew=1.1, zorder=5)
        for candidate, _ in found['candidates']:
            pc = dict(p); pc['q0'] = candidate
            rc = solve(**pc)
            ax.plot(candidate, rc['lam'], '^', ms=5.5, mfc='white', mec=color,
                    mew=1.0, zorder=5)
        print(f"beta={beta:.3f}: roots={found['roots']}, candidates={found['candidates']}")

    ax.set_xlabel(r'$q_0$'); ax.set_xlim(0.0, 0.45)
    ax.legend(frameon=False, fontsize=7.6, loc='upper left', handlelength=1.4)

    for ax in axes.ravel():
        ax.set_ylim(0.0, 1.0)
        ax.set_ylabel(r'$\lambda$')
        ax.tick_params(labelsize=8)

    region_legend = [
        Patch(facecolor=C_INFEASIBLE, edgecolor='none', label='infeasible'),
        Patch(facecolor=C_NO_INFLECTION, edgecolor='none', label='no internal inflection'),
    ]
    axes[0, 0].legend(handles=region_legend, frameon=False, fontsize=7.2,
                      loc='upper right', handlelength=1.2)

    fig.tight_layout(pad=0.7)
    fig.savefig(OUT, bbox_inches='tight')
    print('saved ->', OUT)


if __name__ == '__main__':
    main()
