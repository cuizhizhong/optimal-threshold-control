function [solution,times,problem] = CUI

T=500;   
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts,'N', 1000,'d',2);

color_list = [0 0.4470 0.7410;...
              0.8500 0.3250 0.0980;...
              0.9290 0.6940 0.1250;...
              0.4940 0.1840 0.5560;...
              0.4660 0.6740 0.1880;...
              0.3010 0.7450 0.9330;...
              0.6350 0.0780 0.1840];
current_color = color_list(2, :);


%% 参数
beta=0.16;   beta_1=0.08;   gamma=0.06;   

I_m = 0.02;

%% 初始值+终止值
 I0 = 0.001; 
 S0 = 0.85;

%parameter
problem.setParameter('beta'   , beta);
problem.setParameter('beta_1' , beta_1);
problem.setParameter('gamma' , gamma);
problem.setParameter('I_m', I_m);

% intial state bounds
problem.setInitialBounds('S',     S0);
problem.setInitialBounds('I',     I0);


% Get and set initial guess
initialGuess = problem.getInitialGuess();

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
S = solution.states.S.value; 
I = solution.states.I.value;  

Tc=times.controls.value;
b = solution.controls.b.value;


figure(4)

% --控制量
subplot(3, 1, 1);
plot(Tc,b,'LineWidth',2,'Color',current_color);
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$b^*(t)$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
title('(a)','FontName', 'TimesNewRoman','FontSize',10);  

% --状态量S
subplot(3, 1, 2);
hold on
plot(Tstates, S ,'LineWidth',2,'Color',current_color);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$S$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');

% --状态量I
subplot(3, 1, 3);
hold on
plot(Tstates, I ,'LineWidth',2,'Color',current_color);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$I$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
exportgraphics(gcf, 'CUI.pdf', 'Resolution', 600, 'BackgroundColor', 'white');
end


function varsfun(svh)
%lb:下限
%ub:上限
svh.addState('S', 'lb', 0, 'ub', 1);
svh.addState('I', 'lb', 0, 'ub', 0.02);


%% 调节控制上下限
svh.addControl('b', 'lb', 0.08, 'ub', 0.16);

svh.addParameter('beta');
svh.addParameter('beta_1');
svh.addParameter('gamma');
svh.addParameter('I_m');
end

function daefun(daeh,x,z,u,p)
daeh.setODE('S',  -u.b* x.S* x.I);
daeh.setODE('I',  u.b* x.S* x.I - p.gamma*x.I);
end


function pathcosts(ch,x,z,u,p)
ch.add(p.beta - u.b);
end

 

 % exportgraphics(gcf, 'fig8.pdf', 'ContentType', 'vector');


