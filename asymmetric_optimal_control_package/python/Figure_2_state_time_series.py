#!/usr/bin/env python3
"""Figure 2: state trajectories under the exact optimal policy."""
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

sol1 = solve_ivp(
    rhs_lf,
    (0.0, 200.0),
    (S0, I0),
    events=event_capacity,
    max_step=0.02,
    rtol=1e-10,
    atol=1e-12,
    dense_output=True,
)
tau1 = float(sol1.t_events[0][0])
tau2 = tau1 + q * (S1 - S_h) / (gamma * K)

# Post-release trajectory.
sol3 = solve_ivp(
    rhs_lf,
    (tau2, tau2 + 45.0),
    (S_h, K),
    max_step=0.03,
    rtol=1e-10,
    atol=1e-12,
    dense_output=True,
)
T_end = float(sol3.t[-1])

t1 = np.linspace(0.0, tau1, 350)
y1 = sol1.sol(t1)
t2 = np.linspace(tau1, tau2, 260)
S2 = S1 - (gamma * K / q) * (t2 - tau1)
I2 = np.full_like(t2, K)
t3 = np.linspace(tau2, T_end, 700)
y3 = sol3.sol(t3)

t = np.concatenate([t1, t2[1:], t3[1:]])
S = np.concatenate([y1[0], S2[1:], y3[0, 1:]])
I = np.concatenate([y1[1], I2[1:], y3[1, 1:]])

fig, ax = plt.subplots(figsize=(8.4, 5.4))
ax.plot(t, S, linewidth=2.1, label="$S(t)$")
ax.plot(t, I, linewidth=2.4, label="$I(t)$")
ax.axhline(K, linestyle=":", linewidth=1.5, label="Capacity $K$")
ax.axvline(tau1, linestyle="--", linewidth=1.2)
ax.axvline(tau2, linestyle="--", linewidth=1.2)
ax.text(tau1, 0.94 * ax.get_ylim()[1], "$\\tau_1$", ha="right", va="top")
ax.text(tau2, 0.94 * ax.get_ylim()[1], "$\\tau_2$", ha="left", va="top")
ax.set_xlabel("Time")
ax.set_ylabel("Population fraction")
ax.set_xlim(0.0, T_end)
ax.set_ylim(0.0, 1.03)
ax.grid(alpha=0.25)
ax.legend(frameon=True)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_2_state_time_series.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"tau1={tau1:.8f}, tau2={tau2:.8f}")
print(f"Saved {out}")
