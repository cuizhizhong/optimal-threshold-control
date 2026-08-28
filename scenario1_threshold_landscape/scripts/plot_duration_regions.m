% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_duration_regions.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

x = cfg.eta_percent_list;
y = cfg.c0_list;
Delta_t_matrix = metric_matrix_from_table(landscape, cfg.c0_list, cfg.eta_frac_list, 'Delta_t');
filename = fullfile(cfg.paths.figures, 'region_by_duration.pdf');
plot_region_by_duration(x, y, Delta_t_matrix, filename, logfid);
fprintf(logfid, 'duration region plot finished\n');

function plot_region_by_duration(x, y, Delta_t_matrix, filename, logfid)
region = nan(size(Delta_t_matrix));
region(Delta_t_matrix <= 40) = 1;
region(Delta_t_matrix > 40 & Delta_t_matrix <= 100) = 2;
region(Delta_t_matrix > 100) = 3;

fig = figure('Position', [120, 100, 760, 540], 'Color', 'w', 'Visible', 'on');
ax = axes(fig); hold(ax, 'on'); box(ax, 'on');
imagesc(ax, x, y, region);
set(ax, 'YDir', 'normal');
colormap(ax, [0.34 0.65 0.82; 0.96 0.78 0.35; 0.82 0.32 0.28]);
caxis(ax, [1, 3]);
cb = colorbar(ax, 'Ticks', [1, 2, 3], ...
    'TickLabels', {'$\Delta t\le40$', '$40<\Delta t\le100$', '$\Delta t>100$'});
cb.TickLabelInterpreter = 'latex';

[~, h] = contour(ax, x, y, Delta_t_matrix, [40 100], 'k--', 'LineWidth', 1.2);
try
    h.ShowText = 'on';
    h.LabelColor = 'k';
    h.LabelSpacing = 300;
catch
end

xlabel(ax, '$\eta/N\;(\%)$');
ylabel(ax, '$c_0$');
title(ax, 'Regions classified by $\Delta t$');
xticks(ax, [0.2, 1, 2, 3, 4, 5]);
xlim(ax, [min(x), max(x)]);
ylim(ax, [min(y), max(y)]);
style_axes(ax);
save_figure_safe(fig, filename, logfid);
end

function style_axes(ax)
set(ax, 'LineWidth', 0.8, 'FontSize', 10.5, ...
    'TickDir', 'out', 'Layer', 'top');
end
