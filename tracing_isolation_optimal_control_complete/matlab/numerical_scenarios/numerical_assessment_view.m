function view = numerical_assessment_view(run,cfg)
% 同一后处理入口供runner和重新评估使用。
geom=build_theory_geometry(run.parameters);
reference=analytic_reference(run.parameters,run.x0,geom, ...
    unique([linspace(0,18,cfg.plot.reference_samples)';run.t_state]));
assessment=assess_numerical_case(run,reference,run.parameters,cfg.check);
view=struct('reference',reference,'assessment',assessment);
end
