from pathlib import Path
import matplotlib.pyplot as plt
from common_tracing import Params, simulate_optimal

par = Params()
tr = simulate_optimal(par, t_end=18, n=3001)
sol = tr['summary']

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(tr['t'], tr['s'], linewidth=2.2, label='$s(t)$')
ax.plot(tr['t'], tr['i'], linewidth=2.6, label='$i(t)$')
ax.axhline(par.K, linestyle='--', linewidth=1.5, label='Capacity $K$')
for tt, lab in [
    (float(sol['tau1']), r'$\tau_1$'),
    (float(sol['tau1']) + float(sol['tau_boundary']), r'$\tau_B$'),
    (float(sol['tau1']) + float(sol['tau_boundary']) + float(sol['tau_q1']), r'$\tau_R$'),
]:
    ax.axvline(tt, linestyle=':', linewidth=1.2)
    ax.text(tt + 0.08, 0.94, lab, transform=ax.get_xaxis_transform(), fontsize=9)
ax.set_xlabel('Time')
ax.set_ylabel('Population fraction')
ax.set_title('State trajectories under the optimal policy')
ax.set_ylim(0, 1.02)
ax.legend(loc='upper right')
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_2_state_time_series.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
