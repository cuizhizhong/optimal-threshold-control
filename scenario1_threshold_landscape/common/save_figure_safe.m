function ok = save_figure_safe(fig, filename, logfid, target_size_bp)
%SAVE_FIGURE_SAFE Save a figure as PDF, with fallbacks for older MATLAB.
%   When a target size is supplied, first uses print -dpdf to preserve the
%   requested MediaBox. Otherwise it tries exportgraphics (R2020a+) first.
%   It only drops to PNG if every PDF path fails.

if nargin < 3
    logfid = [];
end
if nargin < 4
    target_size_bp = [];
end

ok = false;
[folder, ~, ~] = fileparts(filename);
if ~exist(folder, 'dir')
    mkdir(folder);
end

set(fig, 'Color', 'w');
set(fig, 'PaperPositionMode', 'auto');
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
        set(fig, ...
            'PaperUnits', 'points', ...
            'PaperSize', target_size_bp, ...
            'PaperPosition', [0, 0, target_size_bp], ...
            'PaperPositionMode', 'manual', ...
            'Renderer', 'painters');
        print(fig, filename, '-dpdf', '-painters');
        log_line(logfid, ['saved at final paper size ', filename]);
        ok = true;
    catch err_size
        log_line(logfid, ['final-size PDF export failed: ', err_size.message]);
    end
end

if ok
    return;
end

try
    exportgraphics(fig, filename, 'ContentType', 'vector', 'BackgroundColor', 'white');
    log_line(logfid, ['saved ', filename]);
    ok = true;
catch err0
    log_line(logfid, ['exportgraphics unavailable: ', err0.message]);
end

if ok
    return;
end

try
    set(fig, 'Renderer', 'painters');
    print(fig, filename, '-dpdf', '-painters', '-r200', '-bestfit');
    log_line(logfid, ['saved ', filename]);
    ok = true;
catch err1
    log_line(logfid, ['PDF painters failed: ', err1.message]);
    try
        set(fig, 'Renderer', 'opengl');
        print(fig, filename, '-dpdf', '-opengl', '-r200', '-bestfit');
        log_line(logfid, ['saved ', filename]);
        ok = true;
    catch err2
        log_line(logfid, ['PDF opengl failed: ', err2.message]);
        png_file = regexprep(filename, '\.pdf$', '.png', 'ignorecase');
        try
            print(fig, png_file, '-dpng', '-r200');
            log_line(logfid, ['saved fallback ', png_file]);
            ok = true;
        catch err3
            log_line(logfid, ['PNG fallback failed: ', err3.message]);
        end
    end
end
end
