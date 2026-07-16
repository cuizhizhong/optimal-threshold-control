clear; clc; close all;

%% 1. Model parameters
% 情景二：全程固定 q(t)=q0，只在控制阶段调节接触率 c(t)。
% 变量 S, I, S_q, I_q 均为有量纲人数，因此所有感染项都除以总人数 N。

gamma = 0.1;          % 康复率
delta = 0.1;          % 隔离感染者 I_q 的转出率
R0    = 3.5;          % 常规防控下的再生数：R0 = beta*c0*(1-q0)/gamma
c0    = 10;           % 常规接触率
q0    = 0.05;         % 全程固定的常规隔离率
N     = 763;          % 总人数
beta  = R0 * gamma / (c0 * (1 - q0));
eta   = 0.05 * N;     % 医疗容量阈值

S0  = 0.99 * N;       % 初始易感人数
I0  = 0.001 * N;      % 初始社区感染人数
Sq0 = 0;              % 初始隔离易感人数
Iq0 = 0;              % 初始隔离感染人数

% 常规阶段与解除控制后的有效系数。
H = beta + q0 * (1 - beta);
beta1_0 = c0 * H / N;
beta2_0 = beta * c0 * (1 - q0) / N;
a = beta2_0 / beta1_0;
rho1 = gamma / beta1_0;
Scrit = gamma / beta2_0;   % S_c = gamma*N/[beta*c0*(1-q0)]

fprintf('================ Parameter information ================\n');
fprintf('N       = %.6f\n', N);
fprintf('gamma   = %.6f\n', gamma);
fprintf('delta   = %.6f\n', delta);
fprintf('R0      = %.6f\n', R0);
fprintf('c0      = %.6f\n', c0);
fprintf('q0      = %.6f\n', q0);
fprintf('beta    = %.6f\n', beta);
fprintf('eta     = %.6f\n', eta);
fprintf('S0      = %.6f\n', S0);
fprintf('I0      = %.6f\n', I0);
fprintf('Scrit   = %.6f\n\n', Scrit);

%% 2. Theoretical step 1: compute S*
% 控制启动前与情景一相同，先用常规防控轨道 I=I(S) 求首次触碰 eta 的点 S*。
I_of_S_pre = @(S) I0 - a .* (S - S0) + rho1 .* log(S ./ S0);

if I0 > eta
    error('Initial condition already exceeds eta: I0 > eta.');
end
if Scrit >= S0
    error('No rising phase under fixed q0: Scrit >= S0.');
end

Imax_background = I_of_S_pre(Scrit);
if Imax_background <= eta
    error(['Under fixed q0 and c0, the trajectory never reaches eta. ', ...
           'Imax = %.10f <= eta = %.10f.'], Imax_background, eta);
end

K = a * S0 + I0 - eta;
z = -(S0 / Scrit) * exp(-K / rho1);
S_star = -Scrit * double(lambertw(-1, z));

if ~isreal(S_star) || S_star > S0 || S_star < Scrit
    error('S_star calculation failed: expected Scrit <= S_star <= S0.');
end

fprintf('Theoretical switching point S* = %.10f\n', S_star);

%% 3. Theoretical step 2: compute t1 and t2
% t1 是常规防控阶段从 S0 下降到 S* 的时间。
integrand_t1 = @(S) 1 ./ (beta1_0 .* S .* I_of_S_pre(S));
t1 = integral(integrand_t1, S_star, S0, 'ArrayValued', true);

fprintf('Theoretical contact-control start time t1 = %.10f days\n', t1);

% 控制期内 I(t)=eta，且 c_c(S)=gamma*N/[beta(1-q0)S]。
% 代入 S 方程得到 S'=-Kc。
Kc = gamma * eta * H / (beta * (1 - q0));

if S_star <= Scrit
    error('t2 calculation failed: S_star must be larger than Scrit.');
end

t2 = t1 + (S_star - Scrit) / Kc;

if ~isreal(t2) || t2 <= t1
    error('t2 calculation failed: no real value satisfying t2 > t1.');
end

fprintf('Kc = %.10f\n', Kc);
fprintf('Theoretical contact-control end time t2 = %.10f days\n', t2);
fprintf('Control duration Delta t = %.10f days\n\n', t2 - t1);

%% 4. Open-loop control c_c(t), fixed q(t), and controlled-phase S(t)
S_analytic = @(t) S_star - Kc .* (t - t1);
c_raw = @(t) gamma * N ./ (beta .* (1 - q0) .* max(S_analytic(t), eps));

c_opt_time = @(t) (t < t1) .* c0 + ...
                  (t >= t1 & t <= t2) .* c_raw(t) + ...
                  (t > t2) .* c0;

q_fixed_time = @(t) q0 + 0 .* t;

c_t1 = gamma * N / (beta * (1 - q0) * S_star);
c_t2_minus = gamma * N / (beta * (1 - q0) * Scrit);

fprintf('c_c(t1)  = %.10f\n', c_t1);
fprintf('c_c(t2-) = %.10f\n', c_t2_minus);
fprintf('c0       = %.10f\n\n', c0);

