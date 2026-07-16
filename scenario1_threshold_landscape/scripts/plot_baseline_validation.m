% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_baseline_validation.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

baseline_rows = struct([]);
for k = 1:numel(cfg.baseline_eta_frac)
    eta_frac = cfg.baseline_eta_frac(k);
    sub = landscape(abs(landscape.c0 - cfg.c0_base) < 1e-10 & ...
        abs(landscape.eta_frac - eta_frac) < 1e-10, :);
    row = table_row_to_struct(sub);
    [traj, platform_error] = compute_trajectory(row);
    row.platform_error = platform_error;
    baseline_rows = append_row(baseline_rows, row, k);

    if abs(eta_frac - 0.020) < 1e-10
        filename = fullfile(cfg.paths.figures, 'baseline_validation_eta0020.pdf');
    else
        filename = fullfile(cfg.paths.figures, 'baseline_validation_eta0002.pdf');
    end
    plot_one_baseline(row, traj, filename, logfid);
end

write_latex_tables('baseline', baseline_rows, ...
    fullfile(cfg.paths.tables, 'baseline_validation_table.tex'));
fprintf(logfid, 'baseline validation finished\n');

function rows = append_row(rows, row, k)
if k == 1
    rows = row;
else
    rows(k) = row;
end
end

function plot_one_baseline(row, traj, filename, logfid)
[t_base, S_base, I_base] = compute_background_baseline(row, max(traj.t));

fig = figure('Position', [80, 60, 1150, 850], 'Color', 'w', 'Visible', 'on');
x_max = max(traj.t);
sgtitle(fig, sprintf('$c_0=%.0f,\\ \\eta/N=%.1f\\%%$', ...
    row.c0, row.eta_percent), 'FontSize', 15, 'Interpreter', 'latex');

ax = subplot(3, 1, 1); hold(ax, 'on'); grid(ax, 'off'); box(ax, 'on');
plot(ax, t_base, I_base, 'k--', 'LineWidth', 2, ...
    'DisplayName', '$I_{\mathrm{no}}$');
plot(ax, traj.t, traj.I, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$I$');
yline(ax, row.eta, 'r--', 'LineWidth', 2, ...
    'DisplayName', '$\eta$');
draw_switch_lines(ax, row);
ylabel(ax, '$I(t)$', 'FontSize', 13);
legend(ax, 'Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim(ax, [0, max([max(I_base), max(traj.I), row.eta]) * 1.15]);
xlim(ax, [0, x_max]);
style_axes(ax);

ax = subplot(3, 1, 2); hold(ax, 'on'); grid(ax, 'off'); box(ax, 'on');
plot(ax, t_base, S_base, 'k--', 'LineWidth', 2, ...
    'DisplayName', '$S_{\mathrm{no}}$');
plot(ax, traj.t, traj.S, 'b-', 'LineWidth', 3, ...
    'DisplayName', '$S$');
yline(ax, row.S_c, 'r--', 'LineWidth', 2, ...
    'DisplayName', '$S_{\mathrm{c}}$');
plot(ax, row.t1, row.S_star, 'ko', 'MarkerFaceColor', 'k', ...
    'HandleVisibility', 'off');
plot(ax, row.t2, row.S_c, 'ks', 'MarkerFaceColor', 'k', ...
    'HandleVisibility', 'off');
draw_switch_lines(ax, row);
ylabel(ax, '$S(t)$', 'FontSize', 13);
legend(ax, 'Location', 'best', 'FontSize', 10, 'Interpreter', 'latex');
ylim(ax, [0, row.N * 1.05]);
xlim(ax, [0, x_max]);
style_axes(ax);

ax = subplot(3, 1, 3); hold(ax, 'on'); grid(ax, 'off'); box(ax, 'on');
plot(ax, traj.t, traj.q, 'm-', 'LineWidth', 3, ...
    'DisplayName', '$q_c(t)$');
yline(ax, row.q0, 'r--', 'LineWidth', 2, ...
    'DisplayName', '$q_0$');
draw_switch_lines(ax, row);
xlabel(ax, '$t$', 'FontSize', 13);
ylabel(ax, '$q_c(t)$', 'FontSize', 13);
legend(ax, 'Location', 'northeast', 'FontSize', 10, 'Interpreter', 'latex');
ylim(ax, [-0.05, min(1.05, max(traj.q) * 1.15 + 0.02)]);
xlim(ax, [0, x_max]);
style_axes(ax);

save_figure_safe(fig, filename, logfid);
end

function [t_base, S_base, I_base] = compute_background_baseline(row, t_end)
ode_background = @(~, Y) [
    -row.c0 * (row.beta + row.q0 * (1 - row.beta)) * Y(1) * Y(2) / row.N;
     row.beta * row.c0 * (1 - row.q0) * Y(1) * Y(2) / row.N - row.gamma * Y(2)
];
options = odeset('RelTol', 1e-8, 'AbsTol', 1e-10);
[t_base, Y_base] = ode45(ode_background, [0, t_end], [row.S0; row.I0], options);
S_base = Y_base(:, 1);
I_base = Y_base(:, 2);
end

function draw_switch_lines(ax, row)
xline(ax, row.t1, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
xline(ax, row.t2, 'k:', 'LineWidth', 1.2, 'HandleVisibility', 'off');
end

function set_graphics_defaults()
set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');
set(groot, 'defaultFigureVisible', 'on');
end

function style_axes(ax)
set(ax, 'LineWidth', 0.9, 'FontSize', 11, ...
    'TickDir', 'in', 'Layer', 'top');
end

function logfid = open_log(cfg, name)
logfid = fopen(fullfile(cfg.paths.logs, name), 'w');
if logfid < 0
    error('Cannot open log file.');
end
end
