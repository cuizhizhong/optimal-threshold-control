function [row, diagnostics] = compute_metrics(beta, gamma, c0, q0, N, eta, S0, I0)
%COMPUTE_METRICS Compute scenario-one threshold-control metrics.

row = empty_metrics();
diagnostics = empty_diagnostic();
row.R0 = beta * c0 * (1 - q0) / gamma;
row.beta = beta;
row.gamma = gamma;
row.c0 = c0;
row.q0 = q0;
row.N = N;
row.eta = eta;
row.eta_frac = eta / N;
row.eta_percent = 100 * eta / N;
row.S0 = S0;
row.I0 = I0;

if beta <= 0 || beta >= 1 || gamma <= 0 || c0 <= 0 || ...
        q0 < 0 || q0 >= 1 || N <= 0 || eta <= 0
    row.status_code = "invalid_parameter";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_parameter', ...
        'Basic parameter bounds failed.');
    return;
end

H = beta + q0 * (1 - beta);
beta1_0 = c0 * H / N;
beta2_0 = beta * c0 * (1 - q0) / N;
a = beta2_0 / beta1_0;
rho1 = gamma / beta1_0;
S_c = gamma / beta2_0;
S_bar = gamma * N * (1 - beta) / (beta * c0);

row.a = a;
row.rho1 = rho1;
row.S_c = S_c;
row.S_bar = S_bar;

I_of_S = @(S) I0 - a .* (S - S0) + rho1 .* log(S ./ S0);

if I0 >= eta
    row.status_code = "initial_above_threshold";
    diagnostics = add_diagnostic(diagnostics, row, 'initial_above_threshold', ...
        'Initial I0 is not below eta.');
    return;
end

if S_c >= S0
    row.status_code = "threshold_not_reached";
    diagnostics = add_diagnostic(diagnostics, row, 'threshold_not_reached', ...
        'S_c is not below S0, so the background infection does not grow first.');
    return;
end

Imax_pre = I_of_S(S_c);
row.Imax_pre = Imax_pre;
if Imax_pre <= eta
    row.status_code = "threshold_not_reached";
    diagnostics = add_diagnostic(diagnostics, row, 'threshold_not_reached', ...
        'Background peak does not exceed eta.');
    return;
end

K = a * S0 + I0 - eta;
z = -(S0 / S_c) * exp(-K / rho1);
S_star_raw = -S_c * double(lambertw(-1, z));
if abs(imag(S_star_raw)) > 1e-8
    row.status_code = "invalid_ordering";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_ordering', ...
        'S_star is not real on the -1 Lambert W branch.');
    return;
end
S_star = real(S_star_raw);

if ~(S0 > S_star && S_star > S_c && S_c > S_bar)
    row.S_star = S_star;
    row.status_code = "invalid_ordering";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_ordering', ...
        'Expected S0 > S_star > S_c > S_bar.');
    return;
end
row.S_star = S_star;

integrand_t1 = @(S) 1 ./ (beta1_0 .* S .* I_of_S(S));
try
    t1 = integral(integrand_t1, S_star, S0, 'ArrayValued', true, ...
        'AbsTol', 1e-11, 'RelTol', 1e-11);
catch err
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', err.message);
    return;
end

term_num = S_star - S_bar;
term_den = S_c - S_bar;
if term_num <= 0 || term_den <= 0
    row.status_code = "invalid_ordering";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_ordering', ...
        'Nonpositive logarithm argument for Delta_t.');
    return;
end

Delta_t = (N / (c0 * eta)) * log(term_num / term_den);
t2 = t1 + Delta_t;
q_max = 1 - gamma * N / (beta * c0 * S_star);
q_t2 = 1 - gamma * N / (beta * c0 * S_c);
q_t2_error = abs(q_t2 - q0);

row.t1 = t1;
row.t2 = t2;
row.Delta_t = Delta_t;
row.q_max = q_max;
row.q_t2_error = q_t2_error;

if Delta_t <= 0 || t2 <= t1
    row.status_code = "invalid_ordering";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_ordering', ...
        'Expected Delta_t > 0 and t2 > t1.');
    return;
end
if q_max > 1 + 1e-8
    row.status_code = "q_out_of_bounds";
    diagnostics = add_diagnostic(diagnostics, row, 'q_out_of_bounds', ...
        'q_max exceeds 1.');
    return;
end
if q_max < q0 - 1e-8
    row.status_code = "q_below_q0";
    diagnostics = add_diagnostic(diagnostics, row, 'q_below_q0', ...
        'q_max is below q0.');
    return;
