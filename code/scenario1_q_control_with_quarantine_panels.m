clear; clc; close all;

%% 1. Parameters
% 本脚本对应情景一：固定接触率 c(t)=c0，只在控制阶段提高隔离率 q(t)。
% 变量 S, I, S_q, I_q 都采用有量纲人数形式，因此感染项中需要除以总人数 N。

gamma = 0.3504;       % 康复率
c0    = 10;           % 固定接触率
q0    = 0.01526;      % 常规隔离率，即控制前后的基础隔离水平
N     = 763;          % 总人数
beta  = 0.155;        % 感染概率参数
R0    = beta * c0 * (1 - q0) / gamma;  % 常规控制下的再生数
eta   = 0.05 * N;     % ICU 阈值或医疗容量阈值

delta = gamma;        % 隔离感染者 I_q 的转出率

S0  = 762;            % 初始易感人数
I0  = 1;              % 初始社区感染人数
Sq0 = 0;              % 初始隔离易感人数
Iq0 = 0;              % 初始隔离感染人数

% 常规阶段的两个有效传播系数。
% beta1_0 控制 S 的下降速度，beta2_0 控制 I 的增长项。
H = beta + q0 * (1 - beta);
beta1_0 = c0 * H / N;
beta2_0 = beta * c0 * (1 - q0) / N;
a = beta2_0 / beta1_0;
rho1 = gamma / beta1_0;
Scrit = gamma / beta2_0;   % 控制结束点 S_c，此时常规控制下有效增长率为 0

fprintf('================ Parameters ================\n');
fprintf('N       = %.6f\n', N);
fprintf('gamma   = %.6f\n', gamma);
fprintf('delta   = %.6f\n', delta);
fprintf('R0      = %.6f\n', R0);
fprintf('c0      = %.6f\n', c0);
fprintf('q0      = %.6f\n', q0);
fprintf('beta    = %.6f\n', beta);
fprintf('beta*c0 = %.6f\n', beta * c0);
fprintf('eta     = %.6f\n', eta);
fprintf('S0      = %.6f\n', S0);
fprintf('I0      = %.6f\n', I0);
fprintf('Scrit   = %.6f\n\n', Scrit);

%% 2. Compute S*
% 常规阶段存在首次积分 I=I(S)。S_star 是 I(t) 首次达到 eta 时的易感人数。
I_of_S = @(S) I0 - a .* (S - S0) + rho1 .* log(S ./ S0);
Imax_background = I_of_S(Scrit);

if I0 > eta
    error('Initial condition already exceeds eta: I0 > eta.');
end

if Imax_background <= eta
    error('No crossing: background peak %.10f does not exceed eta %.10f.', ...
        Imax_background, eta);
end

% 用 Lambert W 的 -1 分支求较大的根 S_star，使控制从上升阶段开始。
K = a * S0 + I0 - eta;
z  = -(S0 / Scrit) * exp(-K / rho1);
S_star = -Scrit * lambertw(-1, z);

if ~isreal(S_star) || S_star > S0 || S_star < Scrit
    error('S_star calculation failed: expected Scrit <= S_star <= S0.');
end

fprintf('S* = %.10f\n', S_star);

%% 3. Compute t1 and t2
% t1 是常规阶段从 S0 下降到 S_star 的时间。
integrand_t1 = @(S) 1 ./ (beta1_0 .* S .* I_of_S(S));
t1 = integral(integrand_t1, S_star, S0, 'ArrayValued', true);

fprintf('t1 = %.10f days\n', t1);

% 控制阶段 I(t)=eta，由 S(t) 的解析解计算解除控制时间 t2。
S_bar = gamma * N * (1 - beta) / (beta * c0);

term_num = S_star - S_bar;
term_den = Scrit - S_bar;

if term_num <= 0 || term_den <= 0
    error('t2 calculation failed: nonpositive logarithm argument.');
end

t2 = t1 + (N / (c0 * eta)) * log(term_num / term_den);

if ~isreal(t2) || t2 <= t1
    error('t2 calculation failed: expected t2 > t1.');
end

fprintf('t2 = %.10f days\n\n', t2);

