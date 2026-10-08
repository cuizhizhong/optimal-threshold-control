function report = verify_revision_validation_unit()
% 第7步统一无优化器入口；合成记录和解析测试不作为主算例实验结果。
checks={@verify_numerical_reference,@verify_reference_dependency_tests, ...
    @verify_numerical_cache,@verify_solver_diagnostics,@verify_numerical_assessment, ...
    @verify_capacity_exit_transition,@verify_numerical_events, ...
    @verify_reference_boundaries,@verify_original_dynamics, ...
    @verify_complete_control_cost,@verify_revision_exporter,@verify_revision_scheduler};
groups=struct('name',{},'passed',{},'report',{});
for k=1:numel(checks)
    result=checks{k}();
    passed=(isfield(result,'passed') && result.passed) || ...
        (isfield(result,'verified') && result.verified);
    assert(passed,'verify_revision_validation_unit:GroupFailed', ...
        'Unit group failed: %s.',func2str(checks{k}));
    groups(k)=struct('name',func2str(checks{k}),'passed',true,'report',result); %#ok<AGROW>
end
report=struct('passed',true,'status','tested','group_count',numel(groups), ...
    'groups',groups,'actual_optimizer_calls',0,'checked_utc',numerical_utc(), ...
    'matlab',version,'execution_type','unit_tests_no_optimizer');
fprintf('REVISION_VALIDATION_UNIT_OK groups=%d actual_optimizer=0\n',numel(groups));
end

function report=verify_reference_boundaries()
cfg=numerical_cases_config(); p=cfg.parameters; g=build_theory_geometry(p); tests={};
x0=[.40;.02]; ref=analytic_reference(p,x0,g,[0;.5;3;20]);
assert(strcmp(ref.region,'A') && ref.J_reference==0 && all(ref.q==0));
assert(all([ref.tau_wait ref.tau_boundary ref.tau_full]==0));
tests{end+1}='safe_E0_exact_zero_cost_and_control';

[sg,ig]=g.switch_point((g.z_B+g.e)/2);
ref=analytic_reference(p,[sg;ig],g,[0;.01;.1]);
assert(strcmp(ref.region,'Gamma') && ref.tau_wait==0 && ref.tau_boundary==0);
assert(ref.events.full_start==0 && isnan(ref.events.capacity_start) && ...
    isnan(ref.events.capacity_end) && all(ref.q==1));
tests{end+1}='Gamma_interior_has_no_zero_length_capacity_platform';

ref=analytic_reference(p,[g.s_B;p.K],g,[0;.01;.1]);
assert(ref.tau_wait==0 && abs(ref.tau_boundary)<1e-12 && ref.events.full_start==0);
assert(isnan(ref.events.capacity_start) && isnan(ref.events.capacity_end) && all(ref.q==1));
tests{end+1}='s_B_K_allows_zero_length_capacity_stage';

sb=g.s_B+.01; ib=g.Phi_B-sb+g.h*log(sb);
ref=analytic_reference(p,[sb;ib],g,[0;.01]);
assert(strcmp(ref.region,'W_Gamma') && ref.tau_wait>0 && ref.tau_boundary==0);
assert(isnan(ref.events.capacity_start) && isnan(ref.events.capacity_end));
assert(abs(g.phi(sb,ib)-g.Phi_B)<1e-13);
tests{end+1}='waiting_public_interface_Phi_equals_Phi_B_no_fake_platform';

regions=cell(1,numel(cfg.cases)); reverse=regions;
for k=1:numel(cfg.cases), regions{k}=classify_initial_state(cfg.cases(k).x0,g,p); end
order=numel(cfg.cases):-1:1;
for k=1:numel(order)
    % 任意命名和排列只能改变输入组织，不能改变状态区域判定。
    other=cfg.cases(order(k)); other.id=sprintf('arbitrary_name_%d',k);
    reverse{order(k)}=classify_initial_state(other.x0,g,p);
end
assert(isequal(regions,reverse));
tests{end+1}='case_names_and_order_do_not_determine_regions';

