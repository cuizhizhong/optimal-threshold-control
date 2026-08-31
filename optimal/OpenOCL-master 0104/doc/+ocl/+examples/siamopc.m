% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%
function [solution,times,problem] = siamopc

% problem = ocl.Problem(5, @varsfun, @daefun, @pathcosts,...
%     'gridconstraints', @gridconstraints, 'terminalcost', @terminalcost, 'N',3);
problem = ocl.Problem(546, @varsfun, @daefun, @pathcosts,...
    'gridconstraints', @gridconstraints,  'N',78);

% intial state bounds
problem.setInitialBounds('S1',   11371000);
problem.setInitialBounds('S2',    47940800-1);
problem.setInitialBounds('S3',    23688200);
problem.setInitialBounds('E1',    0);
problem.setInitialBounds('E2',    0);
problem.setInitialBounds('E3',    0);
problem.setInitialBounds('IS1',    0);
problem.setInitialBounds('IS2',    1);
problem.setInitialBounds('IS3',    0);
problem.setInitialBounds('IM1',    0);
problem.setInitialBounds('IM2',    0);
problem.setInitialBounds('IM3',    0);
problem.setInitialBounds('IA1',    0);
problem.setInitialBounds('IA2',    0);
problem.setInitialBounds('IA3',    0);
problem.setInitialBounds('RU1',    0);
problem.setInitialBounds('RU2',    0);
problem.setInitialBounds('RU3',    0);
problem.setInitialBounds('P1',    0);
problem.setInitialBounds('P2',    0);
problem.setInitialBounds('P3',    0);
problem.setInitialBounds('H1',    0);
problem.setInitialBounds('H2',    0);
problem.setInitialBounds('H3',    0);
problem.setInitialBounds('RK1',    0);
problem.setInitialBounds('RK2',    0);
problem.setInitialBounds('RK3',    0);

problem.setInitialBounds('SV1',    0);
problem.setInitialBounds('SV2',    0);
problem.setInitialBounds('SV3',    0);
problem.setInitialBounds('EV1',    0);
problem.setInitialBounds('EV2',    0);
problem.setInitialBounds('EV3',    0);
problem.setInitialBounds('ISV1',    0);
problem.setInitialBounds('ISV2',    0);
problem.setInitialBounds('ISV3',    0);
problem.setInitialBounds('IMV1',    0);
problem.setInitialBounds('IMV2',   0);
problem.setInitialBounds('IMV3',    0);
problem.setInitialBounds('IAV1',    0);
problem.setInitialBounds('IAV2',    0);
problem.setInitialBounds('IAV3',    0);
problem.setInitialBounds('PV1',    0);
problem.setInitialBounds('PV2',    0);
problem.setInitialBounds('PV3',    0);
problem.setInitialBounds('HV1',   0);
problem.setInitialBounds('HV2',    0);
problem.setInitialBounds('HV3',    0);
problem.setInitialBounds('RV1',    0);
problem.setInitialBounds('RV2',    0);
problem.setInitialBounds('RV3',    0);

problem.setInitialBounds('M',    0);


% Get and set initial guess

initialGuess = problem.getInitialGuess();
  %initialGuess.controls.delta.set('delta',    1);
