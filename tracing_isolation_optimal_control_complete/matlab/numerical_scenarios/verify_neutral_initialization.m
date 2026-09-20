function verify_neutral_initialization()
% 对保存的真实实验验证通过分支，并检查错误设置和失败状态不能冒充一致。
cfg=numerical_cases_config();
d=load(fullfile(cfg.paths.data,'E2.mat'),'run'); main=d.run;
d=load(fullfile(cfg.paths.data,'checks','neutral_E2','E2.mat'),'run'); neutral=d.run;
r=compare_neutral_initialization(main,neutral,cfg.check); assert(r.passed);
r=compare_neutral_initialization(main,[],cfg.check); assert(strcmp(r.status,'missing'));
b=rmfield(neutral,'assessment'); r=compare_neutral_initialization(main,b,cfg.check);
assert(~r.passed && strcmp(r.status,'incomplete'));
b=neutral; b.success=false; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
b=neutral; b.assessment.capacity_excess=2e-6; b.assessment.passed=false;
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
b=neutral; b.J_openocl=main.J_openocl+2*cfg.check.neutral_cost_tolerance;
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
b=neutral; b.solver_settings.N=4000;
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.same_problem);
b=neutral; b.initialization.type='analytic_reference';
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.initialization_valid);
b=neutral; b.assessment.observed_structure='1 -> 0';
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.structure_matches);
fprintf('NEUTRAL_INITIALIZATION_CHECKS_OK\n');
end
