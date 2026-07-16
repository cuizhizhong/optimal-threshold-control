function [traj, platform_error] = compute_trajectory(row)
%COMPUTE_TRAJECTORY Reconstruct the three-stage trajectory for one row.

if ~logical(row.valid)
    error('Cannot compute trajectory for invalid row.');
end

ode_background = @(~, Y) [
    -row.c0 * (row.beta + row.q0 * (1 - row.beta)) * Y(1) * Y(2) / row.N;
     row.beta * row.c0 * (1 - row.q0) * Y(1) * Y(2) / row.N - row.gamma * Y(2)
];
ode_control = @(t, Y) [
    -row.c0 * (row.beta + q_piecewise(row, t) * (1 - row.beta)) * Y(1) * Y(2) / row.N;
     row.beta * row.c0 * (1 - q_piecewise(row, t)) * Y(1) * Y(2) / row.N - row.gamma * Y(2)
];

n_pre = max(60, min(600, ceil(row.t1 * 35) + 2));
n_mid = max(120, min(2200, ceil(row.Delta_t * 10) + 2));
n_post = max(120, min(1200, ceil((row.t_end - row.t2) * 5) + 2));
options = odeset('RelTol', 1e-9, 'AbsTol', 1e-11);

t_pre_grid = linspace(0, row.t1, n_pre);
t_mid_grid = linspace(row.t1, row.t2, n_mid);
t_post_grid = linspace(row.t2, row.t_end, n_post);

[t_pre, Y_pre] = ode45(ode_background, t_pre_grid, [row.S0; row.I0], options);
[t_mid, Y_mid] = ode45(ode_control, t_mid_grid, [row.S_star; row.eta], options);
[t_post, Y_post] = ode45(ode_background, t_post_grid, [row.S_c; row.eta], options);

t = [t_pre; t_mid(2:end); t_post(2:end)];
Y = [Y_pre; Y_mid(2:end, :); Y_post(2:end, :)];
q = q_piecewise(row, t);
cost_rate = 2 .* (max(q - row.q0, 0) ./ (1 - row.q0)).^2;
J_cum = cumtrapz(t, cost_rate);

traj.t = t;
traj.S = Y(:, 1);
traj.I = Y(:, 2);
traj.q = q;
traj.J_cum = J_cum;
platform_error = max(abs(Y_mid(:, 2) - row.eta));
end

function q = q_piecewise(row, t)
q = row.q0 * ones(size(t));
mask = t >= row.t1 & t <= row.t2;
q(mask) = q_control_tau(row, t(mask) - row.t1);
end
