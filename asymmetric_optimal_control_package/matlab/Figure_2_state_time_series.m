function Figure_2_state_time_series
% Figure 2: state trajectories under the exact optimal policy.

beta1_bar = 1.0;
q = 0.8;
beta2_bar = q * beta1_bar;
gamma = 0.3;
S0 = 0.99;
I0 = 0.01;
K = 0.15;
S_h = gamma / beta2_bar;
I_lf = @(S) I0 + q .* (S0 - S) + (gamma / beta1_bar) .* log(S ./ S0);
S1 = fzero(@(S) I_lf(S) - K, [S_h, S0]);

rhs = @(t,y) [-beta1_bar*y(1)*y(2); beta2_bar*y(1)*y(2)-gamma*y(2)];
opts = odeset('RelTol',1e-10,'AbsTol',1e-12,'MaxStep',0.02,'Events',@(t,y) cap_event(t,y,K));
[t_pre,y_pre,te,~,~] = ode45(rhs,[0 200],[S0;I0],opts);
tau1 = te(1);
tau2 = tau1 + q * (S1 - S_h) / (gamma * K);

n2 = 260;
t_bnd = linspace(tau1,tau2,n2)';
S_bnd = S1 - (gamma*K/q).*(t_bnd-tau1);
I_bnd = K*ones(size(t_bnd));

opts3 = odeset('RelTol',1e-10,'AbsTol',1e-12,'MaxStep',0.03);
[t_post,y_post] = ode45(rhs,[tau2 tau2+45],[S_h;K],opts3);

t = [t_pre; t_bnd(2:end); t_post(2:end)];
S = [y_pre(:,1); S_bnd(2:end); y_post(2:end,1)];
I = [y_pre(:,2); I_bnd(2:end); y_post(2:end,2)];

figure('Color','w','Position',[100 100 920 590]);
plot(t,S,'LineWidth',2.1); hold on;
plot(t,I,'LineWidth',2.4);
plot([0,t(end)],[K,K],':','LineWidth',1.5);
yl = [0 1.03];
plot([tau1,tau1],yl,'--','LineWidth',1.2);
plot([tau2,tau2],yl,'--','LineWidth',1.2);
text(tau1-0.3,0.96,'tau_1','HorizontalAlignment','right');
text(tau2+0.1,0.96,'tau_2','HorizontalAlignment','left');
xlabel('Time'); ylabel('Population fraction');
xlim([0,t(end)]); ylim(yl); grid on; box on;
legend({'S(t)','I(t)','Capacity K'},'Location','northeast');

out = fullfile(fileparts(mfilename('fullpath')), '..', 'figures', 'Figure_2_state_time_series.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('tau1=%.8f, tau2=%.8f\n',tau1,tau2);
fprintf('Saved %s\n',out);
end

function [value,isterminal,direction] = cap_event(~,y,K)
value = y(2)-K;
isterminal = 1;
direction = 1;
end
