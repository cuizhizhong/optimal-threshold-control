% Main-paper c0 and eta summary tables from the shared metric engine.

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('current');
ensure_output_dirs(cfg);

logfid = open_log(cfg, 'write_main_summary_tables.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

c0_min = critical_c0_for_eta(cfg.beta, cfg.gamma, cfg.q0, cfg.N, ...
    cfg.main_c0_sweep_eta_frac * cfg.N, cfg.S0, cfg.I0);
c0_values = [c0_min + 0.02, cfg.main_c0_values];
c0_rows = struct([]);
for k = 1:numel(c0_values)
    [row, diagnostics] = compute_metrics( ...
        cfg.beta, cfg.gamma, c0_values(k), cfg.q0, cfg.N, ...
        cfg.main_c0_sweep_eta_frac * cfg.N, cfg.S0, cfg.I0);
    require_valid(row, diagnostics, 'c0', c0_values(k));
    c0_rows = append_row(c0_rows, row, k);
end
c0_table = struct2table(c0_rows);
writetable(c0_table, fullfile(cfg.paths.output_csv, 'main_c0_summary.csv'));
write_latex_tables('main_c0', c0_table, ...
    fullfile(cfg.paths.tables, 'scenario1_c0_summary_table.tex'));

eta_rows = struct([]);
for k = 1:numel(cfg.main_eta_frac_values)
    eta_frac = cfg.main_eta_frac_values(k);
    [row, diagnostics] = compute_metrics( ...
        cfg.beta, cfg.gamma, cfg.main_eta_sweep_c0, cfg.q0, cfg.N, ...
        eta_frac * cfg.N, cfg.S0, cfg.I0);
    require_valid(row, diagnostics, 'eta_frac', eta_frac);
    eta_rows = append_row(eta_rows, row, k);
end
eta_table = struct2table(eta_rows);
writetable(eta_table, fullfile(cfg.paths.output_csv, 'main_eta_summary.csv'));
write_latex_tables('main_eta', eta_table, ...
    fullfile(cfg.paths.tables, 'scenario1_eta_summary_table.tex'));

log_line(logfid, sprintf('main c0 table rows: %d', height(c0_table)));
log_line(logfid, sprintf('main eta table rows: %d', height(eta_table)));
log_line(logfid, 'main-paper summary tables finished');

function require_valid(row, diagnostics, parameter_name, parameter_value)
if logical(row.valid)
    return;
end
message = 'unknown diagnostic';
if ~isempty(diagnostics)
    message = char(diagnostics(1).message);
end
error('write_main_summary_tables:invalidCase', ...
    'Invalid %s=%.10g (%s).', parameter_name, parameter_value, message);
end
