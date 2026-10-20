function view = numerical_assessment_view(run,cfg)
% 同一后处理入口供runner和重新评估使用。
% 先校验raw/payload原结构，再创建计算副本；原有失败仍由assessment如实记录。
originalConsistency=numerical_run_consistency(run,run.parameters,cfg.check.grid_time_tolerance);
par=numerical_normalize_parameters(run.parameters);
geom=build_theory_geometry(par);
reference=analytic_reference(par,run.x0,geom, ...
    unique([linspace(0,18,cfg.plot.reference_samples)';run.t_state]));
assessment=assess_numerical_case(run,reference,par,cfg.check);
assert(isequaln(assessment.consistency,originalConsistency), ...
    'numerical:NormalizationChangedProvenance','Parameter normalization changed source validation.');
view=struct('reference',reference,'assessment',assessment);
end