% initialGuess.states.E1.set('E1',    2);
% initialGuess.states.E2.set('E2',    2);
% initialGuess.states.E3.set('E3',    2);
% initialGuess.states.IS1.set('IS1',    1);
% initialGuess.states.IS2.set('IS2',    1);
% initialGuess.states.IS3.set('IS3',    1);
% initialGuess.states.IM1.set('IM1',    1);
% initialGuess.states.IM2.set('IM2',    1);
% initialGuess.states.IM3.set('IM3',    1);
% initialGuess.states.IA1.set('IA1',    1);
% initialGuess.states.IA2.set('IA2',    1);
% initialGuess.states.IA3.set('IA3',    1);
% initialGuess.states.RU1.set('RU1',    0);
% initialGuess.states.RU2.set('RU2',    0);
% initialGuess.states.RU3.set('RU3',    0);
% initialGuess.states.P1.set('P1',    0);
% initialGuess.states.P2.set('P2',    0);
% initialGuess.states.P3.set('P3',    0);
% initialGuess.states.H1.set('H1',    0);
% initialGuess.states.H2.set('H2',    0);
% initialGuess.states.H3.set('H3',    0);
% initialGuess.states.RK1.set('RK1',    0);
% initialGuess.states.RK2.set('RK2',    0);
% initialGuess.states.RK3.set('RK3',    0);
% 
% initialGuess.states.SV1.set('SV1',    0);
% initialGuess.states.SV2.set('SV2',    0);
% initialGuess.states.SV3.set('SV3',    0);
% initialGuess.states.EV1.set('EV1',    0);
% initialGuess.states.EV2.set('EV2',    0);
% initialGuess.states.EV3.set('EV3',    0);
% initialGuess.states.ISV1.set('ISV1',    0);
% initialGuess.states.ISV2.set('ISV2',    0);
% initialGuess.states.ISV3.set('ISV3',    0);
% initialGuess.states.IMV1.set('IMV1',    0);
% initialGuess.states.IMV2.set('IMV2',   0);
% initialGuess.states.IMV3.set('IMV3',    0);
% initialGuess.states.IAV1.set('IAV1',    0);
% initialGuess.states.IAV2.set('IAV2',    0);
% initialGuess.states.IAV3.set('IAV3',    0);
% initialGuess.states.PV1.set('PV1',    0);
% initialGuess.states.PV1.set('PV2',    0);
% initialGuess.states.PV3.set('PV3',    0);
% initialGuess.states.HV1.set('HV1',   0);
% initialGuess.states.HV2.set('HV2',    0);
% initialGuess.states.HV3.set('HV3',    0);
% initialGuess.states.RV1.set('RV1',    0);
% initialGuess.states.RV2.set('RV2',    0);
% initialGuess.states.RV3.set('RV3',    0);
% 
% initialGuess.states.M.set('M',    0);

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess)

% plot solution
%   figure
%   hold on
%   plot(times.states.value,solution.states.i.value,'-.','LineWidth',2)
%   plot(times.states.value,solution.states.r.value,'--k','LineWidth',2)
%   xlabel('time')
%   legend({'infected','recovered'})
Tcon=times.controls.value
decon=solution.controls.delta.value
figure
hold on
stairs(times.controls.value,solution.controls.v1.value,'r','LineWidth',2)
stairs(times.controls.value,solution.controls.v2.value,'m','LineWidth',2)
stairs(times.controls.value,solution.controls.v3.value,'b','LineWidth',2)
stairs(times.controls.value,solution.controls.delta.value,'g','LineWidth',2)
xlabel('time')
legend({'v_1','v_2','v_3','\delta'})

figure
hold on
plot(times.states.value,solution.states.IS1.value,'r','LineWidth',2)
plot(times.states.value,solution.states.IS2.value,'m','LineWidth',2)
plot(times.states.value,solution.states.IS3.value,'b','LineWidth',2)

figure
plot(solution.controls.delta.value)

xlswrite('fig1.xlsx',[times.states.value;...
    solution.states.S1.value;solution.states.S2.value; solution.states.S3.value;...
    solution.states.E1.value;solution.states.E2.value;solution.states.E3.value;...
    solution.states.IS1.value;solution.states.IS2.value;solution.states.IS3.value;...
    solution.states.IM1.value;solution.states.IM2.value;solution.states.IM3.value;...
    solution.states.IA1.value;solution.states.IA2.value;solution.states.IA3.value;...
    solution.states.RU1.value;solution.states.RU2.value;solution.states.RU3.value;...
    solution.states.P1.value;solution.states.P2.value;solution.states.P3.value;...
    solution.states.H1.value;solution.states.H2.value;solution.states.H3.value;...
    solution.states.RK1.value;solution.states.RK2.value;solution.states.RK3.value;...
    solution.states.SV1.value;solution.states.SV2.value;solution.states.SV3.value;...
    solution.states.EV1.value;solution.states.EV2.value;solution.states.EV3.value;...
    solution.states.ISV1.value;solution.states.ISV2.value;solution.states.ISV3.value;...
    solution.states.IMV1.value;solution.states.IMV2.value;solution.states.IMV3.value;...
    solution.states.IAV1.value;solution.states.IAV2.value;solution.states.IAV3.value;...
    solution.states.PV1.value;solution.states.PV2.value;solution.states.PV3.value;...
    solution.states.HV1.value;solution.states.HV2.value;solution.states.HV3.value;...
    solution.states.RV1.value;solution.states.RV2.value;solution.states.RV3.value])
