#!/usr/bin/env python3
"""Figure 1: phase portrait for the exact proportional two-rate model.

The script is self-contained and writes ../figures/Figure_1_phase_plane.jpg.
"""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

# Parameters
beta1_bar = 1.0
q = 0.8                 # beta2(t) = q beta1(t)
beta2_bar = q * beta1_bar
gamma = 0.3
S0 = 0.99
I0 = 0.01
K = 0.15

S_h = gamma / beta2_bar
x_h = gamma / beta1_bar


def I_laissez(S: np.ndarray | float) -> np.ndarray | float:
    return I0 + q * (S0 - S) + (gamma / beta1_bar) * np.log(S / S0)


# First hit of the capacity on the increasing branch.
S1 = brentq(lambda s: float(I_laissez(s) - K), S_h, S0)

# Final susceptible levels on the uncontrolled and critical orbits.
S_inf_lf = brentq(lambda s: float(I_laissez(s)), 1e-9, S_h)


def I_critical(S: np.ndarray | float) -> np.ndarray | float:
    return K + q * (S_h - S) + (gamma / beta1_bar) * np.log(S / S_h)


S_inf_opt = brentq(lambda s: float(I_critical(s)), 1e-9, S_h)

# Curves, ordered in the direction of time.
S_lf = np.linspace(S0, S_inf_lf, 900)
I_lf = I_laissez(S_lf)

S_pre = np.linspace(S0, S1, 350)
I_pre = I_laissez(S_pre)
S_boundary = np.linspace(S1, S_h, 250)
I_boundary = np.full_like(S_boundary, K)
S_post = np.linspace(S_h, S_inf_opt, 450)
I_post = I_critical(S_post)

fig, ax = plt.subplots(figsize=(8.2, 5.6))
ax.plot(S_lf, I_lf, linestyle="--", linewidth=2.0, label="Laissez-faire")
S_opt = np.concatenate([S_pre, S_boundary[1:], S_post[1:]])
I_opt = np.concatenate([I_pre, I_boundary[1:], I_post[1:]])
ax.plot(S_opt, I_opt, linewidth=2.4, label="Optimal path")
ax.axhline(K, linestyle=":", linewidth=1.5, label="Capacity $K$")
ax.axvline(S_h, linestyle=":", linewidth=1.5, label="$S_h=\\gamma/\\bar\\beta_2$")
ax.scatter([S0, S1, S_h, S_inf_opt], [I0, K, K, 0.0], s=38, zorder=5)
ax.annotate("entry", (S1, K), xytext=(8, 10), textcoords="offset points")
ax.annotate("release", (S_h, K), xytext=(-52, 10), textcoords="offset points")
ax.set_xlabel("Susceptible fraction $S$")
ax.set_ylabel("Infectious fraction $I$")
ax.set_xlim(0, 1.02)
ax.set_ylim(0, max(1.12 * float(np.max(I_lf)), 1.25 * K))
ax.grid(alpha=0.25)
ax.legend(frameon=True)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_1_phase_plane.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"Saved {out}")
