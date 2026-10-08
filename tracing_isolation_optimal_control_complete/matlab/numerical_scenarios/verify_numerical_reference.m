function report = verify_numerical_reference(source)
% 独立 Python fixture 与解析轨道不变量核查；缺失依赖立即报错，不调用优化器。
cfg = numerical_cases_config(); p = cfg.parameters;
if nargin < 1 || isempty(source), source = cfg.paths.analytic_checkpoints; end
if ~isfile(source)
    error('verify_numerical_reference:MissingFixture', ...
        ['Missing analytic fixture: %s\nGenerate it from repository root with:\n' ...
         'python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/' ...
         'generate_analytic_checkpoints.py --write'], source);
end
expected = jsondecode(fileread(source));
assert(expected.schema_version == 2 && ...
    strcmp(expected.status, 'analytical_formula_evaluation_only') && ...
    isequal(expected.openocl_executed, false), ...
    'verify_numerical_reference:FixtureMetadata', 'Invalid analytic fixture metadata.');
names = {'p','c','gamma','K'};
for k = 1:numel(names)
    assertNear(p.(names{k}), expected.parameters.(names{k}), 1e-14, names{k});
end
g = build_theory_geometry(p);
names = {'h','ell','r','s_K','e','z_B','s_B','Phi_A','Phi_B'};
for k = 1:numel(names)
    assertNear(g.(names{k}), expected.geometry.(names{k}), 1e-9, names{k});
end
peakB = fzero(@(s) g.a(g.z_B)+g.ell*log(s/g.z_B)-(s-g.h)*(s-g.r)/s, [g.z_B g.s_B]);
assertNear(peakB,expected.geometry.theta_peak_s_at_z_B,1e-9,'Theta peak');
records = expected.cases;
if iscell(records), records = [records{:}]; end
assert(isstruct(records) && numel(unique({records.case_id})) == numel(records), ...
    'verify_numerical_reference:FixtureCases', 'Duplicated or invalid fixture case_id.');
required = [{cfg.cases.id}, {cfg.safe_check.id}];
assert(isequal(sort({records.case_id}), sort(required)), ...
    'verify_numerical_reference:FixtureCases', 'Fixture case IDs differ from shared inputs.');
maxCostError = 0; maxTimeError = 0;
for k = 1:numel(cfg.cases)
    item = cfg.cases(k); x0 = item.x0;
    check = records(strcmp({records.case_id}, item.id));
    assertNear([check.s0;check.i0], x0, 1e-14, [item.id ' initial state']);
    ref = analytic_reference(p, x0, g, linspace(0,18,2001));
    assert(strcmp(ref.region, item.expected_region) && strcmp(ref.region, check.region));
    assertNear(ref.J_reference, check.J_reference, 1e-9, [item.id ' cost']);
    assertNear([ref.tau_wait ref.tau_boundary ref.tau_full], ...
        [check.tau_wait check.tau_boundary check.tau_full], 1e-8, [item.id ' durations']);
    assertNear([ref.events.full_start ref.events.release], ...
        [check.t_full_start check.t_release], 1e-8, [item.id ' event times']);
    assertNear(ref.events.full_state, [check.s_full;check.i_full], 1e-9, [item.id ' full state']);
    assertNear(ref.events.release_state, [check.s_release;check.i_release], 1e-9, [item.id ' release state']);
    if isempty(check.s_capacity)
        assert(all(isnan(ref.events.capacity_state)) && isnan(ref.events.capacity_start));
    else
        assertNear(ref.events.capacity_state, [check.s_capacity;p.K], 1e-9, [item.id ' capacity state']);
        assertNear(ref.events.capacity_start, ref.tau_wait, 1e-12, [item.id ' capacity start']);
    end
    assert(max(ref.i) <= p.K+1e-9 && min(ref.s)>0 && min(ref.i)>0);
    assert(all(ref.q >= 0 & ref.q <= 1));
    assert(max(ref.s+ref.i) <= sum(x0)+1e-10 && max(diff(ref.s+ref.i)) <= 1e-10);
    assertNear([ref.s(1);ref.i(1)], x0, 1e-12, [item.id ' sampled initial state']);
    er = ref.events.release_state; fs = ref.events.full_state;
    assertNear(safe_peak(er(1), er(2), g.h), p.K, 1e-10, [item.id ' safe endpoint']);
    assertNear(fs(2)-g.ell*log(fs(1)), er(2)-g.ell*log(er(1)), 1e-10, [item.id ' q=1 invariant']);
    assertNear(ref.J_reference, check.J_boundary+p.p*p.c*ref.tau_full, 1e-9, [item.id ' cost accounting']);
    peakTime = ref.events.release+naturalPeakTime(er,p,g);
    assertNear(peakTime,check.t_natural_peak,1e-8,[item.id ' natural peak time']);
    if ref.tau_wait > 0
        before = analytic_reference(p,x0,g,[0;ref.tau_wait/2]);
        assertNear(g.phi(before.s,before.i),repmat(g.phi(x0(1),x0(2)),2,1),1e-9,[item.id ' q=0 invariant']);
    end
    maxCostError = max(maxCostError, abs(ref.J_reference-check.J_reference));
    maxTimeError = max(maxTimeError, abs(ref.events.release-check.t_release));
    % 非零起点、重复点、单点、空阶段和恰好切换处均使用同一段起点。
    ts = [0.123; ref.events.full_start; ref.events.release; 17.25; 0.123];
    sampled = analytic_reference(p,x0,g,ts);
    for j = 1:numel(ts)
        one = analytic_reference(p,x0,g,ts(j));
        assertNear([one.s one.i], [sampled.s(j) sampled.i(j)], 2e-9, [item.id ' sparse sampling']);
    end
    if strcmp(item.id,'E4'), assert(ref.events.capacity_start == 0); end
