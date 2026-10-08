function report = verify_numerical_events()
% 合成轨迹测试检测/比较分离，不运行 OpenOCL，也不改写历史求解数组。
opts=struct('event_control_threshold',1e-3,'event_capacity_threshold',2e-5, ...
    'event_max_transition_cells',2,'event_distance_cells',1, ...
    'event_time_tolerance',1e-10,'capacity_control_tolerance',2e-3);
par=struct('p',0.5,'c',2,'gamma',0.3,'K',0.15); checks={};

% 等待、真实容量弧、单单元退出、完全跟踪及单单元解除。
t=(0:9)'; s=0.8-0.04*t;
i=[0.10;0.12;0.15;0.15;0.15;0.14;0.10;0.07;0.09;0.11];
q=[0;0;linearAverage(s(3),s(4));linearAverage(s(4),s(5));0.7;1;0.45;0;0];
x=[s i]; det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(2,4.5,6.5,[s(3);i(3)],mean(x(5:6,:),1)',mean(x(7:8,:),1)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(det.diagnostics.passed && cmp.agreement_pass && ...
    strcmp(det.observed_structure,'0 -> q_B -> 1 -> 0'));
assert(isequal(det.events.capacity_exit.interval,[4 5]) && ...
    cmp.events.capacity_exit.single_cell_contains_theory);
assert(isequal(det.events.release.interval,[6 7]) && ...
    cmp.events.release.single_cell_contains_theory);
assert(cmp.capacity_control.max_absolute_error<1e-12);
record('all_primary_events_and_actual_transition_intervals');

optsChanged=opts; optsChanged.expected_structure='1 -> 0';
again=detect_numerical_events(t(1:end-1),q,t,x,par.K,optsChanged);
wrong=ref; wrong.expected_structure='1 -> 0';
wrongCmp=compare_numerical_events(det,wrong,par,opts);
assert(isequaln(det,again) && ~wrongCmp.structure_pass && ~wrongCmp.agreement_pass);
assert(isequaln(det.events,again.events));
record('expected_structure_cannot_change_detector');

