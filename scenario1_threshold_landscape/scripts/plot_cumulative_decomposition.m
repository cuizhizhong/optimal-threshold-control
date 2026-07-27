% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_cumulative_decomposition.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

T = readtable(fullfile(cfg.paths.output_csv, 'eta_sensitivity_c0_10.csv'));
plot_one_cumulative_decomposition(T, ...
    fullfile(cfg.paths.figures, 'cumulative_decomposition_c0_10.pdf'), logfid);
fprintf(logfid, 'cumulative decomposition finished\n');

function plot_one_cumulative_decomposition(T, filename, logfid)
fig = figure('Position', [120, 110, 880, 520], 'Color', 'w', 'Visible', 'on');
ax = axes(fig); hold(ax, 'on'); box(ax, 'on');
x = T.eta_percent;
parts = [T.I_pre, T.I_wall, T.I_post];
bar(ax, x, parts, 'stacked', 'BarWidth', 0.85);
plot(ax, x, T.I_t_cum, 'ko-', 'LineWidth', 1.3, 'MarkerFaceColor', 'w', ...
    'DisplayName', '$I_{t_{\rm cum}}$');
xlabel(ax, '$\eta/N\;(\%)$');
ylabel(ax, 'Cumulative infections');
title(ax, '$c_0=10$');
legend(ax, {'$I_{\rm pre}$', '$I_{\rm wall}$', '$I_{\rm post}$', '$I_{t_{\rm cum}}$'}, ...
    'Location', 'best', 'Interpreter', 'latex');
xticks(ax, 0.2:0.2:2.0);
xlim(ax, [0.15, 2.05]);
style_axes(ax);
save_figure_safe(fig, filename, logfid);
end

function style_axes(ax)
set(ax, 'LineWidth', 0.8, 'FontSize', 10.5, ...
    'TickDir', 'out', 'Layer', 'top');
end
