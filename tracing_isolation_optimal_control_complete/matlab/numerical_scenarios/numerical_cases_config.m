function cfg = numerical_cases_config()
% 统一参数、初值及求解设置；配置函数不运行优化，也不包含实际实验结果。

here = fileparts(mfilename('fullpath'));
reportRoot = fileparts(fileparts(here));
repoRoot = fileparts(reportRoot);

cfg.parameters = struct('p', 0.5, 'c', 2.0, 'gamma', 0.3, 'K', 0.15);
cfg.paths.repo_root = repoRoot;
cfg.paths.report_root = reportRoot;
cfg.paths.openocl_root = fullfile(repoRoot, 'optimal', 'OpenOCL-master 0104');
cfg.paths.data = fullfile(reportRoot, 'data', 'numerical_scenarios');
cfg.paths.figures = fullfile(reportRoot, 'figures', 'numerical_scenarios');
cfg.paths.latex = fullfile(reportRoot, 'latex');

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

cfg.cases = [ ...
    makeCase('E1', [0.75; 0.01], 'W_Gamma', '0 -> 1 -> 0', true), ...
    makeCase('E2', [0.99; 0.01], 'W_K', '0 -> q_B -> 1 -> 0', true), ...
    makeCase('E3', [0.50; 0.14], 'T', '1 -> 0', true), ...
    makeCase('E4', [0.70; 0.15], 'B', 'q_B -> 1 -> 0', true), ...
    makeCase('E5', [0.50; 0.15], 'T', '1 -> 0', true) ...
    ];
cfg.safe_check = makeCase('E0', [0.40; 0.02], 'A', '0', false);
cfg.run_order = {'E2', 'E1', 'E4', 'E5', 'E3'};
cfg.status = 'configured';

for k = 1:numel(cfg.cases)
    x0 = cfg.cases(k).x0;
    assert(all(isfinite(x0)) && all(x0 > 0) && ...
        x0(2) <= cfg.parameters.K && sum(x0) <= 1 + 1e-12, ...
        'Invalid initial condition in case %s.', cfg.cases(k).id);
end
end

function out = makeCase(id, x0, region, structure, mainFigure)
out = struct('id', id, 'x0', x0, ...
    'expected_region', region, 'expected_structure', structure, ...
    'include_in_main_figures', mainFigure);
% Do not add observed_structure or an objective value before solving.
end
