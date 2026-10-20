"""Checks for the return (S_q -> S at rate lam) extension in REVISION_PLAN v3.

New notation: beta = transmission probability, h = gamma/(beta c), ell = beta h, p = (1-beta) h.
  1. Symbolic: dPhi/dt, dPsi/dt with return; dF/dt for F = i + z - h ln z, z = s + s_q.
  2. lam -> infinity limit of the five-compartment model equals the theta = 0 two-dimensional model.
  3. Sampled-data simulation of the no-return optimal feedback Q*(s,i) applied to the return model:
       R1 = stop permanently at first entry into the 2D safe set (old release rule),
       R2 = keep applying the feedback (restarts allowed),
       R3 = full tracing until the return-safe certificate M(s+s_q, i) <= K, then stop.
"""
import numpy as np
import sympy as sp
from scipy.optimize import brentq


def symbolic():
    s, sq, i, beta, c, g, lam, q = sp.symbols('s s_q i beta c gamma lambda q', positive=True)
    h = g / (beta * c); ell = beta * h; p = (1 - beta) * h
    sd = -c * (beta + (1 - beta) * q) * s * i + lam * sq
    idot = beta * c * (1 - q) * s * i - g * i
    sqd = (1 - beta) * c * q * s * i - lam * sq
    Phi = i + s - h * sp.log(s); Psi = i - ell * sp.log(s)
    dPhi = sp.diff(Phi, s) * sd + sp.diff(Phi, i) * idot
    dPsi = sp.diff(Psi, s) * sd + sp.diff(Psi, i) * idot
    z = s + sq
    F = i + z - h * sp.log(z)
    dF = sp.diff(F, s) * sd + sp.diff(F, sq) * sqd + sp.diff(F, i) * idot
    print('dPhi - [-c q i (s-p) + lam s_q (1-h/s)] =', sp.simplify(dPhi - (-c * q * i * (s - p) + lam * sq * (1 - h / s))))
    print('dPsi - [beta c (1-q) i (s-p) - ell lam s_q / s] =', sp.simplify(dPsi - (beta * c * (1 - q) * i * (s - p) - ell * lam * sq / s)))
    print('dF - [-beta c q s i - gamma i s_q / z] =', sp.simplify(dF - (-beta * c * q * s * i - g * i * sq / z)))


def rk4(f, y, dt):
    k1 = f(y); k2 = f(y + dt / 2 * k1); k3 = f(y + dt / 2 * k2); k4 = f(y + dt * k3)
    return y + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def lam_limit(beta=0.5, c=2, g=0.3):
    """Same open-loop control in both models; compare (s,i)."""
    qfun = lambda t: 1.0 if 4.0 <= t < 6.0 else 0.0
    def five(lam):
        def run():
            y = np.array([0.99, 0.0, 0.01]); dt = 1e-4 if lam > 10 else 1e-3; out = []
            for k in range(int(30 / dt)):
                q = qfun(k * dt)
                f = lambda y: np.array([-c * (beta + (1 - beta) * q) * y[0] * y[2] + lam * y[1],
                                        (1 - beta) * c * q * y[0] * y[2] - lam * y[1],
                                        (beta * c * (1 - q) * y[0] - g) * y[2]])
                y = rk4(f, y, dt)
                if k % int(0.1 / dt) == 0: out.append((y[0], y[2]))
            return np.array(out)
        return run()
    def theta0():
        y = np.array([0.99, 0.01]); dt = 1e-4; out = []
        for k in range(int(30 / dt)):
            q = qfun(k * dt)
            f = lambda y: np.array([-beta * c * y[0] * y[1], (beta * c * (1 - q) * y[0] - g) * y[1]])
            y = rk4(f, y, dt)
            if k % int(0.1 / dt) == 0: out.append((y[0], y[1]))
        return np.array(out)
    ref = theta0()
    for lam in [10, 100, 1000]:
        print(f'lam={lam:>5}: max |(s,i)_five - (s,i)_theta0| = {np.abs(five(lam) - ref).max():.2e}')


