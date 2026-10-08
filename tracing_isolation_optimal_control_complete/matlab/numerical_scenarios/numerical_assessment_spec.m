function spec = numerical_assessment_spec(cfg)
% reference采样设置也影响后处理指纹，不影响原始求解指纹。
source=numerical_code_hash('assessment');
spec=struct('code_hash',source.hash,'source_files',source.files,'settings',cfg.check, ...
    'reference_samples',cfg.plot.reference_samples,'reference_plot_horizon',18);
end
