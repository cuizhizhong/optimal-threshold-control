"""Re-derive the key formulas of latex/main.tex in the new notation:
beta = transmission probability, h = gamma/(beta c), ell = beta h, p = (1-beta) h.
Each check prints True when the formula as written in the migrated paper is correct."""
import sympy as sp

s, i, q, c, g, beta, K, z, j, eta, sb, ib = sp.symbols('s i q c gamma beta K z j eta sbar ibar', positive=True)
h = g / (beta * c); ell = beta * h; p = (1 - beta) * h
PhiA = sp.Symbol('Phi_A')
a = lambda x: PhiA - x + h * sp.log(x)
G = lambda x: a(x) - ell * sp.log(x)
sd = -c * (beta + (1 - beta) * q) * s * i
idot = (beta * c * (1 - q) * s - g) * i
Phi = i + s - h * sp.log(s); Psi = i - ell * sp.log(s)
Theta = lambda x, y: (x - h) / (y * (x - p))
gfun = (s - h) * (s - p) / s
checks = {}
checks['h = p + ell'] = sp.simplify(h - (p + ell)) == 0
checks['Phi dot = -c q i (s-p)'] = sp.simplify(sp.diff(Phi, s) * sd + idot + c * q * i * (s - p)) == 0
checks['Psi dot = beta c (1-q) i (s-p)'] = sp.simplify(sp.diff(Psi, s) * sd + idot - beta * c * (1 - q) * i * (s - p)) == 0
qB = 1 - h / s
checks['q_B makes i dot = 0'] = sp.simplify(idot.subs(q, qB)) == 0
checks['capacity s dot = -cK(s-p)'] = sp.simplify(sd.subs({q: qB, i: K}) + c * K * (s - p)) == 0
shi, slo = sp.symbols('s_hi s_lo', positive=True)
CB = beta / (K * (1 - beta)) * (sp.log(shi / slo) - beta * sp.log((shi - p) / (slo - p)))
integrand = beta * c * qB / (c * K * (s - p))
checks['C_B closed form'] = sp.simplify(sp.diff(CB, shi) - integrand.subs(s, shi)) == 0
checks['full tracing cost (1/h) ln(i_a/i_b) rate'] = sp.simplify(beta * c - sp.diff(sp.log(i) / h, i) * (-g * i) * (-1)) == 0
checks["a'(s) = (h-s)/s"] = sp.simplify(sp.diff(a(s), s) - (h - s) / s) == 0
checks["G'(z) = (p-z)/z"] = sp.simplify(sp.diff(G(z), z) - (p - z) / z) == 0
# endpoint map sbar(s,i): G(sbar) = i - ell ln s
Gp = sp.diff(G(sb), sb)
sb_s = -(-ell / s) / Gp * (-1) * (-1)  # implicit: G'(sbar) sbar_s = -ell/s
sb_s = (-ell / s) / Gp
sb_i = 1 / Gp
checks['sbar_s = ell sbar/(s(sbar-p))'] = sp.simplify(sb_s - ell * sb / (s * (sb - p))) == 0
checks['sbar_i = -sbar/(sbar-p)'] = sp.simplify(sb_i + sb / (sb - p)) == 0
Wv = (sp.log(i) - sp.log(a(sb))) / h
W_s = -sp.diff(a(sb), sb) * sb_s / (h * a(sb))
W_i = 1 / (h * i) - sp.diff(a(sb), sb) * sb_i / (h * a(sb))
ibar = a(sb)
checks['W_s = (beta/s) Theta(sbar,ibar)'] = sp.simplify(W_s - beta / s * Theta(sb, ibar)) == 0
checks['W_i = (1/h)[1/i - Theta(sbar,ibar)]'] = sp.simplify(W_i - (1 / i - Theta(sb, ibar)) / h) == 0
f0 = (-beta * c * s * i, beta * c * (s - h) * i); f1 = (-c * s * i, -g * i)
checks['H_W(x,1) = 0'] = sp.simplify(W_s * f1[0] + W_i * f1[1] + beta * c) == 0
checks['H_W(x,0) = (beta c/h) i (s-p)[Theta(s,i) - Theta(sbar,ibar)]'] = sp.simplify(
    W_s * f0[0] + W_i * f0[1] - beta * c / h * i * (s - p) * (Theta(s, i) - Theta(sb, ibar))) == 0
zz = sp.Symbol('z0', positive=True)
Iz = a(zz) + ell * sp.log(s / zz)
checks['d/ds ln Theta(s,I_z) formula'] = sp.simplify(sp.diff(sp.log(Theta(s, Iz)), s)
                                                  - ell * (1 / ((s - h) * (s - p)) - 1 / (s * Iz))) == 0
checks['d/ds (g - I_z) = (s-h)(s+p)/s^2'] = sp.simplify(sp.diff(gfun - Iz, s) - (s - h) * (s + p) / s**2) == 0
checks['g(s) = s - h - p + hp/s'] = sp.simplify(gfun - (s - h - p + h * p / s)) == 0
U_i = beta / (j * (eta - p)); U_s = beta * (s - h) / (s * j * (eta - p))
H0U = -beta * c * s * i * U_s + beta * c * (s - h) * i * U_i
SigU = beta * c - c * s * i * ((1 - beta) * U_s + beta * U_i)
checks['waiting H_0,U = 0'] = sp.simplify(H0U) == 0
checks['waiting Sigma_U = beta c[1 - i(s-p)/(j(eta-p))]'] = sp.simplify(SigU - beta * c * (1 - i * (s - p) / (j * (eta - p)))) == 0
xi = sp.Symbol('xi', positive=True); iota = sp.Function('iota')
expr = sp.diff(iota(xi) * (xi - p), xi).subs(sp.diff(iota(xi), xi), h / xi - 1)
checks['d/dxi[iota (xi-p)] = iota - g'] = sp.simplify(expr - (iota(xi) - gfun.subs(s, xi))) == 0
UsK = beta * (s - h) / (K * s * (s - p)); UiK = beta / (K * (s - p))
checks['plateau (1-beta)U_s + beta U_i = beta/(Ks)'] = sp.simplify((1 - beta) * UsK + beta * UiK - beta / (K * s)) == 0
checks['plateau Sigma_U = 0'] = sp.simplify(beta * c - c * s * K * ((1 - beta) * UsK + beta * UiK)) == 0
checks['plateau H_0,U = 0'] = sp.simplify(-beta * c * s * K * UsK + beta * c * (s - h) * K * UiK) == 0
etaK = sp.Symbol('eta_K', positive=True)
checks["dC_B/deta = beta(eta-h)/(K eta(eta-p))"] = sp.simplify(sp.diff(CB.subs(shi, etaK), etaK)
                                                            - beta * (etaK - h) / (K * etaK * (etaK - p))) == 0
A_, B_ = 1 / (1 - beta), -beta / (1 - beta)
checks['partial fractions A=1/(1-beta), B=-beta/(1-beta)'] = sp.simplify((s - h) / (s * (s - p)) - (A_ / s + B_ / (s - p))) == 0
checks["beta h + s - h = s - p"] = sp.simplify(beta * h + s - h - (s - p)) == 0
checks["G'(h) = -beta"] = sp.simplify(((p - z) / z).subs(z, h) + beta) == 0
for k, v in checks.items():
    print(f'{str(v):5}  {k}')
print('ALL OK' if all(checks.values()) else 'SOME FAILED')
