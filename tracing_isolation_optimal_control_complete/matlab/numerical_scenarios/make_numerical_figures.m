function make_numerical_figures()
% 只读取已保存结果。求解器输出不平滑、不截断，也不替换为参考轨道。
cfg=numerical_cases_config(); p=cfg.parameters; g=build_theory_geometry(p);
if ~isfolder(cfg.paths.figures), mkdir(cfg.paths.figures); end
r=cell(1,5);
for k=1:5
    loaded=load(fullfile(cfg.paths.data,sprintf('E%d.mat',k)),'run'); r{k}=loaded.run;
    assert(r{k}.success,'Cannot label a failed solver output as a completed numerical result.');
end
set(groot,'defaultFigureVisible','off');
colors=[0.12 .40 .68;.82 .36 .10;.48 .31 .64;.10 .55 .46;.68 .24 .37];
markers={'o','s','^','d','v'};
z=linspace(g.z_B,g.e-1e-6,501); sg=zeros(size(z)); ig=sg;
for k=1:numel(z), [sg(k),ig(k)]=g.switch_point(z(k)); end
fig=newfigure(18,11.2); ax=axes(fig); hold(ax,'on');
[S,I]=meshgrid(linspace(.001,1,601),linspace(0,p.K,201));
phi=I+S-g.h*log(S); region=3*ones(size(S));
gammaI=interp1(fliplr(sg),fliplr(ig),S,'linear',NaN);
gammaI(S>g.s_B)=Inf;
region(S>g.e & I<gammaI)=2;
region(phi>g.Phi_B)=4;
region(S<=g.h | phi<=g.Phi_A)=1;
region(S+I>1)=NaN;
contourf(ax,S,I,region,[.5 1.5 2.5 3.5 4.5],'LineStyle','none','HandleVisibility','off');
colormap(ax,[.91 .96 .92;.93 .95 .99;.99 .94 .90;.96 .93 .98]); clim(ax,[1 4]);
s=linspace(g.h,g.s_K,401);
hA=plot(ax,s,g.a(s),'Color',[.2 .45 .25],'LineWidth',1.4);
hG=plot(ax,sg,ig,'k-','LineWidth',1.4);
s=linspace(g.s_B,1,500); ib=g.Phi_B-s+g.h*log(s); valid=ib>=0 & ib+s<=1;
hW=plot(ax,s(valid),ib(valid),'k:','LineWidth',1.3);
hK=plot(ax,[.001 1-p.K],[p.K p.K],'k--','LineWidth',1);
for k=1:5
    rr=r{k}; ix=rr.t_state<=18;
    plot(ax,rr.s_state(ix),rr.i_state(ix),'Color',colors(k,:),'LineWidth',1.2, ...
        'Marker',markers{k},'MarkerIndices',1:20:sum(ix),'MarkerSize',3,'HandleVisibility','off');
    plot(ax,rr.x0(1),rr.x0(2),markers{k},'Color',colors(k,:),'MarkerFaceColor',colors(k,:), ...
        'MarkerSize',6,'HandleVisibility','off');
    offsets=[.008 .005;-.045 .005;.035 -.008;.008 -.007;-.05 .006];
    text(ax,rr.x0(1)+offsets(k,1),rr.x0(2)+offsets(k,2),sprintf('E%d',k), ...
        'Color',colors(k,:),'FontSize',10,'FontWeight','bold');
end
text(ax,.24,.065,'A','FontSize',12,'Color',[.2 .45 .25]);
text(ax,.60,.075,'W_\Gamma','FontSize',11,'HorizontalAlignment','center');
text(ax,.91,.065,'W_K','FontSize',12);
text(ax,.43,.145,'T','FontSize',12);
text(ax,g.s_B+.005,p.K+.005,'s_B','FontSize',10);
xlabel(ax,'s'); ylabel(ax,'i'); xlim(ax,[.15 1.01]); ylim(ax,[0 .165]);
legend(ax,[hA hG hW hK],{'Safe boundary','Switching curve \Gamma_K', ...
    'Waiting interface \Phi=\Phi_B','Capacity K'},'Location','southoutside','NumColumns',2,'Box','off');
style(ax); export(fig,'FigN1_regions',cfg);
timepanels(r,[1 2],18,'FigN2_waiting',cfg);
timepanels(r,[3 4 5],8,'FigN3_boundary_tracking',cfg);
fprintf('NUMERICAL_FIGURES_OK\n');
end

function timepanels(r,ids,tmax,name,cfg)
n=numel(ids); fig=newfigure(18,10.8);
layout=tiledlayout(fig,2,n,'TileSpacing','compact','Padding','compact');
for j=1:n
    rr=r{ids(j)}; ref=rr.reference;
    ax=nexttile(layout,j); hold(ax,'on');
    hn=stairs(ax,[rr.t_control;rr.t_state(end)],[rr.q_control;rr.q_control(end)], ...
        'Color',[.12 .40 .68],'LineWidth',1.3);
    % 用重复事件时间表达理论左右极限，避免插值斜坡。
    tt=linspace(0,tmax,2001)'; events=[ref.events.capacity_start ref.events.full_start ref.events.release];
    for t=events(isfinite(events))
        tt=[tt;max(0,t-1e-10);t]; %#ok<AGROW>
    end
    tt=sort(unique(tt)); g=build_theory_geometry(rr.parameters);
    ref=analytic_reference(rr.parameters,rr.x0,g,tt);
    ha=plot(ax,ref.t,ref.q,'k--','LineWidth',1.15);
    xlim(ax,[0 tmax]); ylim(ax,[-.035 1.09]); ylabel(ax,'q(t)');
    title(ax,sprintf('E%d: (%.2f, %.2f)',ids(j),rr.x0(1),rr.x0(2)),'FontWeight','normal');
    style(ax);
    if j==1
        lg=legend(ax,[ha hn],{'Analytical reference','OpenOCL numerical'},'Orientation','horizontal','Box','off');
        lg.Layout.Tile='south';
    end
    ax=nexttile(layout,n+j); hold(ax,'on');
    plot(ax,rr.t_state,rr.i_state,'Color',[.12 .40 .68],'LineWidth',1.3);
    plot(ax,ref.t,ref.i,'k--','LineWidth',1.15);
    yline(ax,rr.parameters.K,':','Color',[.5 .5 .5],'LineWidth',1);
    xlim(ax,[0 tmax]); ylim(ax,[0 .163]); xlabel(ax,'t'); ylabel(ax,'i(t)'); style(ax);
end
export(fig,name,cfg);
end

function f=newfigure(w,h)
f=figure('Color','w','Units','centimeters','Position',[2 2 w h]);
end
function style(ax)
set(ax,'FontName','Times New Roman','FontSize',10,'LineWidth',.7,'Box','on','Layer','top');
end
function export(f,name,cfg)
exportgraphics(f,fullfile(cfg.paths.figures,[name '.pdf']),'ContentType','vector','BackgroundColor','white');
exportgraphics(f,fullfile(cfg.paths.figures,[name '.png']),'Resolution',300,'BackgroundColor','white');
close(f);
end
