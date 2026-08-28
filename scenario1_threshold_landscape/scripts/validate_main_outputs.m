% Numerical acceptance checks for the expanded main-paper landscape.

script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

[landscape, cfg] = read_landscape_table('current');
ensure_output_dirs(cfg);

logfid = open_log(cfg, 'validate_main_outputs.log');
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

expected_rows = numel(cfg.c0_list) * numel(cfg.eta_frac_list);
if height(landscape) ~= expected_rows
    error('validate_main_outputs:rowCount', ...
        'Expected %d rows, found %d.', expected_rows, height(landscape));
end

metric_fields = {'t1', 'Delta_t', 't_end', 'q_max', 'J', 'I_t_cum'};
valid_mask = logical(landscape.valid);
for k = 1:numel(metric_fields)
    values = landscape.(metric_fields{k})(valid_mask);
    if isempty(values) || any(~isfinite(values))
        error('validate_main_outputs:nonfiniteMetric', ...
            'Nonfinite valid values found in %s.', metric_fields{k});
    end
end

diagnostics = readtable(fullfile(cfg.paths.output_csv, 'diagnostics.csv'), ...
    'TextType', 'string');
allowed_codes = ["threshold_not_reached", "q_t2_mismatch"];
if ~isempty(diagnostics)
    unexpected = ~ismember(diagnostics.code, allowed_codes);
    if any(unexpected)
        codes = unique(diagnostics.code(unexpected));
        error('validate_main_outputs:unexpectedDiagnostics', ...
            'Unexpected diagnostic codes: %s', strjoin(cellstr(codes), ', '));
    end
end

eta_fracs = [0.002, 0.005, 0.010, 0.020, 0.050]';
expected_c0 = [4.29, 4.34, 4.42, 4.58, 5.07]';
expected_delta_t = [211.5, 84.0, 41.5, 20.3, 7.58]';
observed_c0 = nan(size(eta_fracs));
observed_delta_t = nan(size(eta_fracs));

for k = 1:numel(eta_fracs)
    sub = landscape(abs(landscape.eta_frac - eta_fracs(k)) < 1e-10 & ...
        logical(landscape.valid), :);
    [observed_delta_t(k), index] = max(sub.Delta_t);
    observed_c0(k) = sub.c0(index);
end

c0_error = abs(observed_c0 - expected_c0);
relative_delta_error = abs(observed_delta_t - expected_delta_t) ./ expected_delta_t;
peak_table = table(eta_fracs, expected_c0, observed_c0, c0_error, ...
    expected_delta_t, observed_delta_t, relative_delta_error);
writetable(peak_table, fullfile(cfg.paths.output_csv, 'peak_validation.csv'));

if any(c0_error > 0.06)
    error('validate_main_outputs:peakLocation', ...
        'At least one discrete peak location differs by more than 0.06.');
end
if any(relative_delta_error > 0.005)
    error('validate_main_outputs:peakHeight', ...
        'At least one peak height differs by more than 0.5%%.');
end

sanity = landscape(abs(landscape.c0 - 3.5) < 1e-10 & ...
    abs(landscape.eta_frac - 0.050) < 1e-10, :);
if height(sanity) ~= 1 || ~logical(sanity.valid(1)) || ...
        sanity.Delta_t(1) <= 0 || sanity.t2(1) <= sanity.t1(1)
    error('validate_main_outputs:sanityCase', ...
        'The c0=3.5, eta/N=5%% case is missing, invalid, or degenerate.');
end

expected_inflection = [false, true, true, true, true];
if numel(cfg.main_c0_values) ~= numel(expected_inflection)
    error('validate_main_outputs:inflectionConfig', ...
        'Expected %d main c0 values, found %d.', ...
        numel(expected_inflection), numel(cfg.main_c0_values));
end

for k = 1:numel(cfg.main_c0_values)
    row_table = landscape(abs(landscape.c0 - cfg.main_c0_values(k)) < 1e-10 & ...
        abs(landscape.eta_frac - cfg.main_c0_sweep_eta_frac) < 1e-10, :);
    row = table_row_to_struct(row_table);
    info = scenario1_inflection_point(row);
    if info.has_inflection ~= expected_inflection(k)
        error('validate_main_outputs:inflectionPresence', ...
            'Unexpected inflection status for c0=%.4g.', row.c0);
    end
    if info.has_inflection && abs(info.q_at_inf - info.q_inf) > 1e-10
        error('validate_main_outputs:inflectionValue', ...
            'q_c(t_inf) does not match q_inf for c0=%.4g.', row.c0);
    end
end

n_eta = numel(cfg.eta_frac_list);
n_c0 = numel(cfg.main_eta_sweep_c0_values);
delta_t_matrix = nan(n_eta, n_c0);
for k = 1:n_c0
    sub = landscape(abs(landscape.c0 - cfg.main_eta_sweep_c0_values(k)) < 1e-10, :);
    sub = sortrows(sub, 'eta_frac');
    if height(sub) ~= n_eta || any(~logical(sub.valid)) || ...
            any(abs(sub.eta_frac - cfg.eta_frac_list(:)) > 1e-10)
        error('validate_main_outputs:etaSweepCoverage', ...
            'c0=%.4g does not cover the full valid eta grid.', ...
            cfg.main_eta_sweep_c0_values(k));
    end
    if any(sub.q_max < 0.45) || any(sub.q_max > 0.85)
        error('validate_main_outputs:qMaxAxisRange', ...
            'q_max for c0=%.4g falls outside [0.45, 0.85].', ...
            cfg.main_eta_sweep_c0_values(k));
    end
    delta_t_matrix(:, k) = sub.Delta_t;
end
if any(any(diff(delta_t_matrix, 1, 2) >= 0))
    error('validate_main_outputs:etaSweepOrdering', ...
        'Selected c0 curves are not strictly ordered by Delta_t.');
end

log_line(logfid, sprintf('row count: %d', height(landscape)));
log_line(logfid, sprintf('valid rows: %d', sum(valid_mask)));
for k = 1:height(peak_table)
    log_line(logfid, sprintf( ...
        'eta/N=%.1f%%: peak c0=%.2f, Delta_t=%.4f', ...
        100 * peak_table.eta_fracs(k), peak_table.observed_c0(k), ...
        peak_table.observed_delta_t(k)));
end
log_line(logfid, sprintf( ...
    'figure 8 c0 curves: %s; full eta coverage and Delta_t ordering passed', ...
    strjoin(compose('%.0f', cfg.main_eta_sweep_c0_values), ', ')));
log_line(logfid, 'main-output numerical validation passed');
