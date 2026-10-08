function report = revision_threshold_saved(cfg,runs)
% 只复核同一主结果的识别阈值；不构建OCP、不加载OpenOCL、不调用solver。
if nargin<2, runs={}; end
folder=fullfile(cfg.paths.data,'revision_checks');
report=struct('schema_version',1,'status','blocked','optimizer_calls',0, ...
    'checked_utc',numerical_utc(),'consistency_pass',false,'rows',[],'blockers',{{}});
if isempty(runs)
    try
        runs=load_selected_numerical_runs(cfg.paths.data);
    catch exception
        if strcmp(exception.identifier,'numerical:MissingSelectionManifest')
            report.blockers={exception.message};
            numerical_write_json(fullfile(folder,'threshold_summary.json'),report); return;
        end
        rethrow(exception);
    end
end
assert(numel(runs)==5,'revision:InvalidThresholdSources','Threshold mode requires all five selected main sources.');
for k=1:5
    run=runs{k}; id=sprintf('E%d',k); ix=find(strcmp({cfg.cases.id},id));
    opts=cfg.solve; opts.N=cfg.cases(ix).main_N; opts.initialization='analytic_reference';
    assert(strcmp(run.case_id,id) && run.success && ...
        strcmp(run.source_status,'verified_record') && isequaln(run.solver_settings,opts) && ...
        isequal(run.parameters,cfg.parameters) && isequal(run.x0(:),cfg.cases(ix).x0(:)) && ...
        strcmp(run.initialization.type,'analytic_reference'), ...
        'revision:InvalidThresholdSources','Threshold source %s is not the predeclared main result.',id);
    % 使用不可覆盖raw进行缓存指纹计算，避免把兼容副本的既有评估嵌入raw哈希。
    index=jsondecode(fileread(fullfile(cfg.paths.data,'run_index.json')));
    entry=find(strcmp({index.entries.run_id},run.run_id)); assert(isscalar(entry));
    rawPath=fullfile(cfg.paths.data,index.entries(entry).raw_file);
    assert(strcmp(numerical_sha256(rawPath,'file'),index.entries(entry).raw_sha256), ...
        'numerical:RawRecordModified','Threshold source raw record changed.');
    loaded=load(rawPath,'run');
    [run,~]=assess_saved_numerical_run(loaded.run,cfg.paths.data,@(raw) numerical_assessment_view(raw,cfg), ...
        numerical_assessment_spec(cfg),false);
    xy=[run.assessment.reintegration.s run.assessment.reintegration.i];
    t=run.assessment.reintegration.t;
    baseline=detect_numerical_events(run.t_control,run.q_control,t,xy,cfg.parameters.K,cfg.check);
    for epsq=cfg.revision.threshold_control
        for epsK=cfg.revision.threshold_capacity
            settings=cfg.check; settings.event_control_threshold=epsq; settings.event_capacity_threshold=epsK;
            detected=detect_numerical_events(run.t_control,run.q_control,t,xy,cfg.parameters.K,settings);
            [eventsPass,comparisons]=compareDetection(baseline,detected);
            passes=strcmp(baseline.observed_structure,detected.observed_structure) && ...
                detected.diagnostics.passed && eventsPass;
            observed=rmfield(detected,{'t','q','state_xy','K'});
            out=struct('case_id',id,'run_id',run.run_id,'solve_fingerprint',run.solve_fingerprint, ...
                'control_threshold',epsq,'capacity_threshold',epsK, ...
                'observed_structure',detected.observed_structure, ...
                'consistency_pass',passes,'event_comparison',comparisons,'detection',observed);
            if isempty(report.rows), report.rows=out; else, report.rows(end+1)=out; end
        end
    end
end
report.status='completed'; report.consistency_pass=all([report.rows.consistency_pass]);
numerical_write_json(fullfile(folder,'threshold_summary.json'),report);
table=struct2table(rmfield(report.rows,{'event_comparison','detection'}));
writetable(table,fullfile(folder,'threshold_summary.csv'));
end

function [passed,comparison]=compareDetection(base,other)
names=fieldnames(base.events); comparison=struct(); passed=true;
for k=1:numel(names)
    a=base.events.(names{k}); b=other.events.(names{k});
    sameStatus=strcmp(a.status,b.status) && a.candidate_count==b.candidate_count;
    distance=NaN; allowed=NaN;
    if a.candidate_count==1 && b.candidate_count==1
        distance=max(abs(a.interval-b.interval));
        allowed=max(a.local_max_cell_width,b.local_max_cell_width);
        eventPass=sameStatus && distance<=allowed+1e-10;
    else
        eventPass=sameStatus && a.candidate_count==0;
    end
    comparison.(names{k})=struct('passed',eventPass,'baseline_status',a.status,'observed_status',b.status, ...
        'baseline_interval',a.interval,'observed_interval',b.interval, ...
        'endpoint_maximum_shift',distance,'local_maximum_cell_width',allowed);
    passed=passed && eventPass;
end
end
