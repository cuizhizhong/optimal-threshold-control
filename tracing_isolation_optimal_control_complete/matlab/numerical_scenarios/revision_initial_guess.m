function [initial,initialGuess] = revision_initial_guess(par,x0,T,grid,guess)
% 非理论初猜由实际分段常数输入积分；不裁剪、压平或调整容量超出。
ts=grid.t_state(:); tc=grid.t_control(:); ti=grid.t_integrator(:);
edges=grid.control_interval_edges(:);
assert(numel(edges)==numel(tc)+1 && all(diff(edges)>0) && ...
    max(abs(edges(1:end-1)-tc))<1e-10 && abs(edges(end)-T)<1e-10 && abs(edges(1))<1e-10, ...
    'revision:InvalidInitialGrid','Initial-guess control intervals must span [0,T].');
initial=guess;
if strcmp(guess.type,'constant_control')
    assert(isscalar(guess.control) && isfinite(guess.control) && guess.control>=0 && guess.control<=1, ...
        'revision:InvalidInitialControl','Constant initial control must lie in [0,1].');
    uc=guess.control*ones(size(tc));
elseif strcmp(guess.type,'seeded_random')
    knots=unique([0:2:min(20,T) T])';
    assert(isfield(guess,'seed') && isscalar(guess.seed) && guess.seed==fix(guess.seed), ...
        'revision:InvalidSeed','seeded_random requires a fixed integer seed.');
    stream=RandStream('mt19937ar','Seed',guess.seed);
    values=0.15+0.70*rand(stream,numel(knots),1);
    if isfield(guess,'knot_times') && ~isempty(guess.knot_times)
        assert(isequal(guess.knot_times(:),knots) && isequal(guess.knot_values(:),values), ...
            'revision:RandomDefinitionMismatch','Stored random knots/values do not match the fixed seed.');
    end
    initial.generator='mt19937ar'; initial.interpolation='linear';
    initial.knot_times=knots; initial.knot_values=values; initial.value_bounds=[0.15 0.85];
    uc=interp1(knots,values,tc,'linear');
else
    error('revision:UnknownInitialization','Non-theory initializer cannot handle %s.',guess.type);
end
xs=NaN(numel(ts),2); xi=NaN(numel(ti),2); y=x0(:);
maxI=y(2); odeopts=odeset('RelTol',2e-10,'AbsTol',1e-13);
for k=1:numel(tc)
    left=edges(k); right=edges(k+1); q=uc(k);
    rhs=@(~,x) [-par.c*(par.p+(1-par.p)*q)*x(1)*x(2); ...
        (par.p*par.c*(1-q)*x(1)-par.gamma)*x(2)];
    sol=ode45(rhs,[left right],y,odeopts);
    ns=find(ts>=left & ts<=right); ni=find(ti>=left & ti<=right);
    if ~isempty(ns), xs(ns,:)=deval(sol,ts(ns)')'; end
    if ~isempty(ni), xi(ni,:)=deval(sol,ti(ni)')'; end
    maxI=max(maxI,max(sol.y(2,:))); y=deval(sol,right);
end
assert(all(isfinite(xs),'all') && all(isfinite(xi),'all'), ...
    'revision:UnfilledInitialStates','Initial-guess state sampling falls outside control intervals.');
if ~isfield(initial,'seed'), initial.seed=[]; end
if ~isfield(initial,'knot_times'), initial.knot_times=[]; end
if ~isfield(initial,'knot_values'), initial.knot_values=[]; end
initial.actual_control_guess=uc;
initialGuess=struct('t_state',ts,'states',xs,'node_states',xs, ...
    't_integrator',ti,'integrator_states',xi,'t_control',tc,'control',uc, ...
    'capacity_excess',max([0;xs(:,2)-par.K;xi(:,2)-par.K]), ...
    'integrator_sample_capacity_excess',max([0;xi(:,2)-par.K]), ...
    'ode_sample_capacity_excess',max(0,maxI-par.K), ...
    'state_control_correspondence','states integrated using actual piecewise constant control');
end
