function Figure_3_optimal_controls
% Figure 3: distinct optimal coefficients beta_1(t) and beta_2(t).

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
[~,~,te,~,~] = ode45(rhs,[0 200],[S0;I0],opts);
tau1 = te(1);
tau2 = tau1 + q * (S1-S_h)/(gamma*K);
T_end = tau2 + 16;

t = linspace(0,T_end,1400);
beta1 = beta1_bar*ones(size(t));
beta2 = beta2_bar*ones(size(t));
idx = (t>tau1) & (t<=tau2);
S_bnd = S1 - (gamma*K/q).*(t(idx)-tau1);
beta1(idx) = gamma ./ (q*S_bnd);
beta2(idx) = gamma ./ S_bnd;

figure('Color','w','Position',[100 100 920 570]);
plot(t,beta1,'LineWidth',2.3); hold on;
plot(t,beta2,'LineWidth',2.3);
plot([0,T_end],[beta1_bar,beta1_bar],':','LineWidth',1.3);
plot([0,T_end],[beta2_bar,beta2_bar],'--','LineWidth',1.3);
yl=[0,1.12*beta1_bar];
plot([tau1,tau1],yl,'--','LineWidth',1.1);
plot([tau2,tau2],yl,'--','LineWidth',1.1);
xlabel('Time'); ylabel('Transmission/removal coefficient');
xlim([0,T_end]); ylim(yl); grid on; box on;
legend({'beta_1^*(t)','beta_2^*(t)=q beta_1^*(t)','beta1bar','beta2bar'},'Location','southeast');

out = fullfile(fileparts(mfilename('fullpath')), '..', 'figures', 'Figure_3_optimal_controls.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('Saved %s\n',out);
end

function [value,isterminal,direction] = cap_event(~,y,K)
value=y(2)-K; isterminal=1; direction=1;
end
