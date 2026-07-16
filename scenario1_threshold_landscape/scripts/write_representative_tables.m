script_dir = fileparts(mfilename('fullpath'));
base_dir = fileparts(script_dir);
addpath(fullfile(base_dir, 'common'));

cfg = scenario1_params('current');
ensure_output_dirs(cfg);

logfid = fopen(fullfile(cfg.paths.logs, 'write_representative_tables.log'), 'w');
if logfid < 0
    error('Cannot open log file.');
end
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

T = readtable(fullfile(cfg.paths.output_csv, 'representative_cases.csv'));
write_latex_tables('representative', T, ...
    fullfile(cfg.paths.tables, 'representative_cases_table.tex'));
fprintf(logfid, 'representative table finished\n');