% 初始完全跟踪的所有适用初始事件固定为真实 [0,0]。
t=(0:3)'; x=[0.6 0.12;0.55 0.10;0.50 0.08;0.45 0.09]; q=[1;1;0];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,0,2,[NaN;NaN],x(1,:)',x(3,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(isequal(det.events.full_start.interval,[0 0]) && ...
    isequal(det.events.intervention.interval,[0 0]) && cmp.agreement_pass);
assert(strcmp(cmp.events.capacity_enter.status,'not_applicable') && ...
    isempty(cmp.events.capacity_enter.theory_time) && ...
    isempty(cmp.events.capacity_enter.time_distance_to_interval) && ...
    ~cmp.events.capacity_enter.contains_theory);
record('initial_full_control_and_absent_capacity_stage');

% 初始容量弧；容量退出为纯阶段直接相邻的共享端点。
t=(0:4)'; x=[0.7 0.15;0.65 0.15;0.60 0.15;0.55 0.10;0.50 0.12];
q=[linearAverage(x(1,1),x(2,1));linearAverage(x(2,1),x(3,1));1;0];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(0,2,3,x(1,:)',x(3,:)',x(4,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(isequal(det.events.capacity_enter.interval,[0 0]) && ...
    isequal(det.events.intervention.interval,[0 0]) && ...
    isequal(det.events.capacity_exit.interval,[2 2]) && ...
    det.events.capacity_exit.transition_cells==0 && cmp.agreement_pass);
assert(~cmp.events.capacity_exit.single_cell_contains_theory);
record('initial_capacity_and_direct_exit');

% 解除后自然轨道回触 i=K。即使两个节点位于 K，q=0 仍属自然阶段。
t=(0:4)'; x=[0.6 0.10;0.55 0.08;0.5 0.15;0.45 0.15;0.4 0.12]; q=[1;0;0;0];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,0,1,[NaN;NaN],x(1,:)',x(2,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(det.events.capacity_enter.candidate_count==0 && ...
    det.events.capacity_exit.candidate_count==0 && det.diagnostics.capacity_arc_count==0 && ...
    isequal(det.diagnostics.natural_capacity_contact_cells,3) && cmp.agreement_pass);
record('late_uncontrolled_capacity_recontact');

% 多次离边/返边及多个候选全部保存，不能按参考时刻选择一个。
t=(0:6)'; q=[0.5;1;0;0.5;1;0];
x=[0.6*ones(7,1) [0.15;0.15;0.10;0.15;0.15;0.10;0.11]];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(0,1,2,x(1,:)',x(2,:)',x(3,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(~det.diagnostics.passed && ~cmp.agreement_pass && ...
    det.events.capacity_enter.candidate_count==2 && det.events.capacity_exit.candidate_count==2 && ...
    det.events.full_start.candidate_count==2 && det.events.release.candidate_count==2);
assert(numel(cmp.events.capacity_exit.candidates)==2 && ...
    strcmp(cmp.events.capacity_exit.status,'multiple_candidates'));
record('multiple_candidates_and_repeated_boundary_visits');

% 三个中间控制单元仍是三个；不能通过删除 transition 得到通过旗标。
t=(0:7)'; q=[0.5;0.6;0.7;0.8;1;0;0];
x=[0.6*ones(8,1) [0.15;0.15;0.14;0.13;0.12;0.10;0.11;0.12]];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(0,2.5,5,x(1,:)',x(4,:)',x(6,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(~det.diagnostics.passed && ~cmp.agreement_pass && ...
    det.events.capacity_exit.transition_cells==3 && ...
    ~cmp.events.capacity_exit.transition_width_pass);
assert(contains(det.observed_sequence,'transition') && ...
    any(strcmp(det.diagnostics.issues,'long_intermediate_control')));
record('long_intermediate_control_preserved_and_rejected');

% 中间控制没有连接到完全跟踪，明确报告缺失与不支持的结构。
t=(0:4)'; q=[0;0;0.6;0]; x=[0.6*ones(5,1) 0.1*ones(5,1)];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,2.5,3,[NaN;NaN],x(3,:)',x(4,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(strcmp(cmp.events.full_start.status,'missing_event') && ~cmp.agreement_pass && ...
    any(strcmp(det.diagnostics.issues,'unexpected_stage_connection')));
record('missing_full_event_and_unclassified_control_bout');

% 纯阶段直接跳变：区间保持共享端点，不含理论时刻也可网格尺度一致。
t=(0:3)'; q=[0;1;0]; x=[0.6 0.10;0.55 0.12;0.5 0.08;0.45 0.10];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,1.25,2.25,[NaN;NaN],x(2,:)',x(3,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(isequal(cmp.events.full_start.interval,[1 1]) && cmp.agreement_pass && ...
    ~cmp.events.full_start.contains_theory && ...
    abs(cmp.events.full_start.time_distance_to_interval-0.25)<1e-12);
record('direct_jump_distance_without_false_containment');

% 不等距网格使用事件两侧真实单元最大宽度，而不是全时域步长。
t=[0;0.2;0.4;0.5;0.7]; q=[0;0.6;1;0];
x=[0.6 0.10;0.58 0.12;0.56 0.11;0.54 0.09;0.52 0.10];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,0.51,0.5,[NaN;NaN],x(3,:)',x(4,:)');
cmp=compare_numerical_events(det,ref,par,opts);
assert(isequal(cmp.events.full_start.interval,[0.2 0.4]) && ...
    abs(cmp.events.full_start.local_max_cell_width-0.2)<1e-12 && ...
    ~cmp.events.full_start.contains_theory && cmp.events.full_start.time_pass);
record('nonuniform_local_cell_distance');

% 安全集零控制无适用付费事件，不进行 NaN 时间比较。
t=(0:2)'; q=[0;0]; x=[0.2 0.05;0.19 0.04;0.18 0.03];
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(NaN,NaN,NaN,[NaN;NaN],[NaN;NaN],[NaN;NaN]);
cmp=compare_numerical_events(det,ref,par,opts);
assert(cmp.agreement_pass && strcmp(cmp.expected_structure,'0') && ...
    strcmp(cmp.events.release.status,'not_applicable') && ...
    ~cmp.capacity_control.applicable && isempty(cmp.capacity_control.max_absolute_error));
record('safe_zero_control_without_fabricated_events');

% 独立制造的平滑轨迹仅用于区间积分及 ODE 稠密输出的最短距离测试。
t=(0:4)'; dense=cell(4,1); x=zeros(5,2); x(1,:)=[0.8 par.K];
for k=1:4
    rate=0; if ismember(k,[2 3]), rate=0.02; end
    dense{k}=ode45(@(~,y) [-0.2*y(1);-rate],t(k:k+1),x(k,:)', ...
        odeset('RelTol',1e-11,'AbsTol',1e-13));
    x(k+1,:)=deval(dense{k},t(k+1))';
end
qbar=1-(par.gamma/(par.p*par.c*x(1,1)))*(exp(0.2)-1)/0.2;
q=[qbar;0.8;1;0];
trajectory=struct('dense_solutions',{dense},'t',t,'s',x(:,1),'i',x(:,2));
det=detect_numerical_events(t(1:end-1),q,t,x,par.K,opts);
ref=reference(0,1.4,3.2,x(1,:)',deval(dense{2},1.4),deval(dense{4},3.2));
cmp=compare_numerical_events(det,ref,par,opts,trajectory);
assert(cmp.agreement_pass && cmp.capacity_control.max_absolute_error<1e-9 && ...
    abs(qbar-(1-par.gamma/(par.p*par.c*x(1,1))))>0.01);
assert(strcmp(cmp.capacity_control.method,'ode_dense_output_interval_quadrature') && ...
    cmp.events.full_start.state_distance_available && ...
    cmp.events.full_start.reference_state_distance_to_event_segment<1e-7 && ...
    abs(cmp.events.full_start.closest_numerical_time-1.4)<1e-6);
record('dense_output_capacity_interval_average_and_state_segment_distance');
fallback=compare_numerical_events(det,ref,par,opts);
assert(strcmp(fallback.capacity_control.method,'piecewise_linear_node_interpolation_interval_integral') && ...
    ~fallback.events.full_start.state_distance_available && ...
    isequal(fallback.events.full_start.numerical_endpoint_states,x(2:3,:)'));
record('explicit_node_interpolation_fallback_and_endpoint_span');

% 验证输入时间网格；长度一致并不足以满足真实控制区间假设。
bad=t(1:end-1); bad(2)=bad(2)+0.01;
thrown=false;
try, detect_numerical_events(bad,q,t,x,par.K,opts);
catch err, thrown=strcmp(err.identifier,'detect_numerical_events:TimeGrid'); end
assert(thrown); record('mismatched_actual_control_interval_rejected');

report=struct('test','verify_numerical_events','passed',true,'case_count',numel(checks), ...
    'checks',{checks},'execution_type','synthetic_unit_tests_no_optimizer');
fprintf('NUMERICAL_EVENTS_CHECKS_OK cases=%d\n',numel(checks));

    function record(name), checks{end+1}=name; end
    function out=linearAverage(left,right)
        out=1-(par.gamma/(par.p*par.c))*log(right/left)/(right-left);
    end
end

function out=reference(cap,full,release,capstate,fullstate,releaseState)
exit=NaN; if isfinite(cap), exit=full; end
out=struct('events',struct('capacity_start',cap,'capacity_end',exit, ...
    'full_start',full,'release',release,'capacity_state',capstate, ...
    'full_state',fullstate,'release_state',releaseState));
end
