function verify_numerical_reference()
% 独立 Python 求根检查点及物理不变量回归，不调用优化器。
cfg=numerical_cases_config(); p=cfg.parameters; g=build_theory_geometry(p);
source=fullfile(cfg.paths.report_root,'validation','numerical_scenarios','analytic_checkpoints.json');
expected=jsondecode(fileread(source));
assert(abs(g.s_B-expected.geometry.s_B)<1e-9);
assert(abs(g.e-expected.geometry.e)<1e-9);
for k=1:5
    x0=cfg.cases(k).x0;
    if iscell(expected.cases), check=expected.cases{k}; else, check=expected.cases(k); end
    ref=analytic_reference(p,x0,g,linspace(0,18,2001));
    assert(strcmp(ref.region,cfg.cases(k).expected_region));
    assert(abs(ref.J_reference-check.J_reference)<1e-9);
    assert(abs(ref.events.release-check.t_release)<1e-8);
    assert(max(ref.i)<=p.K+1e-9 && min(ref.s)>0 && min(ref.i)>0);
    assert(max(ref.s+ref.i)<=sum(x0)+1e-10);
    assert(max(abs([ref.s(1);ref.i(1)]-x0))<1e-12);
    er=ref.events.release_state;
    assert(abs(safe_peak(er(1),er(2),g.h)-p.K)<1e-10);
    assert(abs((ref.events.full_state(2)-g.ell*log(ref.events.full_state(1))) ...
        -(er(2)-g.ell*log(er(1))))<1e-10);
    % 不包含 0、重复点、仅单点、跨过空阶段、恰好切换处。
    ts=[0.123;ref.events.full_start;ref.events.release;17.25;0.123];
    sampled=analytic_reference(p,x0,g,ts);
    for j=1:numel(ts)
        one=analytic_reference(p,x0,g,ts(j));
        assert(max(abs([one.s one.i]-[sampled.s(j) sampled.i(j)]))<2e-9);
    end
    if ismember(k,[1 3 5]), assert(isnan(ref.events.capacity_start)); end
    if k==4, assert(ref.events.capacity_start==0); end
end
r0=analytic_reference(p,cfg.safe_check.x0,g,[1;5;20]);
assert(strcmp(r0.region,'A') && r0.J_reference==0 && all(r0.q==0));
assert(safe_peak(.1,1e-25,g.h)==1e-25);
% 切换曲线上和容量交点为退化弧；等待公共界面归入 W_Gamma。
[sg,ig]=g.switch_point((g.z_B+g.e)/2);
rg=analytic_reference(p,[sg;ig],g,[0;1]); assert(rg.tau_wait==0 && rg.tau_boundary==0);
rb=analytic_reference(p,[g.s_B;p.K],g,[0;1]); assert(rb.tau_boundary==0);
sb=g.s_B+0.02; ib=g.Phi_B-sb+g.h*log(sb);
assert(strcmp(classify_initial_state([sb;ib],g,p),'W_Gamma'));
% 非平凡曲线内点满足原始 Theta 方程。
for z=linspace(g.z_B,g.e-1e-5,30)
    [s,i]=g.switch_point(z);
    assert(s>z && abs((s-g.h)/(i*(s-g.r))-(z-g.h)/(g.a(z)*(z-g.r)))<1e-8);
end
fprintf('ANALYTICAL_REFERENCE_CHECKS_OK\n');
end
