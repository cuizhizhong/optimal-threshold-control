clear; clc; close all;

%% Scenario 2 parameter analysis
% 情景二：全程固定 q(t)=q0，只在控制阶段降低接触率 c(t)。
% 本脚本采用有量纲人数模型，并只分析两个参数 c0 和 eta。

%% 1. Baseline parameters
gamma_base = 0.1;
c0_base    = 10;
q0_base    = 0.05;
N_base     = 763;
R0_base    = 3.5;
beta_base  = R0_base * gamma_base / (c0_base * (1 - q0_base));
eta_base   = 0.05 * N_base;

S0 = 0.99 * N_base;
I0 = 0.001 * N_base;

c0_values = 6:13;
eta_values = N_base .* [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05];

c0_grid  = linspace(6, 13, 260);
eta_grid = linspace(0.02 * N_base, 0.05 * N_base, 220);
c0_feas_grid = linspace(6, 13, 520);
eta_feas_grid = linspace(0.02 * N_base, 0.05 * N_base, 420);

script_dir = fileparts(mfilename('fullpath'));
if isempty(script_dir)
    script_dir = pwd;
end
project_dir = fileparts(script_dir);
table_dir = fullfile(project_dir, 'table');
figure_dir = fullfile(project_dir, 'figures');
if ~exist(table_dir, 'dir')
    mkdir(table_dir);
end
if ~exist(figure_dir, 'dir')
    mkdir(figure_dir);
end

set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');

%% 2. One-dimensional c0 sweep
% 固定 beta,gamma,q0,N,S0,I0,eta，仅改变常规接触水平 c0。
rows_c0 = repmat(empty_metrics(), numel(c0_values), 1);

for k = 1:numel(c0_values)
    c0 = c0_values(k);
    rows_c0(k) = compute_metrics(beta_base, gamma_base, c0, q0_base, ...
        N_base, eta_base, S0, I0);
end

T_c0 = metrics_to_table(rows_c0);
writetable(T_c0, fullfile(table_dir, 'scenario2_c0_summary.csv'));
write_latex_table(T_c0, fullfile(table_dir, 'scenario2_c0_summary_table.tex'), 'c0');

plot_control_relative(rows_c0, fullfile(figure_dir, 'scenario2_u_tau_c0.pdf'), ...
    '$c_0$', arrayfun(@(v) sprintf('%.0f', v), c0_values, 'UniformOutput', false));
plot_control_absolute(rows_c0, fullfile(figure_dir, 'scenario2_u_time_c0.pdf'), ...
    '$c_0$', arrayfun(@(v) sprintf('%.0f', v), c0_values, 'UniformOutput', false));
plot_summary_c0(T_c0, fullfile(figure_dir, 'scenario2_summary_c0.pdf'));

%% 3. One-dimensional eta sweep
% 固定 beta,gamma,c0,q0,N,S0,I0，仅改变医疗容量阈值 eta。
rows_eta = repmat(empty_metrics(), numel(eta_values), 1);

for k = 1:numel(eta_values)
    eta = eta_values(k);
    rows_eta(k) = compute_metrics(beta_base, gamma_base, c0_base, q0_base, ...
        N_base, eta, S0, I0);
end

T_eta = metrics_to_table(rows_eta);
writetable(T_eta, fullfile(table_dir, 'scenario2_eta_summary.csv'));
write_latex_table(T_eta, fullfile(table_dir, 'scenario2_eta_summary_table.tex'), 'eta');

plot_control_relative(rows_eta, fullfile(figure_dir, 'scenario2_u_tau_eta.pdf'), ...
    '$\eta$', arrayfun(@(v) sprintf('%.2fN', v / N_base), eta_values, 'UniformOutput', false));
plot_control_absolute(rows_eta, fullfile(figure_dir, 'scenario2_u_time_eta.pdf'), ...
    '$\eta$', arrayfun(@(v) sprintf('%.2fN', v / N_base), eta_values, 'UniformOutput', false));
plot_summary_eta(T_eta, fullfile(figure_dir, 'scenario2_summary_eta.pdf'), N_base);

%% 4. Two-dimensional heatmaps in (c0, eta)
t1_map = nan(numel(eta_grid), numel(c0_grid));
dt_map = nan(numel(eta_grid), numel(c0_grid));
umax_map = nan(numel(eta_grid), numel(c0_grid));
Jc_map = nan(numel(eta_grid), numel(c0_grid));
feasible_map = false(numel(eta_grid), numel(c0_grid));

