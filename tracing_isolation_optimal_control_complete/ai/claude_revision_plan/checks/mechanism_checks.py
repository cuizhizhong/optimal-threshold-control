"""Independent checks used in REVISION_PLAN.md (constant contact rate).

1. Symbolic: the running cost p*c*q dt equals the 1-form -p dPhi/(i(s-r)); Green integrand.
2. Caseload cost p*c*q*i: best start of full tracing for E1 versus the manuscript cost.
3. Negative discrete cost gaps (E4 main, E3 N=2000) versus V_K - V_{K+delta}.
"""
import numpy as np
import sympy as sp
from scipy.optimize import brentq


def symbolic_cost_form():
    s, i, p, c, g = sp.symbols('s i p c gamma', positive=True)
    h = g / (p * c); r = (1 - p) * h
    f0 = sp.Matrix([-p * c * s * i, p * c * (s - h) * i])
    f1 = sp.Matrix([-c * s * i, -g * i])
    G = f1 - f0
    Delta = sp.simplify(f0[0] * G[1] - f0[1] * G[0])
    u_di = sp.simplify(p * c * f0[0] / Delta)   # coefficient of di in cost form
    v_ds = sp.simplify(-p * c * f0[1] / Delta)  # coefficient of ds in cost form
    Phi = i + s - h * sp.log(s)
    ok = (sp.simplify(v_ds + p / (i * (s - r)) * sp.diff(Phi, s)) == 0
          and sp.simplify(u_di + p / (i * (s - r)) * sp.diff(Phi, i)) == 0)
    w = sp.simplify(sp.diff(u_di, s) - sp.diff(v_ds, i))
    gs = (s - h) * (s - r) / s
    print('cost form == -p dPhi/(i(s-r)):', ok)
    print('Green integrand * i^2 (s-r)^2 / p - (i - g(s)) =', sp.simplify(w * i**2 * (s - r)**2 / p - (i - gs)))


class Model:
    def __init__(self, p, c, g, K):
        self.p, self.c, self.g, self.K = p, c, g, K
        h = g / (p * c); self.h, self.r, self.l = h, (1 - p) * h, p * h
        self.PhiA = K + h - h * np.log(h)
        self.sK = brentq(self.a, h * (1 + 1e-14), 50)

    def a(self, s):
        return self.PhiA - s + self.h * np.log(s)

    def G(self, z):
        return self.a(z) - self.l * np.log(z)

    def Phi(self, s, i):
        return i + s - self.h * np.log(s)

    def zbar(self, s, i):
        return brentq(lambda z: self.G(z) - (i - self.l * np.log(s)), self.h * (1 + 1e-14), min(s, self.sK) * (1 - 1e-14))

    def W(self, s, i):
        return np.log(i / self.a(self.zbar(s, i))) / self.h

    def CB(self, hi, lo):
        p, K, r = self.p, self.K, self.r
        return p / (K * (1 - p)) * (np.log(hi / lo) - p * np.log((hi - r) / (lo - r)))

    def sB(self):
        Th = lambda s, i: (s - self.h) / (i * (s - self.r))
        def D(s):
            z = self.zbar(s, self.K)
            return Th(z, self.a(z)) - Th(s, self.K)
        grid = np.linspace(self.h * (1 + 1e-6), 2, 8000); v = []
        for s in grid:
            try:
                v.append(D(s))
            except ValueError:
                v.append(np.nan)
        v = np.array(v)
        k = [j for j in range(len(v) - 1) if np.isfinite(v[j]) and np.isfinite(v[j + 1]) and v[j] < 0 <= v[j + 1]][0]
        return brentq(D, grid[k], grid[k + 1])

    def V(self, s0, i0):
        """Value for initial states in W_K, B or T (enough for E3/E4)."""
        sB = self.sB(); PhiB = self.Phi(sB, self.K)
        if self.Phi(s0, i0) > PhiB:
            eta = s0 if i0 >= self.K else brentq(lambda s: self.Phi(s, self.K) - self.Phi(s0, i0), sB, s0)
            return self.CB(eta, sB) + self.W(sB, self.K)
        return self.W(s0, i0)


def caseload_cost_E1():
    m = Model(0.5, 2, 0.3, 0.15)
    s0, i0 = 0.75, 0.01
    Phi0 = m.Phi(s0, i0)
    rows = []
    for sg in np.linspace(s0, 0.5102, 400):
        inat = Phi0 - sg + m.h * np.log(sg)
        if inat > m.K:
            break
        try:
            ib = m.a(m.zbar(sg, inat))
        except ValueError:
            continue
        rows.append((sg, inat, (inat - ib) / m.h, np.log(inat / ib) / m.h))
    rows = np.array(rows)
    k1, k2 = np.argmin(rows[:, 2]), np.argmin(rows[:, 3])
    print(f'E1 caseload cost: best start s={rows[k1,0]:.4f} (s0=0.75 = immediate), cost {rows[k1,2]:.5f}')
    print(f'E1 intensity cost: best start (s,i)=({rows[k2,0]:.4f},{rows[k2,1]:.4f}); manuscript (0.5102,0.1342)')


def negative_gaps():
    for lab, (s0, i0), gap, dlt in [('E4 main', (0.70, 0.15), -3.68275844664e-06, 7.70286958773e-07),
                                    ('E3 N=2000', (0.50, 0.14), -6.7554e-05, 7.8301e-06)]:
        v0 = Model(0.5, 2, 0.3, 0.15).V(s0, i0)
        v1 = Model(0.5, 2, 0.3, 0.15 + dlt).V(s0, i0)
        print(f'{lab}: V_K - V_(K+delta) = {v0 - v1:.3e}, |gap| = {abs(gap):.3e}, explained: {v0 - v1 >= abs(gap)}')


if __name__ == '__main__':
    symbolic_cost_form()
    caseload_cost_E1()
    negative_gaps()
