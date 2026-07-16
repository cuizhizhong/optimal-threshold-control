% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_representative_trajectories.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

eta_rows = struct([]);
for k = 1:numel(cfg.selected_eta_frac)
    sub = landscape(abs(landscape.c0 - cfg.c0_base) < 1e-10 & ...
        abs(landscape.eta_frac - cfg.selected_eta_frac(k)) < 1e-10, :);
    eta_rows = append_row(eta_rows, table_row_to_struct(sub), k);
end
plot_eta_trajectories(eta_rows, ...
    fullfile(cfg.paths.figures, 'trajectories_eta_selected_c0_10.pdf'), logfid);

c0_rows = struct([]);
for k = 1:numel(cfg.selected_c0)
    sub = landscape(abs(landscape.c0 - cfg.selected_c0(k)) < 1e-10 & ...
        abs(landscape.eta_frac - 0.010) < 1e-10, :);
    c0_rows = append_row(c0_rows, table_row_to_struct(sub), k);
end
plot_c0_trajectories(c0_rows, ...
    fullfile(cfg.paths.figures, 'trajectories_c0_selected_eta0010.pdf'), logfid);

fprintf(logfid, 'representative trajectories finished\n');

function rows = append_row(rows, row, k)
if k == 1
    rows = row;
else
    rows(k) = row;
end
end

function plot_eta_trajectories(rows, filename, logfid)
fig = figure('Position', [90, 80, 980, 820], 'Color', 'w', 'Visible', 'on');
tl = tiledlayout(fig, 3, 1, 'Padding', 'compact', 'TileSpacing', 'compact');
colors = lines(numel(rows));

ax1 = nexttile(tl); hold(ax1, 'on'); box(ax1, 'on');
ax2 = nexttile(tl); hold(ax2, 'on'); box(ax2, 'on');
ax3 = nexttile(tl); hold(ax3, 'on'); box(ax3, 'on');

for k = 1:numel(rows)
    [traj, ~] = compute_trajectory(rows(k));
    label = sprintf('$\\eta/N=%.1f\\%%$', rows(k).eta_percent);
    plot(ax1, traj.t, traj.I, 'LineWidth', 2, 'Color', colors(k, :), ...
        'DisplayName', label);
    yline(ax1, rows(k).eta, '--', 'Color', colors(k, :), ...
        'LineWidth', 2, 'HandleVisibility', 'off');
    plot(ax2, traj.t, traj.q, 'LineWidth', 2, 'Color', colors(k, :), ...
        'DisplayName', label);
    plot(ax3, traj.t, traj.J_cum, 'LineWidth', 2, 'Color', colors(k, :), ...
        'DisplayName', label);
end

ylabel(ax1, '$I(t)$');
title(ax1, '$c_0=10$');
ylim(ax1, [1, 20]);
legend(ax1, 'Location', 'northeast', 'Interpreter', 'latex');
style_axes(ax1);
ylabel(ax2, '$q_c(t)$');
style_axes(ax2);
xlabel(ax3, '$t$');
ylabel(ax3, '$J(t)$');
style_axes(ax3);

save_figure_safe(fig, filename, logfid);
end

function plot_c0_trajectories(rows, filename, logfid)
fig = figure('Position', [90, 80, 980, 660], 'Color', 'w', 'Visible', 'on');
tl = tiledlayout(fig, 2, 1, 'Padding', 'compact', 'TileSpacing', 'compact');
colors = lines(numel(rows));

ax1 = nexttile(tl); hold(ax1, 'on'); box(ax1, 'on');
ax2 = nexttile(tl); hold(ax2, 'on'); box(ax2, 'on');

for k = 1:numel(rows)
    [traj, ~] = compute_trajectory(rows(k));
    label = sprintf('$c_0=%.0f$', rows(k).c0);
    plot(ax1, traj.t, traj.I, 'LineWidth', 2, 'Color', colors(k, :), ...
        'DisplayName', label);
    yline(ax1, rows(k).eta, '--', 'Color', [0.45 0.45 0.45], ...
        'LineWidth', 2, 'HandleVisibility', 'off');
    plot(ax2, traj.t, traj.q, 'LineWidth', 2, 'Color', colors(k, :), ...
        'DisplayName', label);
end

ylabel(ax1, '$I(t)$');
title(ax1, '$\eta/N=1.0\%$');
legend(ax1, 'Location', 'northeast', 'Interpreter', 'latex');
style_axes(ax1);
xlabel(ax2, '$t$');
ylabel(ax2, '$q_c(t)$');
style_axes(ax2);

save_figure_safe(fig, filename, logfid);
end

function set_graphics_defaults()
set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');
set(groot, 'defaultFigureVisible', 'on');
end

function style_axes(ax)
set(ax, 'LineWidth', 0.8, 'FontSize', 10.5, ...
    'TickDir', 'in', 'TickLength', [0.005 0.025], 'Layer', 'top');
end

function logfid = open_log(cfg, name)
logfid = fopen(fullfile(cfg.paths.logs, name), 'w');
if logfid < 0
    error('Cannot open log file.');
end
end
