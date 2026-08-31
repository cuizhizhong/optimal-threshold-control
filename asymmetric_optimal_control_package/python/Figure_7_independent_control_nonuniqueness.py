#!/usr/bin/env python3
"""Figure 7: zero-cost nonuniqueness with independent beta_1 and beta_2.

For each short pulse duration delta, beta_1 is raised above its baseline at no
cost while beta_2 remains at baseline.  The pulse depletes S below the herd
threshold before I reaches the capacity.  All displayed controls have zero
positive-part suppression cost but are different.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

B1 = 1.0
B2 = 0.8
gamma = 0.3
S0 = 0.99
I0 = 0.02
K = 0.15
S_threshold = gamma / B2
strategies = [(0.05, 0.95), (0.10, 0.85), (0.20, 0.75)]
T_end = 25.0


def integrate_piecewise(delta: float, M: float, dense: bool = False):
    def pulse_rhs(_t, y):
        S, I = y
        return [-M * S * I, B2 * S * I - gamma * I]

    sol1 = solve_ivp(pulse_rhs, (0.0, delta), (S0, I0), rtol=2e-9, atol=1e-11,
                     max_step=max(delta / 150.0, 1e-4), dense_output=dense)
    y_delta = sol1.y[:, -1]

    def base_rhs(_t, y):
        S, I = y
        return [-B1 * S * I, B2 * S * I - gamma * I]

    sol2 = solve_ivp(base_rhs, (delta, T_end), y_delta, rtol=2e-9, atol=1e-11,
                     max_step=0.02, dense_output=dense)
    return sol1, sol2


def terminal_S(delta: float, M: float) -> float:
    sol1, _ = integrate_piecewise(delta, M, dense=False)
    return float(sol1.y[0, -1])


fig, ax = plt.subplots(figsize=(8.4, 5.3))
for delta, target_factor in strategies:
    S_target = target_factor * S_threshold
    lo = B1 * (1.0 + 1e-8)
    hi = 10.0
    while terminal_S(delta, hi) > S_target:
        hi *= 2.0
        if hi > 1e7:
            raise RuntimeError("Could not bracket the acceleration pulse.")
    M = brentq(lambda m: terminal_S(delta, m) - S_target, lo, hi,
               xtol=1e-10, rtol=1e-10)
    sol1, sol2 = integrate_piecewise(delta, M, dense=True)
    t1 = np.linspace(0.0, delta, 120)
    t2 = np.linspace(delta, T_end, 900)
    I = np.concatenate([sol1.sol(t1)[1], sol2.sol(t2)[1, 1:]])
    t = np.concatenate([t1, t2[1:]])
    ax.plot(t, I, linewidth=2.0, label=f"zero cost: delta={delta:.2f}, S(delta)={S_target:.3f}, M={M:.1f}")

# Unregulated comparison.
def base_rhs(_t, y):
    S, I = y
    return [-B1 * S * I, B2 * S * I - gamma * I]

sol0 = solve_ivp(base_rhs, (0.0, T_end), (S0, I0), rtol=2e-9, atol=1e-11,
                 max_step=0.02, dense_output=True)
t0 = np.linspace(0.0, T_end, 1000)
ax.plot(t0, sol0.sol(t0)[1], linestyle="--", linewidth=2.0, label="unregulated baseline")
ax.axhline(K, linestyle=":", linewidth=1.5, label="Capacity $K$")
ax.set_xlabel("Time")
ax.set_ylabel("Infectious fraction $I(t)$")
ax.set_xlim(0.0, T_end)
ax.set_ylim(0.0, max(1.15 * K, 1.08 * float(np.max(sol0.sol(t0)[1]))))
ax.grid(alpha=0.25)
ax.legend(frameon=True, fontsize=8.5)
fig.tight_layout()

out = Path(__file__).resolve().parents[1] / "figures" / "Figure_7_independent_control_nonuniqueness.jpg"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"Saved {out}")
