clear; close all; clc;
thisDir=fileparts(mfilename('fullpath')); root=fileparts(thisDir); T=readtable(fullfile(root,'data','regime_map_long.csv'));
ps=unique(T.p); Ks=unique(T.K); Z=nan(numel(Ks),numel(ps));
for k=1:height(T)
    ix=find(abs(ps-T.p(k))<1e-12,1); iy=find(abs(Ks-T.K(k))<1e-12,1); Z(iy,ix)=T.regime_code(k);
end
figure('Color','w','Position',[100 100 900 590]); imagesc(ps,Ks,Z); set(gca,'YDir','normal');
cb=colorbar; cb.Ticks=[0 1 2 3]; cb.TickLabels={'No control','Direct q=1','Capacity + q=1','Fill-box limit'};
xlabel('Transmission probability p'); ylabel('Capacity K'); title('Regime map for the constant-contact problem'); box on;
out=fullfile(root,'figures','Figure_8_regime_map.jpg'); print(gcf,out,'-djpeg','-r300'); fprintf('%s\n',out);
