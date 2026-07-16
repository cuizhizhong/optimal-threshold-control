clear; clc; close all;

%% Scenario 1 parameter analysis
% Fixed c(t)=c0 for all stages, isolation control q_c(t) only during
% [t1,t2]. The two policy parameters analyzed here are c0 and eta.

%% 1. Baseline parameters
gamma_base = 0.3504;
beta_base  = 0.155;
c0_base    = 10;
q0_base    = 0.01526;
N_base     = 763;
eta_base   = 0.05 * N_base;

S0 = 762;
I0 = 1;

c0_min_eta = critical_c0_for_eta(beta_base, gamma_base, q0_base, ...
    N_base, eta_base, S0, I0);
c0_values = [c0_min_eta + 0.02, 3.5, 4:0.5:6, 7:13];
eta_values = N_base .* [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05];

c0_grid  = linspace(c0_min_eta + 0.02, 13, 320);
eta_grid = linspace(0.02 * N_base, 0.05 * N_base, 220);
c0_feas_grid = linspace(2.5, 13, 620);
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
% Here beta, gamma, q0, N, S0, I0, and eta are fixed.
rows_c0 = repmat(empty_metrics(), numel(c0_values), 1);

for k = 1:numel(c0_values)
    c0 = c0_values(k);
    rows_c0(k) = compute_metrics(beta_base, gamma_base, c0, q0_base, ...
        N_base, eta_base, S0, I0);
end

T_c0 = metrics_to_table(rows_c0);
writetable(T_c0, fullfile(table_dir, 'scenario1_c0_summary.csv'));
write_latex_table(T_c0, fullfile(table_dir, 'scenario1_c0_summary_table.tex'), 'c0');

plot_control_absolute(rows_c0, fullfile(figure_dir, 'scenario1_u_time_c0.pdf'), ...
    '$c_0$', arrayfun(@format_c0_label, c0_values, 'UniformOutput', false));
plot_summary_c0(T_c0, fullfile(figure_dir, 'scenario1_summary_c0.pdf'));

%% 3. One-dimensional eta sweep
% Here beta, gamma, c0, q0, N, S0, and I0 are fixed.
rows_eta = repmat(empty_metrics(), numel(eta_values), 1);

for k = 1:numel(eta_values)
    eta = eta_values(k);
    rows_eta(k) = compute_metrics(beta_base, gamma_base, c0_base, q0_base, ...
        N_base, eta, S0, I0);
end

T_eta = metrics_to_table(rows_eta);
writetable(T_eta, fullfile(table_dir, 'scenario1_eta_summary.csv'));
write_latex_table(T_eta, fullfile(table_dir, 'scenario1_eta_summary_table.tex'), 'eta');

eta_legend_labels = arrayfun(@(v) sprintf('$\\eta/N=%g\\%%$', 100 * v / N_base), ...
    eta_values, 'UniformOutput', false);
plot_control_absolute(rows_eta, fullfile(figure_dir, 'scenario1_u_time_eta.pdf'), ...
    '', eta_legend_labels);
plot_summary_eta(T_eta, fullfile(figure_dir, 'scenario1_summary_eta.pdf'));

%% 4. Two-dimensional heatmaps in (c0, eta)
t1_map = nan(numel(eta_grid), numel(c0_grid));
dt_map = nan(numel(eta_grid), numel(c0_grid));
tend_map = nan(numel(eta_grid), numel(c0_grid));
Itcum_map = nan(numel(eta_grid), numel(c0_grid));
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
            tend_map(i, j) = row.t_end;
            Itcum_map(i, j) = row.I_t_cum;
        end
    end
end

plot_heatmaps(c0_grid, eta_grid, t1_map, dt_map, tend_map, Itcum_map, ...
    fullfile(figure_dir, 'scenario1_heatmaps_c0_eta.pdf'), N_base);
feasible_dense_map = feasibility_grid(beta_base, gamma_base, q0_base, ...
    N_base, S0, I0, c0_feas_grid, eta_feas_grid);

