% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_heatmaps.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

x = cfg.eta_percent_list;
y = cfg.c0_list;
heatmap_specs = {
    't1', 0.5:0.5:4.5, [0 5], '$t_1$', '$t_1$', 'heatmap_t1.pdf';
    'Delta_t', [10 15 20 25 30 40 50 60 80 100 120 160], [0 200], '$\Delta t$', '$\Delta t$', 'heatmap_delta_t.pdf';
    't_end', [40 45 50 55 65 80 100 120 140 160 200], [0 240], '$t_{\rm end}$', '$t_{\rm end}$', 'heatmap_t_end.pdf';
    'q_max', 0.62:0.02:0.84, [0.60 0.85], '$q_{\rm max}$', '$q_{\rm max}$', 'heatmap_q_max.pdf';
    'J', [5 6 7 8 9 10 12 15 20 30 40 50 60], [0 65], '$J$', '$J$', 'heatmap_J.pdf';
    'I_t_cum', 170:10:250, [160 260], '$I_{t_{\rm cum}}$', '$I_{t_{\rm cum}}$', 'heatmap_I_t_cum.pdf'
};

for k = 1:size(heatmap_specs, 1)
    metric_name = heatmap_specs{k, 1};
    levels = heatmap_specs{k, 2};
    color_limits = heatmap_specs{k, 3};
    title_text = heatmap_specs{k, 4};
    cbar_text = heatmap_specs{k, 5};
    filename = fullfile(cfg.paths.figures, heatmap_specs{k, 6});
    try
        Z = metric_matrix_from_table(landscape, cfg.c0_list, cfg.eta_frac_list, metric_name);
        log_line(logfid, ['plotting ', heatmap_specs{k, 6}]);
        plot_one_heatmap(x, y, Z, levels, color_limits, title_text, cbar_text, filename, logfid);
    catch err
        log_line(logfid, ['failed ', heatmap_specs{k, 6}, ': ', err.message]);
    end
end

log_line(logfid, 'heatmaps finished');

function plot_one_heatmap(x, y, Z, levels, color_limits, title_text, cbar_text, filename, logfid)
fig = figure('Position', [120, 100, 788, 734], 'Color', 'w', 'Visible', 'on');
ax = axes(fig); hold(ax, 'on'); box(ax, 'on');

[ETA, C0] = meshgrid(x, y);
contourf(ax, ETA, C0, Z, 200, 'LineColor', 'none');
set(ax, 'YDir', 'normal');
colormap(ax, parula(256));
set_color_limits(ax, color_limits);
cb = colorbar(ax);
cb.Label.String = cbar_text;
cb.Label.Interpreter = 'latex';
cb.Label.FontName = 'Times New Roman';
cb.Label.FontSize = 18;
set(ax, 'Units', 'normalized', 'Position', [0.10 0.22 0.72 0.66]);
set(cb, 'Units', 'normalized', 'Position', [0.839 0.22 0.025 0.66]);

if ~isempty(levels)
    [C, h] = contour(ax, ETA, C0, Z, levels, 'LineColor', 'r', ...
        'LineStyle', '--', 'LineWidth', 1.2);
    try
        clabel(C, h, 'FontSize', 9.5, 'Color', 'k', ...
            'Interpreter', 'latex', 'LabelSpacing', 500);
    catch
        try
            h.ShowText = 'on';
            h.LabelColor = 'k';
            h.LabelSpacing = 500;
        catch
        end
    end
end

xlabel(ax, '$\eta/N\;(\%)$', 'FontSize', 18, 'FontName', 'Times New Roman');
ylabel(ax, '$c_0$', 'FontSize', 18, 'FontName', 'Times New Roman');
title(ax, title_text, 'FontSize', 18, 'FontName', 'Times New Roman');
xticks(ax, 0.2:0.2:2.0);
xlim(ax, [0.2, 2.0]);
ylim(ax, [6, 14]);
style_axes(ax);
save_heatmap_figure_safe(fig, filename, logfid);
end

function set_color_limits(ax, color_limits)
if isempty(color_limits)
    return;
end
try
    clim(ax, color_limits);
catch
    caxis(ax, color_limits);
end
end

function ok = save_heatmap_figure_safe(fig, filename, logfid)
ok = false;
try
    exportgraphics(fig, filename, 'ContentType', 'image', ...
        'Resolution', 600, 'BackgroundColor', 'white');
    log_line(logfid, ['saved ', filename]);
    ok = true;
catch err
    log_line(logfid, ['image export failed: ', err.message]);
    ok = save_figure_safe(fig, filename, logfid);
end

end

function style_axes(ax)
set(ax, 'LineWidth', 0.8, 'FontName', 'Times New Roman', ...
    'FontSize', 14, 'TickDir', 'out', 'TickLength', [0 0], ...
    'Layer', 'top');
end
