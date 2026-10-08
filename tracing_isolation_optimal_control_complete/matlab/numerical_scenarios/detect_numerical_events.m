function out = detect_numerical_events(t_control,q_control,t_state,state_xy,K,opts)
% 仅由数值控制、重积分节点及识别阈值检测阶段，不读取解析参考。
% numerical_endpoint_states 的两列依次是区间左、右端点的 [s;i]。
t=t_state(:); tc=t_control(:); q=q_control(:); n=numel(q);
timeTol=setting(opts,'event_time_tolerance',1e-10);
epsq=setting(opts,'event_control_threshold',1e-3);
epsK=setting(opts,'event_capacity_threshold',2e-5);
maxCells=setting(opts,'event_max_transition_cells',2);
assert(n>=1 && numel(t)==n+1 && numel(tc)==n && ...
    isequal(size(state_xy),[n+1 2]),'detect_numerical_events:Dimensions', ...
    'Expected N controls/start times and N+1 two-component state nodes.');
assert(all(isfinite([t;tc;q;state_xy(:);K])) && all(diff(t)>0) && ...
    max(abs(tc-t(1:n)))<=timeTol,'detect_numerical_events:TimeGrid', ...
    'Control starts must equal the actual state interval endpoints.');
assert(epsq>0 && epsq<0.5 && epsK>0 && K>0 && ...
    maxCells>=0 && fix(maxCells)==maxCells && timeTol>=0, ...
    'detect_numerical_events:Thresholds','Invalid recognition thresholds.');

% 0=自然/解除，1=完全跟踪，2=付费容量段，3=未归类过渡。
label=3*ones(n,1);
label(abs(q)<=epsq)=0;
label(abs(q-1)<=epsq)=1;
atcap=max(abs(state_xy(1:n,2)-K),abs(state_xy(2:n+1,2)-K))<=epsK;
label(atcap & q>epsq & q<1-epsq)=2;
starts=[1;find(diff(label)~=0)+1]; stops=[starts(2:end)-1;n];
names={'0','1','q_B','transition'};
arcs=struct('type',{},'t_start',{},'t_end',{},'cells',{}, ...
    'first_cell',{},'last_cell',{},'cell_widths',{},'capacity_active',{});
