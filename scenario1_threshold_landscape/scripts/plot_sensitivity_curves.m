% close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_sensitivity_curves.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

landscape = readtable(fullfile(cfg.paths.output_csv, 'landscape_summary.csv'));

plot_eta_sensitivity(landscape, cfg.main_eta_sweep_c0_values, ...
    fullfile(cfg.paths.figures, 'eta_sensitivity_selected_c0.pdf'), logfid);
plot_c0_sensitivity(landscape, cfg.c0_response_eta_frac, ...
    fullfile(cfg.paths.figures, 'c0_sensitivity_selected_eta.pdf'), logfid);

fprintf(logfid, 'sensitivity curves finished\n');

function plot_eta_sensitivity(T, c0_values, filename, logfid)
style = scenario1_main_plot_style();
fig = figure('Units', 'points', ...
    'Position', [80, 80, style.sensitivity_size_bp], ...
    'Color', 'w', 'Visible', 'on');
tl = tiledlayout(fig, 2, 3, 'Padding', 'compact', 'TileSpacing', 'compact');
labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
          '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};
fields = {'t1', 'Delta_t', 't_end', 'q_max', 'J', 'I_t_cum'};
color_index = round(linspace(1, size(style.blues, 1), numel(c0_values)));
colors = style.blues(color_index, :);

for k = 1:6
    ax = nexttile(tl);
    hold(ax, 'on');
    scenario1_main_plot_style(ax);
    for c = 1:numel(c0_values)
        sub = T(abs(T.c0 - c0_values(c)) < 1e-10, :);
        sub = sub(logical(sub.valid) & isfinite(sub.(fields{k})), :);
        sub = sortrows(sub, 'eta_percent');
        plot(ax, sub.eta_percent, sub.(fields{k}), '-', ...
            'Color', colors(c, :), ...
            'LineWidth', style.line_width, ...
            'Marker', 'none', ...
            'DisplayName', sprintf('$c_0=%s$', ...
                compact_number(c0_values(c))));
    end
    set(ax, 'XScale', 'log');
    xlabel(ax, '$\eta/N\;(\%)$', ...
        'FontName', style.font_name, 'FontSize', style.label_size);
    ylabel(ax, labels{k}, ...
        'FontName', style.font_name, 'FontSize', style.label_size);
    xticks(ax, [0.2, 0.5, 1, 2, 5]);
    xticklabels(ax, {'0.2', '0.5', '1', '2', '5'});
    xlim(ax, [0.2, 5]);
    if k == 4
        ylim(ax, [0.45, 0.85]);
        yticks(ax, 0.45:0.10:0.85);
        yticklabels(ax, {'0.45', '0.55', '0.65', '0.75', '0.85'});
    end
    add_panel_label(ax, k, style);
    if k == 3
        lgd = legend(ax, 'Location', 'northeast', ...
            'Interpreter', 'latex', 'FontSize', style.legend_size);
        set(lgd, 'Box', 'off', 'ItemTokenSize', [12, 8]);
        drawnow;
        lp = get(lgd, 'Position');   % [x y w h], 归一化图坐标(0=左/下, 1=右/上)
        right_margin = 0.03;        % 离图右边的距离:调大 -> 图例左移
        top_margin   = 0.03;        % 离图顶边的距离:调大 -> 图例下移
        set(lgd, 'Position', ...
            [1 - lp(3) - right_margin, 1 - lp(4) - top_margin, lp(3), lp(4)]);
    end
end
save_figure_safe(fig, filename, logfid, style.sensitivity_size_bp);
close(fig);
end

function plot_c0_sensitivity(T, eta_fracs, filename, logfid)
style = scenario1_main_plot_style();
fig = figure('Units', 'points', ...
    'Position', [80, 80, style.sensitivity_size_bp], ...
    'Color', 'w', 'Visible', 'on');
tl = tiledlayout(fig, 2, 3, 'Padding', 'compact', 'TileSpacing', 'compact');
labels = {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
          '$q_{\max}$', '$J$', '$I_{t_{\rm cum}}$'};
fields = {'t1', 'Delta_t', 't_end', 'q_max', 'J', 'I_t_cum'};
color_index = round(linspace(1, size(style.blues, 1), numel(eta_fracs)));
colors = style.blues(color_index, :);

for k = 1:6
    ax = nexttile(tl);
    hold(ax, 'on');
    scenario1_main_plot_style(ax);
    for e = 1:numel(eta_fracs)
        sub = T(abs(T.eta_frac - eta_fracs(e)) < 1e-10, :);
        sub = sub(logical(sub.valid) & isfinite(sub.(fields{k})), :);
        plot(ax, sub.c0, sub.(fields{k}), '-', ...
            'LineWidth', style.line_width, ...
            'Marker', 'none', ...
            'Color', colors(e, :), ...
            'DisplayName', sprintf('$\\eta/N=%s\\%%$', ...
                compact_number(100 * eta_fracs(e))));
        if k == 2
            [peak_value, peak_index] = max(sub.Delta_t);
            plot(ax, sub.c0(peak_index), peak_value, 'o', ...
                'Color', 'w', ...
                'MarkerFaceColor', style.accent, ...
                'MarkerSize', style.marker_size, ...
                'LineWidth', 0.7, ...
                'HandleVisibility', 'off');
        end
    end
    xlabel(ax, '$c_0$', ...
        'FontName', style.font_name, 'FontSize', style.label_size);
    ylabel(ax, labels{k}, ...
        'FontName', style.font_name, 'FontSize', style.label_size);
    xlim(ax, [2.3, 14]);
    add_panel_label(ax, k, style);
    if k == 3
        lgd = legend(ax, 'Location', 'northeast', ...
            'Interpreter', 'latex', 'FontSize', style.legend_size);
        set(lgd, 'Box', 'off', 'ItemTokenSize', [12, 8]);
        drawnow;
        lp = get(lgd, 'Position');
        set(lgd, 'Position', ...
            [1 - lp(3) - 0.03, 1 - lp(4) - 0.03, lp(3), lp(4)]);
    end
end
save_figure_safe(fig, filename, logfid, style.sensitivity_size_bp);
close(fig);
end

function add_panel_label(ax, index, style)
text(ax, 0.01, 0.99, sprintf('(%c)', char('a' + index - 1)), ...
    'Units', 'normalized', ...
    'HorizontalAlignment', 'left', ...
    'VerticalAlignment', 'top', ...
    'FontName', style.font_name, ...
    'FontSize', style.panel_size, ...
    'Interpreter', 'latex');
end

function text_value = compact_number(value)
if abs(value - round(value)) < 1e-10
    text_value = sprintf('%.0f', value);
else
    text_value = sprintf('%.1f', value);
end
end
