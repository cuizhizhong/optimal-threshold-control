from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_tracing import Params, optimize_constant_c

ps = np.linspace(0.25, 0.85, 28)
Ks = np.linspace(0.06, 0.30, 27)
Z = np.zeros((len(Ks), len(ps)))
for iy, K in enumerate(Ks):
    for ix, p in enumerate(ps):
        try:
            par = Params(p=float(p), c=2.0, gamma=0.3, K=float(K), s0=0.99, i0=0.01)
            sol = optimize_constant_c(par)
            Z[iy, ix] = {'safe': 0, 'direct-q1': 1, 'capacity-q1': 2}[str(sol['regime'])]
        except Exception:
            Z[iy, ix] = np.nan

fig, ax = plt.subplots(figsize=(8.4, 5.6))
im = ax.imshow(Z, origin='lower', aspect='auto', extent=[ps[0], ps[-1], Ks[0], Ks[-1]], interpolation='nearest')
cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2])
cbar.ax.set_yticklabels(['No control', 'Direct $q=1$', 'Capacity + $q=1$'])
ax.set_xlabel('Transmission probability $p$')
ax.set_ylabel('Capacity $K$')
ax.set_title('Regime map for the constant-contact problem')
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_8_regime_map.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
