% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%
function [solution,times,problem] = example

problem = ocl.Problem(1, @varsfun, @daefun, @pathcosts,...
    'N', 200);


% intial state bounds
problem.setInitialBounds('x',    0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();
% initialGuess.states.s.set(995);
% initialGuess.states.e.set(2);
% initialGuess.states.a.set(2);
% initialGuess.states.i.set(1);
% initialGuess.states.r.set(0);
% initialGuess.states.r.set(0);
%

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution

figure
hold on
plot(times.controls.value,solution.controls.u1.value,'r','LineWidth',2)
plot(times.controls.value,solution.controls.u2.value,'r','LineWidth',2)
xlabel('time')


snapnow;
end

function varsfun(svh)
% Scalar x:  -0.25 <= x <= inf
% Scalar y: unbounded

svh.addState('x', 'lb', -inf, 'ub', inf);

% Scalar u: -1 <= F <= 1
svh.addControl('u1', 'lb', 1, 'ub', 2);
svh.addControl('u2', 'lb', -inf, 'ub', inf);
end

function daefun(daeh,x,~,u,~)

daeh.setODE('x',u.u1+u.u2);

end

function pathcosts(ch,x,~,u,~)
ch.add( -x.x);
ch.add( 1/8*u.u1^2);
ch.add( 1/2*u.u2^2);
end

% function gridconstraints(ch,~,~,x,~)
% Ipeak=50;
% ch.add(x.i, '<=', Ipeak);
% 
% end
% 
% function terminalcost(ocl,x,~)
% ocl.add( x.i );
% end
