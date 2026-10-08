function grid = validate_numerical_run_grid(run,opts)
% 重积分采用控制区间端点作为状态节点；先验证这一实际假设。
if nargin<2, opts=struct(); end
tol=1e-10; if isfield(opts,'grid_time_tolerance'), tol=opts.grid_time_tolerance; end
names={'t_state','t_control','s_state','i_state','q_control','x0'};
for k=1:numel(names)
    assert(isfield(run,names{k}),'numerical:MissingArray','Missing array: %s',names{k});
    validateattributes(run.(names{k}),{'numeric'},{'real','finite','vector'});
end
t=run.t_state(:); tc=run.t_control(:); q=run.q_control(:); n=numel(q);
assert(n>0 && numel(tc)==n && numel(t)==n+1 && ...
    numel(run.s_state)==n+1 && numel(run.i_state)==n+1 && numel(run.x0)==2, ...
    'numerical:ArrayDimensions','State/control arrays do not match control intervals.');
edges=[tc;t(end)]; dt=diff(edges);
assert(abs(t(1))<=tol && all(diff(t)>0) && all(dt>0), ...
    'numerical:InvalidTime','Time must begin at zero and increase strictly.');
assert(max(abs(t-edges))<=tol,'numerical:GridEndpoints', ...
    'State times differ from actual piecewise-constant control interval endpoints.');
if isfield(run,'dt_control')
    assert(numel(run.dt_control)==n && max(abs(run.dt_control(:)-dt))<=tol, ...
        'numerical:ControlDurations','Saved control durations differ from actual intervals.');
end
if isfield(run,'actual_grid')
    g=run.actual_grid;
    assert(numel(g.t_state)==n+1 && numel(g.t_control)==n && ...
        max(abs(g.t_state(:)-t))<=tol && max(abs(g.t_control(:)-tc))<=tol, ...
        'numerical:FingerprintGrid','Returned grid differs from fingerprinted grid.');
    if isfield(g,'control_interval_edges')
        assert(numel(g.control_interval_edges)==n+1 && ...
            max(abs(g.control_interval_edges(:)-edges))<=tol,'numerical:FingerprintGrid');
    end
    if isfield(g,'dt_control')
        assert(numel(g.dt_control)==n && max(abs(g.dt_control(:)-dt))<=tol, ...
            'numerical:FingerprintGrid','Fingerprint control durations differ from actual intervals.');
    end
end
for field={'solver_settings','actual_solver_settings'}
    if isfield(run,field{1}) && isfield(run.(field{1}),'T')
        assert(abs(run.(field{1}).T-t(end))<=tol,'numerical:IncompleteHorizon', ...
            'Returned control intervals do not cover the complete requested horizon.');
    end
end
grid=struct('t',t,'edges',edges,'dt',dt,'time_tolerance',tol);
end
