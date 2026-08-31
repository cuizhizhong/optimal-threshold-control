function [solution,times,problem] = CUI_q

T=1000;      
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
beta = 0.22;   gamma=0.1;   c_0=0.8;  
R_0 = beta * c_0 / gamma
I_m = 0.01;

%% 初始值+终止值
 I0 = 0.001; 
 S0 = 0.85;

%parameter
problem.setParameter('beta'   , beta);
problem.setParameter('gamma' , gamma);
problem.setParameter('c_0'   , c_0);
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
q = solution.controls.q.value;


figure(4)

% --控制量
subplot(3, 1, 1);
plot(Tc,q,'LineWidth',2,'Color',current_color);
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$q^*(t)$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
title('(a)','FontName', 'TimesNewRoman','FontSize',10);  

% --状态量S
subplot(3, 1, 2);
hold on
plot(Tstates, S ,'LineWidth',2,'Color',current_color);
yline(gamma/(beta*c_0), 'r--', 'LineWidth', 2);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$S$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');

% --状态量I
subplot(3, 1, 3);
hold on
plot(Tstates, I ,'LineWidth',2,'Color',current_color);
yline(I_m, 'r--', 'LineWidth', 2);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$I$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');

S
I
end


function varsfun(svh)
%lb:下限
%ub:上限
svh.addState('S', 'lb', 0, 'ub', 1);
svh.addState('I', 'lb', 0, 'ub', 0.01);


%% 调节控制上下限
svh.addControl('q', 'lb', 0, 'ub', 1);

svh.addParameter('beta');
svh.addParameter('gamma');
svh.addParameter('c_0');
svh.addParameter('I_m');
end

function daefun(daeh,x,z,u,p)
daeh.setODE('S',  - p.c_0 *(p.beta + (1 - p.beta) * u.q) * x.S* x.I);
daeh.setODE('I',  p.beta * p.c_0 * (1-u.q)* x.S* x.I - p.gamma*x.I);
end


function pathcosts(ch,x,z,u,p)
 %ch.add(-(1-p.beta) * p.c_0 * u.q);
  ch.add(u.q);

end
