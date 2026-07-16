# Initial-condition fitting method comparison

The fitted unknown is only the effective initial community infectious seed I0, with R(0)=0 and S0=N-I0.

- daily sqrt residual: fits daily new community/quarantine cases after a square-root variance-stabilizing transform.
- daily MSE: fits only daily new community/quarantine cases with ordinary residuals.
- paper-style MSE: fits daily new and cumulative community/quarantine cases with ordinary residuals, matching the structure of the He--Tang--Xiao data loss.
