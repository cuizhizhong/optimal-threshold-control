from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_tracing import Params, natural_peak, optimize_constant_c

base = Params()
_, ipk = natural_peak(base)
Ks = np.linspace(0.055, ipk * 1.03, 58)
Jopt, Jfill = [], []
reg = []
for K in Ks:
    if K <= base.i0 * 1.02:
        K = base.i0 * 1.02
    par = Params(p=base.p, c=base.c, gamma=base.gamma, K=float(K), s0=base.s0, i0=base.i0)
    sol = optimize_constant_c(par)
    Jopt.append(float(sol['cost']))
    Jfill.append(float(sol['fill_box_cost']))
    reg.append(sol['regime'])

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(Ks, Jopt, linewidth=2.5, label='Optimal cost')
ax.plot(Ks, Jfill, linestyle='--', linewidth=2.0, label='Pure fill-the-box cost')
ax.axvline(ipk, linestyle=':', linewidth=1.3, label='Natural peak')
ax.set_xlabel('Capacity $K$')
ax.set_ylabel('Minimum control cost')
ax.set_title('Capacity dependence and the cost of enforcing an incorrect structure')
ax.legend()
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_6_capacity_dependence.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
