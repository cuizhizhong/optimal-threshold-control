% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%



function [solution,times,problem] = xp1218
T=100;%T也是要求的最优解
problem = ocl.Problem(10, @varsfun, @daefun, @pathcosts,...
    'N',T,'d',4);
%N (integer): Number of control intervals. Defaults to 20.
%d (2<=d<=5):Degree of the interpolating polynomial in each control interval. Defaults to 3.


% Kt=-c1*exp(-delta)+exp(-mu)*(k+c1);
% dP/dt= gamma*P*(1-0.15*Kt-P/K)-beta*P*N/(1+w*P);
% dN/dt=eta*beta*P*N/(1+w*P)-delta*N;
%parameter
r=0.7;ET=1;%EIL=1.2;
eta=2;
%initial value
N0=0.5;p0=0.8;

problem.setParameter('r'   , r);
problem.setParameter('ET'   , ET);
problem.setParameter('eta'  , eta);


% intial state bounds
problem.setInitialBounds('Nt',     N0);
problem.setInitialBounds('pt',     p0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
size(Tstates)
T=Tstates(1)
Nt=solution.states.Nt.value; pt=solution.states.pt.value;
Tstates(1)
pt(1)

figure
subplot(121)
hold on
yyaxis left
plot(Tstates,Nt,'Color',[0.4940 0.1840 0.5560],'LineWidth',2)
yyaxis right
plot(Tstates,pt,'Color',[0.8500 0.3250 0.0980],'LineWidth',2)
legend('N(t)','p(t)')
%xlim([0 50])
hold off
box on

delta0=solution.controls.delta0.value;
delta1=solution.controls.delta1.value;
delta0(1)
delta1(1)
subplot(122)
Tc=times.controls.value;
hold on
%yyaxis left
% stairs([Tc Tstates(end)],[delta0 delta0(end)],'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
% stairs([Tc Tstates(end)],[delta1 delta1(end)],'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
stairs(Tc,delta0,'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
%yyaxis right
stairs(Tc,delta1,'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
legend('\delta_0(t)','\delta_1(t)');
%xlim([0 50])
box on
snapnow;

%cost
size(delta0),size(pt)
 L =delta0.*pt(1:end-1)+delta1.*(1-pt(1:end-1));            % 积分项
 f = trapz(Tc,L)  

end

function varsfun(svh)

%N=1;
EIL=1.2;

%lb:下限
%ub:上限
svh.addState('Nt', 'lb', 0, 'ub', EIL);
svh.addState('pt', 'lb', 0, 'ub', 1);


%svh.addAlgVar('TN', 'lb', 0, 'ub', Tmax);
% % svh.addAlgVar('QT', 'lb', 0, 'ub', Qmax);
% Scalar u: -1 <= F <= 1

svh.addControl('delta0', 'lb', 0, 'ub',0.2);
svh.addControl('delta1', 'lb', 0.8, 'ub',1);

svh.addParameter('r');
svh.addParameter('ET');
svh.addParameter('eta');
%svh.addParameter('mu');
end

function daefun(daeh,x,z,u,p)


daeh.setODE('Nt', p.r*x.Nt-(u.delta0*x.pt+(1-x.pt)*u.delta1)*x.Nt);
daeh.setODE('pt',p.eta*x.pt*(1-x.pt)*(1-x.Nt/p.ET));

%daeh.setAlgEquation(z.TN-p.delta*x.I - p.delta_q*x.Iq);
end

function pathcosts(ch,x,z,u,p)
%ch.add( -1);
ch.add( u.delta1.*(1-x.pt));
  ch.add( u.delta0.*x.pt);
%max{T}=min{-T}=min(integral(-1,0,T));
end


