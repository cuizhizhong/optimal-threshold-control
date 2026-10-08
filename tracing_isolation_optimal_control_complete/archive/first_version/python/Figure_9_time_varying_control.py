"""Figure 9: prescribed time-varying contacts and unique regularized controls.

The script is independently runnable from any working directory.  It reads the
included reproducibility CSV.  Use ``python generate_data.py --recompute-tv``
to regenerate the optimization data before plotting.
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
data = np.genfromtxt(ROOT / 'data' / 'time_varying_multi_eps.csv', delimiter=',', names=True)

fig, ax = plt.subplots(figsize=(8.4, 5.3))
ax.step(data['time'], data['q_eps_0p10'], where='post', linewidth=1.9, label=r'$\varepsilon=0.10$')
ax.step(data['time'], data['q_eps_0p04'], where='post', linewidth=1.9, label=r'$\varepsilon=0.04$')
ax.step(data['time'], data['q_eps_0p015'], where='post', linewidth=1.9, label=r'$\varepsilon=0.015$')
ax2 = ax.twinx()
ax2.plot(data['time'], data['c'], linestyle='--', linewidth=1.7, label='$c(t)$')
ax.set_xlabel('Time')
ax.set_ylabel(r'Regularized optimal isolation $q_\varepsilon(t)$')
ax2.set_ylabel('Contact rate $c(t)$')
ax.set_ylim(-0.02, 1.04)
ax.set_title('Prescribed time-varying contacts: unique regularized controls')
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc='upper right')
ax.grid(alpha=0.20)
fig.tight_layout()
out = ROOT / 'figures' / 'Figure_9_time_varying_control.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