plot_feasibility(c0_feas_grid, eta_feas_grid, feasible_dense_map, ...
    fullfile(figure_dir, 'scenario1_feasibility_c0_eta.pdf'), N_base);

%% 5. Console summary
disp('Scenario 1 parameter analysis completed.');
fprintf('c0_min(eta = %.6g) = %.10f\n', eta_base, c0_min_eta);
disp('Generated files:');
disp(fullfile(table_dir, 'scenario1_c0_summary.csv'));
disp(fullfile(table_dir, 'scenario1_c0_summary_table.tex'));
disp(fullfile(table_dir, 'scenario1_eta_summary.csv'));
disp(fullfile(table_dir, 'scenario1_eta_summary_table.tex'));
disp(fullfile(figure_dir, 'scenario1_u_time_c0.pdf'));
disp(fullfile(figure_dir, 'scenario1_summary_c0.pdf'));

disp(fullfile(figure_dir, 'scenario1_u_time_eta.pdf'));
disp(fullfile(figure_dir, 'scenario1_summary_eta.pdf'));
disp(fullfile(figure_dir, 'scenario1_heatmaps_c0_eta.pdf'));
disp(fullfile(figure_dir, 'scenario1_feasibility_c0_eta.pdf'));

%% Local functions
function label = format_c0_label(value)
    if abs(value - round(value)) < 1e-10
        label = sprintf('%.0f', value);
    else
        label = sprintf('%.2f', value);
    end
end

function c0_min = critical_c0_for_eta(beta, gamma, q0, N, eta, S0, I0)
    H = beta + q0 * (1 - beta);
    a = beta * (1 - q0) / H;
    if ~(I0 < eta && eta < I0 + a * S0)
        error('The threshold eta must satisfy I0 < eta < I0 + a*S0.');
    end

    growth_boundary = gamma * N / (beta * (1 - q0) * S0);
    peak_gap = @(c0) normal_peak(c0, beta, gamma, q0, N, S0, I0, a) - eta;
    upper = max(2 * growth_boundary, 1);
    while peak_gap(upper) <= 0
        upper = 2 * upper;
    end
    c0_min = fzero(peak_gap, [growth_boundary, upper]);
end

function I_peak = normal_peak(c0, beta, gamma, q0, N, S0, I0, a)
    S_c = gamma * N / (beta * c0 * (1 - q0));
    I_peak = I0 + a * (S0 - S_c) + a * S_c * log(S_c / S0);
