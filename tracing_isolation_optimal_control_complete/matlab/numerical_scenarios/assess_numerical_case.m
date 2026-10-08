function assessment = assess_numerical_case(run,ref,par,opts)
% 原控制重积分用于数值接受；解析参考仅用于另行比较，不修剪任何输出。
grid=validate_numerical_run_grid(run,opts); t=grid.t; q=run.q_control(:); n=numel(q);
s=run.s_state(:); i=run.i_state(:);
odeopts=odeset('RelTol',opts.ode_rel_tol,'AbsTol',opts.ode_abs_tol);
y=zeros(n+1,2); y(1,:)=run.x0(:)'; peak=y(1,2); peakTime=t(1);
solutions=cell(n,1); minima=y(1,:); maxima=y(1,:);
for k=1:n
    rhs=@(~,x) [-par.c*(par.p+(1-par.p)*q(k))*x(1)*x(2); ...
        (par.p*par.c*(1-q(k))*x(1)-par.gamma)*x(2)];
    sol=ode45(rhs,grid.edges(k:k+1),y(k,:)',odeopts); solutions{k}=sol;
    y(k+1,:)=deval(sol,t(k+1))';
    minima=min(minima,min(sol.y,[],2)'); maxima=max(maxima,max(sol.y,[],2)');
    [pk,ix]=max(sol.y(2,:)); pt=sol.x(ix);
    % 常控制区间的感染峰值发生在 s=gamma/[pc(1-q)]。
    if q(k)<1
        hq=par.gamma/(par.p*par.c*(1-q(k)));
        if y(k,1)>hq && y(k+1,1)<hq
            tp=fzero(@(v) susceptible(sol,v)-hq,grid.edges(k:k+1));
            yp=deval(sol,tp); pk=yp(2); pt=tp;
        end
    end
    if pk>peak, peak=pk; peakTime=pt; end
end
assessment.reintegration=struct('t',t,'s',y(:,1),'i',y(:,2),'max_i',peak,'peak_time',peakTime);
assessment.capacity_excess=max(0,peak-par.K);
assessment.state_discrepancy=max(abs(y-[s i]),[],'all');
assessment.state_discrepancy_definition='collocation_node_states_vs_original_control_reintegration';
assessment.initial_error=max(abs([s(1);i(1)]-run.x0(:)));
assessment.control_violation=max([0;-q;q-1]);
assessment.state_violation=max([0;-s;-i;s-1;i-par.K]);
assessment.reintegrated_state_violation=max([0;-minima(:);maxima(1)-1;peak-par.K]);
assessment.signed_extrema=struct('q_min',min(q),'q_max',max(q), ...
    'q_lower_margin',min(q),'q_upper_excess',max(q)-1, ...
    'node_s_min',min(s),'node_s_upper_excess',max(s)-1,'node_i_min',min(i), ...
    'node_capacity_excess',max(i)-par.K,'reintegration_s_min',minima(1), ...
    'reintegration_i_min',minima(2),'reintegration_capacity_excess',peak-par.K, ...
    'initial_state_difference',[s(1);i(1)]-run.x0(:));
assessment.control_interval_lengths=grid.dt;
assessment.J_reintegrated_control=par.p*par.c*sum(q.*grid.dt);
assessment.cost_accounting_error=abs(run.J_openocl-assessment.J_reintegrated_control);
assessment.cost_accounting_pass=isfinite(run.J_openocl) && ...
    assessment.cost_accounting_error<=opts.cost_accounting_tolerance*max(1,abs(assessment.J_reintegrated_control));
tail=tail_diagnostic(run.t_control,q,y(end,1),y(end,2), ...
    par,t(end),opts.tail_duration,opts.tail_control_tolerance,opts.capacity_tolerance);
assessment.tail_max_q=tail.max_abs_q_on_tail;
assessment.terminal_peak=tail.zero_control_future_peak;
assessment.terminal_safe=tail.zero_control_continuation_safe;
assessment.reintegrated_terminal_peak=tail.zero_control_future_peak;
assessment.node_terminal_peak=safe_peak(s(end),i(end),par.gamma/(par.p*par.c));
assessment.tail=tail;
consistency=numerical_run_consistency(run,par,opts.grid_time_tolerance);
assessment.provenance_pass=consistency.provenance_pass; assessment.problem_pass=consistency.problem_pass;
assessment.consistency=consistency;
assessment.numeric_checks=struct('solver_success',logical(run.success), ...
    'provenance',consistency.provenance_pass,'problem',consistency.problem_pass, ...
    'cost_accounting',assessment.cost_accounting_pass, ...
    'capacity',assessment.capacity_excess<=opts.capacity_tolerance, ...
    'state_discrepancy',assessment.state_discrepancy<=opts.state_tolerance, ...
    'initial_state',assessment.initial_error<=opts.state_tolerance, ...
    'control_bounds',assessment.control_violation<=opts.control_tolerance, ...
    'node_state_bounds',assessment.state_violation<=opts.state_tolerance, ...
    'reintegration_state_bounds',assessment.reintegrated_state_violation<=opts.state_tolerance, ...
    'tail_control',tail.control_returned_to_zero,'safe_continuation',tail.zero_control_continuation_safe);
assessment.numeric_pass=all(structfun(@(v) logical(v),assessment.numeric_checks));
det=detect_numerical_events(run.t_control,q,t,y,par.K,opts);
trajectory=struct('dense_solutions',{solutions},'t',t,'s',y(:,1),'i',y(:,2));
cmp=compare_numerical_events(det,ref,par,opts,trajectory);
assessment.arcs=det.arcs; assessment.observed_structure=det.observed_structure;
assessment.transition_cells=sum(det.cell_labels==3);
assessment.structured_events=det.events; assessment.event_detection=det;
assessment.event_comparison=cmp;
% 旧标量摘要只用于显示，不作为连续切换状态或验收门槛。
assessment.events=legacy_events(det,t,y);
gap=assessment.J_reintegrated_control-ref.J_reference;
assessment.signed_cost_difference=gap;
assessment.relative_cost_difference=gap/max(abs(ref.J_reference),1e-12);
if abs(ref.J_reference)<=opts.zero_reference_cost_tolerance
    costPass=abs(gap)<=opts.safe_zero_cost_tolerance; costMode='absolute_zero_cost';
else
    costPass=abs(assessment.relative_cost_difference)<=opts.relative_cost_tolerance; costMode='relative';
end
assessment.cost_agreement=struct('passed',costPass,'mode',costMode,'signed_difference',gap, ...
    'absolute_difference',abs(gap),'relative_difference',assessment.relative_cost_difference);
assessment.agreement_pass=costPass && cmp.agreement_pass;
assessment.passed=assessment.numeric_pass; % 兼容别名，始终只表示数值接受。
assessment.status='assessed';
if gap<0 && ~costPass
    assessment.discrepancy_checks=struct('complete_cost_intervals',assessment.cost_accounting_pass, ...
        'model_parameters_provenance',consistency.problem_pass && consistency.provenance_pass, ...
        'control_bounds',assessment.numeric_checks.control_bounds,'reintegration_capacity',assessment.numeric_checks.capacity, ...
        'terminal_safety',assessment.numeric_checks.safe_continuation);
    if all(structfun(@(v) logical(v),assessment.discrepancy_checks))
        assessment.status='unresolved_discrepancy';
    else
        assessment.status='lower_cost_with_numeric_failures';
    end
end
assessment.notes=['numeric_pass为给定浮点容差内的接受；agreement_pass为独立解析比较。' ...
    '事件使用原始网格区间，状态差指配点节点与原控制重积分之差；均不构成严格可行性或KKT证书。'];
end

function s=susceptible(sol,t)
y=deval(sol,t); s=y(1);
end

function e=legacy_events(det,t,y)
e=struct('capacity_start',NaN,'capacity_end',NaN,'full_start',NaN, ...
    'release',NaN,'full_state',[NaN;NaN],'release_state',[NaN;NaN]);
label=det.cell_labels; ix=find(label==1,1);
if ~isempty(ix), e.full_start=t(ix); e.full_state=y(ix,:)'; end
ix=find(label~=0,1,'last');
if ~isempty(ix) && ix<numel(label), e.release=t(ix+1); e.release_state=y(ix+1,:)'; end
ix=find(label==2);
if ~isempty(ix), e.capacity_start=t(ix(1)); e.capacity_end=t(ix(end)+1); end
end
