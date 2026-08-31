#!/usr/bin/env python3
"""Figure 6: robustness threshold a_0(K) for an added infection cost."""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

beta1_bar = 1.0
gamma = 0.3
x_h = gamma / beta1_bar
rho = brentq(lambda r: r * r + r + math.log(1.0 - r), 0.5, 0.95)
K0 = rho * rho * x_h
lambda0 = (1.0 - rho) * x_h
constant_branch = beta1_bar * rho / ((1.0 - rho) * K0)


def lower_lambda(K: float) -> float:
    # Solve lambda = x_h[ln(lambda/x_h)+1] + K on (0,x_h).
    f = lambda lam: lam - x_h * (math.log(lam / x_h) + 1.0) - K
    return brentq(f, 1e-12, x_h * (1.0 - 1e-12))


K_grid = np.linspace(0.005, 0.29, 500)
a0 = np.empty_like(K_grid)
for j, K in enumerate(K_grid):
    if K <= K0:
        lam = lower_lambda(float(K))
        a0[j] = (gamma - beta1_bar * lam) / (K * lam)
    else:
        a0[j] = constant_branch

fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.plot(K_grid, a0, linewidth=2.3, label="$a_0(K)$")
ax.axvline(K0, linestyle="--", linewidth=1.4, label=f"$K_0={K0:.3f}$")
ax.set_xlabel("Capacity $K$")
ax.set_ylabel("Largest infection-cost weight preserving the policy")
ax.set_xlim(K_grid[0], K_grid[-1])
ax.set_ylim(bottom=0.0)
ax.grid(alpha=0.25)
ax.legend(frameon=True)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_6_infection_cost_threshold.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"rho={rho:.10f}, K0={K0:.10f}, constant={constant_branch:.10f}")
print(f"Saved {out}")