for j=1:numel(starts)
    a=starts(j); b=stops(j);
    arcs(j)=struct('type',names{label(a)+1},'t_start',t(a), ...
        't_end',t(b+1),'cells',b-a+1,'first_cell',a,'last_cell',b, ...
        'cell_widths',diff(t(a:b+1))','capacity_active',label(a)==2);
end

% 保留每个候选。多个候选不借助理论挑选，也不合并离边/返边。
events=struct(); kinds={'intervention','capacity_enter','capacity_exit','full_start','release'};
for j=1:numel(kinds), events.(kinds{j})=emptyEvent(kinds{j}); end
for j=1:numel(arcs)
    a=arcs(j);
    if strcmp(a.type,'q_B')
        events.capacity_enter=append(events.capacity_enter,enterCandidate(j,'capacity_enter'));
        if j<numel(arcs)
            events.capacity_exit=append(events.capacity_exit,exitCandidate(j,'capacity_exit'));
        end
    elseif strcmp(a.type,'1')
        events.full_start=append(events.full_start,enterCandidate(j,'full_start'));
    elseif strcmp(a.type,'0') && j>1
        events.release=append(events.release,enterCandidate(j,'release'));
    end
    % 连续正控制块的首次单元给出干预候选；初始正控制以 [t0,t0] 记录。
    if ~strcmp(a.type,'0') && (j==1 || strcmp(arcs(j-1).type,'0'))
        if j==1
            c=candidate('intervention',t(1),t(1),[],0,'initial',a.type);
            c.status='initial_event';
        elseif strcmp(a.type,'transition')
            to='missing'; if j<numel(arcs), to=arcs(j+1).type; end
            c=candidate('intervention',a.t_start,a.t_end, ...
                a.first_cell:a.last_cell,j-1,'0',to);
            if ~ismember(to,{'q_B','1'}), c.status='unclassified_transition'; end
        else
            c=candidate('intervention',a.t_start,a.t_start,[],j-1,'0',a.type);
        end
        events.intervention=append(events.intervention,c);
    end
end
for j=1:numel(kinds), events.(kinds{j})=finalize(events.(kinds{j})); end

pure=arcs(~strcmp({arcs.type},'transition'));
out=struct('t',t,'q',q,'state_xy',state_xy,'K',K,'cell_labels',label, ...
    'arcs',arcs,'events',events,'observed_structure',strjoin({pure.type},' -> '), ...
    'observed_sequence',strjoin({arcs.type},' -> '),'transition_cells',sum(label==3));
out.thresholds=struct('control',epsq,'capacity',epsK,'max_transition_cells',maxCells, ...
    'time_tolerance',timeTol);
longBlocks=find(strcmp({arcs.type},'transition') & [arcs.cells]>maxCells);
ambiguous={};
for j=1:numel(kinds)
    if events.(kinds{j}).candidate_count>1, ambiguous{end+1}=kinds{j}; end %#ok<AGROW>
end
unexpected=[]; incomplete=[];
for j=1:numel(arcs)
    if ~strcmp(arcs(j).type,'transition'), continue; end
    left='initial'; right='missing';
    if j>1, left=arcs(j-1).type; end
    if j<numel(arcs), right=arcs(j+1).type; end
    if strcmp(right,'missing'), incomplete(end+1)=j; end %#ok<AGROW>
    allowed=(strcmp(left,'initial') && ismember(right,{'q_B','1'})) || ...
        (strcmp(left,'0') && ismember(right,{'q_B','1'})) || ...
        (strcmp(left,'q_B') && strcmp(right,'1')) || ...
        (strcmp(left,'1') && strcmp(right,'0'));
    if ~allowed, unexpected(end+1)=j; end %#ok<AGROW>
end
directUnexpected=[];
for j=1:numel(arcs)-1
    left=arcs(j).type; right=arcs(j+1).type;
    if strcmp(left,'transition') || strcmp(right,'transition'), continue; end
    allowed=(strcmp(left,'0') && ismember(right,{'q_B','1'})) || ...
        (strcmp(left,'q_B') && strcmp(right,'1')) || ...
        (strcmp(left,'1') && strcmp(right,'0'));
    if ~allowed, directUnexpected(end+1)=j; end %#ok<AGROW>
end
issues={};
if ~isempty(longBlocks), issues{end+1}='long_intermediate_control'; end
if ~isempty(ambiguous), issues{end+1}='multiple_event_candidates'; end
if ~isempty(unexpected) || ~isempty(directUnexpected), issues{end+1}='unexpected_stage_connection'; end
if ~isempty(incomplete), issues{end+1}='incomplete_transition_at_horizon'; end
out.diagnostics=struct('passed',isempty(issues),'issues',{issues}, ...
    'long_transition_arc_indices',longBlocks,'ambiguous_events',{ambiguous}, ...
    'unexpected_transition_arc_indices',unexpected, ...
    'unexpected_direct_arc_indices',directUnexpected, ...
    'incomplete_transition_arc_indices',incomplete, ...
    'natural_capacity_contact_cells',find(atcap & label==0)', ...
    'capacity_arc_count',sum(strcmp({arcs.type},'q_B')));
out.notes='数值阶段及候选完整保留；自然零控制回触容量不标为付费容量段。';

    function c=enterCandidate(j,kind)
        a=arcs(j);
        if j==1
            c=candidate(kind,a.t_start,a.t_start,[],0,'initial',a.type);
            c.status='initial_event';
        elseif strcmp(arcs(j-1).type,'transition')
            b=arcs(j-1); from='initial'; if j>2, from=arcs(j-2).type; end
            c=candidate(kind,b.t_start,b.t_end,b.first_cell:b.last_cell,j-2,from,a.type);
        else
            c=candidate(kind,a.t_start,a.t_start,[],j-1,arcs(j-1).type,a.type);
        end
    end

    function c=exitCandidate(j,kind)
        a=arcs(j); b=arcs(j+1);
        if strcmp(b.type,'transition')
            to='missing'; if j+2<=numel(arcs), to=arcs(j+2).type; end
            c=candidate(kind,b.t_start,b.t_end,b.first_cell:b.last_cell,j,'q_B',to);
            if ~strcmp(to,'1'), c.status='unexpected_successor'; end
        else
            c=candidate(kind,a.t_end,a.t_end,[],j,'q_B',b.type);
            if ~strcmp(b.type,'1'), c.status='unexpected_successor'; end
        end
    end

    function c=candidate(kind,left,right,cells,previous,from,to)
        c=eventTemplate(kind); c.status='detected'; c.interval=[left right];
        c.transition_cell_indices=cells; c.transition_cells=numel(cells);
        c.from_type=from; c.to_type=to; c.detected_from_control=true;
        c.capacity_active=strcmp(from,'q_B') || strcmp(to,'q_B');
        il=find(abs(t-left)<=timeTol,1); ir=find(abs(t-right)<=timeTol,1);
        assert(~isempty(il) && ~isempty(ir),'Event interval must use original grid endpoints.');
        c.numerical_endpoint_states=state_xy([il ir],:)';
        c.state_span=norm(state_xy(ir,:)-state_xy(il,:));
        % 一个邻近最大控制单元宽度；绝不扩展真实事件区间。
        nearby=max(1,il-1):min(n,ir);
        c.local_max_cell_width=max(diff(t(nearby(1):nearby(end)+1)));
        c.interval_node_indices=[il ir]; c.preceding_arc_index=previous;
    end
end

function out=emptyEvent(kind)
out=eventTemplate(kind); out.status='missing_event';
out.candidate_count=0; out.candidates=repmat(eventTemplate(kind),0,1);
end

function out=eventTemplate(kind)
out=struct('kind',kind,'status','missing_event','interval',[NaN NaN], ...
    'transition_cells',0,'transition_cell_indices',[], ...
    'detected_from_control',false,'capacity_active',false, ...
    'numerical_endpoint_states',nan(2,2),'state_span',NaN, ...
    'local_max_cell_width',NaN,'interval_node_indices',[NaN NaN], ...
    'preceding_arc_index',NaN,'from_type','missing','to_type','missing');
end

function out=append(out,item)
out.candidates(end+1,1)=item;
out.candidate_count=numel(out.candidates);
end

function out=finalize(out)
count=out.candidate_count; candidates=out.candidates;
if count==1
    out=candidates(1); out.candidate_count=count; out.candidates=candidates;
elseif count>1
    out.status='multiple_candidates';
end
end

function out=setting(opts,name,fallback)
out=fallback; if isfield(opts,name), out=opts.(name); end
end