for i = 1:numel(eta_grid)
    eta = eta_grid(i);
    for j = 1:numel(c0_grid)
        c0 = c0_grid(j);
        row = compute_metrics(beta_base, gamma_base, c0, q0_base, ...
            N_base, eta, S0, I0);
        feasible_map(i, j) = row.feasible;
        if row.feasible
            t1_map(i, j) = row.t1;
            dt_map(i, j) = row.Delta_t;
            umax_map(i, j) = row.u_max;
            Jc_map(i, j) = row.J_c;
        end
    end
end

plot_heatmaps(c0_grid, eta_grid, t1_map, dt_map, umax_map, Jc_map, ...
    fullfile(figure_dir, 'scenario2_heatmaps_c0_eta.pdf'), N_base);
feasible_dense_map = feasibility_grid(beta_base, gamma_base, q0_base, ...
    N_base, S0, I0, c0_feas_grid, eta_feas_grid);

plot_feasibility(c0_feas_grid, eta_feas_grid, feasible_dense_map, ...
    fullfile(figure_dir, 'scenario2_feasibility_c0_eta.pdf'), N_base);

%% 5. Console summary
disp('Scenario 2 parameter analysis completed.');
disp('Generated files:');
disp(fullfile(table_dir, 'scenario2_c0_summary.csv'));
disp(fullfile(table_dir, 'scenario2_c0_summary_table.tex'));
disp(fullfile(figure_dir, 'scenario2_u_tau_c0.pdf'));
disp(fullfile(figure_dir, 'scenario2_u_time_c0.pdf'));
disp(fullfile(figure_dir, 'scenario2_summary_c0.pdf'));
disp(fullfile(table_dir, 'scenario2_eta_summary.csv'));
disp(fullfile(table_dir, 'scenario2_eta_summary_table.tex'));
disp(fullfile(figure_dir, 'scenario2_u_tau_eta.pdf'));
disp(fullfile(figure_dir, 'scenario2_u_time_eta.pdf'));
disp(fullfile(figure_dir, 'scenario2_summary_eta.pdf'));
disp(fullfile(figure_dir, 'scenario2_heatmaps_c0_eta.pdf'));
disp(fullfile(figure_dir, 'scenario2_feasibility_c0_eta.pdf'));

%% Local functions
function row = empty_metrics()
    row = struct( ...
        'feasible', false, ...
        'R0', NaN, ...
        'beta', NaN, ...
        'gamma', NaN, ...
        'c0', NaN, ...
        'q0', NaN, ...
        'N', NaN, ...
        'eta', NaN, ...
        'eta_frac', NaN, ...
        'S0', NaN, ...
        'I0', NaN, ...
        'a', NaN, ...
        'rho1', NaN, ...
        'S_star', NaN, ...
        'S_c', NaN, ...
        'K_c', NaN, ...
        't1', NaN, ...
        't2', NaN, ...
        'Delta_t', NaN, ...
        'c_min', NaN, ...
        'c_min_ratio', NaN, ...
        'u_max', NaN, ...
        'c_avg', NaN, ...
        'J_c', NaN, ...
        'Imax_pre', NaN);
end

