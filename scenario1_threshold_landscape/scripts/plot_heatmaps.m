% Single-metric and composite heatmaps for the scenario-one landscape.

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
c0_boundary = arrayfun(@(eta) critical_c0_for_eta( ...
    cfg.beta, cfg.gamma, cfg.q0, cfg.N, eta, cfg.S0, cfg.I0), ...
    cfg.eta_list);

specs = struct( ...
    'metric', {'t1', 'Delta_t', 't_end', 'q_max', 'J', 'I_t_cum'}, ...
    'title', {'$t_1$', '$\Delta t$', '$t_{\rm end}$', ...
              '$q_{\mathrm{max}}$', '$J$', '$I_{t_{\rm cum}}$'}, ...
    'filename', {'heatmap_t1.pdf', 'heatmap_delta_t.pdf', ...
                 'heatmap_t_end.pdf', 'heatmap_q_max.pdf', ...
                 'heatmap_J.pdf', 'heatmap_I_t_cum.pdf'});

matrices = cell(size(specs));
for k = 1:numel(specs)
    matrices{k} = metric_matrix_from_table( ...
        landscape, cfg.c0_list, cfg.eta_frac_list, specs(k).metric);
    [specs(k).limits, specs(k).levels] = heatmap_scale( ...
        matrices{k}, specs(k).metric);

    filename = fullfile(cfg.paths.figures, specs(k).filename);
    log_line(logfid, sprintf('plotting %s with limits [%g, %g]', ...
        specs(k).filename, specs(k).limits(1), specs(k).limits(2)));
    fig = figure('Position', [120, 100, 788, 734], ...
        'Color', 'w', 'Visible', 'on');
    ax = axes(fig);
    plot_heatmap_axes(ax, x, y, matrices{k}, c0_boundary, ...
        specs(k), '', false);
    save_heatmap_figure_safe(fig, filename, logfid);
    close(fig);
end

composite_indices = [1, 2, 3, 6];
style = scenario1_main_plot_style();
fig = figure('Units', 'points', ...
    'Position', [80, 60, style.heatmap_size_bp], ...
    'Color', 'w', 'Visible', 'on');
tl = tiledlayout(fig, 2, 2, 'Padding', 'compact', 'TileSpacing', 'compact');
for panel = 1:numel(composite_indices)
    k = composite_indices(panel);
    ax = nexttile(tl);
    main_spec = specs(k);
    main_spec.levels = main_composite_contour_levels(main_spec.metric);
    plot_heatmap_axes(ax, x, y, matrices{k}, c0_boundary, ...
        main_spec, sprintf('(%c)', char('a' + panel - 1)), true);
end
composite_file = fullfile(cfg.paths.figures, ...
    'scenario1_heatmaps_c0_eta.pdf');
save_heatmap_figure_safe(fig, composite_file, logfid, ...
    style.heatmap_size_bp);
close(fig);

log_line(logfid, 'heatmaps finished');

function plot_heatmap_axes(ax, x, y, Z, c0_boundary, spec, panel_label, compact)
style = scenario1_main_plot_style();
hold(ax, 'on');
scenario1_main_plot_style(ax);

[ETA, C0] = meshgrid(x, y);
Z_display = extend_to_analytic_boundary(Z);
contourf(ax, ETA, C0, Z_display, 200, 'LineColor', 'none');
set(ax, 'YDir', 'normal', 'Color', 'w');
colormap(ax, parula(256));
set_color_limits(ax, spec.limits);

patch(ax, [x, fliplr(x)], ...
    [repmat(min(y), 1, numel(x)), fliplr(c0_boundary)], ...
    'w', ...
    'EdgeColor', 'none', ...
    'HandleVisibility', 'off');

if ~isempty(spec.levels)
    [C, h] = contour(ax, ETA, C0, Z, spec.levels, ...
        'LineColor', [0.70 0.10 0.12], ...
        'LineStyle', '--', ...
        'LineWidth', 0.9);
    label_matrix = longest_contour_segments( ...
        C, spec.levels, [min(x), max(x)], [min(y), max(y)]);
    if ~isempty(label_matrix)
        clabel(label_matrix, h, spec.levels, ...
            'LabelSpacing', 1000, ...
            'FontSize', style.contour_label_size, ...
            'Color', 'k', ...
            'Interpreter', 'latex');
    end
end

plot(ax, x, c0_boundary, 'k-', ...
    'LineWidth', 1.1, ...
    'HandleVisibility', 'off');

xlabel(ax, '$\eta/N\;(\%)$', ...
    'FontName', style.font_name, 'FontSize', style.label_size);
ylabel(ax, '$c_0$', ...
    'FontName', style.font_name, 'FontSize', style.label_size);
title(ax, spec.title, ...
    'FontName', style.font_name, 'FontSize', style.title_size);
xticks(ax, [0.2, 1, 2, 3, 4, 5]);
yticks(ax, [2.3, 4, 6, 8, 10, 12, 14]);
xlim(ax, [0.2, 5]);
ylim(ax, [2.3, 14]);
pbaspect(ax, [1 1 1]);

cb = colorbar(ax);
cb.Label.Interpreter = 'latex';
cb.Label.String = spec.title;
cb.Label.FontName = style.font_name;
cb.Label.FontSize = style.label_size;
cb.FontName = style.font_name;
cb.FontSize = style.font_size;

