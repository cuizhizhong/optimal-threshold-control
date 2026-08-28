function style = scenario1_main_plot_style(ax)
%SCENARIO1_MAIN_PLOT_STYLE Journal-style settings for main-paper figures.

style.font_name = 'Times New Roman';
style.font_size = 7.5;
style.label_size = 8;
style.title_size = 8;
style.legend_size = 7;
style.panel_size = 8;
style.annotation_size = 7.5;
style.contour_label_size = 7;
style.axes_width = 0.7;
style.line_width = 1.3;
style.reference_width = 0.8;
style.marker_size = 4.5;
style.text_width_bp = 451.28;
style.trajectory_size_bp = [ ...
    0.72 * style.text_width_bp, ...
    0.72 * style.text_width_bp * 347 / 487];
% Fig 7/8: compact, slightly portrait multi-panel (each subplot smaller and
% taller). Fig 9: full width but sized so each heatmap panel renders square
% (each axes also uses pbaspect([1 1 1])).
style.sensitivity_size_bp = [ ...
    0.80 * style.text_width_bp, ...
    0.80 * style.text_width_bp * 0.80];
style.heatmap_size_bp = [ ...
    style.text_width_bp, ...
    style.text_width_bp * 0.78];
style.blues = [
    198 219 239
    158 202 225
    107 174 214
     49 130 189
      8  81 156
] / 255;
style.q_inf = [66 146 198] / 255;
style.accent = [178 24 43] / 255;
style.gray = [0.35 0.35 0.35];
style.light_gray = [0.55 0.55 0.55];

if nargin < 1 || isempty(ax)
    return;
end

set(ax, 'FontName', style.font_name, ...
    'FontSize', style.font_size, ...
    'LineWidth', style.axes_width, ...
    'TickDir', 'out', ...
    'Layer', 'top');
box(ax, 'off');
grid(ax, 'off');
end
