% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_sensitivity_curves.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

eta_sensitivity = readtable(fullfile(cfg.paths.output_csv, 'eta_sensitivity_c0_10.csv'));
c0_sensitivity = readtable(fullfile(cfg.paths.output_csv, 'c0_sensitivity_selected_eta.csv'));

plot_eta_sensitivity(eta_sensitivity, ...
    fullfile(cfg.paths.figures, 'eta_sensitivity_c0_10.pdf'), logfid);
plot_c0_sensitivity(c0_sensitivity, cfg.c0_response_eta_frac, ...
    fullfile(cfg.paths.figures, 'c0_sensitivity_selected_eta.pdf'), logfid);

fprintf(logfid, 'sensitivity curves finished\n');

function plot_eta_sensitivity(T, filename, logfid)
fig = figure('Position', [80, 80, 1180, 720], 'Color', 'w', 'Visible', 'on');
x = T.eta_percent;
labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
          '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};
values = {T.t1, T.Delta_t, T.t_end, T.q_max, T.J, T.I_t_cum};

for k = 1:6
    ax = subplot(2, 3, k); hold(ax, 'on'); box(ax, 'on');
    plot(ax, x, values{k}, '-', 'LineWidth', 2, 'Marker', 'none');
    xlabel(ax, '$\eta/N\;(\%)$');
    ylabel(ax, labels{k});
    title(ax, labels{k});
    xticks(ax, 0.2:0.2:2.0);
    xlim(ax, [0.2, 2.0]);
    style_axes(ax);
end
save_figure_safe(fig, filename, logfid);
end

function plot_c0_sensitivity(T, eta_fracs, filename, logfid)
fig = figure('Position', [80, 80, 1180, 720], 'Color', 'w', 'Visible', 'on');
labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
          '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};
fields = {'t1', 'Delta_t', 't_end', 'q_max', 'J', 'I_t_cum'};
colors = lines(numel(eta_fracs));

for k = 1:6
    ax = subplot(2, 3, k); hold(ax, 'on'); box(ax, 'on');
    for e = 1:numel(eta_fracs)
        sub = T(abs(T.eta_frac - eta_fracs(e)) < 1e-10, :);
        plot(ax, sub.c0, sub.(fields{k}), '-', 'LineWidth', 2, ...
            'Marker', 'none', ...
            'Color', colors(e, :), ...
            'DisplayName', sprintf('$\\eta/N=%.1f\\%%$', 100 * eta_fracs(e)));
    end
    xlabel(ax, '$c_0$');
    ylabel(ax, labels{k});
    title(ax, labels{k});
    xlim(ax, [6, 14]);
    style_axes(ax);
    if k == 1
        legend(ax, 'Location', 'best', 'Interpreter', 'latex');
    end
end
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
    'TickDir', 'in', 'Layer', 'top');
end

function logfid = open_log(cfg, name)
logfid = fopen(fullfile(cfg.paths.logs, name), 'w');
if logfid < 0
    error('Cannot open log file.');
end
end
