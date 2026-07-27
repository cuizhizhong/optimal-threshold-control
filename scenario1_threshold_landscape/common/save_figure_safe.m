function ok = save_figure_safe(fig, filename, logfid)
%SAVE_FIGURE_SAFE Save a figure as PDF, with fallbacks for older MATLAB.
%   Tries exportgraphics (R2020a+) first; on older releases (e.g. R2018b,
%   which has no exportgraphics) it falls back to print -dpdf, and only
%   drops to PNG if every PDF path fails.

if nargin < 3
    logfid = [];
end

ok = false;
[folder, ~, ~] = fileparts(filename);
if ~exist(folder, 'dir')
    mkdir(folder);
end

set(fig, 'Color', 'w');
set(fig, 'PaperPositionMode', 'auto');
drawnow;

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