end

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
        'S_bar', NaN, ...
        't1', NaN, ...
        't2', NaN, ...
        'Delta_t', NaN, ...
        'S_end', NaN, ...
        't_end', NaN, ...
        'q_max', NaN, ...
        'J_q', NaN, ...
        'J', NaN, ...
        'I_t_cum', NaN, ...
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

    if beta <= 0 || beta >= 1 || gamma <= 0 || c0 <= 0 || ...
            q0 < 0 || q0 >= 1 || N <= 0 || eta <= 0
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

    term_num = S_star - S_bar;
    term_den = S_c - S_bar;
    if term_num <= 0 || term_den <= 0
        return;
    end

    Delta_t = (N / (c0 * eta)) * log(term_num / term_den);
    t2 = t1 + Delta_t;
    q_max = 1 - gamma * N / (beta * c0 * S_star);

    if Delta_t <= 0 || t2 <= t1 || q_max < q0 - 1e-8 || q_max > 1 + 1e-8
        return;
    end

    B = gamma * N * (1 - beta) / beta;
    A_part = S_c / B;
    C_part = 1 - c0 * S_c / B;
    log_term = log((c0 * S_star - B) / (c0 * S_c - B));
    J_q = (N / eta) * ( ...
        A_part * log(S_star / S_c) + (C_part / c0) * log_term);
    q_of_S = @(S) 1 - gamma .* N ./ (beta .* c0 .* S);
    normalized_q = @(S) max(q_of_S(S) - q0, 0) ./ (1 - q0);
    J = integral(@(S) 2 .* normalized_q(S).^2 ./ (S - S_bar), ...
        S_c, S_star, 'ArrayValued', true, 'AbsTol', 1e-11, 'RelTol', 1e-11) ...
        * N / (c0 * eta);

    C2 = eta + (beta2_0 / beta1_0) * S_c - rho1 * log(S_c);
    z_end = -(beta2_0 / (beta1_0 * rho1)) * exp((1 - C2) / rho1);
    S_end_raw = -(beta1_0 * rho1 / beta2_0) * double(lambertw(0, z_end));
    if abs(imag(S_end_raw)) > 1e-8
        return;
    end
    S_end = real(S_end_raw);
    if S_end <= 0 || S_end >= S_c
        return;
    end

    integrand_end = @(S) 1 ./ (S .* (beta2_0 .* S - beta1_0 .* rho1 .* log(S) - beta1_0 .* C2));
    try
        t_end_tail = integral(integrand_end, S_c, S_end, ...
            'ArrayValued', true, 'AbsTol', 1e-11, 'RelTol', 1e-11);
    catch
        return;
    end
    t_end = t2 + t_end_tail;
    if ~isfinite(t_end) || t_end <= t2
        return;
    end

    infection_fraction = beta / (beta + q0 * (1 - beta));
    I_t_cum = infection_fraction * (S0 - S_star) + ...
        beta * (S_star - S_c + S_bar * log((S_star - S_bar) / (S_c - S_bar))) + ...
        infection_fraction * (S_c - S_end);

    row.feasible = true;
    row.S_star = S_star;
    row.t1 = t1;
    row.t2 = t2;
    row.Delta_t = Delta_t;
    row.S_end = S_end;
    row.t_end = t_end;
    row.q_max = q_max;
    row.J_q = J_q;
    row.J = J;
    row.I_t_cum = I_t_cum;
end

function feasible_map = feasibility_grid(beta, gamma, q0, N, S0, I0, c0_grid, eta_grid)
    [C0, Eta] = meshgrid(c0_grid, eta_grid);
    H = beta + q0 * (1 - beta);
    beta1_0 = C0 .* H ./ N;
    beta2_0 = beta .* C0 .* (1 - q0) ./ N;
    a = beta2_0 ./ beta1_0;
    rho1 = gamma ./ beta1_0;
    S_c = gamma ./ beta2_0;
    Imax_pre = I0 - a .* (S_c - S0) + rho1 .* log(S_c ./ S0);
    feasible_map = (I0 <= Eta) & (S_c < S0) & (Imax_pre > Eta);
end

function T = metrics_to_table(rows)
    T = struct2table(rows);
    T = T(:, {'c0','R0','eta','eta_frac','S_star','S_c', ...
              't1','t2','Delta_t','S_end','t_end','q_max','J_q','J', ...
              'I_t_cum','Imax_pre','feasible'});
end