class Feedback:
    """No-return optimal feedback Q*(s,i) of the manuscript (theta = 1)."""
    def __init__(self, beta, c, g, K):
        self.beta, self.c, self.g, self.K = beta, c, g, K
        h = g / (beta * c); self.h = h; self.ell = beta * h; self.p = (1 - beta) * h
        self.PhiA = K + h - h * np.log(h)
        self.a = lambda s: self.PhiA - s + h * np.log(s)
        gfun = lambda s: (s - h) * (s - self.p) / s
        sK = brentq(self.a, h * (1 + 1e-12), 50)
        self.e = brentq(lambda s: self.a(s) - gfun(s), h * (1 + 1e-12), sK)
        Th = lambda s, i: (s - h) / (i * (s - self.p))
        zs, sig, jj = [], [], []
        for z in np.linspace(h + 1e-6 * (self.e - h), self.e - 1e-6 * (self.e - h), 3000):
            Iz = lambda s: self.a(z) + self.ell * np.log(s / z)
            speak = brentq(lambda s: Iz(s) - gfun(s), z, 100)
            f = lambda s: Th(s, Iz(s)) - Th(z, self.a(z))
            hi = speak * 1.5
            while f(hi) > 0: hi *= 1.5
            sg = brentq(f, speak, hi); zs.append(z); sig.append(sg); jj.append(Iz(sg))
        order = np.argsort(sig); self.sig = np.array(sig)[order]; self.j = np.array(jj)[order]
        self.sB = float(np.interp(K, self.j, self.sig))

    def IGamma(self, s):
        return np.interp(s, self.sig, self.j, right=np.inf)

    def safe2d(self, s, i):
        return s <= self.h or i + s - self.h * np.log(s) <= self.PhiA

    def __call__(self, s, i):
        if self.safe2d(s, i): return 0.0
        if i >= self.K * (1 - 1e-9) and s > self.sB: return 1 - self.h / s
        if s <= self.e: return 1.0
        return 1.0 if i > self.IGamma(s) else 0.0


def simulate(fb, lam, rule, x0=(0.99, 0.01), T=600, dt=2e-3):
    beta, c, g, K, h = fb.beta, fb.c, fb.g, fb.K, fb.h
    y = np.array([x0[0], 0.0, x0[1]]); cost = 0.0; released = False; stopped = False
    imax_after = 0.0; restarts = 0; prev_q = None; imax = 0.0
    for k in range(int(T / dt)):
        s, sq, i = y
        z = s + sq
        M = i if z <= h else i + z - h - h * np.log(z / h)
        if rule == 'R1':
            if not stopped and fb.safe2d(s, i) and k > 0: stopped = True
            q = 0.0 if stopped else fb(s, i)
        elif rule == 'R2':
            q = fb(s, i)
        else:  # R3: nominal feedback, but no stop until certificate; once certified stop forever
            if not stopped and M <= K and k > 0: stopped = True
            q = 0.0 if stopped else (fb(s, i) if not fb.safe2d(s, i) else 1.0)
        if fb.safe2d(s, i) and k > 0: released = True
        if released: imax_after = max(imax_after, i)
        if prev_q is not None and prev_q == 0.0 and q > 0 and released: restarts += 1
        prev_q = q; imax = max(imax, i)
        f = lambda y: np.array([-c * (beta + (1 - beta) * q) * y[0] * y[2] + lam * y[1],
                                (1 - beta) * c * q * y[0] * y[2] - lam * y[1],
                                (beta * c * (1 - q) * y[0] - g) * y[2]])
        y = rk4(f, y, dt); cost += beta * c * q * dt
    return dict(overshoot=(imax - K) / K, cost=cost, restarts=restarts)


def release_experiment(beta=0.5, c=2, g=0.3, K=0.15, x0=(0.99, 0.01)):
    fb = Feedback(beta, c, g, K)
    print(f'--- release rules, beta={beta}, c={c}, gamma={g}, K={K}, x0={x0}, s_B={fb.sB:.5f}')
    for lam in [0.0, 1 / 28, 1 / 14, 1 / 7, 1 / 2, 5.0, 50.0]:
        r1 = simulate(fb, lam, 'R1', x0); r2 = simulate(fb, lam, 'R2', x0); r3 = simulate(fb, lam, 'R3', x0)
        print(f'lam={lam:7.4f} | R1 overshoot={100*r1["overshoot"]:7.3f}% cost={r1["cost"]:.4f} '
              f'| R2 overshoot={100*r2["overshoot"]:6.3f}% cost={r2["cost"]:.4f} restarts={r2["restarts"]} '
              f'| R3 overshoot={100*r3["overshoot"]:6.3f}% cost={r3["cost"]:.4f}')


if __name__ == '__main__':
    symbolic()
    lam_limit()
    release_experiment()
