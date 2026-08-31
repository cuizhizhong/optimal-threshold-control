% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%



function [solution,times,problem] = xp1218
T=400;%控制时长为0到T
N=T;%Number of control intervals. 
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts,...
    'N',N,'d',5);
%N (integer): Number of control intervals. Defaults to 20.
%d (2<=d<=5):Degree of the interpolating polynomial in each control interval. Defaults to 3.


%parameter
r=0.7;ET=1;eta=2;
%initial value
X0=0.5;p0=0.8;
global EIL
EIL=1.2;

problem.setParameter('r'   , r);
problem.setParameter('ET'   , ET);
problem.setParameter('eta'  , eta);


% intial state bounds
problem.setInitialBounds('Xt',     X0);
problem.setInitialBounds('pt',     p0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();
%initialGuess.states.Nt

% delta0=0.2;delta1=1;
% par=[r eta delta0 delta1 ET];
% options = odeset('RelTol',1e-12,'AbsTol',[1e-12 1e-12]);
% [T,Y] = ode45(@(t,y) xp0(t,y,par),[0:0.5:50],[N0 p0],options);
% x_0=Y(:,1);p_0=Y(:,2);
% item=find(x_0>=1.2);
% x_0(item)=x_0(item);%找出x>EIL的值，将其强制设为最大值EIL
% %X_guess=[x_0;p_0];
% initialGuess.states.Nt.set(x_0');
% initialGuess.states.pt.set(p_0');
% initialGuess.controls.delta0.set(0.2);
% initialGuess.controls.delta1.set(1);

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
Xt=solution.states.Xt.value; pt=solution.states.pt.value;

figure
subplot(131)
hold on
%yyaxis left
plot(Tstates,Xt,'Color',[0.4940 0.1840 0.5560],'LineWidth',2)
%yyaxis right
%plot(Tstates,pt,'Color',[0.8500 0.3250 0.0980],'LineWidth',2)
%legend('x(t)','p(t)')
xlabel('Time (Day)')
ylabel('x^{*}(t)')
xlim([0 T])
title('(a)')
hold off
box on


subplot(132)
hold on
plot(Tstates,pt,'Color',[0.8500 0.3250 0.0980],'LineWidth',2)
xlabel('Time (Day)')
ylabel('p^{*}(t)')
xlim([0 T])
title('(b)')
hold off
box on
%size(Xt)

delta0=solution.controls.delta0.value;
delta1=solution.controls.delta1.value;
Tc=times.controls.value;

subplot(133)
hold on
% stairs(Tc,delta0,'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
% stairs(Tc,delta1,'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
plot(Tc,delta0,'Color',[0.4940 0.1840 0.5560],'LineWidth',2);
plot(Tc,delta1,'Color',[0.8500 0.3250 0.0980],'LineWidth',2);
legend('\delta_0^{*}(t)','\delta_1^{*}(t)');
xlim([0 T])
title('(c)')
xlabel('Time (Day)')
box on
snapnow;

%cost
size(delta0),size(pt)
L =delta0.^2.*pt(1:end-1)+delta1.^2.*(1-pt(1:end-1));            % 积分项
L=L*T/N;
f = trapz(Tc,L)
figure(5)
plot(Tc,L)
end

function varsfun(svh)

%N=1;
%EIL=1.2;
global EIL
%lb:下限
%ub:上限
svh.addState('Xt', 'lb', 0, 'ub', EIL);
svh.addState('pt', 'lb', 0, 'ub', 1);


svh.addControl('delta0', 'lb', 0, 'ub',0.2);
svh.addControl('delta1', 'lb', 0.8, 'ub',1);

svh.addParameter('r');
svh.addParameter('ET');
svh.addParameter('eta');
end

function daefun(daeh,x,z,u,p)


daeh.setODE('Xt', p.r*x.Xt-(u.delta0*x.pt+(1-x.pt)*u.delta1)*x.Xt);
daeh.setODE('pt',p.eta*x.pt*(1-x.pt)*(1-x.Xt/p.ET));

%daeh.setAlgEquation(z.TN-p.delta*x.I - p.delta_q*x.Iq);
end

function pathcosts(ch,x,z,u,p)
%ch.add( -1);
ch.add( u.delta1.*(1-x.pt));
ch.add( u.delta0.*x.pt);
end

% function dy =xp0(t,y,par)
% %par=[r eta delta0 delta1];
% r=par(1);
% eta=par(2);
% delta0=par(3);
% delta1=par(4);
% ET=par(5);
% 
% dy = zeros(2,1);    % a column vector
% x=y(1);
% p=y(2);
% 
% dy(1)=r*x-(delta0*p+(1-p)*delta1)*x;
% dy(2)=eta*p*(1-p)*(1-x/ET);
% end



