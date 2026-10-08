function out = capacity_exit_transition(arcs,theoryTime,opts)
% 兼容旧导出入口：先独立检测 q_B -> (transition ->) 1，再作可选比较。
% supported 只表示真实单控制单元包含；grid_scale_pass 采用新的网格尺度口径。
if nargin<3, opts=struct(); end
tol=setting(opts,'event_time_tolerance',1e-10);
maxCells=setting(opts,'event_max_transition_cells',2);
distanceCells=setting(opts,'event_distance_cells',1);
candidates=struct('status',{},'interval',{},'cells',{},'transition_cells',{}, ...
    'local_max_cell_width',{});
for k=1:numel(arcs)-1
    if ~strcmp(arcs(k).type,'q_B'), continue; end
    if strcmp(arcs(k+1).type,'1')
        item=struct('status','direct_jump','interval',[arcs(k).t_end arcs(k).t_end], ...
            'cells',0,'transition_cells',0,'local_max_cell_width', ...
            max([width(arcs(k)) width(arcs(k+1))]));
        if abs(arcs(k).t_end-arcs(k+1).t_start)>tol, item.status='invalid_interval'; end
    elseif strcmp(arcs(k+1).type,'transition') && k+2<=numel(arcs) && strcmp(arcs(k+2).type,'1')
        a=arcs(k+1);
        item=struct('status','detected','interval',[a.t_start a.t_end], ...
            'cells',a.cells,'transition_cells',a.cells,'local_max_cell_width', ...
            max([width(arcs(k)) width(a) width(arcs(k+2))]));
        if any(~isfinite(item.interval)) || a.t_end<=a.t_start || ...
                a.cells<1 || fix(a.cells)~=a.cells || ...
                abs(arcs(k).t_end-a.t_start)>tol || abs(a.t_end-arcs(k+2).t_start)>tol
            item.status='invalid_interval';
        end
    else
        continue
    end
    candidates(end+1)=item; %#ok<AGROW>
end
out=struct('status','missing_transition','interval',[NaN NaN],'cells',0, ...
    'transition_cells',0,'candidate_count',numel(candidates),'candidates',candidates, ...
    'local_max_cell_width',NaN,'theory_time',[],'contains_theory',false, ...
    'time_distance_to_interval',[],'supported',false,'grid_scale_pass',false);
if numel(candidates)>1, out.status='ambiguous_transitions';
elseif numel(candidates)==1
    item=candidates(1); fields=fieldnames(item);
    for k=1:numel(fields), out.(fields{k})=item.(fields{k}); end
end
if nargin<2, return; end
if isempty(theoryTime) || (isscalar(theoryTime) && isnan(theoryTime))
    if isempty(candidates), out.status='not_applicable'; else, out.status='unexpected_event'; end
    return
end
assert(isscalar(theoryTime) && isfinite(theoryTime),'Invalid theoretical event time.');
out.theory_time=theoryTime;
if numel(candidates)~=1 || strcmp(out.status,'invalid_interval'), return; end
out.time_distance_to_interval=max([out.interval(1)-theoryTime 0 theoryTime-out.interval(2)]);
out.contains_theory=theoryTime>=out.interval(1)-tol && theoryTime<=out.interval(2)+tol;
out.grid_scale_pass=out.cells<=maxCells && ...
    out.time_distance_to_interval<=distanceCells*out.local_max_cell_width+tol;
out.supported=out.cells==1 && out.contains_theory;
if out.cells>maxCells, out.status='too_many_transition_cells';
elseif ~out.grid_scale_pass, out.status='outside_grid_scale';
elseif out.supported, out.status='single_cell_contains_theory';
elseif out.cells==0, out.status='direct_jump';
elseif out.contains_theory, out.status='transition_interval_contains_theory';
else, out.status='grid_scale_agreement_without_containment'; end
end

function out=width(arc)
if isfield(arc,'cell_widths') && ~isempty(arc.cell_widths)
    out=max(arc.cell_widths);
else
    out=(arc.t_end-arc.t_start)/max(arc.cells,1);
end
end

function out=setting(opts,name,fallback)
out=fallback; if isfield(opts,name), out=opts.(name); end
end
