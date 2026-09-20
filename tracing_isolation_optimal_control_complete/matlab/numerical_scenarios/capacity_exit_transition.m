function out = capacity_exit_transition(arcs,theoryTime)
% 只识别相邻 q_B -> transition -> 1，不把其他跳跃误作容量退出。
out=struct('status','missing_transition','interval',[NaN NaN], ...
    'cells',0,'theory_time',theoryTime,'contains_theory',false,'supported',false);
matches=[];
for k=2:numel(arcs)-1
    if strcmp(arcs(k-1).type,'q_B') && strcmp(arcs(k).type,'transition') && ...
            strcmp(arcs(k+1).type,'1')
        matches(end+1)=k; %#ok<AGROW>
    end
end
if isempty(matches), return; end
if numel(matches)>1, out.status='ambiguous_transitions'; return; end
k=matches(1); a=arcs(k); out.interval=[a.t_start a.t_end]; out.cells=a.cells;
if any(~isfinite([out.interval theoryTime])) || a.t_end<=a.t_start || ...
        abs(arcs(k-1).t_end-a.t_start)>1e-10 || abs(a.t_end-arcs(k+1).t_start)>1e-10
    out.status='invalid_interval'; return
end
out.contains_theory=theoryTime>=a.t_start-1e-10 && theoryTime<=a.t_end+1e-10;
if a.cells~=1, out.status='multiple_cells'; return; end
if ~out.contains_theory, out.status='theory_outside'; return; end
out.status='single_cell_contains_theory'; out.supported=true;
end
