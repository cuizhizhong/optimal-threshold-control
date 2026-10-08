function report = verify_neutral_initialization()
% 合成记录只测试比较器，不依赖历史实验，也不启动优化器。
cfg=numerical_cases_config();
main=struct('solver_settings',struct('T',300,'N',8000,'d',2,'initialization','analytic_reference'), ...
    'actual_solver_settings',struct('T',300,'N',8000,'d',2,'tol',1e-9), ...
    'actual_grid',struct('t_state',[0;1;300],'t_control',[0;1]), ...
    'parameters',cfg.parameters,'x0',[.99;.01],'success',true,'J_openocl',2, ...
    'initialization',struct('type','analytic_reference'), ...
    'assessment',struct('numeric_pass',true,'agreement_pass',true,'observed_structure','0 -> q_B -> 1 -> 0'));
neutral=main; neutral.initialization=struct('type','constant_control','control',cfg.check.neutral_control);
neutral.solver_settings.initialization='constant_control';
r=compare_neutral_initialization(main,neutral,cfg.check); assert(r.passed && r.agreement_pass);
tests={'matching_problem_and_accepted_synthetic_outputs'};
r=compare_neutral_initialization(main,[],cfg.check); assert(strcmp(r.status,'missing'));
b=rmfield(neutral,'assessment'); r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && strcmp(r.status,'incomplete'));
b=neutral; b.assessment=rmfield(b.assessment,'numeric_pass');
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && strcmp(r.status,'incomplete'));
tests{end+1}='missing_and_legacy_assessments_rejected';
b=neutral; b.success=false; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
b=neutral; b.assessment.numeric_pass=false; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
b=main; b.assessment.numeric_pass=false; r=compare_neutral_initialization(b,neutral,cfg.check); assert(~r.passed);
tests{end+1}='both_outputs_need_numeric_acceptance';
b=neutral; b.J_openocl=main.J_openocl+2*cfg.check.neutral_cost_tolerance;
r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed);
tests{end+1}='predeclared_absolute_cost_tolerance';
b=neutral; b.solver_settings.N=4000; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.same_problem);
b=neutral; b.actual_solver_settings.tol=1e-8; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.same_problem);
b=neutral; b.actual_grid.t_state(2)=2; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.same_problem);
tests{end+1}='actual_options_grid_and_requested_settings_compared';
b=neutral; b.initialization.type='analytic_reference'; r=compare_neutral_initialization(main,b,cfg.check); assert(~r.passed && ~r.initialization_valid);
tests{end+1}='neutral_guess_definition_checked';
b=neutral; b.assessment.observed_structure='1 -> 0'; b.assessment.agreement_pass=false;
r=compare_neutral_initialization(main,b,cfg.check); assert(r.passed && ~r.agreement_pass && ~r.structure_matches);
tests{end+1}='theory_disagreement_is_independent_of_initialization_numeric_comparison';
report=struct('passed',true,'tests',{tests},'required_tests_passed',numel(tests),'actual_optimizer_calls',0);
fprintf('NEUTRAL_INITIALIZATION_CHECKS_OK tests=%d actual_optimizer=0\n',numel(tests));
end
