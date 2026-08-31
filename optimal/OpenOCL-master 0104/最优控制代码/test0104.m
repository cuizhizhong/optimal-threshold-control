% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%



function [solution,times,problem] = test0104
T=[];%T也是要求的最优解
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts,...
    'N',50,'d',2);
%N (integer): Number of control intervals. Defaults to 20.
%d (2<=d<=5):Degree of the interpolating polynomial in each control interval. Defaults to 3.


% Kt=-c1*exp(-delta)+exp(-mu)*(k+c1);
% dP/dt= gamma*P*(1-0.15*Kt-P/K)-beta*P*N/(1+w*P);
% dN/dt=eta*beta*P*N/(1+w*P)-delta*N;
%parameter
gamma=1; eta=0.45;beta=0.19;w=0.19;K=52;
c1=0.5;k=0.1;
%initial value
P0=10;N0=1;

problem.setParameter('gamma'   , gamma);
problem.setParameter('eta'   , eta);
problem.setParameter('beta'  , beta);
problem.setParameter('w' , w);
problem.setParameter('c1' , c1);
problem.setParameter('K', K);
problem.setParameter('k', k);
%problem.setParameter('mu', mu);

% intial state bounds
problem.setInitialBounds('P',     P0);
problem.setInitialBounds('N',     N0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
T=Tstates(end)
P=solution.states.P.value;N=solution.states.N.value;

figure
subplot(121)
hold on
plot(Tstates,P,'Color',[0.4940 0.1840 0.5560],'LineWidth',2)
plot(Tstates,N,'Color',[0.8500 0.3250 0.0980],'LineWidth',2)
legend('P(t)','N(t)')
hold off

delta=solution.controls.delta.value;
mu=solution.controls.mu.value;
subplot(122)
hold on
Tc=times.controls.value;
stairs([Tc Tstates(end)],[delta delta(end)],'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
stairs([Tc Tstates(end)],[mu mu(end)],'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
%plot(Tc,delta,'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
%plot(Tc,mu,'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
legend('\delta(t)','\mu(t)');
box on
snapnow;

end

function varsfun(svh)

%N=1;
EIL=20;

%lb:下限
%ub:上限
svh.addState('P', 'lb', 0, 'ub', EIL);
svh.addState('N', 'lb', 0, 'ub', inf);


%svh.addAlgVar('TN', 'lb', 0, 'ub', Tmax);
% % svh.addAlgVar('QT', 'lb', 0, 'ub', Qmax);
% Scalar u: -1 <= F <= 1

svh.addControl('delta', 'lb', 0, 'ub',1);
svh.addControl('mu', 'lb', 0, 'ub',1);

svh.addParameter('gamma');
svh.addParameter('eta');
svh.addParameter('beta');
svh.addParameter('w');
svh.addParameter('c1');
svh.addParameter('K');
svh.addParameter('k');
%svh.addParameter('mu');
end

function daefun(daeh,x,z,u,p)

Kt=-p.c1*exp(-u.delta)+exp(-u.mu)*(p.k+p.c1);
daeh.setODE('P', p.gamma*x.P*(1-0.15*Kt-x.P/p.K)-p.beta*x.P*x.N/(1+p.w*x.P));
daeh.setODE('N',p.eta*p.beta*x.P*x.N/(1+p.w*x.P)-u.delta*x.N);

%daeh.setAlgEquation(z.TN-p.delta*x.I - p.delta_q*x.Iq);
end

function pathcosts(ch,x,z,u,p)
ch.add( -1);
%max{T}=min{-T}=min(integral(-1,0,T));
end


