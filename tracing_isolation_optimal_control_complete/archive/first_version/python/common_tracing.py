"""Shared analytical and numerical utilities for the tracing-isolation control model.

Model in population fractions:
    s' = -c [p + (1-p) q] s i
    i' =  p c (1-q) s i - gamma i,
with 0 <= q <= 1 and i <= K.

The linear tracing cost is J = integral p*c*q dt.  For constant c the
optimal feedback has zero-control, capacity-boundary, full-isolation and
zero-control arcs.  This module computes the exact one-dimensional
characterization used by all figure scripts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple
import math
import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.optimize import brentq, minimize_scalar


@dataclass(frozen=True)
class Params:
    p: float = 0.5
    c: float = 2.0
    gamma: float = 0.3
    K: float = 0.15
    s0: float = 0.99
    i0: float = 0.01

    def validate(self) -> None:
        if not (0.0 < self.p < 1.0):
            raise ValueError("p must lie in (0,1)")
        if self.c <= 0 or self.gamma <= 0 or self.K <= 0:
            raise ValueError("c, gamma and K must be positive")
        if not (0 < self.i0 < self.K):
            raise ValueError("require 0 < i0 < K")
        if self.s0 <= 0:
            raise ValueError("s0 must be positive")

    @property
    def b(self) -> float:
        return self.p * self.c

    @property
    def h(self) -> float:
        return self.gamma / self.b

    @property
    def r(self) -> float:
        return (1.0 - self.p) * self.h

    @property
    def ell(self) -> float:
        return self.gamma / self.c  # = p h


def psi(s: np.ndarray | float, h: float) -> np.ndarray | float:
    return np.asarray(s) - h * np.log(np.asarray(s))


def invariant(s: float, i: float, h: float) -> float:
    return i + s - h * math.log(s)


def natural_i(s: np.ndarray | float, par: Params) -> np.ndarray | float:
    s_arr = np.asarray(s)
    return par.i0 + par.s0 - s_arr + par.h * np.log(s_arr / par.s0)


def natural_peak(par: Params) -> Tuple[float, float]:
    """Return (s at peak, i at peak) under q=0."""
    if par.s0 <= par.h:
        return par.s0, par.i0
    ipk = par.i0 + par.s0 - par.h + par.h * math.log(par.h / par.s0)
    return par.h, ipk


def safe_level(par: Params) -> float:
    return par.K + par.h - par.h * math.log(par.h)


def safe_i(s: np.ndarray | float, par: Params) -> np.ndarray | float:
    """Upper safe-boundary branch i + psi(s)=K+psi(h), s>=h."""
    return safe_level(par) - psi(s, par.h)


def ridge_i(s: np.ndarray | float, par: Params) -> np.ndarray | float:
    s_arr = np.asarray(s)
    return (s_arr - par.h) * (s_arr - par.r) / s_arr


def theta(s: np.ndarray | float, i: np.ndarray | float, par: Params) -> np.ndarray | float:
    s_arr = np.asarray(s)
    i_arr = np.asarray(i)
    return (s_arr - par.h) / (i_arr * (s_arr - par.r))


def first_capacity_s(par: Params) -> float:
    """Larger root at which the natural q=0 orbit first reaches i=K."""
    _, ipk = natural_peak(par)
    if ipk <= par.K + 1e-13:
        return par.h
    f = lambda s: float(natural_i(s, par) - par.K)
    return brentq(f, par.h * (1.0 + 1e-12), par.s0, xtol=1e-14, rtol=1e-13)


def natural_hit_time(par: Params, s_target: float) -> float:
    if s_target >= par.s0:
        return 0.0
    integrand = lambda s: 1.0 / (par.b * s * float(natural_i(s, par)))
    return quad(integrand, s_target, par.s0, epsabs=1e-11, epsrel=1e-11, limit=300)[0]


def terminal_from_q1_start(s_a: float, i_a: float, par: Params) -> Tuple[float, float]:
    """Intersection of the q=1 characteristic through (s_a,i_a) with the upper safe boundary."""
    chi = i_a - par.ell * math.log(s_a)
    # G(s)=Phi_*-s+r ln s is strictly decreasing for s>h>r.
    def f(s: float) -> float:
        return safe_level(par) - s + par.r * math.log(s) - chi

    f_h = f(par.h)
    f_a = f(s_a)
    # At a state outside the safe set, f(h)>0 and f(s_a)<0.
    if not (f_h >= -1e-10 and f_a <= 1e-10):
        # Numerical fallback: search for a bracket on (h,s_a).
        grid = np.linspace(par.h, s_a, 600)
        vals = np.array([f(x) for x in grid])
        idx = np.where(vals[:-1] * vals[1:] <= 0)[0]
        if len(idx) == 0:
            raise RuntimeError("q=1 characteristic does not meet the upper safe boundary")
        lo, hi = grid[idx[-1]], grid[idx[-1] + 1]
    else:
        lo, hi = par.h, s_a
    s_b = brentq(f, lo, hi, xtol=1e-14, rtol=1e-13)
    i_b = float(safe_i(s_b, par))
    if i_b <= 0 or i_b > i_a * (1 + 1e-9):
        raise RuntimeError("invalid terminal infection on q=1 arc")
    return s_b, i_b


def q1_cost(s_a: float, i_a: float, par: Params) -> Tuple[float, float, float]:
    s_b, i_b = terminal_from_q1_start(s_a, i_a, par)
    cost = par.b / par.gamma * math.log(i_a / i_b)
    return cost, s_b, i_b


def boundary_cost(s_hi: float, s_lo: float, par: Params) -> float:
    """Cost on i=K from s_hi down to s_lo, using q=1-h/s."""
    if s_hi <= s_lo + 1e-15:
        return 0.0
    p = par.p
    term = math.log(s_hi / s_lo) - p * math.log((s_hi - par.r) / (s_lo - par.r))
    return p / (par.K * (1.0 - p)) * term


def boundary_duration(s_hi: float, s_lo: float, par: Params) -> float:
    if s_hi <= s_lo + 1e-15:
        return 0.0
    return math.log((s_hi - par.r) / (s_lo - par.r)) / (par.c * par.K)


def optimize_constant_c(par: Params) -> Dict[str, float | str]:
    """Compute the exact one-dimensional optimal policy characterization.

    The candidate classes are rigorously implied by the stationary HJB geometry:
    q=0 until either the switching curve or the capacity is reached; possibly a
    capacity boundary arc; q=1 until the maximal q=0-safe orbit; q=0 thereafter.
    """
    par.validate()
    s_peak, i_peak = natural_peak(par)
    phi0 = invariant(par.s0, par.i0, par.h)
    phistar = safe_level(par)
    if i_peak <= par.K + 1e-12 or par.s0 <= par.h:
        return {
            "regime": "safe",
            "s_peak": s_peak,
            "i_peak": i_peak,
            "s1": par.h,
            "s_switch": par.s0,
            "i_switch": par.i0,
            "s_release": par.s0,
            "i_release": par.i0,
            "tau1": 0.0,
            "tau_boundary": 0.0,
            "tau_q1": 0.0,
            "cost": 0.0,
            "fill_box_cost": 0.0,
        }

    s1 = first_capacity_s(par)

    # Candidate 1: wait on q=0 and switch directly to q=1 before capacity.
    # s runs from first-capacity point backwards to the initial point.
    def direct_obj(s: float) -> float:
        i = phi0 - (s - par.h * math.log(s))
        if i <= 0 or i > par.K * (1 + 1e-9):
            return 1e8
        try:
            return q1_cost(s, i, par)[0]
        except Exception:
            return 1e8

    def robust_scalar_min(fun, lo, hi, grid_n=180):
        xs = np.linspace(lo, hi, grid_n)
        vals = np.array([fun(float(x)) for x in xs])
        finite = np.isfinite(vals) & (vals < 1e7)
        if not np.any(finite):
            return math.inf, math.nan
        idx_all = np.where(finite)[0]
        k = idx_all[np.argmin(vals[finite])]
        left = xs[max(0, k-2)]
        right = xs[min(grid_n-1, k+2)]
        if right-left < 1e-12:
            return float(vals[k]), float(xs[k])
        opt = minimize_scalar(fun, bounds=(float(left), float(right)), method="bounded",
                              options={"xatol": 2e-13, "maxiter": 600})
        if not np.isfinite(opt.fun) or opt.fun >= 1e7:
            return float(vals[k]), float(xs[k])
        return float(opt.fun), float(opt.x)

    j_direct_raw, s_direct = robust_scalar_min(direct_obj, s1, par.s0)
    if math.isfinite(j_direct_raw):
        i_direct = float(phi0 - (s_direct - par.h * math.log(s_direct)))
        j_direct, sb_direct, ib_direct = q1_cost(s_direct, i_direct, par)
    else:
        i_direct, j_direct, sb_direct, ib_direct = math.nan, math.inf, math.nan, math.nan

    # Candidate 2: q=0 to capacity, boundary arc, then q=1.
    def boundary_obj(s_a: float) -> float:
        try:
            jq1, _, _ = q1_cost(s_a, par.K, par)
            return boundary_cost(s1, s_a, par) + jq1
        except Exception:
            return 1e8

    j_bound_raw, s_bound = robust_scalar_min(boundary_obj, par.h * (1 + 2e-10), s1)
    if math.isfinite(j_bound_raw):
        j_bound_q1, sb_bound, ib_bound = q1_cost(s_bound, par.K, par)
        j_bound = boundary_cost(s1, s_bound, par) + j_bound_q1
    else:
        j_bound_q1, sb_bound, ib_bound, j_bound = math.inf, math.nan, math.nan, math.inf

    # Pure filling-the-box benchmark: remain on capacity until s=h.
    fill = boundary_cost(s1, par.h, par)

    tol = 2e-7
    if math.isfinite(j_bound) and (not math.isfinite(j_direct) or (j_bound + tol < j_direct and s_bound < s1 - 1e-7)):
        regime = "capacity-q1"
        s_sw, i_sw, sb, ib, cost = s_bound, par.K, sb_bound, ib_bound, j_bound
        tau1 = natural_hit_time(par, s1)
        tbound = boundary_duration(s1, s_sw, par)
    elif math.isfinite(j_direct):
        regime = "direct-q1"
        s_sw, i_sw, sb, ib, cost = s_direct, i_direct, sb_direct, ib_direct, j_direct
        tau1 = natural_hit_time(par, s_sw)
        tbound = 0.0
    else:
        # Fallback: pure capacity tracking to h is always feasible and finite.
        regime = "fill-box"
        s_sw, i_sw, sb, ib, cost = par.h, par.K, par.h, par.K, fill
        tau1 = natural_hit_time(par, s1)
        tbound = boundary_duration(s1, par.h)

    tq1 = math.log(i_sw / ib) / par.gamma
    return {
        "regime": regime,
        "s_peak": s_peak,
        "i_peak": i_peak,
        "s1": s1,
        "s_switch": s_sw,
        "i_switch": i_sw,
        "s_release": sb,
        "i_release": ib,
        "tau1": tau1,
        "tau_boundary": tbound,
        "tau_q1": tq1,
        "cost": cost,
        "fill_box_cost": fill,
        "direct_cost": j_direct,
        "boundary_cost_total": j_bound,
    }


def simulate_optimal(par: Params, t_end: float = 22.0, n: int = 2401) -> Dict[str, np.ndarray | Dict[str, float | str]]:
    sol = optimize_constant_c(par)
    t = np.linspace(0.0, t_end, n)
    s = np.empty_like(t)
    i = np.empty_like(t)
    q = np.zeros_like(t)

    if sol["regime"] == "safe":
        def rhs(_t, y):
            ss, ii = y
            return [-par.b * ss * ii, (par.b * ss - par.gamma) * ii]
        ivp = solve_ivp(rhs, [0, t_end], [par.s0, par.i0], t_eval=t, rtol=1e-10, atol=1e-12)
        s[:], i[:] = ivp.y
    else:
        t0 = float(sol["tau1"])
        tb = float(sol["tau_boundary"])
        tq = float(sol["tau_q1"])
        t_beg_q1 = t0 + tb
        t_release = t_beg_q1 + tq
        s_sw = float(sol["s_switch"])
        i_sw = float(sol["i_switch"])
        s_rel = float(sol["s_release"])
        i_rel = float(sol["i_release"])

        # Natural arc to first active control.
        mask0 = t <= t0 + 1e-13
        def rhs0(_t, y):
            ss, ii = y
            return [-par.b * ss * ii, (par.b * ss - par.gamma) * ii]
        if np.any(mask0):
            ivp0 = solve_ivp(rhs0, [0, max(t0, 1e-12)], [par.s0, par.i0],
                             t_eval=t[mask0], rtol=2e-11, atol=1e-13)
            s[mask0], i[mask0] = ivp0.y

        # Capacity boundary if present.
        maskb = (t > t0) & (t <= t_beg_q1 + 1e-13)
        if np.any(maskb):
            u = t[maskb] - t0
            s1 = float(sol["s1"])
            s[maskb] = par.r + (s1 - par.r) * np.exp(-par.c * par.K * u)
            i[maskb] = par.K
            q[maskb] = 1.0 - par.h / s[maskb]

        # Full tracing q=1.
        mask1 = (t > t_beg_q1) & (t <= t_release + 1e-13)
        if np.any(mask1):
            u = t[mask1] - t_beg_q1
            i[mask1] = i_sw * np.exp(-par.gamma * u)
            s[mask1] = s_sw * np.exp(-(par.c / par.gamma) * (i_sw - i[mask1]))
            q[mask1] = 1.0

        # Natural safe arc after release.
        mask2 = t > t_release
        if np.any(mask2):
            tt = t[mask2] - t_release
            ivp2 = solve_ivp(rhs0, [0, max(tt[-1], 1e-12)], [s_rel, i_rel],
                             t_eval=tt, rtol=2e-11, atol=1e-13)
            s[mask2], i[mask2] = ivp2.y

    beta1 = par.c * (par.p + (1.0 - par.p) * q)
    beta2 = par.p * par.c * (1.0 - q)
    return {"t": t, "s": s, "i": i, "q": q, "beta1": beta1, "beta2": beta2, "summary": sol}


def switching_curve(par: Params, s_max: float = 1.05, n: int = 180) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return switch points and their q=1 terminal points for plotting."""
    # Endpoint where safe boundary meets the q=1 theta ridge.
    f = lambda s: float(safe_i(s, par) - ridge_i(s, par))
    # Find an upper bracket before safe_i becomes nonpositive.
    upper = max(par.h * 1.1, s_max)
    while f(upper) > 0 and upper < 20:
        upper *= 1.3
    s_e = brentq(f, par.h * (1 + 1e-10), upper, xtol=1e-13)

    terminals = np.linspace(par.h * (1 + 5e-4), s_e * (1 - 5e-5), n)
    sw_s, sw_i, te_s, te_i = [], [], [], []
    for sb in terminals:
        ib = float(safe_i(sb, par))
        thb = float(theta(sb, ib, par))
        def iq1(S):
            return ib + par.ell * math.log(S / sb)
        def froot(S):
            return float(theta(S, iq1(S), par) - thb)
        # Locate the second zero after the local maximum.
        lo = sb * (1 + 1e-6)
        last_x, last_v = lo, froot(lo)
        root = None
        hi_limit = max(s_max * 1.4, sb * 1.5)
        grid = np.geomspace(lo, hi_limit, 500)
        for x in grid[1:]:
            v = froot(x)
            if last_v > 0 and v <= 0:
                root = brentq(froot, last_x, x, xtol=1e-12)
                break
            last_x, last_v = x, v
        if root is None or root > s_max:
            continue
        sw_s.append(root)
        sw_i.append(iq1(root))
        te_s.append(sb)
        te_i.append(ib)
    return np.array(sw_s), np.array(sw_i), np.array(te_s), np.array(te_i)