ref=analytic_reference(p,[.1;1e-25],g,[0;1;20]);
assert(strcmp(ref.region,'A') && all(ref.i>0) && all(ref.q==0) && ref.i(1)==1e-25);
assert(safe_peak(.1,1e-25,g.h)==1e-25 && ref.J_reference==0);
tests{end+1}='small_positive_i_below_h_is_not_cancelled_to_zero';

other=p; other.p=.4; gp=build_theory_geometry(other);
assert(abs(gp.r-(gp.h-gp.ell))<1e-14 && abs(gp.r-gp.ell)>1e-3);
assert(abs(gp.r-other.gamma*(1-other.p)/(other.p*other.c))<1e-14);
tests{end+1}='r_equals_h_minus_ell_outside_p_one_half';
report=unit_report(tests);
end

function report=verify_original_dynamics()
cfg=numerical_cases_config(); p=cfg.parameters; g=build_theory_geometry(p);
x0=[.6;.02]; t=linspace(0,3,101); tests={};
for q=[0 .35 1]
    rhs=@(~,x) [-p.c*(p.p+(1-p.p)*q)*x(1)*x(2); ...
        (p.p*p.c*(1-q)*x(1)-p.gamma)*x(2)];
    sol=ode45(rhs,[0 t(end)],x0,odeset('RelTol',1e-11,'AbsTol',1e-14));
    x=deval(sol,t); total=sum(x,1);
    assert(all(x(:)>0) && max(diff(total))<=1e-12 && max(total)<=sum(x0)+1e-12);
    assert(max(abs(sum(rhs(0,x(:,1)))-(-p.c*q*x0(1)*x0(2)-p.gamma*x0(2))))<1e-14);
    if q==0
        assert(max(abs(g.phi(x(1,:),x(2,:))-g.phi(x0(1),x0(2))))<1e-10);
        tests{end+1}='q_zero_natural_invariant_and_positive_monotone_total'; %#ok<AGROW>
    elseif q==1
        assert(max(abs(x(2,:)-x0(2)*exp(-p.gamma*t)))<1e-11);
        assert(max(abs(x(2,:)-g.ell*log(x(1,:))-(x0(2)-g.ell*log(x0(1)))))<1e-10);
        tests{end+1}='q_one_full_tracking_invariant_and_positive_monotone_total'; %#ok<AGROW>
    else
        tests{end+1}='interior_control_original_flow_identity_and_positive_monotone_total'; %#ok<AGROW>
    end
end
report=unit_report(tests);
end

function report=verify_complete_control_cost()
cfg=numerical_cases_config(); p=cfg.parameters;
t=[0;.25;.75;2]; q=[.2;.8;.4]; settings=cfg.solve; settings.T=2; settings.N=3;
grid=struct('t_state',t,'t_control',t(1:end-1),'dt_control',diff(t), ...
    'control_interval_edges',t);
prepared=struct('problem',struct('solve',@output),'ig',[], ...
    'parameters',p,'x0',[.4;.02],'solver_settings',settings, ...
    'actual_solver_settings',settings,'actual_grid',grid, ...
    'initialization',struct('type','synthetic_cost_test'), ...
    'initial_guess',struct('control',q));
run=solve_openocl_case(p,prepared.x0,settings,prepared.initialization,prepared);
hand=p.p*p.c*(.2*.25+.8*.5+.4*1.25);
assert(run.success && abs(run.J_openocl-hand)<1e-14 && abs(hand-p.p*p.c*.95)<1e-14);
assert(isequal(run.dt_control,[.25;.5;1.25]) && run.t_state(end)==2);
assert(abs(run.J_openocl-p.p*p.c*trapz(t(1:end-1),q))>.1);
report=unit_report({'nonuniform_piecewise_constant_full_horizon_cost_not_trapezoid'});
    function [sol,times,info]=output(~)
        sol=struct('states',struct('S',struct('value',[.4 .39 .38 .37]), ...
            'I',struct('value',[.02 .02 .02 .02])), ...
            'controls',struct('q',struct('value',q')));
        times=struct('states',struct('value',t'),'controls',struct('value',t(1:end-1)'));
        info=struct('success',true,'ipopt_stats',struct('success',true,'return_status','Solve_Succeeded'));
    end
end

function out=unit_report(tests)
out=struct('passed',true,'tests',{tests},'test_count',numel(tests),'actual_optimizer_calls',0);
end
