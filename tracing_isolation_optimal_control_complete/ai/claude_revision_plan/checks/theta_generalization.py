"""Generalised removal model: s' = -c[p + theta(1-p)q] s i, i' = [pc(1-q)s - gamma] i.
theta=1 is the manuscript; theta=0 means traced *uninfected* contacts are not removed from S.
Checks whether the early capacity exit s_B > h survives for theta in [0,1]."""
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import quad


def solve(p, c, gamma, K, theta, s0, i0):
    h = gamma / (p * c)
    kap = p + theta * (1 - p)
    r = theta * (1 - p) * h / kap
    l = h - r                       # = gamma/(c*kap), q=1 invariant i - l ln s
    PhiA = K + h - h * np.log(h)
    a = lambda s: PhiA - s + h * np.log(s)
    G = lambda z: a(z) - l * np.log(z)
    sK = brentq(a, h * (1 + 1e-14), 50)
    Th = lambda s, i: (s - h) / (i * (s - r))

    def zbar(s, i):
        return brentq(lambda z: G(z) - (i - l * np.log(s)), h * (1 + 1e-14), min(s, sK) * (1 - 1e-14))

    def D(s):
        z = zbar(s, K)
        return Th(z, a(z)) - Th(s, K)
    grid = np.linspace(h * (1 + 1e-6), min(sK * np.exp(K / l) * 0.999999, 20), 6000)
    vals = []
    for s in grid:
        try:
            vals.append(D(s))
        except ValueError:
            vals.append(np.nan)
    vals = np.array(vals)
    idx = [k for k in range(len(grid) - 1) if np.isfinite(vals[k]) and np.isfinite(vals[k + 1]) and vals[k] < 0 <= vals[k + 1]]
    sB = brentq(D, grid[idx[0]], grid[idx[0] + 1])
    CB = lambda hi, lo: quad(lambda s: p * (s - h) / (s * K * kap * (s - r)), lo, hi)[0]
    s1 = brentq(lambda s: i0 + s0 - s + h * np.log(s / s0) - K, h * (1 + 1e-12), s0)
    z = zbar(sB, K)
    opt = CB(s1, sB) + np.log(K / a(z)) / h
    pure = CB(s1, h)
    # brute-force check: best single exit point sigma on the capacity line
    sig = np.linspace(h * (1 + 1e-4), s1, 4000)
    costs = []
    for sg in sig:
        try:
            zz = zbar(sg, K)
            costs.append(CB(s1, sg) + np.log(K / a(zz)) / h)
        except ValueError:
            costs.append(np.inf)
    sg_best = sig[int(np.argmin(costs))]
    return dict(h=h, r=r, sB=sB, sB_over_h=sB / h, saving=1 - opt / pure, brute_sigma=sg_best)


if __name__ == '__main__':
    for (p, c, g, K, lab) in [(0.5, 2, 0.3, 0.15, 'manuscript E2-type'), (0.155, 10, 0.3504, 0.02, 'Zhou 2024 params, K=0.02')]:
        print(f'--- {lab}: p={p}, c={c}, gamma={g}, K={K}')
        for th in [1.0, 0.5, 0.0]:
            R = solve(p, c, g, K, th, 1 - 1e-4, 1e-4)
            print(f"theta={th:3.1f}  r={R['r']:.4f}  sB/h={R['sB_over_h']:.4f}  brute-force best exit/h={R['brute_sigma']/R['h']:.4f}  saving vs pure capacity={100*R['saving']:.3f}%")