def perturbation_cost_curve(par: Params, n: int = 220) -> Tuple[np.ndarray, np.ndarray, Dict[str, float | str]]:
    """Cost as the boundary-to-q=1 switch location is varied."""
    sol = optimize_constant_c(par)
    s1 = float(sol["s1"])
    grid = np.linspace(par.h * 1.0005, s1, n)
    vals = []
    for s in grid:
        try:
            jq1, _, _ = q1_cost(s, par.K, par)
            vals.append(boundary_cost(s1, s, par) + jq1)
        except Exception:
            vals.append(np.nan)
    return grid, np.asarray(vals), sol


def contact_time_varying(t: np.ndarray | float, c0: float = 2.0) -> np.ndarray | float:
    """A smooth contact surge that returns to c0."""
    t_arr = np.asarray(t)
    return c0 * (1.0 + 0.55 * np.exp(-0.5 * ((t_arr - 5.5) / 1.35) ** 2))


def simulate_piecewise_q(qs: np.ndarray, times: np.ndarray, par: Params,
                         cfun: Callable[[float], float]) -> np.ndarray:
    """RK4 integration for a piecewise-constant q control."""
    y = np.array([par.s0, par.i0], dtype=float)
    ys = [y.copy()]
    for j, qv in enumerate(qs):
        t0, t1 = times[j], times[j + 1]
        dt = t1 - t0
        def f(tt, yy):
            ss, ii = yy
            cc = float(cfun(tt))
            return np.array([-cc * (par.p + (1 - par.p) * qv) * ss * ii,
                             par.p * cc * (1 - qv) * ss * ii - par.gamma * ii])
        k1 = f(t0, y)
        k2 = f(t0 + dt / 2, y + dt * k1 / 2)
        k3 = f(t0 + dt / 2, y + dt * k2 / 2)
        k4 = f(t1, y + dt * k3)
        y = y + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        y = np.maximum(y, 1e-13)
        ys.append(y.copy())
    return np.asarray(ys)