function row = compute_metrics(beta, gamma, c0, q0, N, eta, S0, I0)
    row = empty_metrics();
    row.R0 = beta * c0 * (1 - q0) / gamma;
    row.beta = beta;
    row.gamma = gamma;
    row.c0 = c0;
    row.q0 = q0;
    row.N = N;
    row.eta = eta;
    row.eta_frac = eta / N;
    row.S0 = S0;
    row.I0 = I0;

    if beta <= 0 || gamma <= 0 || c0 <= 0 || q0 < 0 || q0 >= 1 || ...
            N <= 0 || eta <= 0
        return;
    end

    H = beta + q0 * (1 - beta);
    beta1_0 = c0 * H / N;
    beta2_0 = beta * c0 * (1 - q0) / N;
    a = beta2_0 / beta1_0;
    rho1 = gamma / beta1_0;
    S_c = gamma / beta2_0;

    row.a = a;
    row.rho1 = rho1;
    row.S_c = S_c;

    I_of_S = @(S) I0 - a .* (S - S0) + rho1 .* log(S ./ S0);

    if I0 > eta || S_c >= S0
        return;
    end

    Imax_pre = I_of_S(S_c);
    row.Imax_pre = Imax_pre;
    if Imax_pre <= eta
        return;
    end

    K = a * S0 + I0 - eta;
    z = -(S0 / S_c) * exp(-K / rho1);
    S_star_raw = -S_c * double(lambertw(-1, z));
    if abs(imag(S_star_raw)) > 1e-8
        return;
    end
    S_star = real(S_star_raw);

    if S_star > S0 || S_star < S_c
        return;
    end

    integrand_t1 = @(S) 1 ./ (beta1_0 .* S .* I_of_S(S));
    try
        t1 = integral(integrand_t1, S_star, S0, 'ArrayValued', true, ...
            'AbsTol', 1e-11, 'RelTol', 1e-11);
    catch
        return;
    end

    K_c = gamma * eta * H / (beta * (1 - q0));
    Delta_t = (S_star - S_c) / K_c;
    t2 = t1 + Delta_t;
    c_min = gamma * N / (beta * (1 - q0) * S_star);
    c_min_ratio = c_min / c0;
    u_max = 1 - c_min_ratio;

    if Delta_t <= 0 || t2 <= t1 || c_min <= 0 || c_min > c0 * (1 + 1e-8)
        return;
    end

    % J_c = int_{t1}^{t2} (1-c_c(t)/c0) dt.
    J_c = ((S_star - S_c) - S_c * log(S_star / S_c)) / K_c;
    c_avg = c0 * (1 - J_c / Delta_t);

    row.feasible = true;
    row.S_star = S_star;
    row.K_c = K_c;
    row.t1 = t1;
    row.t2 = t2;
    row.Delta_t = Delta_t;
    row.c_min = c_min;
    row.c_min_ratio = c_min_ratio;
    row.u_max = u_max;
    row.c_avg = c_avg;
    row.J_c = J_c;
end

function T = metrics_to_table(rows)
    T = struct2table(rows);
    T = T(:, {'R0','beta','gamma','c0','q0','N','eta','eta_frac','S0','I0', ...
              'S_star','S_c','t1','t2','Delta_t','c_min','c_min_ratio', ...
              'u_max','c_avg','J_c','Imax_pre','feasible'});
end

function write_latex_table(T, filename, sweep_name)
    fid = fopen(filename, 'w');
    if fid < 0
        error('Cannot open %s for writing.', filename);
    end
    cleaner = onCleanup(@() fclose(fid)); %#ok<NASGU>

    if strcmp(sweep_name, 'c0')
        fprintf(fid, '\\begin{tabular}{ccccccc}\n');
        fprintf(fid, '\\toprule\n');
        fprintf(fid, '$c_0$ & $S^*$ & $S_c$ & $t_1$ & $\\Delta t$ & $u_{\\max}$ & $J_c$ \\\\\n');
        x = T.c0;
        fmt = '%.4g';
    else
        fprintf(fid, '\\begin{tabular}{cccccccc}\n');
        fprintf(fid, '\\toprule\n');
        fprintf(fid, '$\\eta$ & $\\eta/N$ & $S^*$ & $S_c$ & $t_1$ & $\\Delta t$ & $u_{\\max}$ & $J_c$ \\\\\n');
        x = T.eta;
        fmt = '%.4f';
    end
    fprintf(fid, '\\midrule\n');
    for k = 1:height(T)
        if T.feasible(k)
            if strcmp(sweep_name, 'c0')
                fprintf(fid, [fmt ' & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n'], ...
                    x(k), T.S_star(k), T.S_c(k), T.t1(k), T.Delta_t(k), ...
                    T.u_max(k), T.J_c(k));
            else
                fprintf(fid, [fmt ' & %.3f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n'], ...
                    x(k), T.eta_frac(k), T.S_star(k), T.S_c(k), T.t1(k), ...
                    T.Delta_t(k), T.u_max(k), T.J_c(k));
            end
        else
            if strcmp(sweep_name, 'c0')
                fprintf(fid, [fmt ' & -- & -- & -- & -- & -- & -- \\\\\n'], x(k));
            else
                fprintf(fid, [fmt ' & %.3f & -- & -- & -- & -- & -- & -- \\\\\n'], ...
                    x(k), T.eta_frac(k));
            end
        end
    end
    fprintf(fid, '\\bottomrule\n');
    fprintf(fid, '\\end{tabular}\n');
end

