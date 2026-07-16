function q = q_control_tau(row, tau)
%Q_CONTROL_TAU Open-loop isolation control on the platform phase.

S_phase = row.S_bar + (row.S_star - row.S_bar) .* ...
    exp(-row.c0 .* row.eta .* tau ./ row.N);
q = 1 - row.gamma .* row.N ./ (row.beta .* row.c0 .* S_phase);
end
