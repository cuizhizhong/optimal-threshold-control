function [solution,times,problem] = CUI_q

T=300;      
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts,'N', 4000,'d',2);

color_list = [0 0.4470 0.7410;...
              0.8500 0.3250 0.0980;...
              0.9290 0.6940 0.1250;...
              0.4940 0.1840 0.5560;...
              0.4660 0.6740 0.1880;...
              0.3010 0.7450 0.9330;...
              0.6350 0.0780 0.1840];
current_color = color_list(5, :);


%% 参数
 beta = 0.5;   gamma=0.1;   c_0=0.8;  I_m = 0.02;
R_0 = beta * c_0 / gamma;

%% 初始值+终止值
 I0 = 0.005; 
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

%% --控制量q
subplot(3, 1, 1);
hold on
plot(Tc,q,'LineWidth',2,'Color',current_color);

%% 解析解
Sc = gamma / (beta * c_0 );
C0 = I0+S0-Sc*log(S0);
arg = -1/Sc * exp(-(C0 - I_m)/Sc);
S_star = -Sc * lambertw(-1, arg);
f = @(x) 1 ./ (-beta * c_0 * x .* (C0 - x + Sc .* log(x)));
t1 = integral(f, S0, S_star);
log_term = (c_0 * S_star + gamma - gamma / beta) / gamma;
t2 = t1 + (1 / (c_0 * I_m)) * log(log_term);
t = t1:0.5:t2;
denominator = (beta*c_0*S_star - gamma*(1-beta)) .* exp(-c_0*I_m*(t - t1)) ...
              + gamma*(1-beta);
q_star = 1 - gamma ./ denominator;
plot(t, q_star, 'b-', 'LineWidth', 2);

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
exportgraphics(gcf, 'CUI_q.pdf', 'Resolution', 600, 'BackgroundColor', 'white');

end


function varsfun(svh)
%lb:下限
%ub:上限
I_m = 0.02;
svh.addState('S', 'lb', 0, 'ub', 1);
svh.addState('I', 'lb', 0, 'ub', I_m);


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
  ch.add(u.q);

end


 % exportgraphics(gcf, 'fig8.pdf', 'ContentType', 'vector');


