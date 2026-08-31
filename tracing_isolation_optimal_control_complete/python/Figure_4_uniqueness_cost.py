from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_tracing import Params, perturbation_cost_curve

par = Params()
s, J, sol = perturbation_cost_curve(par, n=420)
mask = np.isfinite(J)

fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.plot(s[mask], J[mask], linewidth=2.4, label='Admissible boundary-to-$q=1$ family')
ax.axvline(float(sol['s_switch']), linestyle='--', linewidth=1.4, label='Unique minimizer')
ax.scatter([float(sol['s_switch'])], [float(sol['cost'])], s=55, zorder=4)
ax.set_xlabel('Susceptible level at switch from boundary control to $q=1$')
ax.set_ylabel('Total control cost')
ax.set_title('Strict one-dimensional minimum and almost-everywhere uniqueness')
ax.legend()
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_4_uniqueness_cost.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