%% 5. Numerical simulation: controlled system and fixed-q0 baseline
% 状态顺序为 Y=[S; I; S_q; I_q]。
ode_system_regular = @(t, Y) [
    -c0 * H * Y(1) * Y(2) / N;
     beta * c0 * (1 - q0) * Y(1) * Y(2) / N - gamma * Y(2);
     (1 - beta) * c0 * q0 * Y(1) * Y(2) / N;
     beta * c0 * q0 * Y(1) * Y(2) / N - delta * Y(4)
];

ode_system_control = @(t, Y) [
    -c_opt_time(t) * H * Y(1) * Y(2) / N;
     beta * c_opt_time(t) * (1 - q0) * Y(1) * Y(2) / N - gamma * Y(2);
     (1 - beta) * c_opt_time(t) * q0 * Y(1) * Y(2) / N;
     beta * c_opt_time(t) * q0 * Y(1) * Y(2) / N - delta * Y(4)
];

% Baseline for Scenario 2: q(t)=q0 and c(t)=c0 for all t.
ode_system_base = @(t, Y) [
    -c0 * H * Y(1) * Y(2) / N;
     beta * c0 * (1 - q0) * Y(1) * Y(2) / N - gamma * Y(2)
];

t_end = t2 + 50;
Y_init_ctrl = [S0; I0; Sq0; Iq0];
Y_init_base = [S0; I0];
options = odeset('RelTol', 1e-8, 'AbsTol', 1e-10);

