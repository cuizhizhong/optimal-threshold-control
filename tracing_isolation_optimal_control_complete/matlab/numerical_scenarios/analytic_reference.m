function ref = analytic_reference(par,x0,geom,t_eval)
% 从各段真实起点构造参考解，采样点不必包含 0 或切换时刻。
t=t_eval(:); assert(all(isfinite(t)) && all(t>=0));
[region,hit]=classify_initial_state(x0,geom,par);
tw=0; tb=0; tf=0; cb=0; cap=[NaN;NaN]; full=[NaN;NaN]; release=x0(:);
if ~strcmp(region,'A')
    if ismember(region,{'W_K','B'})
        cap=hit;
        tw=waiting_time(x0,cap(1),geom,par);
        tb=log((cap(1)-geom.r)/(geom.s_B-geom.r))/(par.c*par.K);
        cb=par.p/(par.K*(1-par.p))*(log(cap(1)/geom.s_B)- ...
            par.p*log((cap(1)-geom.r)/(geom.s_B-geom.r)));
        full=[geom.s_B;par.K];
    elseif strcmp(region,'W_Gamma')
        full=hit; tw=waiting_time(x0,hit(1),geom,par);
    else
        full=x0(:);
    end
    assert(full(1)*exp(-full(2)/geom.ell)<geom.s_K);
    psi=full(2)-geom.ell*log(full(1));
    sr=fzero(@(s) geom.G(s)-psi,[geom.h min(full(1),geom.s_K)],optimset('TolX',1e-13));
    release=[sr;geom.a(sr)];
    assert(release(2)>0 && release(2)<=full(2));
    tf=log(full(2)/release(2))/par.gamma;
end
tfull=tw+tb; tr=tfull+tf;
s=nan(size(t)); i=s; q=zeros(size(t));
if strcmp(region,'A')
    y=natural(x0,t,par); s=y(1,:)'; i=y(2,:)';
else
    ix=t<tw;
    if any(ix), y=natural(x0,t(ix),par); s(ix)=y(1,:)'; i(ix)=y(2,:)'; end
    ix=t>=tw & t<tfull;
    s(ix)=geom.r+(cap(1)-geom.r)*exp(-par.c*par.K*(t(ix)-tw));
    i(ix)=par.K; q(ix)=1-geom.h./s(ix);
    ix=t>=tfull & t<tr;
    i(ix)=full(2)*exp(-par.gamma*(t(ix)-tfull));
    s(ix)=full(1)*exp(-(par.c/par.gamma)*(full(2)-i(ix))); q(ix)=1;
    ix=t>=tr;
    if any(ix), y=natural(release,t(ix)-tr,par); s(ix)=y(1,:)'; i(ix)=y(2,:)'; end
end
tc=NaN; te=NaN;
if tb>1e-12, tc=tw; te=tfull; end
if strcmp(region,'A'), tfull=NaN; tr=NaN; end
events=struct('capacity_start',tc,'capacity_end',te,'full_start',tfull, ...
    'release',tr,'capacity_state',cap,'full_state',full,'release_state',release);
ref=struct('t',t,'s',s,'i',i,'q',q,'region',region,'events',events, ...
    'tau_wait',tw,'tau_boundary',tb,'tau_full',tf,'J_reference',cb+par.p*par.c*tf);
assert(all(isfinite([s;i;q])));
end

function tw=waiting_time(x0,sEnd,geom,par)
if abs(x0(1)-sEnd)<1e-12, tw=0; return; end
phi=geom.phi(x0(1),x0(2));
tw=integral(@(s) 1./(par.p*par.c*s.*(phi-s+geom.h*log(s))), ...
    sEnd,x0(1),'AbsTol',1e-11,'RelTol',1e-11);
end

function y=natural(x0,t,par)
if max(t)==0, y=repmat(x0(:),1,numel(t)); return; end
rhs=@(~,x) [-par.p*par.c*x(1)*x(2);(par.p*par.c*x(1)-par.gamma)*x(2)];
sol=ode45(rhs,[0 max(t)],x0(:),odeset('RelTol',2e-10,'AbsTol',1e-13));
y=deval(sol,t');
end
