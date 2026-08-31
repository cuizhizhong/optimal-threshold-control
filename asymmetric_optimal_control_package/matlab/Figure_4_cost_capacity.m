function Figure_4_cost_capacity
% Figure 4: minimal suppression cost versus capacity for several q values.

beta1_bar=1.0; gamma=0.3; S0=0.99; I0=0.01;
q_values=[0.65,0.80,0.95,1.10];
K=linspace(0.015,0.40,650);

figure('Color','w','Position',[100 100 900 590]); hold on;
labels=cell(size(q_values)); maxC=0;
for j=1:numel(q_values)
    q=q_values(j); x0=q*S0; xh=gamma/beta1_bar;
    Ipeak=I0+x0-xh+(gamma/beta1_bar)*log(xh/x0);
    C=((beta1_bar/gamma).*(I0+x0-K)-log(beta1_bar*x0/gamma)-1)./K;
    C(K>=Ipeak)=0; C=max(C,0);
    maxC=max(maxC,max(C));
    plot(K,C,'LineWidth',2.0);
    labels{j}=sprintf('q=%.2f, peak=%.3f',q,Ipeak);
end
xlabel('Capacity K'); ylabel('Minimal suppression cost J^*');
xlim([K(1),K(end)]); ylim([0,1.03*maxC]); grid on; box on;
legend(labels,'Location','northeast');

out=fullfile(fileparts(mfilename('fullpath')),'..','figures','Figure_4_cost_capacity.jpg');
print(gcf,out,'-djpeg','-r300');
fprintf('Saved %s\n',out);
end
