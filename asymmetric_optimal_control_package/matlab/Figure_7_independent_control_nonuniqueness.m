function Figure_7_independent_control_nonuniqueness
% Figure 7: zero-cost nonuniqueness with independent beta_1 and beta_2.

B1=1.0; B2=0.8; gamma=0.3; S0=0.99; I0=0.02; K=0.15;
S_threshold=gamma/B2;
strategies=[0.05,0.95; 0.10,0.85; 0.20,0.75]; T_end=25;

figure('Color','w','Position',[100 100 930 590]); hold on;
labels=cell(1,size(strategies,1)+2);
for j=1:size(strategies,1)
    delta=strategies(j,1);
    S_target=strategies(j,2)*S_threshold;
    lo=B1*(1+1e-8); hi=10;
    while terminalS(delta,hi,B2,gamma,S0,I0)>S_target
        hi=2*hi;
        if hi>1e7, error('Could not bracket pulse magnitude.'); end
    end
    M=fzero(@(m) terminalS(delta,m,B2,gamma,S0,I0)-S_target,[lo,hi]);
    t1=linspace(0,delta,120);
    rhs1=@(t,y)[-M*y(1)*y(2); B2*y(1)*y(2)-gamma*y(2)];
    [tp,yp]=ode45(rhs1,t1,[S0;I0],odeset('RelTol',2e-9,'AbsTol',1e-11));
    rhs2=@(t,y)[-B1*y(1)*y(2); B2*y(1)*y(2)-gamma*y(2)];
    t2=linspace(delta,T_end,900);
    [tb,yb]=ode45(rhs2,t2,yp(end,:)',odeset('RelTol',2e-9,'AbsTol',1e-11));
    plot([tp;tb(2:end)],[yp(:,2);yb(2:end,2)],'LineWidth',2.0);
    labels{j}=sprintf('zero cost: delta=%.2f, S(delta)=%.3f, M=%.1f',delta,S_target,M);
end

rhs0=@(t,y)[-B1*y(1)*y(2); B2*y(1)*y(2)-gamma*y(2)];
t0=linspace(0,T_end,1000);
[tb0,yb0]=ode45(rhs0,t0,[S0;I0],odeset('RelTol',2e-9,'AbsTol',1e-11));
plot(tb0,yb0(:,2),'--','LineWidth',2.0);
plot([0,T_end],[K,K],':','LineWidth',1.5);
labels{end-1}='unregulated baseline'; labels{end}='Capacity K';
xlabel('Time'); ylabel('Infectious fraction I(t)');
xlim([0,T_end]); ylim([0,max(1.15*K,1.08*max(yb0(:,2)))]); grid on; box on;
legend(labels,'Location','northeast','FontSize',8);

out=fullfile(fileparts(mfilename('fullpath')),'..','figures','Figure_7_independent_control_nonuniqueness.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('Saved %s\n',out);
end

function Sdelta=terminalS(delta,M,B2,gamma,S0,I0)
rhs=@(t,y)[-M*y(1)*y(2); B2*y(1)*y(2)-gamma*y(2)];
[~,y]=ode45(rhs,[0,delta],[S0;I0],odeset('RelTol',2e-8,'AbsTol',1e-10,'MaxStep',max(delta/80,1e-4)));
Sdelta=y(end,1);
end