function write_latex_table(T, filename, sweep_name)
    fid = fopen(filename, 'w');
    if fid < 0
        error('Cannot open %s for writing.', filename);
    end
    cleaner = onCleanup(@() fclose(fid));

    if strcmp(sweep_name, 'c0')
        fprintf(fid, '\\begin{tabular}{ccccccccc}\n');
        fprintf(fid, '\\toprule\n');
        fprintf(fid, '$c_0$ & $S^*$ & $S_c$ & $t_1$ & $\\Delta t$ & $t_{\\rm end}$ & $q_{\\max}$ & $J$ & $I_{t_{\\rm cum}}$ \\\\\n');
        x1 = T.c0;
        x2 = [];
    else
        fprintf(fid, '\\begin{tabular}{cccccccccc}\n');
        fprintf(fid, '\\toprule\n');
        fprintf(fid, '$\\eta$ & $\\eta/N$ & $S^*$ & $S_c$ & $t_1$ & $\\Delta t$ & $t_{\\rm end}$ & $q_{\\max}$ & $J$ & $I_{t_{\\rm cum}}$ \\\\\n');
        x1 = T.eta;
        x2 = T.eta_frac;
    end
    fprintf(fid, '\\midrule\n');
    for k = 1:height(T)
        if T.feasible(k)
            if strcmp(sweep_name, 'c0')
                fprintf(fid, '%.4g & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n', ...
                    x1(k), T.S_star(k), T.S_c(k), T.t1(k), T.Delta_t(k), ...
                    T.t_end(k), T.q_max(k), T.J(k), T.I_t_cum(k));
            else
                fprintf(fid, '%.4g & %.4g & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n', ...
                    x1(k), x2(k), T.S_star(k), T.S_c(k), T.t1(k), T.Delta_t(k), ...
                    T.t_end(k), T.q_max(k), T.J(k), T.I_t_cum(k));
            end
        else
            if strcmp(sweep_name, 'c0')
                fprintf(fid, '%.4g & -- & -- & -- & -- & -- & -- & -- & -- \\\\\n', x1(k));
            else
                fprintf(fid, '%.4g & %.4g & -- & -- & -- & -- & -- & -- & -- & -- \\\\\n', x1(k), x2(k));
            end
        end
    end
    fprintf(fid, '\\bottomrule\n');
    fprintf(fid, '\\end{tabular}\n');
end

function plot_control_absolute(rows, filename, param_label, param_values)
    fig = figure('Position', [120, 120, 760, 480], 'Color', 'w');
    ax = axes(fig); hold(ax, 'on'); box(ax, 'on'); grid(ax, 'off');
    format_axes(ax);

    colors = lines(numel(rows));
    q_top = 0.1;
    t_top = 0;
    has_curve = false;
    for k = 1:numel(rows)
        row = rows(k);
        if ~row.feasible
            continue;
        end
        has_curve = true;
        t = linspace(0, row.t2 + 0.25 * row.Delta_t, 550);
        q = row.q0 * ones(size(t));
        mask = (t >= row.t1) & (t <= row.t2);
        q(mask) = q_control_tau(row, t(mask) - row.t1);
        q_top = max(q_top, max(q));
        t_top = max(t_top, max(t));

        if isempty(param_label)
            display_name = param_values{k};
        else
            display_name = sprintf('%s=%s', param_label, param_values{k});
        end
        plot(ax, t, q, 'LineWidth', 1.35, 'Color', colors(k, :), ...
            'DisplayName', display_name);
        plot(ax, row.t1, row.q_max, 'o', 'MarkerSize', 4.0, ...
            'MarkerFaceColor', 'w', 'MarkerEdgeColor', colors(k, :), ...
            'LineWidth', 0.9, 'HandleVisibility', 'off');
        plot(ax, row.t2, row.q0, 's', 'MarkerSize', 4.0, ...
            'MarkerFaceColor', 'w', 'MarkerEdgeColor', colors(k, :), ...
            'LineWidth', 0.9, 'HandleVisibility', 'off');
    end

    xlabel(ax, '$t$');
    ylabel(ax, '$q_c(t)$');
    title(ax, 'isolation control');
    xlim(ax, [0, max(1, t_top)]);
    ylim(ax, [0, min(1.02, 1.12 * q_top + 0.02)]);
    if has_curve
        legend(ax, 'Location', 'best', 'Interpreter', 'latex');
    end
    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function q = q_control_tau(row, tau)
    S_phase = row.S_bar + (row.S_star - row.S_bar) .* ...
        exp(-row.c0 .* row.eta .* tau ./ row.N);
    q = 1 - row.gamma .* row.N ./ (row.beta .* row.c0 .* S_phase);
end

