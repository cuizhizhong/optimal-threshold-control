#!/usr/bin/env python3
"""Figure 3: distinct optimal coefficients beta_1(t) and beta_2(t)."""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

beta1_bar = 1.0
q = 0.8
beta2_bar = q * beta1_bar
gamma = 0.3
S0 = 0.99
I0 = 0.01
K = 0.15
S_h = gamma / beta2_bar


def I_laissez(S: float) -> float:
    return I0 + q * (S0 - S) + (gamma / beta1_bar) * math.log(S / S0)


S1 = brentq(lambda s: I_laissez(s) - K, S_h, S0)


def rhs_lf(_t: float, y: np.ndarray) -> list[float]:
    S, I = y
    return [-beta1_bar * S * I, beta2_bar * S * I - gamma * I]


def event_capacity(_t: float, y: np.ndarray) -> float:
    return y[1] - K


event_capacity.terminal = True
event_capacity.direction = 1
sol = solve_ivp(rhs_lf, (0.0, 200.0), (S0, I0), events=event_capacity,
                max_step=0.02, rtol=1e-10, atol=1e-12)
tau1 = float(sol.t_events[0][0])
tau2 = tau1 + q * (S1 - S_h) / (gamma * K)
T_end = tau2 + 16.0

t = np.linspace(0.0, T_end, 1400)
beta1 = np.full_like(t, beta1_bar)
beta2 = np.full_like(t, beta2_bar)
mask = (t > tau1) & (t <= tau2)
S_boundary = S1 - (gamma * K / q) * (t[mask] - tau1)
beta1[mask] = gamma / (q * S_boundary)
beta2[mask] = gamma / S_boundary

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(t, beta1, linewidth=2.3, label="$\\beta_1^*(t)$")
ax.plot(t, beta2, linewidth=2.3, label="$\\beta_2^*(t)=q\\beta_1^*(t)$")
ax.axhline(beta1_bar, linestyle=":", linewidth=1.3, label="$\\bar\\beta_1$")
ax.axhline(beta2_bar, linestyle="--", linewidth=1.3, label="$\\bar\\beta_2$")
ax.axvline(tau1, linestyle="--", linewidth=1.1)
ax.axvline(tau2, linestyle="--", linewidth=1.1)
ax.set_xlabel("Time")
ax.set_ylabel("Transmission/removal coefficient")
ax.set_xlim(0.0, T_end)
ax.set_ylim(0.0, 1.12 * beta1_bar)
ax.grid(alpha=0.25)
ax.legend(frameon=True, ncol=2)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_3_optimal_controls.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"Saved {out}")
