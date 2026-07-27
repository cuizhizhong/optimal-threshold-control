close all;

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params();
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

diagnostic_table = diagnostics_to_table(diagnostics);
writetable(diagnostic_table, fullfile(cfg.paths.output_csv, 'diagnostics.csv'));

valid_count = sum(logical(landscape.valid));
log_line(logfid, sprintf('valid rows: %d / %d', valid_count, height(landscape)));
log_line(logfid, sprintf('diagnostic rows: %d', height(diagnostic_table)));
log_line(logfid, 'data generation finished');

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

function T = diagnostics_to_table(diagnostics)
if isempty(diagnostics)
    T = table([], [], [], [], strings(0, 1), strings(0, 1), ...
        'VariableNames', {'eta_frac', 'eta_percent', 'eta', 'c0', 'code', 'message'});
else
    T = struct2table(diagnostics);
end
end
