function assessment = assess_numerical_case(run,ref,par,opts)
% 原始控制重积分、独立事件识别和尾段检查；不修剪状态或控制。
t=run.t_state(:); q=run.q_control(:); n=numel(q);
assert(numel(t)==n+1 && all(isfinite([t;run.s_state;run.i_state;q])));
odeopts=odeset('RelTol',opts.ode_rel_tol,'AbsTol',opts.ode_abs_tol);
y=zeros(n+1,2); y(1,:)=run.x0'; peak=y(1,2); peakTime=0;
for k=1:n
    rhs=@(~,x) [-par.c*(par.p+(1-par.p)*q(k))*x(1)*x(2); ...
        (par.p*par.c*(1-q(k))*x(1)-par.gamma)*x(2)];
    sol=ode45(rhs,t(k:k+1),y(k,:)',odeopts);
    y(k+1,:)=deval(sol,t(k+1))';
    [pk,ix]=max(sol.y(2,:)); pt=sol.x(ix);
    % 常值控制区间内部峰值发生在 s=gamma/[pc(1-q)]。
    if q(k)<1
        hq=par.gamma/(par.p*par.c*(1-q(k)));
        if y(k,1)>hq && y(k+1,1)<hq
            tp=fzero(@(v) susceptible(sol,v)-hq,t(k:k+1));
            yp=deval(sol,tp); pk=yp(2); pt=tp;
        end
    end
    if pk>peak, peak=pk; peakTime=pt; end
end
assessment.reintegration=struct('t',t,'s',y(:,1),'i',y(:,2),'max_i',peak,'peak_time',peakTime);
assessment.capacity_excess=max(0,peak-par.K);
assessment.state_discrepancy=max(abs(y-[run.s_state run.i_state]),[],'all');
assessment.initial_error=max(abs([run.s_state(1);run.i_state(1)]-run.x0));
assessment.control_violation=max([0;-q;q-1]);
assessment.state_violation=max([0;-run.s_state;-run.i_state;run.s_state-1;run.i_state-par.K]);
tail=tail_diagnostic(run.t_control,q,run.s_state(end),run.i_state(end), ...
    par,t(end),opts.tail_duration,opts.tail_control_tolerance);
assessment.tail_max_q=tail.max_abs_q_on_tail;
assessment.terminal_peak=tail.zero_control_future_peak;
assessment.terminal_safe=tail.zero_control_continuation_safe;
assessment.reintegrated_terminal_peak=safe_peak(y(end,1),y(end,2),par.gamma/(par.p*par.c));
assessment.tail=tail;
% 标签 0=自然/解除，1=完全跟踪，2=容量，3=未归类过渡。
epsq=opts.event_control_threshold;
label=3*ones(n,1); label(abs(q)<=epsq)=0; label(q>=1-epsq)=1;
atcap=max(abs([run.i_state(1:end-1)-par.K run.i_state(2:end)-par.K]),[],2)<=opts.event_capacity_threshold;
label(atcap & q>epsq & q<1-epsq)=2;
starts=[1;find(diff(label)~=0)+1]; stops=[starts(2:end)-1;n];
arcs=struct('type',{},'t_start',{},'t_end',{},'cells',{}); words={};
names={'0','1','q_B','transition'};
for j=1:numel(starts)
    a=starts(j); b=stops(j); kind=label(a);
    arcs(j)=struct('type',names{kind+1},'t_start',t(a),'t_end',t(b+1),'cells',b-a+1);
    if kind~=3 && (isempty(words) || ~strcmp(words{end},names{kind+1}))
        words{end+1}=names{kind+1}; %#ok<AGROW>
    end
end
assessment.arcs=arcs; assessment.observed_structure=strjoin(words,' -> ');
assessment.transition_cells=sum(label==3);
assessment.events=struct('capacity_start',NaN,'capacity_end',NaN,'full_start',NaN, ...
    'release',NaN,'full_state',[NaN;NaN],'release_state',[NaN;NaN]);
ix=find(label==1,1);
if ~isempty(ix)
    assessment.events.full_start=t(ix);
    assessment.events.full_state=[run.s_state(ix);run.i_state(ix)];
end
ix=find(label~=0,1,'last');
if ~isempty(ix) && ix<n
    assessment.events.release=t(ix+1);
    assessment.events.release_state=[run.s_state(ix+1);run.i_state(ix+1)];
end
ix=find(label==2);
if ~isempty(ix)
    assessment.events.capacity_start=t(ix(1)); assessment.events.capacity_end=t(ix(end)+1);
end
assessment.relative_cost_difference=(run.J_openocl-ref.J_reference)/max(ref.J_reference,eps);
assessment.passed=run.success && assessment.capacity_excess<=opts.capacity_tolerance && ...
    assessment.state_discrepancy<=opts.state_tolerance && assessment.initial_error<=opts.state_tolerance && ...
    assessment.control_violation<=opts.control_tolerance && assessment.state_violation<=opts.state_tolerance && ...
    tail.control_returned_to_zero && tail.zero_control_continuation_safe && ...
    assessment.reintegrated_terminal_peak<=par.K+opts.capacity_tolerance;
assessment.notes='阶段由原始控制及容量接近程度识别；过渡单元保留，事件精度受网格限制。';
end

function s=susceptible(sol,t)
y=deval(sol,t); s=y(1);
end
