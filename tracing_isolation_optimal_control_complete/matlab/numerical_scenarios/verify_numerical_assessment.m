function report = verify_numerical_assessment()
% 合成原控制轨道回归，不调用优化器，不把合成数据当作主算例结果。
cfg=numerical_cases_config(); par=cfg.parameters; opts=cfg.check; opts.tail_duration=.2;
base=synthetic([0;.1;.4;1],[0;0;0],[.2;.01],par);
g=build_theory_geometry(par); ref=analytic_reference(par,base.x0,g,base.t_state);
a=assess_numerical_case(base,ref,par,opts);
assert(a.numeric_pass && a.agreement_pass && strcmp(a.cost_agreement.mode,'absolute_zero_cost'));
tests={'safe_zero_cost_absolute_test'};

r=synthetic([0;.1;.4;1],[.5;0;0],base.x0,par);
a=assess_numerical_case(r,ref,par,opts);
assert(a.numeric_pass && ~a.agreement_pass && abs(a.J_reintegrated_control-.05)<1e-14);
assert(strcmp(a.state_discrepancy_definition,'collocation_node_states_vs_original_control_reintegration'));
tests{end+1}='numeric_acceptance_independent_of_theory_and_weighted_cost';

different=ref; different.J_reference=1;
b=assess_numerical_case(base,different,par,opts);
assert(b.numeric_pass && ~b.agreement_pass && strcmp(b.status,'unresolved_discrepancy'));
tests{end+1}='lower_cost_unresolved_is_retained';

bad=r; bad.t_control(2)=.11;
expectError(@() assess_numerical_case(bad,ref,par,opts),'numerical:GridEndpoints');
bad=r; bad.dt_control(2)=.5;
expectError(@() validate_numerical_run_grid(bad,opts),'numerical:ControlDurations');
bad=r; bad.s_state=bad.s_state(1:end-1);
expectError(@() validate_numerical_run_grid(bad,opts),'numerical:ArrayDimensions');
tests{end+1}='actual_grid_and_array_dimensions_checked_before_reintegration';

bad=r; bad.J_openocl=trapz(bad.t_control,bad.q_control);
a=assess_numerical_case(bad,ref,par,opts);
assert(~a.numeric_pass && ~a.cost_accounting_pass);
tests{end+1}='trapezoidal_cost_across_jumps_rejected';

bad=rmfield(base,'provenance'); a=assess_numerical_case(bad,ref,par,opts);
assert(~a.numeric_pass && ~a.provenance_pass && a.agreement_pass);
bad=base; bad.parameters.gamma=.31; a=assess_numerical_case(bad,ref,par,opts);
assert(~a.numeric_pass && ~a.problem_pass);
tests{end+1}='legacy_and_problem_mismatch_cannot_pass';

bad=synthetic([0;.1;.4;1],[-1e-4;0;0],base.x0,par);
before=bad; a=assess_numerical_case(bad,ref,par,opts);
assert(~a.numeric_pass && a.signed_extrema.q_min<0 && isequaln(before,bad));
bad=base; bad.success=false; a=assess_numerical_case(bad,ref,par,opts); assert(~a.numeric_pass);
tests{end+1}='raw_bounds_and_solver_failure_are_not_repaired';

bad=base; bad.s_state(end)=bad.s_state(end)+2e-5;
a=assess_numerical_case(bad,ref,par,opts);
assert(~a.numeric_pass && a.state_discrepancy>opts.state_tolerance && ...
    a.reintegrated_terminal_peak<=par.K && strcmp(a.tail.terminal_state_source,'original_control_reintegration'));
tests{end+1}='collocation_discrepancy_and_reintegrated_terminal_state';

bad=synthetic([0;1;10;20],[0;0;0],[.75;.01],par);
rr=analytic_reference(par,bad.x0,g,bad.t_state);
a=assess_numerical_case(bad,rr,par,opts);
assert(~a.numeric_pass && a.capacity_excess>opts.capacity_tolerance);
tests{end+1}='original_control_capacity_peak_including_interval_interior';

t=tail_diagnostic([0;.1;.4],[.5;0;0],.2,.01,par,1,.7,1e-6,1e-6);
assert(t.control_returned_to_zero && isequal(t.tail_interval_indices,[2;3]));
t=tail_diagnostic([0;.1;.4],[0;.5;0],.2,.01,par,1,.7,1e-6,1e-6);
assert(~t.control_returned_to_zero);
tests{end+1}='tail_checks_overlap_with_whole_actual_intervals';

runs=cell(1,5);
spec=numerical_assessment_spec(cfg);
for k=1:5
    settings=cfg.solve; settings.N=cfg.cases(k).main_N;
    runs{k}=struct('case_id',cfg.cases(k).id,'success',true,'assessment', ...
        struct('numeric_pass',true,'agreement_pass',true,'passed',true, ...
        'observed_structure',cfg.cases(k).expected_structure), ...
        'parameters',cfg.parameters,'x0',cfg.cases(k).x0,'solver_settings',settings, ...
        'initialization',struct('type','analytic_reference'),'source_status','verified_record', ...
        'assessment_provenance',struct('code_hash',spec.code_hash),'assessment_settings',spec.settings);
