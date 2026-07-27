function cfg = scenario1_params(~)
%SCENARIO1_PARAMS Shared scenario-one parameters and fixed output paths.
%   An optional mode argument is accepted for backward compatibility and is
%   ignored; all results are written under current_run/. To keep an old run,
%   copy current_run/ aside manually before rerunning.

base_dir = fileparts(fileparts(mfilename('fullpath')));
run_dir = fullfile(base_dir, 'current_run');

cfg.beta = 0.155;
cfg.gamma = 0.3504;
cfg.q0 = 0.01526;
cfg.N = 763;
cfg.S0 = 762;
cfg.I0 = 1;
cfg.c0_base = 10;

cfg.eta_frac_list = 0.002:0.0002:0.020;
cfg.eta_list = cfg.eta_frac_list * cfg.N;
cfg.eta_percent_list = 100 * cfg.eta_frac_list;
cfg.c0_list = 6:0.1:14;

cfg.selected_eta_frac = [0.002, 0.005, 0.010, 0.020];
cfg.c0_response_eta_frac = [0.002, 0.010, 0.020];
cfg.selected_c0 = [6, 10, 14];
cfg.baseline_eta_frac = [0.020, 0.002];

cfg.paths.base_dir = base_dir;
cfg.paths.run_dir = run_dir;
cfg.paths.output_csv = fullfile(run_dir, 'output_csv');
cfg.paths.figures = fullfile(run_dir, 'figures');
cfg.paths.tables = fullfile(run_dir, 'tables');
cfg.paths.logs = fullfile(run_dir, 'logs');
end
