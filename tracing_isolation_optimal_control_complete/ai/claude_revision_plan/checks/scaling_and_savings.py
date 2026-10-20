"""Independent check of s_B, optimal cost, savings and epidemiological side quantities
for the tracing-isolation capacity problem (constant c). Formulas from main.tex."""
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import quad


def setup(p, c, gamma, K):
    h = gamma / (p * c); l = p * h; r = (1 - p) * h
    PhiA = K + h - h * np.log(h)
    a = lambda s: PhiA - s + h * np.log(s)
    G = lambda z: a(z) - l * np.log(z)
    sK = brentq(a, h * (1 + 1e-14), 50.0)
    Theta = lambda s, i: (s - h) / (i * (s - r))
    return dict(h=h, l=l, r=r, PhiA=PhiA, a=a, G=G, sK=sK, Theta=Theta, p=p, c=c, K=K)


def endpoint(P, s, i):
    # full-tracing endpoint zbar on safe boundary: G(z) = i - l ln s, z in (h, s)
    target = i - P['l'] * np.log(s)
    f = lambda z: P['G'](z) - target
    return brentq(f, P['h'] * (1 + 1e-14), min(s, P['sK']) * (1 - 1e-14))


def sB(P):
    K, h = P['K'], P['h']
    def D(s):
        z = endpoint(P, s, K)
        return P['Theta'](z, P['a'](z)) - P['Theta'](s, K)
    grid = np.linspace(h * (1 + 1e-6), min(P['sK'] * np.exp(K / P['l']) * 0.999999, 20), 4000)
    vals = []
    for s in grid:
        try:
            vals.append(D(s))
        except ValueError:
            vals.append(np.nan)
    vals = np.array(vals)
    idx = [k for k in range(len(grid) - 1) if np.isfinite(vals[k]) and np.isfinite(vals[k + 1]) and vals[k] < 0 <= vals[k + 1]]
    return brentq(D, grid[idx[0]], grid[idx[0] + 1])


def CB(P, hi, lo):
    p, K, r = P['p'], P['K'], P['r']
    return p / (K * (1 - p)) * (np.log(hi / lo) - p * np.log((hi - r) / (lo - r)))


def W(P, s, i):
    z = endpoint(P, s, i)
    return np.log(i / P['a'](z)) / P['h'], z


def analyse(p, c, gamma, K, s0, i0):
    P = setup(p, c, gamma, K); h, r = P['h'], P['r']
    s1 = brentq(lambda s: i0 + s0 - s + h * np.log(s / s0) - K, h * (1 + 1e-12), s0)
    sb = sB(P)
    pure = CB(P, s1, h)
    w, zbar = W(P, sb, K)
    opt = CB(P, s1, sb) + w
    # uninfected susceptibles quarantined (fraction of N): (1-p) * int c q s i dt
    cap_q = lambda lo, hi: (1 - p) * quad(lambda s: (s - h) / (s - r), lo, hi)[0]
    Qpure = cap_q(h, s1)
    Qopt = cap_q(sb, s1) + (1 - p) * (sb - zbar)
    # final natural susceptible (same for both: both end on Phi = PhiA)
    sinf = brentq(lambda s: s - h * np.log(s) - P['PhiA'], 1e-12, h * (1 - 1e-12))
    # durations
    T_cap_pure = np.log((s1 - r) / (h - r)) / (c * K)
    T_cap_opt = np.log((s1 - r) / (sb - r)) / (c * K)
    T_full = np.log(K / P['a'](zbar)) / gamma
    return dict(h=h, sB=sb, sB_over_h=sb / h, zbar=zbar, ibar=P['a'](zbar), pure=pure, opt=opt,
                saving=1 - opt / pure, Qpure=Qpure, Qopt=Qopt, sinf=sinf,
                true_S_pure=sinf + Qpure, true_S_opt=sinf + Qopt,
                Tpure=T_cap_pure, Topt=T_cap_opt + T_full)


if __name__ == '__main__':
    print('--- E2 reproduction (paper: sB=0.54769512, J*=1.529511, saving 3.10%) ---')
    R = analyse(0.5, 2, 0.3, 0.15, 0.99, 0.01)
    for k, v in R.items():
        print(f'{k:12s} {v:.6f}')
    print('\n--- K sweep, p=0.5,c=2,gamma=0.3 (R0=3.33), s0=1-1e-4, i0=1e-4 ---')
    print(f"{'K':>8} {'sB/h':>8} {'saving%':>8} {'ibar/K':>8} {'Qpure':>8} {'Qopt':>8} {'sinf+Qopt':>9} {'h':>6}")
    for K in [0.15, 0.05, 0.01, 0.003, 0.001]:
        R = analyse(0.5, 2, 0.3, K, 1 - 1e-4, 1e-4)
        print(f"{K:8.3f} {R['sB_over_h']:8.4f} {100*R['saving']:8.3f} {R['ibar']/K:8.4f} {R['Qpure']:8.4f} {R['Qopt']:8.4f} {R['true_S_opt']:9.4f} {R['h']:6.3f}")
    print('\n--- p sweep at fixed R0=pc/gamma=3.33, gamma=0.3, K=0.01 ---')
    for p in [0.05, 0.2, 0.5, 0.8, 0.95]:
        c = 0.3 * (1 / 0.3) / p
        R = analyse(p, c, 0.3, 0.01, 1 - 1e-4, 1e-4)
        print(f"p={p:4.2f} c={c:6.2f} sB/h={R['sB_over_h']:.4f} saving={100*R['saving']:.3f}%  Qopt={R['Qopt']:.4f} Qpure={R['Qpure']:.4f}")
