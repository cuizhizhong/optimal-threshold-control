from pathlib import Path
import matplotlib.pyplot as plt
from common_tracing import Params, simulate_optimal

par = Params()
tr = simulate_optimal(par, t_end=13, n=2601)

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(tr['t'], tr['q'], linewidth=2.5, label='Isolation fraction $q^*(t)$')
ax.plot(tr['t'], tr['beta1'] / par.c, linewidth=2.0, label=r'$\beta_1^*/c$')
ax.plot(tr['t'], tr['beta2'] / par.c, linewidth=2.0, label=r'$\beta_2^*/c$')
ax.axhline(par.p, linestyle='--', linewidth=1.2, label='Natural normalized rate $p$')
ax.set_xlabel('Time')
ax.set_ylabel('Control / normalized coefficient')
ax.set_title('One control produces two different optimal coefficients')
ax.set_ylim(-0.02, 1.05)
ax.legend(loc='upper right')
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_3_control_coefficients.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