%% 4. Open-loop q*(t), S(t), and c(t)
% 控制阶段的解析轨道。这里不是用数值解中的 S(t) 反馈，而是用理论轨道给出开环控制。
S_analytic = @(t) (S_star - S_bar) .* exp(-c0 * eta .* (t - t1) ./ N) + S_bar;

% This is the explicit time-domain open-loop control derived in the text.
% It is algebraically identical to 1 - gamma*N/(beta*c0*S_analytic(t)),
% but does not use the simulated state S(t) as feedback inside the ODE.
q_control_time = @(t) 1 - 1 ./ ( ...
    (q0 / (1 - q0) + beta) .* exp(c0 * eta .* (t2 - t) ./ N) ...
    + 1 - beta);

% 检查时间形式 q_c(t) 与状态形式 q_c(S(t)) 是否一致。
q_from_analytic_S = @(t) 1 - gamma * N ./ ((beta * c0) .* S_analytic(t));
q_check_t = linspace(t1, t2, 200);
q_formula_error = max(abs(q_control_time(q_check_t) - q_from_analytic_S(q_check_t)));
if q_formula_error > 1e-10
    error('Time-domain q_c(t) is inconsistent with q_c(S(t)).');
end

q_check = q_control_time(q_check_t);
if min(q_check) < q0 - 1e-10 || max(q_check) > 1 + 1e-10
    error('Required q_c(t) is outside the feasible interval [q0, 1].');
end

% 分段隔离率：控制前后为 q0，控制期为理论推导得到的 q_c(t)。
q_opt_time = @(t) (t < t1) .* q0 + ...
                  (t >= t1 & t <= t2) .* q_control_time(t) + ...
                  (t > t2) .* q0;

c_time = @(t) c0 + 0 .* t;  % 情景一始终固定接触率

%% 5. Numerical simulation
% Controlled system state: Y = [S; I; S_q; I_q].
% 前两维是主系统，后两维用于记录进入隔离通道的人数。
ode_system_regular = @(t, Y) [
    -c0 * (beta + (1 - beta) * q0) * Y(1) * Y(2) / N;
     beta * c0 * (1 - q0) * Y(1) * Y(2) / N - gamma * Y(2);
     (1 - beta) * c0 * q0 * Y(1) * Y(2) / N;
     beta * c0 * q0 * Y(1) * Y(2) / N - delta * Y(4)
];

ode_system_control = @(t, Y) [
    -c0 * (beta + (1 - beta) * q_control_time(t)) * Y(1) * Y(2) / N;
     beta * c0 * (1 - q_control_time(t)) * Y(1) * Y(2) / N - gamma * Y(2);
     (1 - beta) * c0 * q_control_time(t) * Y(1) * Y(2) / N;
     beta * c0 * q_control_time(t) * Y(1) * Y(2) / N - delta * Y(4)
];

% Background baseline: q(t) = q0, c(t) = c0.
% baseline 用于展示没有增强隔离控制时的疫情走势。
ode_system_base = @(t, Y) [
    -c0 * (beta + (1 - beta) * q0) * Y(1) * Y(2) / N;
     beta * c0 * (1 - q0) * Y(1) * Y(2) / N - gamma * Y(2)
];

t_end = t2 + 50;
t_span = [0, t_end];
Y_init_opt = [S0; I0; Sq0; Iq0];
Y_init_base = [S0; I0];
options = odeset('RelTol', 1e-8, 'AbsTol', 1e-10);

