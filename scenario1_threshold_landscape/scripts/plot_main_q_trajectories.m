% Main-paper q_c(t) trajectories for c0 and eta comparisons.

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);
set_graphics_defaults();

logfid = open_log(cfg, 'plot_main_q_trajectories.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

c0_rows = fetch_rows(landscape, cfg.main_c0_values, ...
    cfg.main_c0_sweep_eta_frac, 'c0');
plot_q_family(c0_rows, 'c0', ...
    fullfile(cfg.paths.figures, 'scenario1_u_time_c0.pdf'), logfid);

eta_rows = fetch_rows(landscape, cfg.main_eta_frac_values, ...
    cfg.main_eta_sweep_c0, 'eta');
plot_q_family(eta_rows, 'eta', ...
    fullfile(cfg.paths.figures, 'scenario1_u_time_eta.pdf'), logfid);

log_line(logfid, 'main-paper q_c trajectories finished');

function rows = fetch_rows(landscape, values, fixed_value, sweep_name)
rows = struct([]);
for k = 1:numel(values)
    if strcmp(sweep_name, 'c0')
        sub = landscape(abs(landscape.c0 - values(k)) < 1e-10 & ...
            abs(landscape.eta_frac - fixed_value) < 1e-10, :);
    else
        sub = landscape(abs(landscape.c0 - fixed_value) < 1e-10 & ...
            abs(landscape.eta_frac - values(k)) < 1e-10, :);
    end
    if height(sub) ~= 1 || ~logical(sub.valid(1))
        error('plot_main_q_trajectories:missingCase', ...
            'Expected one valid %s case for value %.8g.', sweep_name, values(k));
    end
    rows = append_row(rows, table_row_to_struct(sub), k);
end
end

function plot_q_family(rows, sweep_name, filename, logfid)
style = scenario1_main_plot_style();
fig = figure('Units', 'points', ...
    'Position', [120, 100, style.trajectory_size_bp], ...
    'Color', 'w', 'Visible', 'on');
ax = axes(fig);
hold(ax, 'on');
scenario1_main_plot_style(ax);

n_rows = numel(rows);
color_index = round(linspace(1, size(style.blues, 1), n_rows));
colors = style.blues(color_index, :);
x_max = max([rows.t2] + 0.08 * [rows.Delta_t]);
y_max = min(1, 1.08 * max([rows.q_max]) + 0.02);

q0_handle = plot(ax, [0, x_max], [rows(1).q0, rows(1).q0], '--', ...
    'Color', style.gray, ...
    'LineWidth', style.reference_width);
q_inf = 1 - 1 / (2 * (1 - rows(1).beta));
qinf_handle = plot(ax, [0, x_max], [q_inf, q_inf], ':', ...
    'Color', style.q_inf, ...
    'LineWidth', 1.2);

curve_handles = gobjects(n_rows, 1);
curve_labels = cell(n_rows, 1);
for k = 1:n_rows
    row = rows(k);
    tau = linspace(0, row.Delta_t, max(350, ceil(12 * row.Delta_t)));
    t = row.t1 + tau;
    q = q_control_tau(row, tau);

    if strcmp(sweep_name, 'c0')
        curve_labels{k} = sprintf('$c_0=%s$', compact_number(row.c0));
    else
        curve_labels{k} = sprintf('$\\eta/N=%s\\%%$', ...
            compact_number(row.eta_percent));
    end

    curve_handles(k) = plot(ax, t, q, '-', ...
        'Color', colors(k, :), ...
        'LineWidth', style.line_width);
    plot(ax, row.t1, row.q_max, '^', ...
        'Color', colors(k, :), ...
        'MarkerFaceColor', 'w', ...
        'MarkerSize', style.marker_size, ...
        'LineWidth', style.reference_width, ...
        'HandleVisibility', 'off');
    plot(ax, row.t2, row.q0, '|', ...
        'Color', colors(k, :), ...
        'MarkerSize', 7, ...
        'LineWidth', 1.2, ...
        'HandleVisibility', 'off');

    info = scenario1_inflection_point(row);
    if info.has_inflection
        plot(ax, info.t_inf, info.q_at_inf, 'o', ...
            'Color', 'w', ...
            'MarkerFaceColor', style.accent, ...
            'MarkerSize', style.marker_size, ...
            'LineWidth', 0.7, ...
            'HandleVisibility', 'off');
    end
end

xlabel(ax, '$t$ (days)', 'FontName', style.font_name, ...
    'FontSize', style.label_size);
ylabel(ax, '$q_c(t)$', 'FontName', style.font_name, ...
    'FontSize', style.label_size);
if strcmp(sweep_name, 'c0')
    title(ax, sprintf('$\\eta/N=%s\\%%$', ...
        compact_number(rows(1).eta_percent)), ...
        'FontName', style.font_name, 'FontSize', style.title_size);
else
    title(ax, sprintf('$c_0=%s$', compact_number(rows(1).c0)), ...
        'FontName', style.font_name, 'FontSize', style.title_size);
end
xlim(ax, [0, x_max]);
ylim(ax, [0, y_max]);

legend_handles = [curve_handles; qinf_handle; q0_handle];
legend_labels = [curve_labels; {'$q_{\rm inf}$'; '$q_0$'}];
lgd = legend(ax, legend_handles, legend_labels, ...
    'Location', 'northeast', ...
    'Interpreter', 'latex', ...
    'FontSize', style.legend_size);
set(lgd, 'Box', 'off');

save_figure_safe(fig, filename, logfid, style.trajectory_size_bp);
close(fig);
end

function text_value = compact_number(value)
if abs(value - round(value)) < 1e-10
    text_value = sprintf('%.0f', value);
else
    text_value = sprintf('%.1f', value);
end
end
