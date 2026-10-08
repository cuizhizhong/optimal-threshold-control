function out = compare_numerical_events(detected,ref,par,opts,trajectory)
% 独立比较器：只在数值检测完成之后使用解析时刻、状态和预期结构。
% 时间门槛是网格尺度诊断；状态距离不机械施加 1e-6 门槛。
if nargin<5, trajectory=struct(); end
timeTol=setting(opts,'event_time_tolerance',1e-10);
maxCells=setting(opts,'event_max_transition_cells',2);
distanceCells=setting(opts,'event_distance_cells',1);
assert(maxCells>=0 && distanceCells>=0 && timeTol>=0, ...
    'compare_numerical_events:Thresholds','Invalid event comparison thresholds.');
kinds={'intervention','capacity_enter','capacity_exit','full_start','release'};
theory=theoreticalEvents(ref,timeTol);
out=struct('events',struct(),'expected_structure',expectedStructure(ref,theory,detected.t(1),timeTol), ...
    'observed_structure',detected.observed_structure,'diagnostic_pass',detected.diagnostics.passed);
eventPass=true;
for j=1:numel(kinds)
    name=kinds{j}; ev=detected.events.(name); th=theory.(name);
    compared=ev; compared.theory_time=th.time;
    compared.theory_state=th.state; compared.applicable=th.applicable;
    compared.time_distance_to_interval=[]; compared.contains_theory=false;
    compared.single_cell_contains_theory=false;
    compared.reference_state_distance_to_event_segment=[];
    compared.state_distance_available=false; compared.state_distance_method='not_available';
    compared.state_distance_reason='no_unique_detected_event';
    compared.time_pass=false; compared.transition_width_pass=false; compared.passed=false;
    % 每个候选分别比较并保留。理论不能用于从多个候选中挑出一个。
    candidateComparisons=cell(numel(ev.candidates),1);
    for k=1:numel(ev.candidates)
        candidateComparisons{k}=compareCandidate(ev.candidates(k),th);
    end
    if isempty(candidateComparisons), compared.candidates=struct([]);
    else, compared.candidates=vertcat(candidateComparisons{:}); end
    if ~th.applicable
        if ev.candidate_count==0
            compared.status='not_applicable'; compared.passed=true;
            compared.state_distance_reason='theoretical_stage_absent';
        else
            compared.status='unexpected_event';
        end
    elseif ev.candidate_count==0
        compared.status='missing_event';
    elseif ev.candidate_count>1
        compared.status='multiple_candidates';
    else
        c=compared.candidates(1); fields=fieldnames(c);
        for k=1:numel(fields), compared.(fields{k})=c.(fields{k}); end
        compared.candidate_count=1; compared.candidates=c;
    end
    out.events.(name)=compared; eventPass=eventPass && compared.passed;
end
out.structure_pass=strcmp(out.observed_structure,out.expected_structure);
out.capacity_control=capacityComparison(detected,par,opts,trajectory);
out.event_pass=eventPass;
out.agreement_pass=out.diagnostic_pass && out.structure_pass && eventPass && out.capacity_control.passed;
out.thresholds=struct('max_transition_cells',maxCells,'distance_cells',distanceCells, ...
    'time_tolerance',timeTol,'capacity_control_tolerance', ...
    setting(opts,'capacity_control_tolerance',2e-3));
