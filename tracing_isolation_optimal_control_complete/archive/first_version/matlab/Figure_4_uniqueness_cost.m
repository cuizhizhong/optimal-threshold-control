clear; close all; clc;
thisDir=fileparts(mfilename('fullpath')); root=fileparts(thisDir);
par=default_par(); sol=optimize_constant_c(par); gridS=linspace(par.h*1.0005,sol.s1,420); J=nan(size(gridS));
for k=1:numel(gridS)
    try, J(k)=boundary_cost(sol.s1,gridS(k),par)+q1_cost(gridS(k),par.K,par); catch, J(k)=NaN; end
end
figure('Color','w','Position',[100 100 880 560]); hold on;
plot(gridS,J,'LineWidth',2.4,'DisplayName','Admissible boundary-to-q=1 family');
xline(sol.s_switch,'--','LineWidth',1.4,'DisplayName','Unique minimizer');
scatter(sol.s_switch,sol.cost,55,'filled','HandleVisibility','off');
xlabel('Susceptible level at boundary-to-q=1 switch'); ylabel('Total control cost');
title('Strict one-dimensional minimum and a.e. uniqueness'); grid on; box on; legend('Location','northwest');
out=fullfile(root,'figures','Figure_4_uniqueness_cost.jpg'); print(gcf,out,'-djpeg','-r300'); fprintf('%s\n',out);


function par = default_par()
par.p = 0.5; par.c = 2.0; par.gamma = 0.3; par.K = 0.15;
par.s0 = 0.99; par.i0 = 0.01;
par.b = par.p*par.c;
par.h = par.gamma/par.b;
par.r = (1-par.p)*par.h;
par.ell = par.gamma/par.c;
end

function y = natural_i(s,par)
y = par.i0 + par.s0 - s + par.h.*log(s./par.s0);
end

function [speak,ipeak] = natural_peak(par)
if par.s0 <= par.h
    speak = par.s0; ipeak = par.i0;
else
    speak = par.h;
    ipeak = par.i0 + par.s0 - par.h + par.h*log(par.h/par.s0);
end
end

function val = safe_level(par)
val = par.K + par.h - par.h*log(par.h);
end

function y = safe_i(s,par)
y = safe_level(par) - (s - par.h.*log(s));
end

function y = ridge_i(s,par)
y = (s-par.h).*(s-par.r)./s;
end

function y = theta_fun(s,i,par)
y = (s-par.h)./(i.*(s-par.r));
end

function s1 = first_capacity_s(par)
[~,ipeak] = natural_peak(par);
if ipeak <= par.K + 1e-12
    s1 = par.h;
else
    f = @(s) natural_i(s,par)-par.K;
    s1 = fzero(f,[par.h*(1+1e-10),par.s0]);
end
end

function tau = natural_hit_time(par,sTarget)
if sTarget >= par.s0
    tau = 0;
else
    f = @(s) 1./(par.b.*s.*natural_i(s,par));
    tau = integral(f,sTarget,par.s0,'RelTol',1e-10,'AbsTol',1e-12);
end
end

function [sb,ib] = terminal_from_q1_start(sa,ia,par)
chi = ia - par.ell*log(sa);
f = @(s) safe_level(par) - s + par.r*log(s) - chi;
lo = par.h*(1+1e-12); hi = sa;
if f(lo)*f(hi) > 0
    grid = linspace(par.h,sa,800);
    vals = arrayfun(f,grid);
    idx = find(vals(1:end-1).*vals(2:end)<=0,1,'last');
    if isempty(idx), error('No q=1 terminal intersection.'); end
    lo = grid(idx); hi = grid(idx+1);
end
sb = fzero(f,[lo,hi]);
ib = safe_i(sb,par);
if ib <= 0 || ib > ia*(1+1e-8)
    error('Invalid q=1 terminal point.');
end
end

function [cost,sb,ib] = q1_cost(sa,ia,par)
[sb,ib] = terminal_from_q1_start(sa,ia,par);
cost = par.b/par.gamma*log(ia/ib);
end