end
assert(numerical_main_verification(runs,cfg.cases,cfg.parameters,cfg.solve,spec).verified);
runs{4}.assessment.agreement_pass=false;
assert(~numerical_main_verification(runs,cfg.cases,cfg.parameters,cfg.solve,spec).verified);
runs{4}.assessment.agreement_pass=true; runs{3}.assessment=rmfield(runs{3}.assessment,'numeric_pass');
assert(~numerical_main_verification(runs,cfg.cases,cfg.parameters,cfg.solve,spec).verified);
assert(~numerical_main_verification(runs(1:4),cfg.cases,cfg.parameters,cfg.solve,spec).verified);
tests{end+1}='main_verification_requires_all_new_flags_and_five_cases';

runs{3}.assessment.numeric_pass=true;
badCases=cfg.cases; badCases(1).x0(1)=.8;
assert(~numerical_main_verification(runs,badCases,cfg.parameters,cfg.solve,spec).verified);
badPar=cfg.parameters; badPar.gamma=.31;
assert(~numerical_main_verification(runs,cfg.cases,badPar,cfg.solve,spec).verified);
badSpec=spec; badSpec.code_hash='stale_assessment';
assert(~numerical_main_verification(runs,cfg.cases,cfg.parameters,cfg.solve,badSpec).verified);
assert(numerical_additional_verification(runs{2},cfg,'grid',spec));
assert(~numerical_additional_verification(runs{1},cfg,'neutral',spec));
neutral=runs{1}; neutral.initialization=struct('type','constant_control','control',.7);
neutral.solver_settings.initialization='constant_control';
assert(numerical_additional_verification(neutral,cfg,'neutral',spec));
neutral.x0(1)=.8; assert(~numerical_additional_verification(neutral,cfg,'neutral',spec));
tests{end+1}='current_inputs_assessment_and_additional_request_must_match';

neutralTests=verify_neutral_initialization();
report=struct('passed',true,'tests',{tests},'required_tests_passed',numel(tests), ...
    'neutral_tests',neutralTests,'actual_optimizer_calls',0,'checked_utc',numerical_utc(),'matlab',version);
fprintf('NUMERICAL_ASSESSMENT_TESTS_OK tests=%d actual_optimizer=0\n',numel(tests));
end

function run=synthetic(t,q,x0,p)
q=q(:); t=t(:); y=zeros(numel(t),2); y(1,:)=x0';
for k=1:numel(q)
    f=@(~,x) [-p.c*(p.p+(1-p.p)*q(k))*x(1)*x(2);(p.p*p.c*(1-q(k))*x(1)-p.gamma)*x(2)];
    sol=ode45(f,t(k:k+1),y(k,:)',odeset('RelTol',2e-11,'AbsTol',1e-13));
    y(k+1,:)=deval(sol,t(k+1))';
end
a=struct('T',t(end),'N',numel(q),'controls_regularization',false,'terminal_constraint','none', ...
    'terminal_cost','none','grid_constraints','none','grid_costs','none','state_lower_bounds',[0 0], ...
    'state_upper_bounds',[1 p.K],'control_lower_bound',0,'control_upper_bound',1,'initial_state',x0);
run=struct('case_id','synthetic','parameters',p,'x0',x0,'solver_settings',a, ...
    'actual_solver_settings',a,'actual_grid',struct('t_state',t,'t_control',t(1:end-1)), ...
    'initialization',struct('type','synthetic'),'initial_guess',struct('synthetic',true), ...
    't_state',t,'t_control',t(1:end-1),'q_control',q,'s_state',y(:,1),'i_state',y(:,2), ...
    'dt_control',diff(t),'success',true,'J_openocl',p.p*p.c*sum(q.*diff(t)), ...
    'run_id','synthetic_test_only','source_status','verified_record');
names={'case_id','parameters','x0','solver_settings','actual_solver_settings','actual_grid','initialization','initial_guess'};
payload=struct(); for k=1:numel(names), payload.(names{k})=run.(names{k}); end
payload.solve_code_hash='synthetic_test_only'; payload.environment_fingerprint='synthetic_test_only';
run.solve_fingerprint_payload=payload; run.solve_fingerprint=numerical_sha256(payload);
run.provenance=struct('solve_commit','synthetic_test_only','solve_code_hash','synthetic_test_only', ...
    'solve_dirty',true,'solve_started_utc','synthetic_test_only','environment_fingerprint','synthetic_test_only');
end

function expectError(fn,id)
try, fn(); error('test:ExpectedFailure','Expected %s.',id);
catch e, assert(strcmp(e.identifier,id),'Unexpected failure: %s',e.message); end
end
