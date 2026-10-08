function report = verify_numerical_preparation()
% 真实OpenOCL构建和初猜检查；只构建NLP，绝不调用solve。
cfg=numerical_cases_config();
addpath(cfg.paths.openocl_root,fullfile(cfg.paths.openocl_root,'Lib','casadi'));
% 已有CasADi先确认可用；禁止触发OpenOCL下载/初始化目录写入。
probe=casadi.SX.sym('preparation_probe'); clear probe;
oldSetup=getenv('OCL_CASADI_SETUP'); setenv('OCL_CASADI_SETUP','true');
cleanup=onCleanup(@() setenv('OCL_CASADI_SETUP',oldSetup)); %#ok<NASGU>
opts=cfg.solve; opts.T=1; opts.N=4;
guess=struct('type','constant_control','control',0.7);
prepared=prepare_openocl_case(cfg.parameters,cfg.cases(1).x0,opts,guess);
assert(numel(prepared.actual_grid.t_state)==5 && numel(prepared.actual_grid.t_control)==4);
assert(numel(prepared.actual_grid.t_integrator)==opts.N*opts.d);
assert(all(prepared.initial_guess.control==0.7));
assert(isequal(reshape(prepared.ig.controls.q.value,[],1),prepared.initial_guess.control));
assert(isequal(reshape(prepared.ig.states.S.value,[],1),prepared.initial_guess.node_states(:,1)));
assert(isequal(reshape(prepared.ig.integrator.states.I.value,[],1),prepared.initial_guess.integrator_states(:,2)));
assert(all(abs(prepared.actual_grid.dt_control-0.25)<1e-14));
assert(prepared.actual_solver_settings.casadi_options.ipopt.print_level==0 && ...
    prepared.actual_solver_settings.casadi_options.print_time==0);
source=numerical_code_hash('solve'); provenance=numerical_solve_provenance(cfg);
report=struct('passed',true,'optimizer_calls',0,'nlp_constructed',true, ...
    'T',opts.T,'N',opts.N,'d',opts.d,'actual_grid',prepared.actual_grid, ...
    'actual_solver_settings',prepared.actual_solver_settings, ...
    'initialization',prepared.initialization,'source_hash',source.hash, ...
    'environment',provenance.environment,'environment_fingerprint',provenance.environment_fingerprint, ...
    'checked_utc',numerical_utc());
clear prepared;
fprintf('NUMERICAL_PREPARATION_OK N=4 solver_calls=0 source_hash=%s\n',source.hash);
end
