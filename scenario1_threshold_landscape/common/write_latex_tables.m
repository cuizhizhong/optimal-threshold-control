function write_latex_tables(kind, data, filename)
%WRITE_LATEX_TABLES Write compact LaTeX tables for the active run.

[folder, ~, ~] = fileparts(filename);
if ~exist(folder, 'dir')
    mkdir(folder);
end

fid = fopen(filename, 'w');
if fid < 0
    error('Cannot open %s.', filename);
end
cleaner = onCleanup(@() fclose(fid)); %#ok<NASGU>

switch lower(string(kind))
    case "baseline"
        write_baseline(fid, data);
    case "representative"
        write_representative(fid, data);
    case "main_c0"
        write_main_c0(fid, data);
    case "main_eta"
        write_main_eta(fid, data);
    otherwise
        error('Unknown table kind: %s', kind);
end
end

function write_baseline(fid, rows)
fprintf(fid, '\\begin{tabular}{ccccccccccccc}\n');
fprintf(fid, '\\toprule\n');
fprintf(fid, ['$c_0$ & $\\eta/N$ & $S^*$ & $S_c$ & $t_1$ & ', ...
    '$t_2$ & $\\Delta t$ & $t_{\\rm end}$ & $q_{\\max}$ & ', ...
    '$q_{\\rm mean}$ & $J$ & $I_{t_{\\rm cum}}$ & $\\max|I-\\eta|$ \\\\\n']);
fprintf(fid, '\\midrule\n');
for k = 1:numel(rows)
    fprintf(fid, ['%.0f & %.1f\\%% & %.4f & %.4f & %.4f & %.4f & ', ...
        '%.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.2e \\\\\n'], ...
        rows(k).c0, rows(k).eta_percent, rows(k).S_star, rows(k).S_c, ...
        rows(k).t1, rows(k).t2, rows(k).Delta_t, rows(k).t_end, ...
        rows(k).q_max, rows(k).q_mean, rows(k).J, rows(k).I_t_cum, ...
        rows(k).platform_error);
end
fprintf(fid, '\\bottomrule\n');
fprintf(fid, '\\end{tabular}\n');
end

function write_main_c0(fid, T)
fprintf(fid, '\\begin{tabular}{ccccccccc}\n');
fprintf(fid, '\\toprule\n');
fprintf(fid, ['$c_0$ & $S^*$ & $S_c$ & $t_1$ & $\\Delta t$ & ', ...
    '$t_{\\rm end}$ & $q_{\\max}$ & $J$ & $I_{t_{\\rm cum}}$ \\\\\n']);
fprintf(fid, '\\midrule\n');
for k = 1:height(T)
    fprintf(fid, ['%.4g & %.4f & %.4f & %.4f & %.4f & %.4f & ', ...
        '%.4f & %.4f & %.4f \\\\\n'], ...
        T.c0(k), T.S_star(k), T.S_c(k), T.t1(k), T.Delta_t(k), ...
        T.t_end(k), T.q_max(k), T.J(k), T.I_t_cum(k));
end
fprintf(fid, '\\bottomrule\n');
fprintf(fid, '\\end{tabular}\n');
end

function write_main_eta(fid, T)
fprintf(fid, '\\begin{tabular}{cccccccccc}\n');
fprintf(fid, '\\toprule\n');
fprintf(fid, ['$\\eta$ & $\\eta/N$ & $S^*$ & $S_c$ & $t_1$ & ', ...
    '$\\Delta t$ & $t_{\\rm end}$ & $q_{\\max}$ & $J$ & ', ...
    '$I_{t_{\\rm cum}}$ \\\\\n']);
fprintf(fid, '\\midrule\n');
for k = 1:height(T)
    fprintf(fid, ['%.4g & %.4g & %.4f & %.4f & %.4f & %.4f & ', ...
        '%.4f & %.4f & %.4f & %.4f \\\\\n'], ...
        T.eta(k), T.eta_frac(k), T.S_star(k), T.S_c(k), ...
        T.t1(k), T.Delta_t(k), T.t_end(k), T.q_max(k), ...
        T.J(k), T.I_t_cum(k));
end
fprintf(fid, '\\bottomrule\n');
fprintf(fid, '\\end{tabular}\n');
end

function write_representative(fid, T)
fprintf(fid, '\\begin{tabular}{cccccccc}\n');
fprintf(fid, '\\toprule\n');
fprintf(fid, ['$\\eta/N$ & $c_0$ & $t_1$ & $\\Delta t$ & ', ...
    '$t_{\\rm end}$ & $q_{\\max}$ & $J$ & $I_{t_{\\rm cum}}$ \\\\\n']);
fprintf(fid, '\\midrule\n');
for k = 1:height(T)
    fprintf(fid, '%.1f\\%% & %.0f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n', ...
        T.eta_percent(k), T.c0(k), T.t1(k), T.Delta_t(k), ...
        T.t_end(k), T.q_max(k), T.J(k), T.I_t_cum(k));
end
fprintf(fid, '\\bottomrule\n');
fprintf(fid, '\\end{tabular}\n');
end
