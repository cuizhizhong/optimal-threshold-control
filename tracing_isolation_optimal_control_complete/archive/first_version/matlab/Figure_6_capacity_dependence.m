clear; close all; clc;
thisDir=fileparts(mfilename('fullpath')); root=fileparts(thisDir); T=readtable(fullfile(root,'data','capacity_sensitivity.csv'));
figure('Color','w','Position',[100 100 900 560]); hold on;
plot(T.K,T.optimal_cost,'LineWidth',2.5,'DisplayName','Optimal cost');
plot(T.K,T.fill_box_cost,'--','LineWidth',2.0,'DisplayName','Pure fill-the-box cost');
peak=0.3418232594582696; xline(peak,':','LineWidth',1.3,'DisplayName','Natural peak');
xlabel('Capacity K'); ylabel('Minimum control cost'); title('Capacity dependence'); grid on; box on; legend('Location','northeast');
out=fullfile(root,'figures','Figure_6_capacity_dependence.jpg'); print(gcf,out,'-djpeg','-r300'); fprintf('%s\n',out);
