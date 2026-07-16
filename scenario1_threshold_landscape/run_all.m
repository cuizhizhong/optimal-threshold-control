close all;

script_dir = fileparts(mfilename('fullpath'));
addpath(fullfile(script_dir, 'common'));
scripts_dir = fullfile(script_dir, 'scripts');

run_script(fullfile(scripts_dir, 'generate_landscape_data.m'));
cfg = scenario1_params('current');
ensure_output_dirs(cfg);

logfid = fopen(fullfile(cfg.paths.logs, 'run_all.log'), 'w');
if logfid < 0
    error('Cannot open run_all log file.');
end
cleanup_log = onCleanup(@() fclose(logfid)); %#ok<NASGU>

scripts = {
    'plot_baseline_validation.m'
    'plot_sensitivity_curves.m'
    'plot_heatmaps.m'
    'plot_duration_regions.m'
    'plot_representative_trajectories.m'
    'plot_cumulative_decomposition.m'
    'write_representative_tables.m'
};

for k = 1:numel(scripts)
    script_name = scripts{k};
    try
        fprintf('[%s] running %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), script_name);
        fprintf(logfid, '[%s] running %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), script_name);
        run_script(fullfile(scripts_dir, script_name));
        fprintf(logfid, '[%s] finished %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), script_name);
    catch err
        fprintf(2, '[%s] failed %s: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), ...
            script_name, err.message);
        fprintf(logfid, '[%s] failed %s: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), ...
            script_name, err.message);
    end
end

fprintf('Scenario 1 threshold landscape run finished:\n%s\n', cfg.paths.run_dir);
fprintf(logfid, 'run finished: %s\n', cfg.paths.run_dir);

function run_script(script_file)
run(script_file);
end