xlswrite('fig11.xlsx',[solution.controls.v1.value;solution.controls.v2.value;solution.controls.v3.value;...
    solution.controls.delta.value])
snapnow;
end

function varsfun(svh)
% Scalar x:  -0.25 <= x <= inf
% Scalar y: unbounded
n_pop=8.3e7;
N1=0.1370*n_pop;N2=0.5776*n_pop;N3=0.2854*n_pop;

svh.addState('S1', 'lb', 0, 'ub', N1);
svh.addState('S2', 'lb', 0, 'ub', N2);
svh.addState('S3', 'lb', 0, 'ub', N3);
svh.addState('E1', 'lb', 0, 'ub', N1);
svh.addState('E2', 'lb', 0, 'ub', N2);
svh.addState('E3', 'lb', 0, 'ub', N3);
svh.addState('IS1', 'lb', 0, 'ub', N1);
svh.addState('IS2', 'lb', 0, 'ub', N2);
svh.addState('IS3', 'lb', 0, 'ub', N3);
svh.addState('IM1', 'lb', 0, 'ub', N1);
svh.addState('IM2', 'lb', 0, 'ub', N2);
svh.addState('IM3', 'lb', 0, 'ub', N3);
svh.addState('IA1', 'lb', 0, 'ub', N1);
svh.addState('IA2', 'lb', 0, 'ub', N2);
svh.addState('IA3', 'lb', 0, 'ub', N3);
svh.addState('RU1', 'lb', 0, 'ub', N1);
svh.addState('RU2', 'lb', 0, 'ub', N2);
svh.addState('RU3', 'lb', 0, 'ub', N3);
svh.addState('P1', 'lb', 0, 'ub', N1);
svh.addState('P2', 'lb', 0, 'ub', N2);
svh.addState('P3', 'lb', 0, 'ub', N3);
svh.addState('H1', 'lb', 0, 'ub', N1);
svh.addState('H2', 'lb', 0, 'ub', N2);
svh.addState('H3', 'lb', 0, 'ub', N3);
svh.addState('RK1', 'lb', 0, 'ub', N1);
svh.addState('RK2', 'lb', 0, 'ub', N2);
svh.addState('RK3', 'lb', 0, 'ub', N3);

svh.addState('SV1', 'lb', 0, 'ub', N1);
svh.addState('SV2', 'lb', 0, 'ub', N2);
svh.addState('SV3', 'lb', 0, 'ub', N3);
svh.addState('EV1', 'lb', 0, 'ub', N1);
svh.addState('EV2', 'lb', 0, 'ub', N2);
svh.addState('EV3', 'lb', 0, 'ub', N3);
svh.addState('ISV1', 'lb', 0, 'ub', N1);
svh.addState('ISV2', 'lb', 0, 'ub', N2);
svh.addState('ISV3', 'lb', 0, 'ub', N3);
svh.addState('IMV1', 'lb', 0, 'ub', N1);
svh.addState('IMV2', 'lb', 0, 'ub', N2);
svh.addState('IMV3', 'lb', 0, 'ub', N3);
svh.addState('IAV1', 'lb', 0, 'ub', N1);
svh.addState('IAV2', 'lb', 0, 'ub', N2);
svh.addState('IAV3', 'lb', 0, 'ub', N3);
svh.addState('PV1', 'lb', 0, 'ub', N1);
svh.addState('PV2', 'lb', 0, 'ub', N2);
svh.addState('PV3', 'lb', 0, 'ub', N3);
svh.addState('HV1', 'lb', 0, 'ub', N1);
svh.addState('HV2', 'lb', 0, 'ub', N2);
svh.addState('HV3', 'lb', 0, 'ub', N3);
svh.addState('RV1', 'lb', 0, 'ub', N1);
svh.addState('RV2', 'lb', 0, 'ub', N2);
svh.addState('RV3', 'lb', 0, 'ub', N3);

svh.addState('M', 'lb', 0, 'ub', n_pop);

