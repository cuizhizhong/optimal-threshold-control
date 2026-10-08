function prepared = prepare_openocl_case(par,x0,opts,guess)
% 构建原OCP及真正传入求解器的初猜；此函数不调用solve。
assert(~opts.controls_regularization && strcmp(opts.terminal_constraint,'none'), ...
    'The approved OCP has no control regularization or terminal constraint.');
opts.initialization=guess.type;
problem=ocl.Problem(opts.T,@varsfun,@daefun,@pathcosts, ...
    'N',opts.N,'d',opts.d,'controls_regularization',false, ...
    'casadi_options',opts.casadi_options,'verbose',false);
problem.setInitialBounds('S',x0(1)); problem.setInitialBounds('I',x0(2));
ig=problem.getInitialGuess(); colloc=problem.solver.collocationList{1};
H=opts.T*problem.stage.H_norm;
tv=ocl.Variable.create(ocl.simultaneous.timesStruct(numel(H),colloc.num_t), ...
    ocl.simultaneous.times(H,colloc));
ts=reshape(tv.states.value,[],1); tc=reshape(tv.controls.value,[],1); ti=reshape(tv.integrator.value,[],1);
if strcmp(guess.type,'analytic_reference')
    geom=build_theory_geometry(par);
    rs=analytic_reference(par,x0,geom,ts); ri=analytic_reference(par,x0,geom,ti);
    rc=analytic_reference(par,x0,geom,tc);
    xs=[rs.s rs.i]; xi=[ri.s ri.i]; uc=rc.q;
elseif strcmp(guess.type,'constant_control')
    q0=guess.control;
    rhs=@(~,x) dynamics(x,q0,par);
    sol=ode45(rhs,[0 opts.T],x0,odeset('RelTol',2e-10,'AbsTol',1e-13));
    xs=deval(sol,ts')'; xi=deval(sol,ti')'; uc=q0*ones(size(tc));
else
    error('numerical:UnknownInitialization','Unknown initialization type: %s',guess.type);
end
ig.states.S.set(xs(:,1)'); ig.states.I.set(xs(:,2)');
ig.integrator.states.S.set(xi(:,1)'); ig.integrator.states.I.set(xi(:,2)');
ig.controls.q.set(uc');
actualOptions=opts.casadi_options;
% 当前OpenOCL的verbose=false实际加入这两个设置。
actualOptions.ipopt.print_level=0; actualOptions.print_time=0;
settings=struct('T',opts.T,'N',numel(H),'d',colloc.order,'nlp_solver','ipopt', ...
    'nlp_casadi_mx',false,'controls_regularization',false, ...
    'controls_regularization_value',1e-6,'terminal_constraint','none', ...
    'terminal_cost','none','grid_constraints','none','grid_costs','none', ...
    'casadi_options',actualOptions,'verbose',false,'state_lower_bounds',[0 0], ...
    'state_upper_bounds',[1 par.K],'control_lower_bound',0,'control_upper_bound',1, ...
    'initial_state',x0(:),'unspecified_ipopt_options','plugin defaults identified by environment fingerprint', ...
    'initialization_ode_options',struct('RelTol',2e-10,'AbsTol',1e-13));
grid=struct('t_state',ts,'t_control',tc,'t_integrator',ti, ...
    'control_interval_edges',[tc;ts(end)],'dt_control',diff([tc;ts(end)]), ...
    'H_norm',problem.stage.H_norm(:),'collocation_tau',colloc.tau_root(:));
assert(numel(tc)==numel(H) && all(grid.dt_control>0));
initial=guess;
if ~isfield(initial,'seed'), initial.seed=[]; end
if ~isfield(initial,'knot_times'), initial.knot_times=[]; end
if ~isfield(initial,'knot_values'), initial.knot_values=[]; end
initial.actual_control_guess=uc;
initialGuess=struct('t_state',ts,'states',xs,'node_states',xs, ...
    't_integrator',ti,'integrator_states',xi,'t_control',tc,'control',uc, ...
    'capacity_excess',max([0;xs(:,2)-par.K;xi(:,2)-par.K]));
prepared=struct('problem',problem,'ig',ig,'parameters',par,'x0',x0(:), ...
    'solver_settings',opts,'actual_solver_settings',settings,'actual_grid',grid, ...
    'initialization',initial,'initial_guess',initialGuess);
    function varsfun(svh)
        svh.addState('S','lb',0,'ub',1);
        svh.addState('I','lb',0,'ub',par.K);
        svh.addControl('q','lb',0,'ub',1);
    end
    function daefun(daeh,x,~,u,~)
        daeh.setODE('S',-par.c*(par.p+(1-par.p)*u.q)*x.S*x.I);
        daeh.setODE('I',(par.p*par.c*(1-u.q)*x.S-par.gamma)*x.I);
    end
    function pathcosts(ch,~,~,u,~)
        ch.add(par.p*par.c*u.q);
    end
end

function f=dynamics(x,q,p)
f=[-p.c*(p.p+(1-p.p)*q)*x(1)*x(2);(p.p*p.c*(1-q)*x(1)-p.gamma)*x(2)];
end
