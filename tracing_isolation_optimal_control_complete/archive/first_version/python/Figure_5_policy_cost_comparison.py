from pathlib import Path
import matplotlib.pyplot as plt
from common_tracing import Params, optimize_constant_c, q1_cost, natural_i

par = Params()
sol = optimize_constant_c(par)
s1 = float(sol['s1'])
values = [
    float(sol['cost']),
    float(sol['fill_box_cost']),
    q1_cost(s1, par.K, par)[0],
    q1_cost(__import__('scipy').optimize.brentq(lambda x: natural_i(x, par)-0.10, par.h, par.s0), 0.10, par)[0],
]
labels = ['Optimal', 'Pure fill-the-box', 'Full isolation at capacity', 'Full isolation at $i=0.10$']

fig, ax = plt.subplots(figsize=(8.4, 5.2))
bars = ax.bar(labels, values)
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, value + 0.03, f'{value:.3f}', ha='center', va='bottom', fontsize=9)
ax.set_ylabel('Total tracing cost')
ax.set_title('Cost comparison of feasible policies')
ax.tick_params(axis='x', rotation=16)
ax.grid(axis='y', alpha=0.22)
fig.tight_layout()
out = Path(__file__).resolve().parents[1] / 'figures' / 'Figure_5_policy_cost_comparison.jpg'
fig.savefig(out, dpi=300, bbox_inches='tight')
print(out)