out.notes=['真实过渡区间不扩张；距离至多一个邻近最大控制单元表示网格尺度一致。' ...
    '单网格包含结论另由 single_cell_contains_theory 字段给出。状态最短距离仅作浮点诊断。'];

    function c=compareCandidate(c,th)
        c.theory_time=th.time; c.theory_state=th.state; c.applicable=th.applicable;
        c.time_distance_to_interval=[]; c.contains_theory=false;
        c.single_cell_contains_theory=false;
        c.transition_width_pass=c.transition_cells<=maxCells;
        c.time_pass=false; c.passed=false;
        c.reference_state_distance_to_event_segment=[];
        c.state_distance_available=false; c.state_distance_method='not_available';
        c.state_distance_reason='theoretical_event_absent';
        c.closest_numerical_time=[]; c.closest_numerical_state=[];
        if ~th.applicable, c.status='unexpected_event'; return; end
        left=c.interval(1); right=c.interval(2);
        c.interval_width=right-left;
        c.time_distance_to_interval=max([left-th.time 0 th.time-right]);
        c.contains_theory=th.time>=left-timeTol && th.time<=right+timeTol;
        c.single_cell_contains_theory=c.transition_cells==1 && c.contains_theory;
        c.time_pass=c.time_distance_to_interval<=distanceCells*c.local_max_cell_width+timeTol;
        recognized=ismember(c.status,{'detected','initial_event'});
        c.passed=recognized && c.transition_width_pass && c.time_pass;
        if ~recognized
            % 保留检测器异常的原状态，不用理论一致性改写它。
        elseif ~c.transition_width_pass
            c.status='too_many_transition_cells';
        elseif ~c.time_pass
            c.status='outside_grid_scale';
        elseif c.single_cell_contains_theory
            c.status='single_cell_contains_theory';
        elseif c.contains_theory && c.transition_cells==0
            c.status='point_event_contains_theory';
        elseif c.contains_theory
            c.status='transition_interval_contains_theory';
        else
            c.status='grid_scale_agreement_without_containment';
        end
        [dist,at,x,method,reason]=stateDistance(c,th.state,trajectory,detected);
        c.reference_state_distance_to_event_segment=dist;
        c.state_distance_available=~isempty(dist);
        c.state_distance_method=method; c.state_distance_reason=reason;
        c.closest_numerical_time=at; c.closest_numerical_state=x;
    end
end

function theory=theoreticalEvents(ref,timeTol)
assert(isfield(ref,'events'),'compare_numerical_events:MissingReference','Reference must contain events.');
e=ref.events;
cap=eventTime(e,'capacity_start'); full=eventTime(e,'full_start'); release=eventTime(e,'release');
exit=eventTime(e,'capacity_end'); if isempty(exit) && ~isempty(cap), exit=full; end
capstate=eventState(e,'capacity_state'); fullstate=eventState(e,'full_state');
releaseState=eventState(e,'release_state');
theory.capacity_enter=theoryEvent(cap,capstate);
theory.capacity_exit=theoryEvent(exit,fullstate);
theory.full_start=theoryEvent(full,fullstate);
theory.release=theoryEvent(release,releaseState);
if ~isempty(cap) && (isempty(full) || cap<=full+timeTol)
    theory.intervention=theoryEvent(cap,capstate);
else
    theory.intervention=theoryEvent(full,fullstate);
end
end

function out=eventTime(e,name)
out=[];
if isfield(e,name) && isscalar(e.(name)) && isfinite(e.(name)), out=e.(name); end
end

function out=eventState(e,name)
out=[];
if isfield(e,name) && numel(e.(name))==2 && all(isfinite(e.(name)))
    out=e.(name)(:);
end
end

function out=theoryEvent(time,state)
out=struct('applicable',~isempty(time),'time',time,'state',state);
end

function word=expectedStructure(ref,theory,t0,tol)
if isfield(ref,'expected_structure')
    word=char(ref.expected_structure); return
end
if ~theory.intervention.applicable, word='0'; return; end
parts={};
if theory.intervention.time>t0+tol, parts{end+1}='0'; end
if theory.capacity_enter.applicable, parts{end+1}='q_B'; end
if theory.full_start.applicable, parts{end+1}='1'; end
if theory.release.applicable, parts{end+1}='0'; end
word=strjoin(parts,' -> ');
end

function [distance,at,x,method,reason]=stateDistance(ev,reference,trajectory,detected)
distance=[]; at=[]; x=[]; method='not_available'; reason='reference_state_unavailable';
if isempty(reference), return; end
left=ev.interval(1); right=ev.interval(2);
if left==right
    x=ev.numerical_endpoint_states(:,1); at=left; distance=norm(x-reference);
    method='original_grid_endpoint'; reason=''; return;
