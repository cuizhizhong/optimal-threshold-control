clear; close all; clc;
thisDir=fileparts(mfilename('fullpath')); root=fileparts(thisDir); T=readtable(fullfile(root,'data','probability_sensitivity.csv'));
figure('Color','w','Position',[100 100 900 560]);
plot(T.p,T.saving_percent,'LineWidth',2.5); xlabel('Transmission probability per contact p');
ylabel('Cost saving relative to fill-the-box (%)'); title('Why tracing isolation changes the optimal geometry'); grid on; box on;
out=fullfile(root,'figures','Figure_7_probability_dependence.jpg'); print(gcf,out,'-djpeg','-r300'); fprintf('%s\n',out);
