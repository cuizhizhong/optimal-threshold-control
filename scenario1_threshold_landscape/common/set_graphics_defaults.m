function set_graphics_defaults()
%SET_GRAPHICS_DEFAULTS Use LaTeX interpreters and keep figures visible.

set(groot, 'defaultTextInterpreter', 'latex');
set(groot, 'defaultAxesTickLabelInterpreter', 'latex');
set(groot, 'defaultLegendInterpreter', 'latex');
set(groot, 'defaultFigureVisible', 'on');
end
