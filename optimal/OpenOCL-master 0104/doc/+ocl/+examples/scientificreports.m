% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%
function [solution,times,problem] = scientificreports

  problem = ocl.Problem(300, @varsfun, @daefun, @pathcosts,...
      'gridconstraints', @gridconstraints, 'terminalcost', @terminalcost,'N', 30);
  

  % intial state bounds
  problem.setInitialBounds('s',    1000);
  problem.setInitialBounds('e',     10);
  problem.setInitialBounds('a',     10);
  problem.setInitialBounds('i',     10);
  problem.setInitialBounds('r',     0);
  problem.setInitialBounds('p',     0);

  % Get and set initial guess
  initialGuess = problem.getInitialGuess();
  initialGuess.states.s.set(995);
  initialGuess.states.e.set(2);
  initialGuess.states.a.set(2); 
  initialGuess.states.i.set(1);
  initialGuess.states.r.set(0);
  initialGuess.states.r.set(0);
%     

  % Run solver to obtain solution
  [solution,times] = problem.solve(initialGuess);

  % plot solution
  figure
  hold on
  plot(times.states.value,solution.states.i.value,'-.','LineWidth',2)
  plot(times.states.value,solution.states.r.value,'--k','LineWidth',2)
  xlabel('time')
  legend({'infected','recovered'})
  
  figure
  hold on
  stairs(times.controls.value,solution.controls.alpha_a.value,'r','LineWidth',2)
  stairs(times.controls.value,solution.controls.alpha_i.value,'m','LineWidth',2)
  stairs(times.controls.value,solution.controls.k.value,'b','LineWidth',2)
  xlabel('time')
  legend({'\alpha_a','\alpha_i','k'})

  snapnow;
end

function varsfun(svh)
  % Scalar x:  -0.25 <= x <= inf
  % Scalar y: unbounded
  N=1e3;
  svh.addState('s', 'lb', 0, 'ub', N);
  svh.addState('e', 'lb', 0, 'ub', N);
  svh.addState('a', 'lb', 0, 'ub', N);
  svh.addState('i', 'lb', 0, 'ub', N);
  svh.addState('r', 'lb', 0, 'ub', N);
  svh.addState('p', 'lb', 0, 'ub', N);
  
  % Scalar u: -1 <= F <= 1
  svh.addControl('alpha_a', 'lb', 0.05, 'ub', 0.5);
  svh.addControl('alpha_i', 'lb', 0.01, 'ub', 0.3);
  svh.addControl('k', 'lb', 0.15, 'ub', 0.3);
end

function daefun(daeh,x,~,u,~)
  N=1e3;
  gamma=0;
  t_la=0.5;
  rho=0.1;
  beta=0.025;
  mu=0.025;
  daeh.setODE('s', -u.alpha_a/N*x.s*x.a-u.alpha_i/N*x.s*x.i+gamma*x.r);
  daeh.setODE('e', u.alpha_a/N*x.s*x.a+u.alpha_i/N*x.s*x.i-t_la*x.e);
  daeh.setODE('a', t_la*x.e-u.k*x.a-rho*x.a);
  daeh.setODE('i', u.k*x.a-beta*x.i-mu*x.i);
  daeh.setODE('r',rho*x.a+beta*x.i-gamma*x.r);
  daeh.setODE('p',mu*x.i);
end

function pathcosts(ch,x,~,u,~)
lambdak=0.1;
  ch.add( -u.alpha_a );
  ch.add( -u.alpha_i);
  ch.add( lambdak*u.k );
end

function gridconstraints(ch,~,~,x,~)
Ipeak=50;
  ch.add(x.i, '<=', Ipeak);

end

function terminalcost(ocl,x,~)
  ocl.add( x.i );
end
