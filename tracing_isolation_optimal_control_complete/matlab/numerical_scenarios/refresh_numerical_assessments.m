function refresh_numerical_assessments()
% 后处理修订后，重新检查保存的原始输出；不调用求解器、不改控制数组。
cfg=numerical_cases_config(); files=dir(fullfile(cfg.paths.data,'**','*.mat'));
for k=1:numel(files)
    filename=fullfile(files(k).folder,files(k).name); d=load(filename,'run'); run=d.run;
    if ~isfield(run,'reference'), continue; end
    run.assessment=assess_numerical_case(run,run.reference,run.parameters,cfg.check);
    run.assessment_settings=cfg.check;
    save(filename,'run','-v7');
end
export_numerical_latex();
end
