#!/usr/bin/env python3
"""Generate the numerical summary CSV used in the manuscript."""
from pathlib import Path
import csv
import math

from scipy.integrate import solve_ivp
from scipy.optimize import brentq

B = 1.0
q = 0.8
B2 = q * B
gamma = 0.3
S0 = 0.99
I0 = 0.01
K = 0.15
x0 = q * S0
xh = gamma / B
Sh = gamma / B2
Ipeak = I0 + x0 - xh + (gamma / B) * math.log(xh / x0)
S1 = brentq(lambda S: I0 + q*(S0-S) + (gamma/B)*math.log(S/S0) - K, Sh, S0)
x1 = q*S1

def rhs(_t, y):
    S, I = y
    return [-B*S*I, B2*S*I-gamma*I]

def event(_t, y): return y[1]-K
event.terminal = True
event.direction = 1
sol = solve_ivp(rhs, (0, 200), (S0, I0), events=event, rtol=1e-11, atol=1e-13, max_step=0.02)
tau1 = float(sol.t_events[0][0])
tau2 = tau1 + (x1-xh)/(gamma*K)
Jstar = ((B/gamma)*(I0+x0-K)-math.log(B*x0/gamma)-1)/K
Fc = K+xh-(gamma/B)*math.log(xh)
lam = brentq(lambda x: x-(gamma/B)*math.log(x)-Fc, 1e-12, xh*(1-1e-12))
Sinf = lam/q

rows = [
    ("beta1_bar", B, "natural coefficient in S equation"),
    ("q", q, "fixed ratio beta2/beta1"),
    ("beta2_bar", B2, "natural coefficient in I equation"),
    ("gamma", gamma, "recovery rate"),
    ("S0", S0, "initial susceptible fraction"),
    ("I0", I0, "initial infectious fraction"),
    ("K", K, "capacity"),
    ("S_h", Sh, "release/herd threshold in S"),
    ("I_peak_laissez", Ipeak, "unregulated infection peak"),
    ("S_entry", S1, "first capacity-hit susceptible level"),
    ("tau1", tau1, "capacity-entry time"),
    ("tau2", tau2, "release time"),
    ("J_star", Jstar, "minimal suppression cost"),
    ("S_infinity_opt", Sinf, "final susceptible fraction under optimum"),
]
out = Path(__file__).resolve().parents[1]/"data"/"numerical_summary.csv"
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["quantity", "value", "description"])
    w.writerows(rows)
print(f"Saved {out}")
