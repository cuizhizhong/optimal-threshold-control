#!/usr/bin/env python3
"""Figure 5: cost of feasible plateau policies; unique minimum occurs at h=K."""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

beta1_bar = 1.0
q = 0.8
gamma = 0.3
S0 = 0.99
I0 = 0.01
K = 0.15
x0 = q * S0
x_h = gamma / beta1_bar
S_h = x_h / q


def I_laissez(S: float) -> float:
    return I0 + q * (S0 - S) + (gamma / beta1_bar) * math.log(S / S0)


def plateau_cost(h: float) -> float:
    S_entry = brentq(lambda s: I_laissez(s) - h, S_h, S0)
    x_entry = q * S_entry
    return ((beta1_bar / gamma) * (x_entry - x_h) - math.log(x_entry / x_h)) / h


h_grid = np.linspace(I0 + 0.003, K, 320)
cost = np.array([plateau_cost(float(h)) for h in h_grid])
J_star = float(cost[-1])

fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.plot(h_grid, cost, linewidth=2.3, label="Feasible plateau family")
ax.scatter([K], [J_star], s=55, zorder=5, label="Unique optimum $h=K$")
ax.axvline(K, linestyle=":", linewidth=1.4)
ax.set_xlabel("Chosen infection plateau $h$")
ax.set_ylabel("Suppression cost $C(h)$")
ax.set_xlim(h_grid[0], K * 1.015)
ax.set_ylim(bottom=0.0)
ax.grid(alpha=0.25)
ax.legend(frameon=True)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_5_uniqueness_plateau_cost.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"J*={J_star:.10f}")
print(f"Saved {out}")
