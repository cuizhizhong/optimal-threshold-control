close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('new');
ensure_output_dirs(cfg);

log_file = fullfile(cfg.paths.logs, 'generate_landscape_data.log');
logfid = fopen(log_file, 'w');
if logfid < 0
    error('Cannot open log file: %s', log_file);
end
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>
log_line(logfid, ['active run: ', cfg.paths.run_dir]);

rows = struct([]);
diagnostics = empty_diagnostic();
row_id = 0;

for j = 1:numel(cfg.c0_list)
    c0 = cfg.c0_list(j);
    for i = 1:numel(cfg.eta_list)
        row_id = row_id + 1;
        eta = cfg.eta_list(i);
        [row, row_diagnostics] = compute_metrics( ...
            cfg.beta, cfg.gamma, c0, cfg.q0, cfg.N, eta, cfg.S0, cfg.I0);
        rows = append_row(rows, row, row_id);
        diagnostics = append_diagnostics(diagnostics, row_diagnostics);
    end
end

landscape = struct2table(rows);
if any(strcmp('status_code', landscape.Properties.VariableNames))
    landscape.status_code = [];
end

landscape_file = fullfile(cfg.paths.output_csv, 'landscape_summary.csv');
writetable(landscape, landscape_file);
log_line(logfid, sprintf('wrote %s (%d rows)', landscape_file, height(landscape)));

eta_sensitivity = landscape(abs(landscape.c0 - cfg.c0_base) < 1e-10, :);
eta_sensitivity = sortrows(eta_sensitivity, 'eta_frac');
writetable(eta_sensitivity, fullfile(cfg.paths.output_csv, 'eta_sensitivity_c0_10.csv'));

c0_sensitivity = table();
for k = 1:numel(cfg.c0_response_eta_frac)
    sub = landscape(abs(landscape.eta_frac - cfg.c0_response_eta_frac(k)) < 1e-10, :);
    c0_sensitivity = [c0_sensitivity; sub]; %#ok<AGROW>
end
c0_sensitivity = sortrows(c0_sensitivity, {'eta_frac', 'c0'});
writetable(c0_sensitivity, fullfile(cfg.paths.output_csv, 'c0_sensitivity_selected_eta.csv'));

representative = table();
for e = [0.002, 0.010, 0.020]
    for c = cfg.selected_c0
        sub = landscape(abs(landscape.eta_frac - e) < 1e-10 & ...
            abs(landscape.c0 - c) < 1e-10, :);
        representative = [representative; sub]; %#ok<AGROW>
    end
end
representative = sortrows(representative, {'eta_frac', 'c0'});
writetable(representative, fullfile(cfg.paths.output_csv, 'representative_cases.csv'));

diagnostics = append_global_checks(diagnostics, landscape);
diagnostic_table = diagnostics_to_table(diagnostics);
writetable(diagnostic_table, fullfile(cfg.paths.output_csv, 'diagnostics.csv'));

valid_count = sum(logical(landscape.valid));
log_line(logfid, sprintf('valid rows: %d / %d', valid_count, height(landscape)));
log_line(logfid, sprintf('diagnostic rows: %d', height(diagnostic_table)));
log_line(logfid, 'data generation finished');

function rows = append_row(rows, row, row_id)
if row_id == 1
    rows = row;
else
    rows(row_id) = row;
end
end

function diagnostics = empty_diagnostic()
diagnostics = struct('eta_frac', {}, 'eta_percent', {}, 'eta', {}, ...
    'c0', {}, 'code', {}, 'message', {});
end

function diagnostics = append_diagnostics(diagnostics, new_diagnostics)
if isempty(new_diagnostics)
    return;
end
diagnostics = [diagnostics; new_diagnostics(:)];
end

function diagnostics = add_diagnostic(diagnostics, row, code, message)
item.eta_frac = row.eta_frac;
item.eta_percent = row.eta_percent;
item.eta = row.eta;
item.c0 = row.c0;
item.code = string(code);
item.message = string(message);
diagnostics = [diagnostics; item]; %#ok<AGROW>
end

function diagnostics = append_global_checks(diagnostics, T)
tol = 1e-7;
for k = 1:height(T)
    row = table_row_to_struct(T(k, :));
    if ~logical(row.valid)
        diagnostics = add_diagnostic(diagnostics, row, 'invalid_row', ...
            'Row is not valid in landscape summary.');
        continue;
    end
    if ~(row.I0 < row.eta && row.eta < row.Imax_pre)
        diagnostics = add_diagnostic(diagnostics, row, 'threshold_inequality_failed', ...
            'Expected I0 < eta < Imax_pre.');
    end
    if ~(row.S0 > row.S_star && row.S_star > row.S_c && row.S_c > row.S_bar)
        diagnostics = add_diagnostic(diagnostics, row, 'ordering_check_failed', ...
            'Expected S0 > S_star > S_c > S_bar.');
    end
    if row.Delta_t <= 0 || row.t_end <= row.t2
        diagnostics = add_diagnostic(diagnostics, row, 'time_ordering_failed', ...
            'Expected Delta_t > 0 and t_end > t2.');
    end
    if row.q_max > 1 + tol
        diagnostics = add_diagnostic(diagnostics, row, 'q_out_of_bounds', ...
            'q_max exceeds 1.');
    end
    if row.q_t2_error > tol
        diagnostics = add_diagnostic(diagnostics, row, 'q_t2_mismatch', ...
            'q_c(t2) is not close to q0.');
    end
    if row.cum_decomp_error > tol
        diagnostics = add_diagnostic(diagnostics, row, 'cumulative_mismatch', ...
            'Cumulative infection decomposition mismatch.');
    end
end
end

function T = diagnostics_to_table(diagnostics)
if isempty(diagnostics)
    T = table([], [], [], [], strings(0, 1), strings(0, 1), ...
        'VariableNames', {'eta_frac', 'eta_percent', 'eta', 'c0', 'code', 'message'});
else
    T = struct2table(diagnostics);
end
end

function log_line(logfid, message)
line = sprintf('[%s] %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), message);
fprintf('%s', line);
fprintf(logfid, '%s', line);
end
