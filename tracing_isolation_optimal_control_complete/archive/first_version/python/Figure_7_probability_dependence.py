from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_tracing import Params, optimize_constant_c, natural_peak

ps = np.linspace(0.24, 0.84, 50)
saving = []
validp = []
for p in ps:
    par = Params(p=float(p), c=2.0, gamma=0.3, K=0.15, s0=0.99, i0=0.01)
    _, ipk = natural_peak(par)
    if ipk <= par.K or par.s0 <= par.h:
        continue
    sol = optimize_constant_c(par)
    jf = float(sol['fill_box_cost'])
    jo = float(sol['cost'])
    if jf > 1e-10:
        validp.append(p)
        saving.append(100.0 * (jf - jo) / jf)

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.plot(validp, saving, linewidth=2.5)
ax.set_xlabel('Transmission probability per contact $p$')
ax.set_ylabel('Cost saving relative to pure fill-the-box (%)')
ax.set_title('Why tracing isolation changes the optimal geometry')
ax.grid(alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_7_probability_dependence.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