if ~isempty(panel_label)
    text(ax, 0, 1.025, panel_label, ...
        'Units', 'normalized', ...
        'HorizontalAlignment', 'left', ...
        'VerticalAlignment', 'bottom', ...
        'FontName', style.font_name, ...
        'FontSize', style.panel_size, ...
        'Interpreter', 'latex');
end
end

function Z_display = extend_to_analytic_boundary(Z)
% Fill only leading NaNs for display; a white analytic mask is applied later.
Z_display = Z;
for column = 1:size(Z, 2)
    first_valid = find(isfinite(Z(:, column)), 1, 'first');
    if ~isempty(first_valid) && first_valid > 1
        Z_display(1:first_valid - 1, column) = Z(first_valid, column);
    end
end
end

function [limits, levels] = heatmap_scale(Z, metric_name)
if strcmp(metric_name, 'Delta_t')
    limits = [0, 215];
    levels = [2, 5, 10, 20, 40, 80, 120, 160, 200];
    return;
end

values = Z(isfinite(Z));
if isempty(values)
    error('plot_heatmaps:noFiniteValues', ...
        'No finite values for metric %s.', metric_name);
end
value_min = min(values);
value_max = max(values);
if value_max <= value_min
    limits = [value_min - 0.5, value_max + 0.5];
    levels = [];
    return;
end

step = nice_step((value_max - value_min) / 8);
lower = floor(value_min / step) * step;
upper = ceil(value_max / step) * step;
if lower == upper
    upper = lower + step;
end
limits = [lower, upper];
levels = (lower + step):step:(upper - step);
end

function levels = main_composite_contour_levels(metric_name)
switch metric_name
    case 't1'
        levels = [1, 2, 5, 10, 20];
    case 'Delta_t'
        levels = [5, 10, 20, 40, 80];
    case 't_end'
        levels = [30, 50, 80, 120, 180];
    case 'I_t_cum'
        levels = [180, 220, 260, 300, 340];
    otherwise
        error('plot_heatmaps:unknownMainMetric', ...
            'No main-composite contour levels are defined for %s.', ...
            metric_name);
end
end

function label_matrix = longest_contour_segments( ...
        contour_matrix, requested_levels, x_bounds, y_bounds)
% Keep only the longest normalized-arclength component at each level.
best_points = cell(size(requested_levels));
best_lengths = -inf(size(requested_levels));
column = 1;
x_span = diff(x_bounds);
y_span = diff(y_bounds);

while column <= size(contour_matrix, 2)
    level = contour_matrix(1, column);
    point_count = round(contour_matrix(2, column));
    last_column = column + point_count;
    if point_count < 2 || last_column > size(contour_matrix, 2)
        column = last_column + 1;
        continue;
    end

    points = contour_matrix(:, column + 1:last_column);
    [level_error, level_index] = min(abs(requested_levels - level));
    level_tolerance = 1e-9 * max(1, abs(requested_levels(level_index)));
    if level_error <= level_tolerance
        dx = diff(points(1, :)) / x_span;
        dy = diff(points(2, :)) / y_span;
        normalized_length = sum(hypot(dx, dy));
        if normalized_length > best_lengths(level_index)
            best_lengths(level_index) = normalized_length;
            best_points{level_index} = points;
        end
    end
    column = last_column + 1;
end

label_matrix = [];
for k = 1:numel(requested_levels)
    points = best_points{k};
    if isempty(points)
        continue;
    end
    label_matrix = [label_matrix, ... %#ok<AGROW>
        [requested_levels(k); size(points, 2)], points];
end
end

function value = nice_step(raw_value)
exponent = floor(log10(raw_value));
fraction = raw_value / 10^exponent;
if fraction <= 1
    nice_fraction = 1;
elseif fraction <= 2
    nice_fraction = 2;
elseif fraction <= 5
    nice_fraction = 5;
else
    nice_fraction = 10;
end
value = nice_fraction * 10^exponent;
end

function set_color_limits(ax, color_limits)
try
    clim(ax, color_limits);
catch
    caxis(ax, color_limits);
end
end

function ok = save_heatmap_figure_safe(fig, filename, logfid, target_size_bp)
if nargin < 4
    target_size_bp = [];
end
ok = false;
axes_handles = findall(fig, 'Type', 'axes');
for k = 1:numel(axes_handles)
    try
        axes_handles(k).Toolbar.Visible = 'off';
    catch
    end
end
drawnow;
if ~isempty(target_size_bp)
    try
        exportgraphics(fig, filename, ...
            'ContentType', 'image', ...
            'Resolution', 600, ...
            'BackgroundColor', 'white');
        log_line(logfid, ['saved near final paper size ', filename]);
        ok = true;
    catch err_size
        log_line(logfid, ['final-size image PDF export failed: ', ...
            err_size.message]);
    end
end
if ok
    return;
end
try
    exportgraphics(fig, filename, ...
        'ContentType', 'image', ...
        'Resolution', 600, ...
        'BackgroundColor', 'white');
    log_line(logfid, ['saved ', filename]);
    ok = true;
catch err
    log_line(logfid, ['image export failed: ', err.message]);
    ok = save_figure_safe(fig, filename, logfid);
end
end