end
if ~isfield(trajectory,'dense_solutions') || ...
        numel(trajectory.dense_solutions)~=numel(detected.q)
    reason='ode_dense_output_unavailable_endpoints_and_span_reported'; return;
end
distance=Inf; method='ode_dense_output_and_bounded_search'; reason='';
for k=ev.transition_cell_indices
    sol=trajectory.dense_solutions{k}; interval=detected.t(k:k+1);
    if isempty(sol)
        distance=[]; at=[]; x=[]; method='not_available'; reason='empty_dense_solution'; return;
    end
    [middle,value]=fminbnd(@(v) squaredDistance(sol,v,reference),interval(1),interval(2), ...
        optimset('TolX',1e-12,'Display','off'));
    times=[interval(1) middle interval(2)];
    values=[squaredDistance(sol,times(1),reference) value squaredDistance(sol,times(3),reference)];
    [best,index]=min(values);
    if sqrt(best)<distance
        distance=sqrt(best); at=times(index); x=deval(sol,at);
    end
end
end

function value=squaredDistance(sol,time,reference)
x=deval(sol,time); value=sum((x(:)-reference(:)).^2);
end

function out=capacityComparison(detected,par,opts,trajectory)
indices=find(detected.cell_labels==2);
out=struct('applicable',~isempty(indices),'status','not_applicable','passed',true, ...
    'cell_indices',indices','intervals',[],'control',[],'q_B_interval_average',[], ...
    'signed_error',[],'max_absolute_error',[],'tolerance', ...
    setting(opts,'capacity_control_tolerance',2e-3),'method','not_applicable', ...
    'reason','no_positive_length_paid_capacity_cells');
if isempty(indices), return; end
assert(isfinite(out.tolerance) && out.tolerance>=0,'Invalid q_B comparison tolerance.');
hasDense=isfield(trajectory,'dense_solutions') && ...
    numel(trajectory.dense_solutions)==numel(detected.q);
averages=zeros(size(indices)); h=par.gamma/(par.p*par.c);
for j=1:numel(indices)
    k=indices(j); left=detected.t(k); right=detected.t(k+1);
    if hasDense
        sol=trajectory.dense_solutions{k};
        if isempty(sol)
            out.status='not_available'; out.passed=false; out.reason='empty_dense_solution'; return;
        end
        averages(j)=integral(@(v) boundaryControl(sol,v,h),left,right, ...
            'AbsTol',1e-11,'RelTol',1e-9)/(right-left);
    else
        % 降级口径明确记录；主评估入口传入原控制重积分的 ODE 稠密输出。
        s=detected.state_xy(k:k+1,1);
        if any(s<=0)
            out.status='not_available'; out.passed=false; out.reason='nonpositive_susceptible'; return;
        end
        if abs(s(2)-s(1))<=eps(max(s))
            averages(j)=1-h/s(1);
        else
            averages(j)=1-h*log(s(2)/s(1))/(s(2)-s(1));
        end
    end
end
out.intervals=[detected.t(indices) detected.t(indices+1)];
out.control=detected.q(indices); out.q_B_interval_average=averages;
out.signed_error=out.control-averages;
out.max_absolute_error=max(abs(out.signed_error));
out.passed=out.max_absolute_error<=out.tolerance;
if out.passed, out.status='within_tolerance'; else, out.status='outside_tolerance'; end
if hasDense, out.method='ode_dense_output_interval_quadrature';
else, out.method='piecewise_linear_node_interpolation_interval_integral'; end
out.reason='';
end

function value=boundaryControl(sol,time,h)
shape=size(time); y=deval(sol,time(:)');
assert(all(y(1,:)>0),'compare_numerical_events:NonpositiveState', ...
    'q_B interval average requires positive reintegrated susceptible states.');
value=reshape(1-h./y(1,:),shape);
end

function out=setting(opts,name,fallback)
out=fallback; if isfield(opts,name), out=opts.(name); end
end
