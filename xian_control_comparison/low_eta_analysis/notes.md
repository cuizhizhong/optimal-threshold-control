# Low-threshold stress-test notes

Purpose: answer whether simply lowering the threshold solves the late-start problem.

Main finding: lowering eta starts control earlier and lowers the peak, but the gain in start time is small compared with the increase in control duration and clearance time.

Key comparison:

- eta=26326: t1=16.90, control duration=85.07, clear time=258.11.
- eta=100: t1=11.38, control duration=22523.29, clear time=23748.32.

Interpretation:

- Lower eta means the threshold is reached earlier, so t1 decreases.
- But the platform phase holds I(t)=eta. When eta is very low, S(t) is depleted very slowly.
- The theoretical duration contains a leading 1/eta factor, so low eta quickly creates unrealistic control times.
- Therefore lowering the capacity threshold is not a sufficient fix. A better extension is to keep a capacity threshold eta_cap and introduce an earlier warning threshold eta_warn < eta_cap.
