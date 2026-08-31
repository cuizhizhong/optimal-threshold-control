"""Figure 10: state constraint under a prescribed contact surge.

The script is independently runnable from any working directory and uses the
included regularized-optimum and no-control CSV files.
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
opt = np.genfromtxt(ROOT / 'data' / 'time_varying_regularized_solution.csv', delimiter=',', names=True)
no = np.genfromtxt(ROOT / 'data' / 'time_varying_no_control.csv', delimiter=',', names=True)
K = 0.15

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(opt['time'], opt['i'], linewidth=2.5, label='Optimized $i(t)$')
ax.plot(no['time'], no['i_no'], linestyle='--', linewidth=2.0, label='No isolation')
ax.axhline(K, linestyle=':', linewidth=1.6, label='Capacity $K$')
ax.set_xlabel('Time')
ax.set_ylabel('Infectious fraction')
ax.set_title('State constraint under a contact surge')
ax.legend()
ax.grid(alpha=0.22)
fig.tight_layout()
out = ROOT / 'figures' / 'Figure_10_time_varying_states.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
