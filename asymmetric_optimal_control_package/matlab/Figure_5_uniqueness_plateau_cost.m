function Figure_5_uniqueness_plateau_cost
% Figure 5: cost of feasible plateau policies; the minimum is h=K.

beta1_bar=1.0; q=0.8; gamma=0.3; S0=0.99; I0=0.01; K=0.15;
xh=gamma/beta1_bar; Sh=xh/q;
I_lf=@(S) I0+q.*(S0-S)+(gamma/beta1_bar).*log(S./S0);
h=linspace(I0+0.003,K,320);
C=zeros(size(h));
for j=1:numel(h)
    Sentry=fzero(@(S) I_lf(S)-h(j),[Sh,S0]);
    xentry=q*Sentry;
    C(j)=((beta1_bar/gamma)*(xentry-xh)-log(xentry/xh))/h(j);
end

figure('Color','w','Position',[100 100 900 570]);
plot(h,C,'LineWidth',2.3); hold on;
scatter(K,C(end),55,'filled');
yl=[0,1.04*max(C)];
plot([K,K],yl,':','LineWidth',1.4);
xlabel('Chosen infection plateau h'); ylabel('Suppression cost C(h)');
xlim([h(1),1.015*K]); ylim(yl); grid on; box on;
legend({'Feasible plateau family','Unique optimum h=K'},'Location','northwest');

out=fullfile(fileparts(mfilename('fullpath')),'..','figures','Figure_5_uniqueness_plateau_cost.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('J*=%.10f\n',C(end));
fprintf('Saved %s\n',out);
end
