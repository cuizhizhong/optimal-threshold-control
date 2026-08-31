% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%



function [solution,times,problem] = xyp_2_0102
T=400;%控制时长为0到T
N=T;%Number of control intervals. 
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts,...
    'N',N,'d',5);
%N (integer): Number of control intervals. Defaults to 20.
%d (2<=d<=5):Degree of the interpolating polynomial in each control interval. Defaults to 3.



%parameter
r=1;k=52;w=0.1;theta=1.5;eta=0.45;delta=0.36;tau=1.5;mu=1.2;ET=6;

global EIL
EIL=7;

%initial value
X0=4;Y0=5;p0=0.3;

problem.setParameter('r'   , r);
problem.setParameter('k'   , k);
problem.setParameter('w'   , w);
problem.setParameter('theta'   , theta);
problem.setParameter('eta'  , eta);
problem.setParameter('delta'   , delta);
problem.setParameter('tau'   , tau);
problem.setParameter('mu'   , mu);
problem.setParameter('ET'   , ET);


% intial state bounds
problem.setInitialBounds('Xt',     X0);
problem.setInitialBounds('Yt',     Y0);
problem.setInitialBounds('pt',     p0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();
%initialGuess.states.Nt


% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);


% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
Xt=solution.states.Xt.value; Yt=solution.states.Yt.value;
pt=solution.states.pt.value;


figure
subplot(131)
hold on
plot(Tstates,Xt,'Color',[0.4940 0.1840 0.5560],'LineWidth',2)
plot(Tstates,Yt,'Color',[0.8500 0.3250 0.0980],'LineWidth',2)
legend('x^{*}(t)','y^{*}(t)')
xlabel('Time (Day)')
xlim([0 T])
title('(a)')
hold off
box on


subplot(132)
hold on
plot(Tstates,pt,'Color',[0.4940 0.1840 0.5560],'LineWidth',2)
legend('p^{*}(t)')
xlim([0 T])
xlabel('Time (Day)')
hold off
title('(b)')
box on

beta0=solution.controls.beta0.value;
beta1=solution.controls.beta1.value;

subplot(133)
Tc=times.controls.value;
hold on
plot(Tc,beta0,'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
plot(Tc,beta1,'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
legend('\beta_0^{*}(t)','\beta_1^{*}(t)');
%xlim([0 50])
xlabel('Time (Day)')
title('(c)')
box on
snapnow;

%cost
size(beta0),size(pt)
L =beta0.*pt(1:end-1)+beta1.*(1-pt(1:end-1))+(1-pt(1:end-1))*tau;            % 积分项
L=L*T/N;
f = trapz(Tc,L)
figure(5)
plot(Tc,L)
end

function varsfun(svh)

global EIL
%lb:下限
%ub:上限
svh.addState('Xt', 'lb', 0, 'ub', EIL);
svh.addState('Yt', 'lb', 0, 'ub', inf);
svh.addState('pt', 'lb', 0, 'ub', 1);



svh.addControl('beta0', 'lb', 0, 'ub',0.05);
svh.addControl('beta1', 'lb', 0.1, 'ub',0.3);

svh.addParameter('r');
svh.addParameter('k');
svh.addParameter('w');
svh.addParameter('theta');
svh.addParameter('eta');
svh.addParameter('delta');
svh.addParameter('tau');
svh.addParameter('mu');
svh.addParameter('ET');
end

function daefun(daeh,x,z,u,p)

daeh.setODE('Xt', p.r*x.Xt*(1-x.Xt/p.k)-(x.pt*u.beta0+(1-x.pt)*u.beta1)*x.Xt*x.Yt/(1+p.w*x.Xt)-(1-x.pt)*p.theta*x.Xt);
daeh.setODE('Yt', p.eta*(x.pt*u.beta0+(1-x.pt)*u.beta1)*x.Xt*x.Yt/(1+p.w*x.Xt)-p.delta*x.Yt+(1-x.pt)*p.tau);
daeh.setODE('pt',p.mu*x.pt*(1-x.pt)*(1-x.Xt/p.ET));

%daeh.setAlgEquation(z.TN-p.delta*x.I - p.delta_q*x.Iq);
end

function pathcosts(ch,x,z,u,p)
%ch.add( -1);
ch.add( u.beta1.*(1-x.pt));
ch.add( u.beta0.*x.pt);
ch.add((1-x.pt)*p.tau);

end

