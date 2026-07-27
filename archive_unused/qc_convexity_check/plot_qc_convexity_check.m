clear; clc; close all;

% 只比较两组参数下同一个开环隔离率 q_c(t) 的曲率形状。
% 不运行完整 SIQR 数值模拟，也不叠加 TDINN 或常规控制轨迹。

out_dir = fileparts(mfilename('fullpath'));
% 在 MATLAB 桌面中运行时保留图窗，方便手动放大；
% 使用 matlab -batch 验证时自动关闭图窗，避免进程等待。
keep_figures_open = usejava('desktop');

text_case.name = 'Text example';
text_case.file_tag = 'text_case';
text_case.N = 763;
text_case.gamma = 0.1;
text_case.R0 = 3.5;
text_case.c0 = 10;
text_case.q0 = 0.05;
text_case.beta = text_case.R0 * text_case.gamma / (text_case.c0 * (1 - text_case.q0));
text_case.eta = 0.05 * text_case.N;
text_case.S0 = 0.99 * text_case.N;
text_case.I0 = 0.001 * text_case.N;

xian_case.name = "Xi'an baseline";
xian_case.file_tag = 'xian_case';
xian_case.N = 13163000;
xian_case.beta = 0.1498;
xian_case.gamma = 0.2953;
xian_case.c0 = 12.8872;
xian_case.q0 = 0.3230;
xian_case.eta = 26326;
xian_case.S0 = 13162999.998993373;
xian_case.I0 = 0.0010066282337901089;

plot_case_qc(text_case, out_dir, keep_figures_open);
plot_case_qc(xian_case, out_dir, keep_figures_open);

function result = compute_case_qc(p)
    H = p.beta + p.q0 * (1 - p.beta);
    beta1 = p.c0 * H / p.N;
    beta2 = p.beta * p.c0 * (1 - p.q0) / p.N;
    a = beta2 / beta1;
    rho1 = p.gamma / beta1;

    Sc = p.gamma / beta2;
    Sbar = p.gamma * p.N * (1 - p.beta) / (p.beta * p.c0);
    I_of_S = @(S) p.I0 - a .* (S - p.S0) + rho1 .* log(S ./ p.S0);

    Imax_background = I_of_S(Sc);
    if p.I0 > p.eta
        error('%s: I0 already exceeds eta.', p.name);
    end
    if Imax_background <= p.eta
        error('%s: background trajectory never reaches eta.', p.name);
    end

    Sstar = fzero(@(S) I_of_S(S) - p.eta, [Sc, p.S0]);
    % S* 来自首次积分曲线；t1 用常规阶段 ODE 事件定位，避免西安 I0 极小时
    % 对 S 积分带来的数值警告。这一步只用于定位时间，不模拟控制阶段。
    ode_regular = @(~, Y) [
        -p.c0 * H * Y(1) * Y(2) / p.N;
         p.beta * p.c0 * (1 - p.q0) * Y(1) * Y(2) / p.N - p.gamma * Y(2)
    ];
    event_eta = @(t, Y) reach_eta_event(t, Y, p.eta);
    ode_options = odeset('RelTol', 1e-10, 'AbsTol', 1e-10, 'Events', event_eta);
    [~, ~, te] = ode45(ode_regular, [0, 5000], [p.S0; p.I0], ode_options);
    if isempty(te)
        error('%s: ODE event did not reach eta.', p.name);
    end
    t1 = te(1);

    control_duration = (p.N / (p.c0 * p.eta)) * log((Sstar - Sbar) / (Sc - Sbar));
    t2 = t1 + control_duration;

    k = p.c0 * p.eta / p.N;
    Sth = @(t) Sbar + (Sstar - Sbar) .* exp(-k .* (t - t1));
    qc = @(t) 1 - p.gamma * p.N ./ (p.beta * p.c0 .* Sth(t));

    t_inf = NaN;
    tau_inf = NaN;
    inflection_in_window = false;
    if Sc < 2 * Sbar && 2 * Sbar < Sstar
        tau_inf = (1 / k) * log((Sstar - Sbar) / Sbar);
        t_inf = t1 + tau_inf;
        inflection_in_window = (t_inf >= t1 && t_inf <= t2);
    end

    result = struct();
    result.Sstar = Sstar;
    result.Sc = Sc;
    result.Sbar = Sbar;
    result.t1 = t1;
    result.t2 = t2;
    result.control_duration = control_duration;
    result.t_inf = t_inf;
    result.tau_inf = tau_inf;
    result.inflection_in_window = inflection_in_window;
    result.qc = qc;
    result.q_start = qc(t1);
    result.q_end = qc(t2);
