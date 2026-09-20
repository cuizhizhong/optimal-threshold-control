function geom = build_theory_geometry(par)
% 按正文定义构造几何；函数句柄只用于解析计算，不进入 OCP。
h = par.gamma/(par.p*par.c); ell = par.gamma/par.c; r = h-ell;
assert(par.p>0 && par.p<1 && par.c>0 && par.gamma>0 && par.K>0);
phiA = par.K+h-h*log(h);
a = @(s) phiA-s+h*log(s);
g = @(s) (s-h).*(s-r)./s;
hi = max(1,2*h);
while a(hi)>0, hi=2*hi; end
sk = fzero(a,[h hi]);
e = fzero(@(s) a(s)-g(s),[h sk]);
geom = struct('h',h,'ell',ell,'r',r,'Phi_A',phiA,'s_K',sk,'e',e);
geom.a = a;
geom.phi = @(s,i) i+s-h*log(s);
geom.G = @(s) a(s)-ell*log(s);
% 除去平凡根后的等价切换方程，在合并端点附近也保持稳定。
geom.switch_point = @(z) switch_point(z,h,r,ell,e,a);
lo=h+0.5*(e-h);
while capacity_at(lo,geom)<par.K, lo=h+(lo-h)/10; end
zB=fzero(@(z) capacity_at(z,geom)-par.K,[lo e]);
[sB,iB]=geom.switch_point(zB);
assert(abs(iB-par.K)<1e-9);
geom.z_B=zB; geom.s_B=sB; geom.Phi_B=geom.phi(sB,par.K);
end

function i=capacity_at(z,geom)
[~,i]=geom.switch_point(z);
end

function [s,i]=switch_point(z,h,r,ell,e,a)
assert(z>h && z<=e);
if z==e
    s=e; i=a(e); return % 已知合并极限，不当作非平凡曲线内点。
end
az=a(z);
fun=@(d) az-(z-h)*(z+d-r)*log_ratio(d,z);
hi=max(e-z,0.01);
while fun(hi)>0, hi=2*hi; end
d=fzero(fun,[0 hi],optimset('TolX',1e-13));
s=z+d; i=az+ell*log1p(d/z);
assert(d>0 && i>0 && abs(fun(d))<1e-9);
end

function v=log_ratio(d,z)
if d==0, v=1/z; else, v=log1p(d/z)/d; end
end
