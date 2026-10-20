"""High-precision checks of the small-K expansions and the q<=m feasibility envelope
proposed in the second-round ChatGPT plan (constant contact rate, theta=1 model).

Claims checked:
  (1) s_B - h = K/p - (1-p) K^2 / (p^3 h) + O(K^3)
  (2) Delta J = C_B(s_B, h) - W(s_B, K) = K^2 / (24 p^4 h^3) + O(K^3)   (common capacity tail)
  (3) T_fill - T* (positive-control time on the common tail) -> 1/(p gamma)
  (4) q<=m: F_m = i + rho_m s - d_m ln s satisfies dF_m/dt = p c (m-q)(s-r) i / D_m,
      and B_m(s) is the maximal feasible infection envelope (checked by simulation).
"""
import mpmath as mp
import numpy as np
from scipy.integrate import solve_ivp

mp.mp.dps = 50


def geometry(p, c, g, K):
    p, c, g, K = map(mp.mpf, (p, c, g, K))
    h = g / (p * c); r = (1 - p) * h; l = p * h
    PhiA = K + h - h * mp.log(h)
    a = lambda s: PhiA - s + h * mp.log(s)
    G = lambda z: a(z) - l * mp.log(z)
    Th = lambda s, i: (s - h) / (i * (s - r))
    return dict(p=p, c=c, g=g, K=K, h=h, r=r, l=l, a=a, G=G, Th=Th)


def zbar(P, s, i):
    target = i - P['l'] * mp.log(s)
    h = P['h']
    return mp.findroot(lambda z: P['G'](z) - target, (h * (1 + mp.mpf('1e-30')), s), solver='anderson')


def sB(P):
    h, K, p = P['h'], P['K'], P['p']
    def D(s):
        z = zbar(P, s, K)
        return P['Th'](z, P['a'](z)) - P['Th'](s, K)
    guess = h + K / p
    return mp.findroot(D, (guess * (1 - mp.mpf('0.2') * K / h), guess * (1 + mp.mpf('0.2') * K / h)), solver='anderson')


def tails(P):
    p, c, g, K, h, r = P['p'], P['c'], P['g'], P['K'], P['h'], P['r']
    s_b = sB(P)
    z = zbar(P, s_b, K); ib = P['a'](z)
    CB = p / (K * (1 - p)) * (mp.log(s_b / h) - p * mp.log((s_b - r) / (h - r)))
    W = mp.log(K / ib) / h
    T_fill = mp.log((s_b - r) / (h - r)) / (c * K)
    T_star = mp.log(K / ib) / g
    return s_b, CB - W, T_fill - T_star


def check_asymptotics(p=0.5, c=2, g=0.3):
    print(f'--- small-K expansions, p={p}, c={c}, gamma={g}')
    for K in ['1e-2', '1e-3', '1e-4', '1e-5']:
        P = geometry(p, c, g, K)
        s_b, dJ, dT = tails(P)
        h, Kv, pv = P['h'], P['K'], P['p']
        e1 = (s_b - h) - (Kv / pv - (1 - pv) * Kv**2 / (pv**3 * h))
        c2 = dJ / Kv**2
        print(f'K={K:>5}: [(s_B-h) - 2nd-order]/K^3 = {mp.nstr(e1 / Kv**3, 6):>10}   '
              f'DeltaJ/K^2 = {mp.nstr(c2, 8)} (claim {mp.nstr(1 / (24 * pv**4 * h**3), 8)})   '
              f'T_fill-T* = {mp.nstr(dT, 8)} (claim {mp.nstr(1 / (pv * P["g"]), 8)})')


def check_feasibility(p=0.5, c=2, g=0.3, K=0.15, m=0.6):
    print(f'--- q<=m feasibility envelope, p={p}, c={c}, gamma={g}, K={K}, m={m}')
    h = g / (p * c); r = (1 - p) * h
    Dm = p + (1 - p) * m; rho = p * (1 - m) / Dm; d = g / (c * Dm); hm = g / (p * c * (1 - m))
    B = lambda s: K if s <= hm else K - rho * (s - hm) + d * np.log(s / hm)
    # symbolic-free check of dF_m/dt formula at random states and controls
    rng = np.random.default_rng(0); worst = 0.0
    for _ in range(2000):
        s, i, q = rng.uniform(r * 1.01, 1), rng.uniform(1e-4, 0.3), rng.uniform(0, m)
        sd = -c * (p + (1 - p) * q) * s * i; idot = (p * c * (1 - q) * s - g) * i
        Fdot = idot + rho * sd - d * sd / s
        worst = max(worst, abs(Fdot - p * c * (m - q) * (s - r) * i / Dm))
    print(f'max |dF_m/dt - formula| over random samples = {worst:.2e}')

    def peak_under_max_control(s0, i0):
        f = lambda t, y: [-c * (p + (1 - p) * m) * y[0] * y[1], (p * c * (1 - m) * y[0] - g) * y[1]]
        sol = solve_ivp(f, [0, 2000], [s0, i0], rtol=1e-11, atol=1e-14, max_step=0.5)
        return sol.y[1].max()
    print(f'h={h:.4f}, h_m={hm:.4f}')
    for s0 in [0.55, 0.7, 0.85]:
        if s0 <= hm:
            continue
        b = B(s0)
        if b <= 0:
            print(f's0={s0}: envelope B_m={b:.4f} <= 0 (no feasible positive infection)'); continue
        below, above = peak_under_max_control(s0, 0.999 * b), peak_under_max_control(s0, 1.001 * b)
        print(f's0={s0}: B_m={b:.6f}; peak with q=m from 0.999B: {below:.6f} (<=K), from 1.001B: {above:.6f} (>K)')


if __name__ == '__main__':
    check_asymptotics()
    check_asymptotics(p=0.155, c=10, g=0.3504)
    check_feasibility()