def optimize_time_varying(par: Params, T: float = 18.0, n: int = 72,
                          eps: float = 0.035, smooth: float = 0.004,
                          cfun: Callable[[float], float] | None = None,
                          maxiter: int = 800) -> Dict[str, np.ndarray | float | bool | str]:
    """Direct-transcription solution for prescribed time-varying contact rate.

    The regularized objective is
        integral [p c(t) q + eps q^2/2] dt
        + smooth/2 * integral |q'|^2 dt.
    The small strictly convex terms remove mesh-scale ties and implement the
    uniqueness criterion discussed in the report.
    """
    from scipy.optimize import minimize
    if cfun is None:
        cfun = lambda tt: float(contact_time_varying(tt, par.c))
    times = np.linspace(0.0, T, n + 1)
    mids = 0.5 * (times[:-1] + times[1:])
    dt = T / n
    cmid = np.array([cfun(x) for x in mids])

    # Warm start from the constant-c analytical policy.
    ana = simulate_optimal(par, t_end=T, n=n + 1)
    q0 = np.clip(0.82 * np.asarray(ana["q"][:-1]), 0, 1)

    def objective(qs: np.ndarray) -> float:
        val = dt * np.sum(par.p * cmid * qs + 0.5 * eps * qs * qs)
        if smooth > 0 and len(qs) > 1:
            val += 0.5 * smooth / dt * np.sum(np.diff(qs) ** 2)
        return float(val)

    def states(qs: np.ndarray) -> np.ndarray:
        return simulate_piecewise_q(qs, times, par, cfun)

    h0 = par.gamma / (par.p * par.c)
    phi_safe0 = par.K + h0 - h0 * math.log(h0)

    def cap_constraint(qs: np.ndarray) -> np.ndarray:
        return par.K - states(qs)[:, 1]

    def terminal_constraint(qs: np.ndarray) -> float:
        ss, ii = states(qs)[-1]
        return float(phi_safe0 - (ii + ss - h0 * math.log(ss)))

    cons = [
        {"type": "ineq", "fun": cap_constraint},
        {"type": "ineq", "fun": terminal_constraint},
    ]
    result = minimize(
        objective,
        q0,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 2e-10, "disp": False},
    )
    qs = np.clip(result.x, 0, 1)
    ys = states(qs)
    return {
        "success": bool(result.success),
        "message": str(result.message),
        "objective": float(objective(qs)),
        "times": times,
        "mids": mids,
        "q": qs,
        "states": ys,
        "c": np.array([cfun(x) for x in times]),
        "eps": eps,
        "smooth": smooth,
    }
