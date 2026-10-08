function cfg = numerical_cases_config(inputPath)
% 统一参数、初值及求解设置；配置函数不运行优化，也不包含实际实验结果。

here = fileparts(mfilename('fullpath'));
reportRoot = fileparts(fileparts(here));
repoRoot = fileparts(reportRoot);

if nargin < 1 || isempty(inputPath)
    inputPath = fullfile(reportRoot, 'validation', 'numerical_scenarios', 'scenario_inputs.json');
end
assert(isfile(inputPath), 'numerical_cases_config:MissingInputs', ...
    'Missing shared scenario inputs: %s', inputPath);
inputs = jsondecode(fileread(inputPath));
assert(inputs.schema_version == 1, 'Unsupported scenario input schema.');
cfg.parameters = inputs.parameters;
assert(cfg.parameters.p > 0 && cfg.parameters.p < 1 && ...
    all([cfg.parameters.c cfg.parameters.gamma cfg.parameters.K] > 0), ...
    'Invalid model parameters in %s.', inputPath);
cfg.paths.repo_root = repoRoot;
cfg.paths.report_root = reportRoot;
cfg.paths.openocl_root = fullfile(repoRoot, 'optimal', 'OpenOCL-master 0104');
% 非空环境变量覆盖候选默认路径；配置本身不加载求解器。
openoclRoot = getenv('OPENOCL_ROOT');
if ~isempty(strtrim(openoclRoot)), cfg.paths.openocl_root = openoclRoot; end
cfg.paths.data = fullfile(reportRoot, 'data', 'numerical_scenarios');
cfg.paths.figures = fullfile(reportRoot, 'figures', 'numerical_scenarios');
cfg.paths.latex = fullfile(reportRoot, 'latex');
cfg.paths.scenario_inputs = inputPath;
cfg.paths.analytic_checkpoints = fullfile(reportRoot, 'validation', ...
    'numerical_scenarios', 'analytic_checkpoints.json');

% 长时域截断设置。主 OCP 不施加终端状态约束或终端成本。
cfg.solve.T = 300;
cfg.solve.N = 4000;
cfg.solve.d = 2;
cfg.solve.controls_regularization = false;
cfg.solve.terminal_constraint = 'none';
cfg.solve.initialization = 'analytic_reference';
cfg.solve.casadi_options.ipopt.tol = 1e-9;
cfg.solve.casadi_options.ipopt.constr_viol_tol = 1e-9;
cfg.solve.casadi_options.ipopt.max_iter = 5000;
% 沿用 IPOPT 默认边界松弛，结果按原始模型的边界容差另行核查。
cfg.solve.casadi_options.ipopt.bound_relax_factor = 1e-8;

% Original script settings for a separate baseline regression only.
cfg.original_baseline = struct('T', 300, 'N', 4000, 'd', 2);

cfg.plot.waiting_tmax = 18;
cfg.plot.tracking_boundary_tmax = 8;
cfg.plot.reference_samples = 6001;

% Internal diagnostic targets, NOT measured errors or rigorous bounds.
cfg.check.state_tolerance = 1e-6;
cfg.check.capacity_tolerance = 1e-6;
cfg.check.control_tolerance = 1e-6;
cfg.check.tail_duration = 20;
cfg.check.tail_control_tolerance = 1e-6;
cfg.check.event_control_threshold = 1e-3;
% 阶段识别阈值与连续容量验收容差分开：平台离散节点略低于 K。
cfg.check.event_capacity_threshold = 2e-5;
cfg.check.ode_rel_tol = 2e-10;
cfg.check.ode_abs_tol = 1e-12;
cfg.check.refine_case_id = 'E2';
cfg.check.refine_N = 8000;
cfg.check.neutral_guess_case_id = 'E1';
cfg.check.neutral_control = 0.7;
cfg.check.neutral_cost_tolerance = 1e-5;

records = inputs.cases;
assert(isstruct(records) && numel(unique({records.case_id})) == numel(records), ...
    'Missing or duplicated case_id in shared inputs.');
mainIds = cellstr(inputs.main_case_ids);
requiredIds = [mainIds(:); {inputs.safe_case_id}];
assert(numel(unique(requiredIds)) == numel(requiredIds) && ...
    isequal(sort({records.case_id}'), sort(requiredIds)), ...
    'Shared input case IDs must match main_case_ids and safe_case_id.');
for k = 1:numel(mainIds)
    item = readCase(records, mainIds{k});
    if k == 1, cfg.cases = item; else, cfg.cases(k) = item; end
end
cfg.safe_check = readCase(records, inputs.safe_case_id);
cfg.run_order = cellstr(inputs.run_order)';
assert(isequal(sort(cfg.run_order(:)), sort(mainIds(:))), ...
    'run_order must contain every main case exactly once.');
cfg.status = 'configured';

for k = 1:numel(cfg.cases)
    x0 = cfg.cases(k).x0;
    assert(all(isfinite(x0)) && all(x0 > 0) && ...
        x0(2) <= cfg.parameters.K && sum(x0) <= 1 + 1e-12, ...
        'Invalid initial condition in case %s.', cfg.cases(k).id);
end
end

function out = readCase(records, id)
index = find(strcmp({records.case_id}, id));
assert(isscalar(index), 'Expected exactly one input case %s.', id);
row = records(index);
out = struct('id', id, 'x0', [row.s0; row.i0], ...
    'expected_region', row.expected_region, 'expected_structure', row.expected_structure, ...
    'include_in_main_figures', row.include_in_main_figures, 'main_N', row.main_N);
assert(isfinite(out.main_N) && out.main_N > 0 && fix(out.main_N) == out.main_N, ...
    'Invalid predefined main_N for %s.', id);
% Do not add observed_structure or an objective value before solving.
end