function plot_control_relative(rows, filename, param_label, param_values)
    fig = figure('Position', [120, 120, 760, 480], 'Color', 'w');
    ax = axes(fig); hold(ax, 'on'); box(ax, 'on'); grid(ax, 'off');

    colors = lines(numel(rows));
    has_curve = false;
    for k = 1:numel(rows)
        row = rows(k);
        if ~row.feasible
            continue;
        end
        has_curve = true;
        tau = linspace(0, row.Delta_t, 500);
        S_phase = row.S_star - row.K_c .* tau;
        u = 1 - row.S_c ./ S_phase;
        plot(ax, tau, u, 'LineWidth', 1.2, 'Color', colors(k, :), ...
            'DisplayName', sprintf('%s=%s', param_label, param_values{k}));
    end

    xlabel(ax, '$\tau=t-t_1$');
    ylabel(ax, '$u_c(\tau)=1-c_c(\tau)/c_0$');
    title(ax, 'contact reduction after control starts');
    ylim(ax, [0, 1.05]);
    style_axes(ax);
    if has_curve
        legend(ax, 'Location', 'best', 'Interpreter', 'latex', ...
            'Box', 'off', 'FontSize', 8);
    end
    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_control_absolute(rows, filename, param_label, param_values)
    fig = figure('Position', [120, 120, 760, 480], 'Color', 'w');
    ax = axes(fig); hold(ax, 'on'); box(ax, 'on'); grid(ax, 'off');

    colors = lines(numel(rows));
    has_curve = false;
    for k = 1:numel(rows)
        row = rows(k);
        if ~row.feasible
            continue;
        end
        has_curve = true;
        t = linspace(0, row.t2 + 0.25 * row.Delta_t, 700);
        u = zeros(size(t));
        mask = (t >= row.t1) & (t <= row.t2);
        S_phase = row.S_star - row.K_c .* (t(mask) - row.t1);
        u(mask) = 1 - row.S_c ./ S_phase;
        plot(ax, t, u, 'LineWidth', 1.2, 'Color', colors(k, :), ...
            'DisplayName', sprintf('%s=%s', param_label, param_values{k}));
        plot(ax, row.t1, row.u_max, 'o', 'MarkerSize', 4, ...
            'LineWidth', 1.0, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', colors(k, :), ...
            'HandleVisibility', 'off');
        plot(ax, row.t2, 0, 's', 'MarkerSize', 4, ...
            'LineWidth', 1.0, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', colors(k, :), ...
            'HandleVisibility', 'off');
    end

    xlabel(ax, '$t$');
    ylabel(ax, '$u_c(t)=1-c_c(t)/c_0$');
    title(ax, 'contact reduction in absolute time');
    ylim(ax, [0, 1.05]);
    style_axes(ax);
    if has_curve
        legend(ax, 'Location', 'best', 'Interpreter', 'latex', ...
            'Box', 'off', 'FontSize', 8);
    end
    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_summary_c0(T, filename)
    fig = figure('Position', [80, 80, 1150, 660], 'Color', 'w');
    x = T.c0;
    labels = {'$S^*$ and $S_c$', '$t_1$', '$\Delta t$', ...
              '$u_{\max}$', '$J_c$', '$\bar c/c_0$'};

    subplot(2,3,1); hold on; box on; grid off;
    plot(x, T.S_star, 'o-', 'LineWidth', 1.2, 'MarkerSize', 4, ...
        'MarkerFaceColor', 'w', 'DisplayName', '$S^*$');
    plot(x, T.S_c, 's--', 'LineWidth', 1.2, 'MarkerSize', 4, ...
        'MarkerFaceColor', 'w', 'DisplayName', '$S_c$');
    xlabel('$c_0$'); ylabel('$S$'); title(labels{1}); style_axes(gca);
    legend('Location','best', 'Box', 'off', 'FontSize', 8);

    subplot(2,3,2); plot_metric(x, T.t1, '$c_0$', '$t_1$', labels{2});
    subplot(2,3,3); plot_metric(x, T.Delta_t, '$c_0$', '$\Delta t$', labels{3});
    subplot(2,3,4); plot_metric(x, T.u_max, '$c_0$', '$u_{\max}$', labels{4});
    subplot(2,3,5); plot_metric(x, T.J_c, '$c_0$', '$J_c$', labels{5});
    subplot(2,3,6); plot_metric(x, T.c_avg ./ T.c0, '$c_0$', '$\bar c/c_0$', labels{6});

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_summary_eta(T, filename, N)
    fig = figure('Position', [80, 80, 1150, 660], 'Color', 'w');
    x = T.eta ./ N;
    labels = {'$S^*$ and $S_c$', '$t_1$', '$\Delta t$', ...
              '$u_{\max}$', '$J_c$', '$\bar c/c_0$'};

    subplot(2,3,1); hold on; box on; grid off;
    plot(x, T.S_star, 'o-', 'LineWidth', 1.2, 'MarkerSize', 4, ...
        'MarkerFaceColor', 'w', 'DisplayName', '$S^*$');
    plot(x, T.S_c, 's--', 'LineWidth', 1.2, 'MarkerSize', 4, ...
        'MarkerFaceColor', 'w', 'DisplayName', '$S_c$');
    xlabel('$\eta/N$'); ylabel('$S$'); title(labels{1}); style_axes(gca);
    legend('Location','best', 'Box', 'off', 'FontSize', 8);

    subplot(2,3,2); plot_metric(x, T.t1, '$\eta/N$', '$t_1$', labels{2});
    subplot(2,3,3); plot_metric(x, T.Delta_t, '$\eta/N$', '$\Delta t$', labels{3});
    subplot(2,3,4); plot_metric(x, T.u_max, '$\eta/N$', '$u_{\max}$', labels{4});
    subplot(2,3,5); plot_metric(x, T.J_c, '$\eta/N$', '$J_c$', labels{5});
    subplot(2,3,6); plot_metric(x, T.c_avg ./ T.c0, '$\eta/N$', '$\bar c/c_0$', labels{6});

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_metric(x, y, xlabel_text, ylabel_text, title_text)
    hold on; box on; grid off;
    plot(x, y, 'o-', 'LineWidth', 1.2, 'MarkerSize', 4, ...
        'MarkerFaceColor', 'w', 'MarkerEdgeColor', [0 0.4470 0.7410]);
    xlabel(xlabel_text);
    ylabel(ylabel_text);
    title(title_text);
    style_axes(gca);
