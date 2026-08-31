% Copyright 2019 Jonas Koenemann, Moritz Diehl, University of Freiburg
% Copyright 2015-2018 Jonas Koennemanm, Giovanni Licitra
% Redistribution is permitted under the 3-Clause BSD License terms. Please
% ensure the above copyright notice is visible in any derived work.
%
function [solution,times,problem] = Siamwithoutvaccination2

problem = ocl.Problem(630, @varsfun, @daefun, @pathcosts,'gridconstraints',@gridconstraints,'N',90);

n1=0.1370;n2=0.5776;n3=0.2854;Hmax=1e4;
% intial state bounds
problem.setInitialBounds('S1',   n1-0.001 );
problem.setInitialBounds('S2',   n2-0.002);
problem.setInitialBounds('S3',   n3 );

problem.setInitialBounds('E1',   0.001 );
problem.setInitialBounds('E2',   0.002);
problem.setInitialBounds('E3',   0 );

problem.setInitialBounds('IS1',    0);
problem.setInitialBounds('IS2',    0);
problem.setInitialBounds('IS3',    0);

problem.setInitialBounds('IM1',   0 );
problem.setInitialBounds('IM2',   0 );
problem.setInitialBounds('IM3',  0);

problem.setInitialBounds('IA1',   0 );
problem.setInitialBounds('IA2',   0 );
problem.setInitialBounds('IA3',   0 );

problem.setInitialBounds('RU1',  0  );
problem.setInitialBounds('RU2',  0  );
problem.setInitialBounds('RU3',  0  );

problem.setInitialBounds('P1',   0 );
problem.setInitialBounds('P2',   0 );
problem.setInitialBounds('P3',   0 );

problem.setInitialBounds('H1',   0 );
problem.setInitialBounds('H2',   0 );
problem.setInitialBounds('H3',   0 );

problem.setInitialBounds('RK1',   0 );
problem.setInitialBounds('RK2',   0 );
problem.setInitialBounds('RK3',   0 );

%problem.setInitialBounds('Htotal',   0 );


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
npop=8.3e7;
% plot solution
figure
hold on
%plot(times.states.value,solution.states.S.value,'-.','LineWidth',2)
plot(times.states.value,npop*(solution.states.H1.value+solution.states.H2.value+solution.states.H3.value),'--k','LineWidth',2)
%plot(times.states.value,npop*solution.AlgVar.H1total.value,'--k','LineWidth',2)
xlabel('time')
legend({'Htotal'})

figure
hold on
stairs(times.controls.value,solution.controls.delta.value,'r','LineWidth',2)
xlabel('time')
title('\delta')
% 
% figure
% hold on
% stairs(times.controls.value,1-solution.controls.delta.value,'r','LineWidth',2)
% xlabel('time')
% title('1-\delta')

% figure
% hold on
% stairs([1:1:10],solution.controls.delta.value,'r','LineWidth',2)
% snapnow;
end

function varsfun(svh)
% Scalar x:  -0.25 <= x <= inf
% Scalar y: unbounded
N1=0.1370;N2=0.5776;N3=0.2854;
npop=8.3e7;
Hmax=1e4;hmax=Hmax/npop;

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

%svh.addState('Htotal', 'lb', 0, 'ub', hmax);
% Scalar u: -1 <= F <= 1
svh.addControl('delta', 'lb', 0, 'ub', 1);
%svh.addAlgVar('Htotal', 'lb', 0, 'ub', hmax);
end

function daefun(daeh,x,Htotal,u,~)
phiS=0.25;phiM=0.25;phiA=0.1667;
gamma=0.1923;rho=0.091;sigma=0.0952;
paiS1=0.0053;paiS2=0.0031;paiS3=0.0302;
paiM1=0.1211;paiM2=0.2201;paiM3=0.2512;
paiA1=0.8737;paiA2=0.7768;paiA3=0.7186;
beta11=0.4612;beta12=0.4819;beta13=0.1243;
beta21=0.4819;beta22=0.6304;beta23=0.2944;
beta31=0.1243;beta32=0.2944;beta33=0.1802;

npop=8.3e7;
Hmax=1e4;hmax=Hmax/npop;

I1=x.IS1+x.IM1+x.IA1;
I2=x.IS2+x.IM2+x.IA2;
I3=x.IS3+x.IM3+x.IA3;

Lambda1=beta11*x.S1*I1+beta12*x.S1*I2+beta13*x.S1*I3;
Lambda2=beta21*x.S2*I1+beta22*x.S2*I2+beta23*x.S2*I3;
Lambda3=beta31*x.S3*I1+beta32*x.S3*I2+beta33*x.S3*I3;

% V1=x.S1+x.E1+x.IS1+x.IM1+x.IA1+x.RU1;
% V2=x.S2+x.E2+x.IS2+x.IM2+x.IA2+x.RU2;
% V3=x.S3+x.E3+x.IS3+x.IM1+x.IA3+x.RU3;

daeh.setODE('S1',-u.delta*Lambda1);
daeh.setODE('S2',-u.delta*Lambda2);
daeh.setODE('S3',-u.delta*Lambda3);

daeh.setODE('E1', u.delta*Lambda1-gamma*x.E1);
daeh.setODE('E2', u.delta*Lambda2-gamma*x.E2);
daeh.setODE('E3', u.delta*Lambda3-gamma*x.E3);

daeh.setODE('IS1',paiS1*gamma*x.E1-phiS*x.IS1);
daeh.setODE('IS2',paiS2*gamma*x.E2-phiS*x.IS2);
daeh.setODE('IS3',paiS3*gamma*x.E3-phiS*x.IS3);

daeh.setODE('IM1',paiM1*gamma*x.E1-phiM*x.IM1);
daeh.setODE('IM2',paiM2*gamma*x.E2-phiM*x.IM2);
daeh.setODE('IM3',paiM3*gamma*x.E3-phiM*x.IM3);

daeh.setODE('IA1',paiA1*gamma*x.E1-phiA*x.IA1);
daeh.setODE('IA2',paiA2*gamma*x.E2-phiA*x.IA2);
daeh.setODE('IA3',paiA3*gamma*x.E3-phiA*x.IA3);

daeh.setODE('RU1',phiA*x.IA1);
daeh.setODE('RU2',phiA*x.IA3);
daeh.setODE('RU3',phiA*x.IA3);

daeh.setODE('P1',phiS*x.IS1-rho*x.P1);
daeh.setODE('P2',phiS*x.IS2-rho*x.P2);
daeh.setODE('P3',phiS*x.IS3-rho*x.P3);

daeh.setODE('H1',rho*x.P1-sigma*x.H1);
daeh.setODE('H2',rho*x.P2-sigma*x.H2);
daeh.setODE('H3',rho*x.P3-sigma*x.H3);

daeh.setODE('RK1',phiM*x.IM1+sigma*x.H1);
daeh.setODE('RK2',phiM*x.IM2+sigma*x.H2);
daeh.setODE('RK3',phiM*x.IM3+sigma*x.H3);

%daeh.setODE('Htotal',rho*x.P1-sigma*x.H1+rho*x.P2-sigma*x.H2+rho*x.P3-sigma*x.H3);

%daeh.setAlgEquation(Htotal-x.H1-x.H2-x.H3);
end

function pathcosts(ch,x,~,u,~)
ch.add( (1-u.delta)^2);
end

function gridconstraints(ch,~,~,x,~)
 npop=8.3e7;Hmax=1e4;
  ch.add(npop*(x.H1+x.H2+x.H3),'<=',Hmax);
end