% Scalar u: -1 <= F <= 1
svh.addControl('delta', 'lb', 0, 'ub', 1);
svh.addControl('v1', 'lb', 0, 'ub', inf);
svh.addControl('v2', 'lb', 0, 'ub', inf);
svh.addControl('v3', 'lb', 0, 'ub', inf);
end

function daefun(daeh,x,~,u,~)
n_pop=8.3e7;
phiS=0.25;phiM=0.25;phiA=0.1667;
gamma=0.1923;rho=0.091;sigma=0.0952;
paiS1=0.0053;paiS2=0.0031;paiS3=0.0302;
paiM1=0.1211;paiM2=0.2201;paiM3=0.2512;
paiA1=0.8737;paiA2=0.7768;paiA3=7186;

beta11=0.4612;beta12=0.4819;beta13=0.1243;
beta21=0.4819;beta22=0.6304;beta23=0.2944;
beta31=0.1243;beta32=0.2944;beta33=0.1802;

q=0.9;
Vmax=1e5;

I1=x.IS1+x.IM1+x.IA1+x.ISV1+x.IMV1+x.IAV1;
I2=x.IS2+x.IM2+x.IA2+x.ISV2+x.IMV2+x.IAV2;
I3=x.IS3+x.IM3+x.IA3+x.ISV3+x.IMV3+x.IAV3;

lambda1=u.delta*beta11*x.S1*I1+u.delta*beta12*x.S1*I2+u.delta*beta13*x.S1*I3;
lambda2=u.delta*beta21*x.S2*I1+u.delta*beta22*x.S2*I2+u.delta*beta23*x.S2*I3;
lambda3=u.delta*beta31*x.S3*I1+u.delta*beta32*x.S3*I2+u.delta*beta33*x.S3*I3;
lambdaV1=u.delta*beta11*x.SV1*I1+u.delta*beta12*x.SV1*I2+u.delta*beta13*x.SV1*I3;
lambdaV2=u.delta*beta21*x.SV2*I1+u.delta*beta22*x.SV2*I2+u.delta*beta23*x.SV2*I3;
lambdaV3=u.delta*beta31*x.SV3*I1+u.delta*beta32*x.SV3*I2+u.delta*beta33*x.SV3*I3;

V1=x.S1+x.E1+x.IS1+x.IM1+x.IA1+x.RU1;
V2=x.S2+x.E2+x.IS2+x.IM2+x.IA2+x.RU2;
V3=x.S3+x.E3+x.IS3+x.IM3+x.IA3+x.RU3;

daeh.setODE('S1', -lambda1-u.v1*x.S1);
daeh.setODE('S2', -lambda2-u.v2*x.S2);
daeh.setODE('S3', -lambda3-u.v3*x.S3);
daeh.setODE('E1', lambda1-(gamma+u.v1)*x.E1);
daeh.setODE('E2', lambda2-(gamma+u.v2)*x.E2);
daeh.setODE('E3', lambda3-(gamma+u.v3)*x.E3);
daeh.setODE('IS1',paiS1*gamma*x.E1-(phiS+u.v1)*x.IS1);
daeh.setODE('IS2',paiS2*gamma*x.E2-(phiS+u.v2)*x.IS2);
daeh.setODE('IS3',paiS3*gamma*x.E3-(phiS+u.v3)*x.IS3);
daeh.setODE('IM1',paiM1*gamma*x.E1-(phiM+u.v1)*x.IM1);
daeh.setODE('IM2',paiM2*gamma*x.E2-(phiM+u.v2)*x.IM2);
daeh.setODE('IM3',paiM3*gamma*x.E3-(phiM+u.v3)*x.IM3);
daeh.setODE('IA1',paiA1*gamma*x.E1-(phiA+u.v1)*x.IA1);
daeh.setODE('IA2',paiA2*gamma*x.E2-(phiA+u.v2)*x.IA2);
daeh.setODE('IA3',paiA3*gamma*x.E3-(phiA+u.v3)*x.IA3);
daeh.setODE('RU1',phiA*x.IA1-u.v1*x.RU1);
daeh.setODE('RU2',phiA*x.IA2-u.v1*x.RU2);
daeh.setODE('RU3',phiA*x.IA3-u.v1*x.RU3);
daeh.setODE('P1',phiS*x.IS1-rho*x.P1);
daeh.setODE('P2',phiS*x.IS2-rho*x.P2);
daeh.setODE('P3',phiS*x.IS3-rho*x.P3);
daeh.setODE('H1',rho*x.P1-sigma*x.H1);
daeh.setODE('H2',rho*x.P2-sigma*x.H2);
daeh.setODE('H3',rho*x.P3-sigma*x.H3);
daeh.setODE('RK1',phiM*x.IM1+sigma*x.H1);
daeh.setODE('RK2',phiM*x.IM2+sigma*x.H2);
daeh.setODE('RK3',phiM*x.IM3+sigma*x.H3);