end

function plot_heatmaps(c0_grid, eta_grid, t1_map, dt_map, umax_map, Jc_map, filename, N)
    fig = figure('Position', [80, 80, 1100, 780], 'Color', 'w');

    subplot(2,2,1);
    heatmap_panel(c0_grid, eta_grid, t1_map, '$t_1$', N);

    subplot(2,2,2);
    heatmap_panel(c0_grid, eta_grid, dt_map, '$\Delta t$', N);

    subplot(2,2,3);
    heatmap_panel(c0_grid, eta_grid, umax_map, '$u_{\max}$', N);

    subplot(2,2,4);
    heatmap_panel(c0_grid, eta_grid, Jc_map, '$J_c$', N);

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function heatmap_panel(c0_grid, eta_grid, Z, ttl, N)
    imagesc(c0_grid, eta_grid ./ N, Z);
    set(gca, 'YDir', 'normal');
    xlabel('$c_0$');
    ylabel('$\eta/N$');
    title(ttl);
    colorbar;
    box on;
    style_axes(gca);
end

function feasible_map = feasibility_grid(beta, gamma, q0, N, S0, I0, c0_grid, eta_grid)
    [C0_grid, Eta_grid] = meshgrid(c0_grid, eta_grid);
    H = beta + q0 * (1 - beta);
    beta1_0 = C0_grid .* H ./ N;
    beta2_0 = beta .* C0_grid .* (1 - q0) ./ N;
    a = beta2_0 ./ beta1_0;
    rho1 = gamma ./ beta1_0;
    S_c = gamma ./ beta2_0;

    Imax = I0 - a .* (S_c - S0) + rho1 .* log(S_c ./ S0);
    feasible_map = (I0 <= Eta_grid) & (S_c < S0) & (Imax > Eta_grid);
end

function plot_feasibility(c0_grid, eta_grid, feasible_map, filename, N)
    fig = figure('Position', [120, 120, 680, 500], 'Color', 'w');
    imagesc(c0_grid, eta_grid ./ N, double(feasible_map));
    set(gca, 'YDir', 'normal');
    colormap([0.88 0.88 0.88; 0.20 0.55 0.90]);
    colorbar('Ticks', [0, 1], 'TickLabels', {'No crossing', 'Crossing'});
    xlabel('$c_0$');
    ylabel('$\eta/N$');
    title('Feasibility of reaching $I=\eta$');
    box on;
    style_axes(gca);
    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function style_axes(ax)
    ax.LineWidth = 0.75;
    ax.FontSize = 10;
    ax.TickDir = 'in';
    ax.XMinorTick = 'off';
    ax.YMinorTick = 'off';
    ax.XGrid = 'off';
    ax.YGrid = 'off';
    ax.XMinorGrid = 'off';
    ax.YMinorGrid = 'off';
    ax.Layer = 'top';
end
