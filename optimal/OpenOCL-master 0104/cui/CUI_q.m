function [solution,times,problem] = CUI_q

% 用较长求解区间逼近报告中的无限时域问题；图中只显示前 18 个时间单位。
T = 300;
T_plot = 18;
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts, ...
    'N', 4000, 'd', 2, 'controls_regularization', false);

color_list = [0 0.4470 0.7410;...
              0.8500 0.3250 0.0980;...
              0.9290 0.6940 0.1250;...
              0.4940 0.1840 0.5560;...
              0.4660 0.6740 0.1880;...
              0.3010 0.7450 0.9330;...
              0.6350 0.0780 0.1840];
current_color = color_list(5, :);


%% 参数
% 报告基准参数：p=0.5, c=2, gamma=0.3, K=0.15。
 beta = 0.5;   gamma = 0.3;   c_0 = 2.0;   I_m = 0.15;
R_0 = beta * c_0 / gamma;

%% 初始值+终止值
 I0 = 0.01;
 S0 = 0.99;

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

% 用报告的解析基准轨道初始化直接配点变量，改善状态约束问题的收敛性。
t_guess_state = linspace(0, T, numel(initialGuess.states.S.value))';
[S_guess, I_guess, ~] = baseline_reference(t_guess_state, beta, gamma, c_0, S0, I0, I_m);
t_guess_control = linspace(0, T, numel(initialGuess.controls.q.value))';
[~, ~, q_guess] = baseline_reference(t_guess_control, beta, gamma, c_0, S0, I0, I_m);
initialGuess.states.S.set(S_guess');
initialGuess.states.I.set(I_guess');
initialGuess.controls.q.set(q_guess');

% Run solver to obtain solution
[solution,times] = problem.solve(initialGuess);

% plot solution
Tstates=times.states.value;
S = solution.states.S.value; 
I = solution.states.I.value;  

Tc=times.controls.value;
q = solution.controls.q.value;

% 报告表中的解析分段解，用于独立比较数值结果。
t_ref = linspace(0, T_plot, 4001)';
[S_ref, I_ref, q_ref] = baseline_reference(t_ref, beta, gamma, c_0, S0, I0, I_m);

J_num = beta * c_0 * trapz(Tc, q);
J_report = 1.5295111602;
fprintf('\nOpenOCL baseline result\n');
fprintf('R0 = %.10f\n', R_0);
fprintf('max(I) = %.10f (K = %.10f)\n', max(I), I_m);
fprintf('J_num = integral(p*c*q dt) = %.10f\n', J_num);
fprintf('J_report = %.10f, relative error = %.4f%%\n', ...
    J_report, 100 * abs(J_num - J_report) / J_report);


figure(4);
clf;
set(gcf, 'Color', 'w', 'Position', [100 100 760 760]);

%% --控制量q
subplot(3, 1, 1);
hold on
plot(Tc, q, 'LineWidth', 2, 'Color', current_color, ...
    'DisplayName', 'OpenOCL numerical');
plot(t_ref, q_ref, '--', 'LineWidth', 2, 'Color', color_list(1, :), ...
    'DisplayName', 'Report analytical');

xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$q^*(t)$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
title('(a) Optimal control','FontName', 'TimesNewRoman','FontSize',10);
xlim([0 T_plot]); ylim([-0.03 1.05]); grid on; box on;
legend('Location', 'northeast', 'Box', 'off');

% --状态量S
subplot(3, 1, 2);
hold on
plot(Tstates, S, 'LineWidth', 2, 'Color', current_color, ...
    'DisplayName', 'OpenOCL numerical');
plot(t_ref, S_ref, '--', 'LineWidth', 2, 'Color', color_list(1, :), ...
    'DisplayName', 'Report analytical');
yline(gamma/(beta*c_0), 'r--', 'LineWidth', 2, ...
    'DisplayName', 'h = gamma/(pc)');
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$S$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
title('(b) Susceptible fraction','FontName', 'TimesNewRoman','FontSize',10);
xlim([0 T_plot]); ylim([0 1.02]); grid on; box on;

% --状态量I
subplot(3, 1, 3);
hold on
plot(Tstates, I, 'LineWidth', 2, 'Color', current_color, ...
    'DisplayName', 'OpenOCL numerical');
plot(t_ref, I_ref, '--', 'LineWidth', 2, 'Color', color_list(1, :), ...
    'DisplayName', 'Report analytical');
yline(I_m, 'r--', 'LineWidth', 2, ...
    'DisplayName', 'Capacity K');
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$I$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
title('(c) Infectious fraction','FontName', 'TimesNewRoman','FontSize',10);
xlim([0 T_plot]); ylim([0 0.18]); grid on; box on;
exportgraphics(gcf, 'CUI_q.pdf', 'Resolution', 600, 'BackgroundColor', 'white');
exportgraphics(gcf, 'CUI_q.png', 'Resolution', 300, 'BackgroundColor', 'white');

end


function varsfun(svh)
%lb:下限
%ub:上限
I_m = 0.15;
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
  % 报告目标泛函：J = integral(p*c*q dt)。
  ch.add(p.beta * p.c_0 * u.q);

end


function [S, I, q] = baseline_reference(t, beta, gamma, c_0, S0, I0, I_m)
% 报告基准参数下的解析最优轨道：0 -> q_B -> 1 -> 0。
% 下列切换量来自报告表“基准参数下的解析--数值结果”。
s1 = 0.7775221610;
s_switch = 0.5476951355;
i_switch = I_m;
s_release = 0.4516637907;
i_release = 0.1210828901;
tau1 = 4.3491915577;
tau_boundary = 1.5203108877;
tau_q1 = 0.7138664706;
t_boundary_end = tau1 + tau_boundary;
t_release = t_boundary_end + tau_q1;
h = gamma / (beta * c_0);
r = (1 - beta) * h;

t = t(:);
S = nan(size(t));
I = nan(size(t));
q = zeros(size(t));
rhs0 = @(~, y) [-beta*c_0*y(1)*y(2); ...
    (beta*c_0*y(1)-gamma)*y(2)];
ode_opts = odeset('RelTol', 2e-10, 'AbsTol', 1e-12);

idx = find(t <= tau1 + 1e-12);
if numel(idx) >= 2
    [~, Y] = ode45(rhs0, t(idx), [S0; I0], ode_opts);
    S(idx) = Y(:, 1); I(idx) = Y(:, 2);
elseif numel(idx) == 1
    S(idx) = S0; I(idx) = I0;
end

idx = find(t > tau1 & t <= t_boundary_end + 1e-12);
if ~isempty(idx)
    u = t(idx) - tau1;
    S(idx) = r + (s1-r).*exp(-c_0*I_m.*u);
    I(idx) = I_m;
    q(idx) = 1 - h./S(idx);
end

idx = find(t > t_boundary_end & t <= t_release + 1e-12);
if ~isempty(idx)
    u = t(idx) - t_boundary_end;
    I(idx) = i_switch.*exp(-gamma.*u);
    S(idx) = s_switch.*exp(-(c_0/gamma).*(i_switch-I(idx)));
    q(idx) = 1;
end

idx = find(t > t_release);
if ~isempty(idx)
    t_after = t(idx) - t_release;
    [~, Y] = ode45(rhs0, [0; t_after], [s_release; i_release], ode_opts);
    S(idx) = Y(2:end, 1); I(idx) = Y(2:end, 2);
end
end


 % exportgraphics(gcf, 'fig8.pdf', 'ContentType', 'vector');