function val = boundary_cost(shi,slo,par)
if shi <= slo + 1e-14
    val = 0; return;
end
term = log(shi/slo) - par.p*log((shi-par.r)/(slo-par.r));
val = par.p/(par.K*(1-par.p))*term;
end

function val = boundary_duration(shi,slo,par)
if shi <= slo + 1e-14
    val = 0; return;
end
val = log((shi-par.r)/(slo-par.r))/(par.c*par.K);
end

function [fbest,xbest] = robust_min(fun,lo,hi)
xs = linspace(lo,hi,180);
vals = arrayfun(fun,xs);
valid = isfinite(vals) & vals < 1e7;
if ~any(valid)
    fbest = inf; xbest = NaN; return;
end
inds = find(valid); [~,j] = min(vals(valid)); k = inds(j);
left = xs(max(1,k-2)); right = xs(min(numel(xs),k+2));
if right-left < 1e-12
    xbest = xs(k); fbest = vals(k); return;
end
opts = optimset('TolX',2e-12,'Display','off');
[xloc,floc] = fminbnd(fun,left,right,opts);
if ~isfinite(floc) || floc >= 1e7
    xbest = xs(k); fbest = vals(k);
else
    xbest = xloc; fbest = floc;
end
end

function val = direct_objective(s,par,phi0)
i = phi0 - (s-par.h*log(s));
if i <= 0 || i > par.K*(1+1e-8)
    val = 1e8; return;
end
try
    val = q1_cost(s,i,par);
catch
    val = 1e8;
end
end

function val = boundary_objective(s,par,s1)
try
    jq = q1_cost(s,par.K,par);
    val = boundary_cost(s1,s,par)+jq;
catch
    val = 1e8;
end
end

function sol = optimize_constant_c(par)
[speak,ipeak] = natural_peak(par);
phi0 = par.i0 + par.s0 - par.h*log(par.s0);
if ipeak <= par.K + 1e-12 || par.s0 <= par.h
    sol.regime='safe'; sol.s_peak=speak; sol.i_peak=ipeak;
    sol.s1=par.h; sol.s_switch=par.s0; sol.i_switch=par.i0;
    sol.s_release=par.s0; sol.i_release=par.i0;
    sol.tau1=0; sol.tau_boundary=0; sol.tau_q1=0;
    sol.cost=0; sol.fill_box_cost=0; sol.direct_cost=0; sol.boundary_cost_total=0;
    return;
end
s1 = first_capacity_s(par);
funD = @(s) direct_objective(s,par,phi0);
[jd,sd] = robust_min(funD,s1,par.s0);
if isfinite(jd)
    id = phi0 - (sd-par.h*log(sd));
    [jd,sbd,ibd] = q1_cost(sd,id,par);
else
    id=NaN; sbd=NaN; ibd=NaN;
end
funB = @(s) boundary_objective(s,par,s1);
[jb,sbnd] = robust_min(funB,par.h*(1+2e-10),s1);
if isfinite(jb)
    [jq,sbb,ibb] = q1_cost(sbnd,par.K,par);
    jb = boundary_cost(s1,sbnd,par)+jq;
else
    sbb=NaN; ibb=NaN;
end
fill = boundary_cost(s1,par.h,par);
tol=2e-7;
if isfinite(jb) && (~isfinite(jd) || (jb+tol<jd && sbnd<s1-1e-7))
    sol.regime='capacity-q1'; sw=sbnd; iw=par.K; srel=sbb; irel=ibb; cost=jb;
    tau1=natural_hit_time(par,s1); tb=boundary_duration(s1,sw);
elseif isfinite(jd)
    sol.regime='direct-q1'; sw=sd; iw=id; srel=sbd; irel=ibd; cost=jd;
    tau1=natural_hit_time(par,sw); tb=0;
else
    sol.regime='fill-box'; sw=par.h; iw=par.K; srel=par.h; irel=par.K; cost=fill;
    tau1=natural_hit_time(par,s1); tb=boundary_duration(s1,par.h);
