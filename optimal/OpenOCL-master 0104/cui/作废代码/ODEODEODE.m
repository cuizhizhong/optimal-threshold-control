
clear; clc;
global  beta  gamma  c_0  t1  t2 S0 I0 I_m Sc C S_star

beta = 0.5;   gamma=0.1;   c_0=0.8;  I_m = 0.02;
R_0 = beta * c_0 / gamma;

%% 初始值+终止值
 S0 = 0.85;
 I0 = 0.005; 
 
Sc = gamma / (beta * c_0 );
C = I0+S0-Sc*log(S0);
arg = -1/Sc * exp(-(C - I_m)/Sc);
S_star = -Sc * lambertw(-1, arg);
f = @(x) 1 ./ (-beta * c_0 * x .* (C - x + Sc .* log(x)));
t1 = integral(f, S0, S_star);
log_term = (c_0 * S_star + gamma - gamma / beta) / gamma;
t2 = t1 + (1 / (c_0 * I_m)) * log(log_term);
fprintf('t1 = %.2f, t2 = %.2f, S* = %.4f\n', t1, t2, S_star);


initialvalue = [S0, I0];
options = odeset('RelTol', 1e-9, 'AbsTol', 1e-11);  % 更小的误差容限
[T1,X1]=ode45(@ODE_SI,0:0.01:300,initialvalue, options);
S = X1(:,1);   I = X1(:,2);


t_q = 0:0.01:300;
q_val = zeros(size(t_q));

for i = 1:length(t_q)
    t = t_q(i);
    if t < t1
        q_val(i) = 0;
    elseif t >= t1 && t < t2
        den = (beta*c_0*S_star - gamma*(1-beta)) * exp(-c_0*I_m*(t-t1)) + gamma*(1-beta);
        q_val(i) = 1 - gamma / den;
    else
        q_val(i) = 0;
    end
end

%% 绘图（3张图：q(t), S(t), I(t)）
figure(1)

subplot(3,1,1);  
hold on
plot(t_q, q_val, 'k-', 'LineWidth', 2);
xline(t1, 'm--', 'LineWidth', 2);
xline(t2, 'g--', 'LineWidth', 2);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$q(t)$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');
ylim([0, 1]);


subplot(3,1,2);
hold on
plot(T1,S,'k-','LineWidth', 2);
yline(gamma/(beta*c_0), 'r--', 'LineWidth', 2);
xline(t1, 'm--', 'LineWidth', 2);
xline(t2, 'g--', 'LineWidth', 2);
hold off
xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$S$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');


subplot(3,1,3);
hold on
plot(T1,I,'k-','LineWidth', 2);
yline(I_m, 'r--', 'LineWidth', 2);
xline(t1, 'm--', 'LineWidth', 2);
xline(t2, 'g--', 'LineWidth', 2);
hold off

ylim_now = ylim;
y_pos = ylim_now(1) - 0.08*(ylim_now(2)-ylim_now(1));  % x轴下方位置
text(t1, y_pos, '$t_1$','FontName','TimesNewRoman','FontSize',10,...
    'Color','m','Interpreter','latex','HorizontalAlignment','center');
text(t2, y_pos, '$t_2$','FontName','TimesNewRoman','FontSize',10,...
    'Color','g','Interpreter','latex','HorizontalAlignment','center');

xlabel('t','FontName', 'TimesNewRoman','FontSize',10);
ylabel('$I$','FontName', 'TimesNewRoman','FontSize',10,'Interpreter', 'Latex');