daeh.setODE('SV1', -lambdaV1+(1-q)*u.v1*x.S1);
daeh.setODE('SV2', -lambdaV2+(1-q)*u.v2*x.S2);
daeh.setODE('SV3', -lambdaV3+(1-q)*u.v3*x.S3);
daeh.setODE('EV1', u.v1*x.E1+lambdaV1-gamma*x.EV1);
daeh.setODE('EV2', u.v2*x.E2+lambdaV2-gamma*x.EV2);
daeh.setODE('EV3', u.v3*x.E3+lambdaV3-gamma*x.EV3);
daeh.setODE('ISV1',u.v1*x.IS1+paiS1*gamma*x.EV1-phiS*x.ISV1);
daeh.setODE('ISV2',u.v2*x.IS2+paiS2*gamma*x.EV2-phiS*x.ISV2);
daeh.setODE('ISV3',u.v3*x.IS3+paiS3*gamma*x.EV3-phiS*x.ISV3);
daeh.setODE('IMV1',u.v1*x.IM1+paiM1*gamma*x.EV1-phiM*x.IMV1);
daeh.setODE('IMV2',u.v2*x.IM2+paiM2*gamma*x.EV2-phiM*x.IMV2);
daeh.setODE('IMV3',u.v3*x.IM3+paiM3*gamma*x.EV3-phiM*x.IMV3);
daeh.setODE('IAV1',u.v1*x.IA1+paiA1*gamma*x.EV1-phiA*x.IAV1);
daeh.setODE('IAV2',u.v2*x.IA2+paiA2*gamma*x.EV2-phiA*x.IAV2);
daeh.setODE('IAV3',u.v3*x.IA3+paiA3*gamma*x.EV3-phiA*x.IAV3);
daeh.setODE('PV1',phiS*x.ISV1-rho*x.PV1);
daeh.setODE('PV2',phiS*x.ISV2-rho*x.PV2);
daeh.setODE('PV3',phiS*x.ISV3-rho*x.PV3);
daeh.setODE('HV1',rho*x.PV1-sigma*x.HV1);
daeh.setODE('HV2',rho*x.PV2-sigma*x.HV2);
daeh.setODE('HV3',rho*x.PV3-sigma*x.HV3);
daeh.setODE('RV1',u.v1*x.RU1+q*u.v1*x.S1+phiA*x.IAV1+phiM*x.IMV1+sigma*x.HV1);
daeh.setODE('RV2',u.v2*x.RU2+q*u.v2*x.S2+phiA*x.IAV2+phiM*x.IMV2+sigma*x.HV3);
daeh.setODE('RV3',u.v3*x.RU3+q*u.v3*x.S3+phiA*x.IAV3+phiM*x.IMV3+sigma*x.HV3);

daeh.setODE('M', n_pop*(u.v1*V1+u.v2*V2+u.v3*V3)-Vmax);

end

function pathcosts(ch,x,~,u,~)
ch.add((1-u.delta)^2 );
k=1e-3;
ch.add( k*(u.v1^2+u.v2^2+u.v3^2) );
end

% function terminalcost(ocl,x,~)
% k=1e-3;
% ocl.add( k*(u.v1^2+u.v2^2+u.v3^2)^(1/2) );
% end

function gridconstraints(ch,~,~,x,~)
n_pop=8.3e7;
Hmax=1e4;
ch.add(n_pop*(x.H1+x.HV1+x.H2+x.HV2+x.H3+x.HV3), '<=', Hmax);
ch.add(x.M, '<=', 0);
end