% 分三段积分，避免 ode45 的步长跨过 t1 和 t2 两个控制切换点。
[t_pre, Y_pre] = ode45(ode_system_regular, [0, t1], Y_init_opt, options);
[t_mid, Y_mid] = ode45(ode_system_control, [t1, t2], Y_pre(end, :).', options);
[t_post, Y_post] = ode45(ode_system_regular, [t2, t_end], Y_mid(end, :).', options);

t_sim = [t_pre; t_mid(2:end); t_post(2:end)];
Y_out = [Y_pre; Y_mid(2:end, :); Y_post(2:end, :)];
S_sim  = Y_out(:, 1);
I_sim  = Y_out(:, 2);
Sq_sim = Y_out(:, 3);
Iq_sim = Y_out(:, 4);
q_sim  = q_opt_time(t_sim);
c_sim  = c_time(t_sim);

[t_sim_base, Y_out_base] = ode45(ode_system_base, t_span, Y_init_base, options);
S_sim_base = Y_out_base(:, 1);
I_sim_base = Y_out_base(:, 2);

%% 6. Numerical checks
[max_I_opt, idx_opt_peak] = max(I_sim);
t_peak_opt = t_sim(idx_opt_peak);

[max_I_base, idx_base_peak] = max(I_sim_base);
t_peak_base = t_sim_base(idx_base_peak);

[~, idx_t1] = min(abs(t_sim - t1));
[~, idx_t2] = min(abs(t_sim - t2));

S_num_t1 = S_sim(idx_t1);
I_num_t1 = I_sim(idx_t1);

S_num_t2 = S_sim(idx_t2);
I_num_t2 = I_sim(idx_t2);
q_num_t2 = q_sim(idx_t2);

fprintf('================ Numerical verification ================\n');
fprintf('Controlled max I(t) = %.10f, at t = %.10f days\n', max_I_opt, t_peak_opt);
fprintf('|max I - eta|      = %.10e\n\n', abs(max_I_opt - eta));
idx_control = (t_sim >= t1) & (t_sim <= t2);
fprintf('Max |I(t)-eta| on [t1,t2] = %.10e\n\n', ...
        max(abs(I_sim(idx_control) - eta)));

fprintf('Background max I(t) = %.10f, at t = %.10f days\n\n', max_I_base, t_peak_base);

fprintf('Near t1: S(t1)=%.10f, I(t1)=%.10f\n', S_num_t1, I_num_t1);
fprintf('Theory:  S*=%.10f, eta=%.10f\n', S_star, eta);
fprintf('Errors: |S(t1)-S*|=%.10e, |I(t1)-eta|=%.10e\n\n', ...
        abs(S_num_t1 - S_star), abs(I_num_t1 - eta));

fprintf('Near t2: S(t2)=%.10f, I(t2)=%.10f, q(t2)=%.10f\n', ...
        S_num_t2, I_num_t2, q_num_t2);
fprintf('Theory:  Scrit=%.10f\n', Scrit);
fprintf('Error:   |S(t2)-Scrit|=%.10e\n', abs(S_num_t2 - Scrit));
fprintf('========================================================\n');

%% 7. Six-panel plotting version
% 六宫格依次展示 I, S_q, S, I_q, q(t), c(t)。
set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');

figure('Position', [80, 60, 1300, 950], 'Color', 'w');

% Panel 1: I，社区感染人数
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

% Panel 2: S_q，隔离易感人数
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

% Panel 3: S，易感人数
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

% Panel 4: I_q，隔离感染人数
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

% Panel 5: q(t)，隔离率
subplot(3,2,5); hold on; grid off; box on;

plot(t_sim, q_sim, 'm-', 'LineWidth', 3, ...
    'DisplayName', '$q(t)$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, 0.04, '$t_1$', 'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.04, '$t_2$', 'FontSize', 11, 'Interpreter', 'latex');

xlabel('$t$', 'FontSize', 13);
ylabel('$q(t)$', 'FontSize', 13);
title('$q(t)$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([-0.05, max(q_sim) * 1.15 + 0.02]);
set(gca, 'FontSize', 11);

% Panel 6: c(t)，接触率
subplot(3,2,6); hold on; grid off; box on;

plot(t_sim, c_sim, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$c(t)=c_0$');

xline(t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');

text(t1 + 0.8, 0.04 * c0, '$t_1$', 'FontSize', 11, 'Interpreter', 'latex');
text(t2 + 0.8, 0.04 * c0, '$t_2$', 'FontSize', 11, 'Interpreter', 'latex');

xlabel('$t$', 'FontSize', 13);
ylabel('$c(t)$', 'FontSize', 13);
title('$c(t)$', 'FontSize', 14);
legend('Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim([0, c0 * 1.2]);
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
figure_path = fullfile(figure_dir, 'optimal_control_with_quarantine_panels.pdf');

exportgraphics(gcf, figure_path, ...
    'Resolution', 600, 'BackgroundColor', 'white');

fprintf('Six-panel PDF exported successfully: %s\n', figure_path);
