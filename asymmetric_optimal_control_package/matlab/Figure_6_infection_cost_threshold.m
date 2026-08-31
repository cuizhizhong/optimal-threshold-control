function Figure_6_infection_cost_threshold
% Figure 6: robustness threshold a_0(K) for an added infection cost.

beta1_bar=1.0; gamma=0.3; xh=gamma/beta1_bar;
rho=fzero(@(r) r.^2+r+log(1-r),[0.5,0.95]);
K0=rho^2*xh;
constant=beta1_bar*rho/((1-rho)*K0);
K=linspace(0.005,0.29,500);
a0=zeros(size(K));
for j=1:numel(K)
    if K(j)<=K0
        lam=fzero(@(z) z-xh*(log(z/xh)+1)-K(j),[1e-12,xh*(1-1e-10)]);
        a0(j)=(gamma-beta1_bar*lam)/(K(j)*lam);
    else
        a0(j)=constant;
    end
end

figure('Color','w','Position',[100 100 900 570]);
plot(K,a0,'LineWidth',2.3); hold on;
yl=[0,1.04*max(a0)];
plot([K0,K0],yl,'--','LineWidth',1.4);
xlabel('Capacity K');
ylabel('Largest infection-cost weight preserving the policy');
xlim([K(1),K(end)]); ylim(yl); grid on; box on;
legend({'a_0(K)',sprintf('K_0=%.3f',K0)},'Location','northwest');

out=fullfile(fileparts(mfilename('fullpath')),'..','figures','Figure_6_infection_cost_threshold.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('rho=%.10f, K0=%.10f, constant=%.10f\n',rho,K0,constant);
fprintf('Saved %s\n',out);
end