end
sol.s_peak=speak; sol.i_peak=ipeak; sol.s1=s1;
sol.s_switch=sw; sol.i_switch=iw; sol.s_release=srel; sol.i_release=irel;
sol.tau1=tau1; sol.tau_boundary=tb; sol.tau_q1=log(iw/irel)/par.gamma;
sol.cost=cost; sol.fill_box_cost=fill; sol.direct_cost=jd; sol.boundary_cost_total=jb;
end

function tr = simulate_optimal(par,tEnd,n)
sol = optimize_constant_c(par);
t = linspace(0,tEnd,n)'; s=nan(size(t)); i=nan(size(t)); q=zeros(size(t));
rhs0 = @(tt,y) [-par.b*y(1)*y(2); (par.b*y(1)-par.gamma)*y(2)];
opts=odeset('RelTol',2e-10,'AbsTol',1e-12);
if strcmp(sol.regime,'safe')
    [~,Y]=ode45(rhs0,t,[par.s0;par.i0],opts); s=Y(:,1); i=Y(:,2);
else
    t0=sol.tau1; tB=t0+sol.tau_boundary; tR=tB+sol.tau_q1;
    idx=find(t<=t0+1e-12);
    if numel(idx)>=2
        [~,Y]=ode45(rhs0,t(idx),[par.s0;par.i0],opts); s(idx)=Y(:,1); i(idx)=Y(:,2);
    elseif numel(idx)==1
        s(idx)=par.s0; i(idx)=par.i0;
    end
    idx=find(t>t0 & t<=tB+1e-12);
    if ~isempty(idx)
        u=t(idx)-t0; s(idx)=par.r+(sol.s1-par.r).*exp(-par.c*par.K.*u); i(idx)=par.K;
        q(idx)=1-par.h./s(idx);
    end
    idx=find(t>tB & t<=tR+1e-12);
    if ~isempty(idx)
        u=t(idx)-tB; i(idx)=sol.i_switch.*exp(-par.gamma.*u);
        s(idx)=sol.s_switch.*exp(-(par.c/par.gamma).*(sol.i_switch-i(idx))); q(idx)=1;
    end
    idx=find(t>tR);
    if ~isempty(idx)
        tt=t(idx)-tR; tsp=[0;tt];
        [~,Y]=ode45(rhs0,tsp,[sol.s_release;sol.i_release],opts);
        s(idx)=Y(2:end,1); i(idx)=Y(2:end,2);
    end
end
tr.t=t; tr.s=s; tr.i=i; tr.q=q;
tr.beta1=par.c*(par.p+(1-par.p).*q); tr.beta2=par.p*par.c*(1-q); tr.summary=sol;
end

function [swS,swI,teS,teI] = switching_curve(par,sMax,n)
f=@(s) safe_i(s,par)-ridge_i(s,par);
upper=max(par.h*1.1,sMax);
while f(upper)>0 && upper<20, upper=upper*1.3; end
se=fzero(f,[par.h*(1+1e-10),upper]);
terms=linspace(par.h*(1+5e-4),se*(1-5e-5),n);
swS=[];swI=[];teS=[];teI=[];
for m=1:numel(terms)
    sb=terms(m); ib=safe_i(sb,par); thb=theta_fun(sb,ib,par);
    iq1=@(S) ib+par.ell*log(S/sb);
    fr=@(S) theta_fun(S,iq1(S),par)-thb;
    lo=sb*(1+1e-6); lastx=lo; lastv=fr(lo); root=NaN;
    hi=max(sMax*1.4,sb*1.5); grid=logspace(log10(lo),log10(hi),500);
    for k=2:numel(grid)
        v=fr(grid(k));
        if lastv>0 && v<=0
            root=fzero(fr,[lastx,grid(k)]); break;
        end
        lastx=grid(k); lastv=v;
    end
    if isfinite(root) && root<=sMax
        swS(end+1)=root; swI(end+1)=iq1(root); teS(end+1)=sb; teI(end+1)=ib; %#ok<AGROW>
    end
end
end
