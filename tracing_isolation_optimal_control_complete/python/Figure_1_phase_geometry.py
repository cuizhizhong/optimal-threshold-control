from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_tracing import Params, optimize_constant_c, simulate_optimal, switching_curve, safe_i, natural_i

par = Params()
sol = optimize_constant_c(par)
tr = simulate_optimal(par, t_end=14, n=2401)

sgrid = np.linspace(par.h, par.s0, 700)
lf_i = natural_i(sgrid, par)
safe = safe_i(sgrid, par)
sw_s, sw_i, _, _ = switching_curve(par, s_max=par.s0, n=240)

fig, ax = plt.subplots(figsize=(8.4, 5.8))
ax.plot(sgrid, lf_i, linestyle='--', linewidth=1.8, label='Uncontrolled orbit')
ax.plot(sgrid, safe, linestyle=':', linewidth=2.0, label='Maximal safe orbit')
if len(sw_s):
    order = np.argsort(sw_s)
    ax.plot(sw_s[order], sw_i[order], linewidth=2.0, label='Switching curve')
ax.axhline(par.K, linestyle='-.', linewidth=1.5, label='Capacity')
ax.axvline(par.h, linestyle=':', linewidth=1.2, label=r'$s=h$')
ax.plot(tr['s'], tr['i'], linewidth=3.0, label='Optimal trajectory')

pts = [
    (par.s0, par.i0, 'initial'),
    (float(sol['s1']), par.K, 'first hit'),
    (float(sol['s_switch']), float(sol['i_switch']), 'switch to q=1'),
    (float(sol['s_release']), float(sol['i_release']), 'release'),
]
for x, y, lab in pts:
    ax.scatter([x], [y], s=40, zorder=5)
    ax.annotate(lab, (x, y), xytext=(5, 7), textcoords='offset points', fontsize=9)

ax.set_xlim(0.08, 1.01)
ax.set_ylim(0, max(0.38, 1.08 * np.nanmax(lf_i)))
ax.set_xlabel('Susceptible fraction $s$')
ax.set_ylabel('Infectious fraction $i$')
ax.set_title('Phase-plane geometry of the unique tracing-isolation policy')
ax.legend(loc='upper left', fontsize=8.6, ncol=2)
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_1_phase_geometry.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
