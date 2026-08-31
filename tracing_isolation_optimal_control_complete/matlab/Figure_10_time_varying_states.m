clear; close all; clc;
thisDir=fileparts(mfilename('fullpath')); root=fileparts(thisDir);
A=readtable(fullfile(root,'data','time_varying_regularized_solution.csv')); B=readtable(fullfile(root,'data','time_varying_no_control.csv')); K=0.15;
figure('Color','w','Position',[100 100 900 560]); hold on;
plot(A.time,A.i,'LineWidth',2.5,'DisplayName','Optimized i(t)');
plot(B.time,B.i_no,'--','LineWidth',2.0,'DisplayName','No isolation');
plot([min(A.time) max(A.time)],[K K],':','LineWidth',1.6,'DisplayName','Capacity K');
xlabel('Time'); ylabel('Infectious fraction'); title('State constraint under a contact surge'); grid on; box on; legend('Location','northeast');
out=fullfile(root,'figures','Figure_10_time_varying_states.jpg'); print(gcf,out,'-djpeg','-r300'); fprintf('%s\n',out);
