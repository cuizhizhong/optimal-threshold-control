function report = refresh_numerical_assessments()
% 只新增独立assessment；原始记录与历史兼容文件保持原字节。
cfg=numerical_cases_config(); spec=numerical_assessment_spec(cfg);
files=dir(fullfile(cfg.paths.data,'runs','*.mat'));
% 没有新runs时允许对历史数据诊断，但来源始终为legacy_unverified。
if isempty(files), files=dir(fullfile(cfg.paths.data,'E*.mat')); end
report=struct('run_ids',{{}},'source_status',{{}},'assessment_called',[]);
for k=1:numel(files)
    filename=fullfile(files(k).folder,files(k).name); d=load(filename,'run');
    if ~isfield(d,'run') || ~d.run.success, continue; end
    [view,called]=assess_saved_numerical_run(d.run,cfg.paths.data, ...
        @(raw) numerical_assessment_view(raw,cfg),spec,false);
    report.run_ids{end+1}=view.run_id;
    report.source_status{end+1}=view.source_status;
    report.assessment_called(end+1)=called;
end
numerical_write_json(fullfile(cfg.paths.data,'revision_checks','assessment_refresh.json'),report);
end
