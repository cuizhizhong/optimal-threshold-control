function diagnostics = numerical_solver_diagnostics(info,elapsedSeconds,unavailableReason)
% 只提取真实返回字段；NaN 在 JSON 中为 null，不能用其他迭代量替代残差。
if nargin<2, elapsedSeconds=NaN; end
if nargin<3 || isempty(unavailableReason)
    unavailableReason='当前 OpenOCL/CasADi 返回信息未包含此字段。';
end
diagnostics=struct('schema_version',1,'raw_info_fields',{{}}, ...
    'ipopt_stats_fields',{{}},'iteration_fields',{{}});
diagnostics.success=missing(unavailableReason,'求解器返回的成功状态。');
diagnostics.return_status=missing(unavailableReason,'求解器返回的原始状态字符串。');
diagnostics.iteration_count=missing(unavailableReason,'求解器报告的迭代数。');
diagnostics.elapsed_seconds=scalarMetric(elapsedSeconds,'tic/toc around problem.solve', ...
    'OpenOCL solve 调用的墙钟耗时，单位为秒；不包含问题构建。');
diagnostics.openocl_solve_total_seconds=missing(unavailableReason,'OpenOCL info.timeMeasures.solveTotal。');
diagnostics.openocl_casadi_solve_seconds=missing(unavailableReason,'OpenOCL info.timeMeasures.solveCasadi。');
diagnostics.plugin_wall_seconds=missing(unavailableReason,'CasADi 记录的 NLP 插件墙钟耗时。');
diagnostics.primal_infeasibility=missing(unavailableReason, ...
    'IPOPT 最后一次迭代报告的 inf_pr；保留插件原口径，不作为连续时间可行性证明。');
diagnostics.dual_infeasibility=missing(unavailableReason, ...
    'IPOPT 最后一次迭代报告的 inf_du；当前返回接口不提供完整缩放定义。');
diagnostics.complementarity=missing( ...
    '已核对的 OpenOCL info/CasADi stats 未返回互补残差；iterations.mu 是 barrier 参数。', ...
    '未由 barrier 参数、步长或无定义的乘子运算构造互补残差。');
diagnostics.kkt_residual=missing( ...
    '当前返回接口缺少真实乘子及明确的缩放定义，无法取得 KKT 残差。', ...
    '不由 inf_pr、inf_du、mu 或迭代步长拼出 KKT 证书。');
diagnostics.kkt_certificate_status='not_available';
if ~isstruct(info) || ~isscalar(info), return; end
diagnostics.raw_info_fields=fieldnames(info)';
if isfield(info,'success')
    diagnostics.success=booleanMetric(info.success,'info.success','求解器返回的成功状态。');
end
stats=struct();
if isfield(info,'ipopt_stats') && isstruct(info.ipopt_stats) && isscalar(info.ipopt_stats)
    stats=info.ipopt_stats;
    diagnostics.ipopt_stats_fields=fieldnames(stats)';
end
if isfield(stats,'return_status') && (ischar(stats.return_status) || ...
        (isstring(stats.return_status) && isscalar(stats.return_status)))
    diagnostics.return_status=available(char(stats.return_status),'info.ipopt_stats.return_status', ...
        '求解器返回的原始状态字符串。');
end
if isfield(stats,'iter_count')
    diagnostics.iteration_count=scalarMetric(stats.iter_count,'info.ipopt_stats.iter_count', ...
        '求解器报告的迭代数。');
end
if isfield(stats,'t_wall_my_solver')
    diagnostics.plugin_wall_seconds=scalarMetric(stats.t_wall_my_solver, ...
        'info.ipopt_stats.t_wall_my_solver','CasADi 记录的 NLP 插件墙钟耗时，单位为秒。');
end
if isfield(info,'timeMeasures') && isstruct(info.timeMeasures) && isscalar(info.timeMeasures)
    times=info.timeMeasures;
    if isfield(times,'solveTotal')
        diagnostics.openocl_solve_total_seconds=scalarMetric(times.solveTotal, ...
            'info.timeMeasures.solveTotal','OpenOCL 报告的总求解墙钟耗时，单位为秒。');
    end
    if isfield(times,'solveCasadi')
        diagnostics.openocl_casadi_solve_seconds=scalarMetric(times.solveCasadi, ...
            'info.timeMeasures.solveCasadi','OpenOCL 报告的 CasADi 调用墙钟耗时，单位为秒。');
    end
end
if isfield(stats,'iterations') && isstruct(stats.iterations) && isscalar(stats.iterations)
    iterations=stats.iterations;
    diagnostics.iteration_fields=fieldnames(iterations)';
    if isfield(iterations,'inf_pr')
        diagnostics.primal_infeasibility=lastMetric(iterations.inf_pr, ...
            'info.ipopt_stats.iterations.inf_pr(end)',diagnostics.primal_infeasibility.definition);
    end
    if isfield(iterations,'inf_du')
        diagnostics.dual_infeasibility=lastMetric(iterations.inf_du, ...
            'info.ipopt_stats.iterations.inf_du(end)',diagnostics.dual_infeasibility.definition);
    end
end
end

function metric=lastMetric(values,source,definition)
% 只读最后一项；最后一项无效时不向前挑选较好的有限值。
if isnumeric(values) && isreal(values) && isvector(values) && ~isempty(values)
    metric=scalarMetric(values(end),source,definition);
else
    metric=missing('返回的迭代字段缺失、为空或不是实数向量。',definition);
    metric.source=source;
end
end

function metric=scalarMetric(value,source,definition)
if isnumeric(value) && isreal(value) && isscalar(value) && isfinite(value)
    metric=available(double(value),source,definition);
else
    metric=missing('返回值缺失或不是有限实数标量。',definition);
    metric.source=source;
end
end

function metric=booleanMetric(value,source,definition)
if (islogical(value) || isnumeric(value)) && isreal(value) && isscalar(value) && ...
        isfinite(value) && any(value==[0 1])
    metric=available(logical(value),source,definition);
else
    metric=missing('返回的 success 不是标量布尔值。',definition);
    metric.source=source;
end
end

function metric=available(value,source,definition)
metric=struct('value',value,'status','available','source',source,'reason','','definition',definition);
end

function metric=missing(reason,definition)
metric=struct('value',NaN,'status','not_available','source','','reason',reason,'definition',definition);
end
