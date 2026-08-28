function info = scenario1_inflection_point(row)
%SCENARIO1_INFLECTION_POINT Locate the internal inflection of q_c(t).

info.q_inf = 1 - 1 / (2 * (1 - row.beta));
info.has_inflection = false;
info.t_inf = NaN;
info.tau_inf = NaN;
info.q_at_inf = NaN;

if ~logical(row.valid)
    return;
end

tol = 1e-10;
strength_condition = row.q0 + tol < info.q_inf && ...
    info.q_inf < row.q_max - tol;
state_condition = row.S_c + tol < 2 * row.S_bar && ...
    2 * row.S_bar < row.S_star - tol;
if ~(strength_condition && state_condition)
    return;
end

ratio = (row.S_star - row.S_bar) / row.S_bar;
if ratio <= 0
    return;
end

info.tau_inf = row.N / (row.c0 * row.eta) * log(ratio);
info.t_inf = row.t1 + info.tau_inf;
info.q_at_inf = q_control_tau(row, info.tau_inf);
info.has_inflection = info.t_inf > row.t1 && info.t_inf < row.t2;
end