end

function [value, isterminal, direction] = reach_eta_event(~, Y, eta)
    value = Y(2) - eta;
    isterminal = 1;
    direction = 1;
end

function plot_case_qc(p, out_dir, keep_figures_open)
    r = compute_case_qc(p);

    fprintf('\n==== %s ====\n', p.name);
    fprintf('S*       = %.12g\n', r.Sstar);
    fprintf('Sc       = %.12g\n', r.Sc);
    fprintf('Sbar     = %.12g\n', r.Sbar);
    fprintf('2*Sbar   = %.12g\n', 2 * r.Sbar);
    fprintf('t1       = %.12g\n', r.t1);
    fprintf('t2       = %.12g\n', r.t2);
    fprintf('Delta t  = %.12g\n', r.control_duration);
    fprintf('q_c(t1)  = %.12g\n', r.q_start);
    fprintf('q_c(t2)  = %.12g\n', r.q_end);
    if r.inflection_in_window
        fprintf('t_inf    = %.12g\n', r.t_inf);
        fprintf('(t_inf-t1)/(t2-t1) = %.12g\n', r.tau_inf / r.control_duration);
    else
        fprintf('t_inf    = outside [t1,t2]\n');
    end

    pad = 0.05 * r.control_duration;
    t_min = r.t1 - pad;
    t_max = r.t2 + pad;
    t = linspace(t_min, t_max, 1200);
    q = p.q0 + zeros(size(t));
    mask = (t >= r.t1) & (t <= r.t2);
    q(mask) = r.qc(t(mask));

    fig = figure('Color', 'w', 'Position', [100, 100, 900, 560]);
    plot(t, q, 'LineWidth', 3.0, 'Color', [0.78, 0.10, 0.16], ...
        'DisplayName', '$q_c(t)$');
    hold on;
    yline(p.q0, ':', 'LineWidth', 1.4, 'Color', [0.25, 0.25, 0.25], ...
        'DisplayName', '$q_0$');
    xline(r.t1, '--', 'LineWidth', 1.4, 'Color', [0.15, 0.15, 0.15], ...
        'HandleVisibility', 'off');
    xline(r.t2, '--', 'LineWidth', 1.4, 'Color', [0.45, 0.45, 0.45], ...
        'HandleVisibility', 'off');
    if r.inflection_in_window
        xline(r.t_inf, '-.', 'LineWidth', 1.8, 'Color', [0.00, 0.35, 0.75], ...
            'HandleVisibility', 'off');
    end

    xlabel('$t$', 'Interpreter', 'latex', 'FontSize', 14);
    ylabel('$q(t)$', 'Interpreter', 'latex', 'FontSize', 14);
    legend('Interpreter', 'latex', 'Location', 'best', 'FontSize', 11);
    grid off;
    box on;
    set(gca, 'FontSize', 12, 'LineWidth', 1.0);

    pdf_path = fullfile(out_dir, sprintf('qc_%s_qt.pdf', p.file_tag));
    png_path = fullfile(out_dir, sprintf('qc_%s_qt.png', p.file_tag));
    exportgraphics(fig, pdf_path, 'ContentType', 'vector');
    exportgraphics(fig, png_path, 'Resolution', 300);

    if ~keep_figures_open
        close(fig);
    end
end
