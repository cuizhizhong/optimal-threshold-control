#!/usr/bin/env python3
"""Figure 4: minimal suppression cost versus capacity for several q values."""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np

beta1_bar = 1.0
gamma = 0.3
S0 = 0.99
I0 = 0.01
q_values = [0.65, 0.80, 0.95, 1.10]
K_grid = np.linspace(0.015, 0.40, 650)


def peak_and_cost(q: float, K: np.ndarray) -> tuple[float, np.ndarray]:
    x0 = q * S0
    x_h = gamma / beta1_bar
    if x0 <= x_h:
        return I0, np.zeros_like(K)
    I_peak = I0 + x0 - x_h + (gamma / beta1_bar) * math.log(x_h / x0)
    active = K < I_peak
    expression = (
        (beta1_bar / gamma) * (I0 + x0 - K)
        - np.log(beta1_bar * x0 / gamma)
        - 1.0
    ) / K
    return I_peak, np.where(active, np.maximum(expression, 0.0), 0.0)


fig, ax = plt.subplots(figsize=(8.2, 5.4))
for q in q_values:
    peak, cost = peak_and_cost(q, K_grid)
    ax.plot(K_grid, cost, linewidth=2.0, label=f"q={q:.2f}, peak={peak:.3f}")
ax.set_xlabel("Capacity $K$")
ax.set_ylabel("Minimal suppression cost $J^*$")
ax.set_xlim(K_grid[0], K_grid[-1])
ax.set_ylim(bottom=0.0)
ax.grid(alpha=0.25)
ax.legend(frameon=True)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_4_cost_capacity.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"Saved {out}")