end
if q_t2_error > 1e-8
    diagnostics = add_diagnostic(diagnostics, row, 'q_t2_mismatch', ...
        'q_c(t2) is not close to q0.');
end

q_of_S = @(S) 1 - gamma .* N ./ (beta .* c0 .* S);
normalized_q = @(S) max(q_of_S(S) - q0, 0) ./ (1 - q0);
try
    J_q = integral(@(S) normalized_q(S) ./ (S - S_bar), ...
        S_c, S_star, 'ArrayValued', true, 'AbsTol', 1e-11, 'RelTol', 1e-11) ...
        * N / (c0 * eta);
    J = integral(@(S) 2 .* normalized_q(S).^2 ./ (S - S_bar), ...
        S_c, S_star, 'ArrayValued', true, 'AbsTol', 1e-11, 'RelTol', 1e-11) ...
        * N / (c0 * eta);
catch err
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', err.message);
    return;
end
q_mean = q0 + (1 - q0) * J_q / Delta_t;

C2 = eta + (beta2_0 / beta1_0) * S_c - rho1 * log(S_c);
z_end = -(beta2_0 / (beta1_0 * rho1)) * exp((1 - C2) / rho1);
S_end_raw = -(beta1_0 * rho1 / beta2_0) * double(lambertw(0, z_end));
if abs(imag(S_end_raw)) > 1e-8
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', ...
        'S_end is not real on the 0 Lambert W branch.');
    return;
end
S_end = real(S_end_raw);
if S_end <= 0 || S_end >= S_c
    row.S_end = S_end;
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', ...
        'Expected 0 < S_end < S_c.');
    return;
end

integrand_end = @(S) 1 ./ ...
    (S .* (beta2_0 .* S - beta1_0 .* rho1 .* log(S) - beta1_0 .* C2));
try
    t_end_tail = integral(integrand_end, S_c, S_end, ...
        'ArrayValued', true, 'AbsTol', 1e-11, 'RelTol', 1e-11);
catch err
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', err.message);
    return;
end
t_end = t2 + t_end_tail;
if ~isfinite(t_end) || t_end <= t2
    row.status_code = "invalid_tail";
    diagnostics = add_diagnostic(diagnostics, row, 'invalid_tail', ...
        'Expected finite t_end > t2.');
    return;
end

infection_fraction = beta / (beta + q0 * (1 - beta));
I_pre = infection_fraction * (S0 - S_star);
I_wall = beta * (S_star - S_c + ...
    S_bar * log((S_star - S_bar) / (S_c - S_bar)));
I_post = infection_fraction * (S_c - S_end);
I_t_cum = I_pre + I_wall + I_post;

row.valid = true;
row.status_code = "ok";
row.S_end = S_end;
row.t_end = t_end;
row.q_mean = q_mean;
row.J_q = J_q;
row.J = J;
row.I_pre = I_pre;
row.I_wall = I_wall;
row.I_post = I_post;
row.I_t_cum = I_t_cum;
end

function row = empty_metrics()
row = struct( ...
    'valid', false, ...
    'status_code', "", ...
    'R0', NaN, ...
    'beta', NaN, ...
    'gamma', NaN, ...
    'c0', NaN, ...
    'q0', NaN, ...
    'N', NaN, ...
    'eta', NaN, ...
    'eta_frac', NaN, ...
    'eta_percent', NaN, ...
    'S0', NaN, ...
    'I0', NaN, ...
    'a', NaN, ...
    'rho1', NaN, ...
    'S_star', NaN, ...
    'S_c', NaN, ...
    'S_bar', NaN, ...
    't1', NaN, ...
    't2', NaN, ...
    'Delta_t', NaN, ...
    'S_end', NaN, ...
    't_end', NaN, ...
    'q_max', NaN, ...
    'q_mean', NaN, ...
    'J_q', NaN, ...
    'J', NaN, ...
    'I_pre', NaN, ...
    'I_wall', NaN, ...
    'I_post', NaN, ...
    'I_t_cum', NaN, ...
    'Imax_pre', NaN, ...
    'q_t2_error', NaN);
end

function diagnostic = empty_diagnostic()
diagnostic = struct('eta_frac', {}, 'eta_percent', {}, 'eta', {}, ...
    'c0', {}, 'code', {}, 'message', {});
end

function diagnostics = add_diagnostic(diagnostics, row, code, message)
item.eta_frac = row.eta_frac;
item.eta_percent = row.eta_percent;
item.eta = row.eta;
item.c0 = row.c0;
item.code = string(code);
item.message = string(message);
diagnostics = [diagnostics; item]; %#ok<AGROW>
end