function plot_summary_c0(T, filename)
    fig = figure('Position', [80, 80, 1150, 660], 'Color', 'w');
    x = T.c0;
    labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
              '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};

    subplot(2,3,1); plot_metric(x, T.t1, '$c_0$', '$t_1$', labels{1});
    subplot(2,3,2); plot_metric(x, T.Delta_t, '$c_0$', '$\Delta t$', labels{2});
    subplot(2,3,3); plot_metric(x, T.t_end, '$c_0$', '$t_{\rm end}$', labels{3});
    subplot(2,3,4); plot_metric(x, T.q_max, '$c_0$', '$q_{\max}$', labels{4});
    subplot(2,3,5); plot_metric(x, T.J, '$c_0$', '$J$', labels{5});
    subplot(2,3,6); plot_metric(x, T.I_t_cum, '$c_0$', '$I_{t_{\rm cum}}$', labels{6});

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_summary_eta(T, filename)
    fig = figure('Position', [80, 80, 1150, 660], 'Color', 'w');
    x = T.eta;
    labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
              '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};

    subplot(2,3,1); plot_metric(x, T.t1, '$\eta$', '$t_1$', labels{1});
    subplot(2,3,2); plot_metric(x, T.Delta_t, '$\eta$', '$\Delta t$', labels{2});
    subplot(2,3,3); plot_metric(x, T.t_end, '$\eta$', '$t_{\rm end}$', labels{3});
    subplot(2,3,4); plot_metric(x, T.q_max, '$\eta$', '$q_{\max}$', labels{4});
    subplot(2,3,5); plot_metric(x, T.J, '$\eta$', '$J$', labels{5});
    subplot(2,3,6); plot_metric(x, T.I_t_cum, '$\eta$', '$I_{t_{\rm cum}}$', labels{6});

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function plot_metric(x, y, xlabel_text, ylabel_text, title_text)
    hold on; box on; grid off;
    format_axes(gca);
    plot(x, y, 'o-', 'LineWidth', 1.25, 'MarkerSize', 4.2, ...
        'MarkerFaceColor', 'w');
    xlabel(xlabel_text);
    ylabel(ylabel_text);
    title(title_text);
end

function format_axes(ax)
    set(ax, 'LineWidth', 0.8, 'FontSize', 10.5, ...
        'GridAlpha', 0.16, 'MinorGridAlpha', 0.08);
end

function plot_heatmaps(c0_grid, eta_grid, t1_map, dt_map, tend_map, Itcum_map, filename, N)
    fig = figure('Position', [80, 80, 1100, 780], 'Color', 'w');

    subplot(2,2,1);
    heatmap_panel(c0_grid, eta_grid, t1_map, '$t_1$', N);

    subplot(2,2,2);
    heatmap_panel(c0_grid, eta_grid, dt_map, '$\Delta t$', N);

    subplot(2,2,3);
    heatmap_panel(c0_grid, eta_grid, tend_map, '$t_{\rm end}$', N);

    subplot(2,2,4);
    heatmap_panel(c0_grid, eta_grid, Itcum_map, '$I_{t_{\rm cum}}$', N);

    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end

function heatmap_panel(c0_grid, eta_grid, Z, ttl, N)
    imagesc(c0_grid, eta_grid ./ N, Z);
    set(gca, 'YDir', 'normal');
    format_axes(gca);
    xlabel('$c_0$');
    ylabel('$\eta/N$');
    title(ttl);
    colorbar;
    box on;
end

function plot_feasibility(c0_grid, eta_grid, feasible_map, filename, N)
    fig = figure('Position', [120, 120, 680, 500], 'Color', 'w');
    imagesc(c0_grid, eta_grid ./ N, double(feasible_map));
    set(gca, 'YDir', 'normal');
    format_axes(gca);
    colormap([0.88 0.88 0.88; 0.20 0.55 0.90]);
    colorbar('Ticks', [0, 1], 'TickLabels', {'No crossing', 'Crossing'});
    xlabel('$c_0$');
    ylabel('$\eta/N$');
    title('Feasibility of reaching $I=\eta$');
    box on;
    exportgraphics(fig, filename, 'Resolution', 600, 'BackgroundColor', 'white');
    close(fig);
end
