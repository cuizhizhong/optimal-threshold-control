function [region,hit] = classify_initial_state(x0,geom,par)
% 由状态和自然轨道标号判别；不使用算例 ID。
s=x0(1); i=x0(2); tol=1e-11;
assert(all(isfinite(x0)) && s>0 && i>0 && i<=par.K+tol && s+i<=1+tol);
hit=[NaN;NaN];
if safe_peak(s,i,geom.h)<=par.K+tol
    region='A'; return
end
phi=geom.phi(s,i);
if phi>geom.Phi_B+tol
    if abs(i-par.K)<=tol
        region='B'; hit=x0(:);
    else
        region='W_K';
        hit=[fzero(@(v) geom.phi(v,par.K)-phi,[geom.h s]);par.K];
    end
    return
end
if abs(phi-geom.Phi_B)<=tol
    z=geom.z_B;
else
    z=fzero(@(v) switch_label(v,geom)-phi,[geom.z_B geom.e]);
end
[sg,ig]=geom.switch_point(z); hit=[sg;ig];
if abs(s-sg)<=tol
    region='Gamma';
elseif s>sg
    region='W_Gamma';
else
    region='T';
end
end

function value=switch_label(z,geom)
[s,i]=geom.switch_point(z); value=geom.phi(s,i);
end