% 分三段积分，避免 ode45 跨过 t1 和 t2 两个控制切换点。
[t_pre, Y_pre] = ode45(ode_system_regular, [0, t1], Y_init_ctrl, options);
[t_mid, Y_mid] = ode45(ode_system_control, [t1, t2], Y_pre(end, :).', options);
[t_post, Y_post] = ode45(ode_system_regular, [t2, t_end], Y_mid(end, :).', options);

t_sim = [t_pre; t_mid(2:end); t_post(2:end)];
Y_out = [Y_pre; Y_mid(2:end, :); Y_post(2:end, :)];
S_sim  = Y_out(:, 1);
I_sim  = Y_out(:, 2);
Sq_sim = Y_out(:, 3);
Iq_sim = Y_out(:, 4);
c_sim  = c_opt_time(t_sim);
q_sim  = q_fixed_time(t_sim);

[t_sim_base, Y_out_base] = ode45(ode_system_base, [0, t_end], Y_init_base, options);
S_sim_base = Y_out_base(:, 1);
I_sim_base = Y_out_base(:, 2);

%% 6. Numerical checks
[max_I_ctrl, idx_ctrl_peak] = max(I_sim);
t_peak_ctrl = t_sim(idx_ctrl_peak);

[max_I_base, idx_base_peak] = max(I_sim_base);
t_peak_base = t_sim_base(idx_base_peak);

[~, idx_t1] = min(abs(t_sim - t1));
[~, idx_t2] = min(abs(t_sim - t2));
idx_control = (t_sim >= t1) & (t_sim <= t2);

S_num_t1 = S_sim(idx_t1);
I_num_t1 = I_sim(idx_t1);

S_num_t2 = S_sim(idx_t2);
I_num_t2 = I_sim(idx_t2);
c_num_t2 = c_sim(idx_t2);
q_num_t2 = q_sim(idx_t2);

fprintf('================ Numerical verification ================\n');
fprintf('Controlled max I(t) = %.10f, at t = %.10f days\n', max_I_ctrl, t_peak_ctrl);
fprintf('|max I - eta|      = %.10e\n\n', abs(max_I_ctrl - eta));
fprintf('Max |I(t)-eta| on [t1,t2] = %.10e\n\n', ...
        max(abs(I_sim(idx_control) - eta)));

fprintf('Fixed-q0 baseline max I(t) = %.10f, at t = %.10f days\n\n', ...
        max_I_base, t_peak_base);

fprintf('Near t1: S(t1)=%.10f, I(t1)=%.10f\n', S_num_t1, I_num_t1);
fprintf('Theory:  S*=%.10f, eta=%.10f\n', S_star, eta);
fprintf('Errors: |S(t1)-S*|=%.10e, |I(t1)-eta|=%.10e\n\n', ...
        abs(S_num_t1 - S_star), abs(I_num_t1 - eta));

fprintf('Near t2: S(t2)=%.10f, I(t2)=%.10f, c(t2)=%.10f, q(t2)=%.10f\n', ...
        S_num_t2, I_num_t2, c_num_t2, q_num_t2);
fprintf('Theory:  Scrit=%.10f, c0=%.10f, q0=%.10f\n', Scrit, c0, q0);
fprintf('Errors: |S(t2)-Scrit|=%.10e, |c(t2)-c0|=%.10e\n', ...
        abs(S_num_t2 - Scrit), abs(c_num_t2 - c0));
fprintf('========================================================\n');

%% 7. Six-panel plotting
set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');

figure('Position', [80, 60, 1300, 950], 'Color', 'w');

% Panel 1: I(t)
subplot(3,2,1); hold on; grid off; box on;

plot(t_sim_base, I_sim_base, 'k-.', 'LineWidth', 2, ...
    'DisplayName', '$I_{\mathrm{base}}$');
plot(t_sim, I_sim, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$I$');
yline(eta, 'r--', 'LineWidth', 2, ...
    'DisplayName', '$\eta$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, 0.35 * eta, '$t_1$', 'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.35 * eta, '$t_2$', 'FontSize', 11, 'Interpreter', 'latex');

ylabel('$I(t)$', 'FontSize', 13);
title('$I$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, max([max(I_sim_base), max(I_sim), eta]) * 1.15]);
set(gca, 'FontSize', 11);

% Panel 2: S_q(t)
subplot(3,2,2); hold on; grid off; box on;

plot(t_sim, Sq_sim, 'Color', [0.00 0.55 0.08], 'LineWidth', 3, ...
    'DisplayName', '$S_q$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, max(Sq_sim) * 0.12 + eps, '$t_1$', ...
    'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, max(Sq_sim) * 0.12 + eps, '$t_2$', ...
    'FontSize', 11, 'Interpreter', 'latex');

ylabel('$S_q(t)$', 'FontSize', 13);
title('$S_q$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, max(Sq_sim) * 1.20 + 1e-4]);
set(gca, 'FontSize', 11);

% Panel 3: S(t)
subplot(3,2,3); hold on; grid off; box on;

plot(t_sim_base, S_sim_base, 'k-.', 'LineWidth', 2, ...
    'DisplayName', '$S_{\mathrm{base}}$');
plot(t_sim, S_sim, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$S$');
yline(Scrit, 'r--', 'LineWidth', 2, ...
    'DisplayName', '$S_{\mathrm{c}}$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

plot(t_sim(idx_t1), S_sim(idx_t1), 'ko', 'MarkerFaceColor', 'k', ...
    'DisplayName', '$t_1$');
plot(t_sim(idx_t2), S_sim(idx_t2), 'ks', 'MarkerFaceColor', 'k', ...
    'DisplayName', '$t_2$');

text(t1 + 0.8, 0.06 * N, '$t_1$', 'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.06 * N, '$t_2$', 'FontSize', 11, 'Interpreter', 'latex');

ylabel('$S(t)$', 'FontSize', 13);
title('$S$', 'FontSize', 14);
legend('Location', 'best', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, N * 1.05]);
set(gca, 'FontSize', 11);

% Panel 4: I_q(t)
subplot(3,2,4); hold on; grid off; box on;

plot(t_sim, Iq_sim, 'Color', [0.43 0.00 0.62], 'LineWidth', 3, ...
    'DisplayName', '$I_q$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, max(Iq_sim) * 0.12 + eps, '$t_1$', ...
    'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, max(Iq_sim) * 0.12 + eps, '$t_2$', ...
    'FontSize', 11, 'Interpreter', 'latex');

ylabel('$I_q(t)$', 'FontSize', 13);
title('$I_q$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, max(Iq_sim) * 1.20 + 1e-4]);
set(gca, 'FontSize', 11);

% Panel 5: c(t)
subplot(3,2,5); hold on; grid off; box on;

plot(t_sim, c_sim, 'm-', 'LineWidth', 3, ...
    'DisplayName', '$c(t)$');
yline(c0, 'k--', 'LineWidth', 1.5, ...
    'DisplayName', '$c_0$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, 0.04 * c0, '$t_1$', 'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.04 * c0, '$t_2$', 'FontSize', 11, 'Interpreter', 'latex');

xlabel('$t$', 'FontSize', 13);
ylabel('$c(t)$', 'FontSize', 13);
title('$c(t)$', 'FontSize', 14);
legend('Location', 'southeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, c0 * 1.15]);
set(gca, 'FontSize', 11);

% Panel 6: q(t)
subplot(3,2,6); hold on; grid off; box on;

plot(t_sim, q_sim, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$q(t)=q_0$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, 0.08 * max(q0, 1e-3), '$t_1$', ...
    'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.08 * max(q0, 1e-3), '$t_2$', ...
    'FontSize', 11, 'Interpreter', 'latex');

xlabel('$t$', 'FontSize', 13);
ylabel('$q(t)$', 'FontSize', 13);
title('$q(t)$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, max(q0 * 1.8, 0.1)]);
set(gca, 'FontSize', 11);

script_dir = fileparts(mfilename('fullpath'));
if isempty(script_dir)
    script_dir = pwd;
end
project_dir = fileparts(script_dir);
figure_dir = fullfile(project_dir, 'figures');
if ~exist(figure_dir, 'dir')
    mkdir(figure_dir);
end
figure_path = fullfile(figure_dir, 'scenario2_c_control_fixed_q0.pdf');

exportgraphics(gcf, figure_path, ...
    'Resolution', 600, 'BackgroundColor', 'white');

fprintf('Scenario 2 six-panel PDF exported successfully: %s\n', figure_path);