end
check = records(strcmp({records.case_id}, cfg.safe_check.id));
assertNear([check.s0;check.i0], cfg.safe_check.x0, 1e-14, 'safe case initial state');
r0 = analytic_reference(p,cfg.safe_check.x0,g,[0;1;5;20]);
assert(strcmp(r0.region,'A') && strcmp(check.region,'A') && ...
    check.J_reference == 0 && r0.J_reference == 0 && all(r0.q == 0));
assert(all([check.tau_wait check.tau_boundary check.tau_full check.J_boundary] == 0) && ...
    isempty(check.s_capacity) && isempty(check.s_full) && isempty(check.i_full) && ...
    isempty(check.t_full_start) && isempty(check.t_release));
assertNear([check.s_release;check.i_release],cfg.safe_check.x0,1e-14,'safe release state');
assertNear(naturalPeakTime(cfg.safe_check.x0,p,g),check.t_natural_peak,1e-8,'safe natural peak time');
assert(max(r0.s+r0.i) <= sum(cfg.safe_check.x0)+1e-10 && max(r0.i) <= p.K+1e-9);
assert(safe_peak(.1,1e-25,g.h) == 1e-25);
% 原始 Theta 等式与 MATLAB 已消去平凡根的方程交叉核查。
for z = linspace(g.z_B,g.e-1e-5,30)
    [s,i] = g.switch_point(z);
    assert(s > z);
    assertNear((s-g.h)/(i*(s-g.r)), (z-g.h)/(g.a(z)*(z-g.r)), 1e-8, 'original Theta equation');
    assert(i < (s-g.h)*(s-g.r)/s);  % 非平凡根在峰点右侧。
end
[sg,ig] = g.switch_point((g.z_B+g.e)/2);
rg = analytic_reference(p,[sg;ig],g,[0;1]); assert(rg.tau_wait == 0 && rg.tau_boundary == 0);
rb = analytic_reference(p,[g.s_B;p.K],g,[0;1]); assert(rb.tau_boundary == 0);
sb = g.s_B+0.02; ib = g.Phi_B-sb+g.h*log(sb);
assert(strcmp(classify_initial_state([sb;ib],g,p),'W_Gamma'));
report = struct('verified',true,'fixture_path',source,'case_count',numel(records), ...
    'max_cost_error',maxCostError,'max_release_time_error',maxTimeError,'optimizer_executions',0);
fprintf('ANALYTICAL_REFERENCE_CHECKS_OK cases=%d max_cost_error=%.3g max_release_time_error=%.3g\n', ...
    report.case_count, maxCostError, maxTimeError);
end

function value = naturalPeakTime(x0,p,g)
if x0(1) <= g.h, value = 0; return; end
phi = g.phi(x0(1),x0(2));
value = integral(@(s) 1./(p.p*p.c*s.*(phi-s+g.h*log(s))), ...
    g.h,x0(1),'AbsTol',1e-11,'RelTol',1e-11);
end

function assertNear(actual, expected, tolerance, label)
assert(isequal(size(actual),size(expected)) && all(isfinite(actual(:))) && ...
    all(isfinite(expected(:))) && max(abs(actual(:)-expected(:))) < tolerance, ...
    'verify_numerical_reference:FixtureMismatch', 'Analytic fixture mismatch: %s.', label);
end
