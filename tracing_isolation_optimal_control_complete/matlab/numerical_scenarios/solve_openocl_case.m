function run = solve_openocl_case(par,x0,opts,guess)
% 独立直接配点问题。理论仅提供可选初猜，不进入目标或约束。
problem=ocl.Problem(opts.T,@varsfun,@daefun,@pathcosts, ...
    'N',opts.N,'d',opts.d,'controls_regularization',false, ...
    'casadi_options',opts.casadi_options,'verbose',false);
problem.setInitialBounds('S',x0(1)); problem.setInitialBounds('I',x0(2));
ig=problem.getInitialGuess(); colloc=problem.solver.collocationList{1};
H=opts.T*problem.stage.H_norm;
tv=ocl.Variable.create(ocl.simultaneous.timesStruct(opts.N,colloc.num_t), ...
    ocl.simultaneous.times(H,colloc));
ts=reshape(tv.states.value,[],1); tc=reshape(tv.controls.value,[],1); ti=reshape(tv.integrator.value,[],1);
if strcmp(guess.type,'analytic_reference')
    geom=build_theory_geometry(par);
    rs=analytic_reference(par,x0,geom,ts); ri=analytic_reference(par,x0,geom,ti);
    rc=analytic_reference(par,x0,geom,tc);
    xs=[rs.s rs.i]; xi=[ri.s ri.i]; uc=rc.q;
else
    q0=guess.control;
    rhs=@(~,x) dynamics(x,q0,par);
    sol=ode45(rhs,[0 opts.T],x0,odeset('RelTol',2e-10,'AbsTol',1e-13));
    xs=deval(sol,ts')'; xi=deval(sol,ti')'; uc=q0*ones(size(tc));
end
ig.states.S.set(xs(:,1)'); ig.states.I.set(xs(:,2)');
ig.integrator.states.S.set(xi(:,1)'); ig.integrator.states.I.set(xi(:,2)');
ig.controls.q.set(uc');
[solution,times,info]=problem.solve(ig);
run=struct('parameters',par,'x0',x0(:),'solver_settings',opts,'initialization',guess, ...
    't_state',reshape(times.states.value,[],1),'s_state',reshape(solution.states.S.value,[],1), ...
    'i_state',reshape(solution.states.I.value,[],1),'t_control',reshape(times.controls.value,[],1), ...
    'q_control',reshape(solution.controls.q.value,[],1),'success',logical(info.success), ...
    'return_status',info.ipopt_stats.return_status,'solver_info',info);
run.dt_control=diff([run.t_control;run.t_state(end)]);
assert(numel(run.q_control)==numel(run.dt_control) && all(run.dt_control>0));
run.J_openocl=par.p*par.c*sum(run.q_control.*run.dt_control);
run.environment=struct('matlab',version,'openocl',which('ocl'),'casadi',which('casadi.MX'));
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
