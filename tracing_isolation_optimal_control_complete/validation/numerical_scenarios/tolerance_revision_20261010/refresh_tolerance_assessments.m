function report = refresh_tolerance_assessments()
% 仅重评基线中的35个保存结果；不进入调度、优化或结果再选择流程。
here=fileparts(mfilename('fullpath'));
reportRoot=fileparts(fileparts(fileparts(here)));
addpath(fullfile(reportRoot,'matlab','numerical_scenarios'));
cfg=revision_validation_config(); dataRoot=cfg.paths.data;
baseline=fullfile(here,'baseline_data'); revisionId='tolerance_revision_20261010';
reportPath=fullfile(here,'assessment_revision_report.json');
oldManifest=readjson(fullfile(baseline,'selection_manifest.json'));
oldIndex=readjson(fullfile(baseline,'run_index.json'));
assert(strcmp(numerical_sha256(fullfile(dataRoot,'run_index.json'),'file'), ...
    numerical_sha256(fullfile(baseline,'run_index.json'),'file')), ...
    'tolerance:ChangedRunIndex','Run index differs from the captured baseline.');
assert(numel(oldIndex.entries)==35 && numel(oldManifest.entries)==5);
protected=snapshot(dataRoot,baseline,here);
experiments=cfg.revision.experiments; assert(numel(experiments)==35);
mapping=sourceMapping(baseline,oldManifest,experiments);
assert(numel(unique(mapping))==35);
seedEntry=oldManifest.entries(1);
oldRecord=readassessment(dataRoot,seedEntry.run_id,seedEntry.assessment_fingerprint);
oldSettings=oldRecord.assessment_settings;
expected=oldSettings; expected.state_tolerance=1e-5;
expected.capacity_tolerance=1e-5; expected.capacity_control_tolerance=3e-3;
assert(isequaln(cfg.check,expected),'tolerance:UnexpectedSettings', ...
    'Only state/capacity=1e-5 and capacity_control=3e-3 may change.');
assert(oldSettings.state_tolerance==1e-6 && oldSettings.capacity_tolerance==1e-6 ...
    && oldSettings.capacity_control_tolerance==2e-3 && cfg.check.relative_cost_tolerance==1e-4);
oldCfg=cfg; oldCfg.check=oldSettings;
oldSpec=numerical_assessment_spec(oldCfg); spec=numerical_assessment_spec(cfg);
solveSource=numerical_code_hash('solve');
runs=cell(1,35); oldRuns=cell(1,35); oldPaths=cell(1,35);
report=struct('schema_version',1,'revision_id',revisionId,'status','started', ...
    'checked_utc',numerical_utc(),'optimizer_executions',0,'solver_calls',0, ...
    'assessment_calls',0,'reused_current_assessments',0,'original_settings',oldSettings, ...
    'current_settings',cfg.check,'source_run_count',35,'rows',[], ...
    'phase','loading_saved_records','protected_file_count',numel(protected));
try
    % 先验证全部原始来源及旧sidecar；验证完成前不写新评估。
    for ix=1:35
        e=experiments(ix); entryIndex=find(strcmp({oldIndex.entries.run_id},mapping{ix}));
        assert(isscalar(entryIndex)); entry=oldIndex.entries(entryIndex);
        path=fullfile(dataRoot,entry.raw_file);
        assert(strcmp(numerical_sha256(path,'file'),entry.raw_sha256));
        loaded=load(path,'run'); raw=loaded.run;
        assert(strcmp(raw.run_id,entry.run_id) && strcmp(raw.solve_fingerprint,entry.solve_fingerprint) ...
            && raw.success && strcmp(raw.source_status,'verified_record') ...
            && strcmp(raw.provenance.solve_code_hash,solveSource.hash));
        assert(strcmp(raw.case_id,e.case_id) && isequaln(raw.parameters,e.parameters) ...
            && isequaln(raw.x0(:),e.x0(:)) && isequaln(raw.solver_settings,e.solver_settings));
        names=fieldnames(e.initialization);
        for j=1:numel(names)
            name=names{j}; assert(isfield(raw.initialization,name) ...
                && isequaln(raw.initialization.(name),e.initialization.(name)));
        end
        fingerprint=assessmentFingerprint(raw,oldSpec);
        [record,oldPaths{ix}]=readassessment(dataRoot,raw.run_id,fingerprint);
        verifyassessment(record,raw,oldSpec,fingerprint);
        oldRuns{ix}=attachassessment(raw,record); runs{ix}=raw;
    end
    report.phase='reassessing_saved_records';
    for ix=1:35
        raw=runs{ix};
        [runs{ix},called]=assess_saved_numerical_run(raw,dataRoot, ...
            @(saved) numerical_assessment_view(saved,cfg),spec,false);
        report.assessment_calls=report.assessment_calls+double(called);
        report.reused_current_assessments=report.reused_current_assessments+double(~called);
        fingerprint=assessmentFingerprint(raw,spec);
        [record,newPath]=readassessment(dataRoot,raw.run_id,fingerprint);
        verifyassessment(record,raw,spec,fingerprint);
        assert(~strcmp(fingerprint,oldRuns{ix}.assessment_fingerprint));
        assert(isequaln(oldRuns{ix}.reference,runs{ix}.reference), ...
            'tolerance:ReferenceChanged','Changing acceptance tolerances changed the analytic reference.');
        assert(isequaln(oldRuns{ix}.assessment.reintegration,runs{ix}.assessment.reintegration), ...
            'tolerance:ReintegrationChanged','Changing acceptance tolerances changed reintegration.');
        assert(isequaln(oldRuns{ix}.assessment.cost_agreement,runs{ix}.assessment.cost_agreement));
        item=flagrow(experiments(ix),oldRuns{ix},runs{ix},oldPaths{ix},newPath);
        if isempty(report.rows), report.rows=item; else, report.rows(end+1)=item; end
        fprintf('TOLERANCE ASSESSMENT %s %d/35 numeric=%d agreement=%d status=%s\n', ...
            experiments(ix).configuration_id,ix,item.new_numeric_pass,item.new_agreement_pass,item.new_status);
        if mod(ix,5)==0
            report.completed_assessment_count=ix; report.updated_utc=numerical_utc();
            numerical_write_json(reportPath,report);
        end
    end
    report.original_counts=counts(oldRuns); report.current_counts=counts(runs);
    report.unresolved_discrepancies=report.rows(strcmp({report.rows.new_status},'unresolved_discrepancy'));
    coarse=[report.rows.N]==2000;
    report.remaining_N2000_failures=report.rows(coarse & ...
        (~[report.rows.new_numeric_pass] | ~[report.rows.new_agreement_pass]));
    assert(~isempty(report.remaining_N2000_failures));
    for id={'E2','E4'}
        ix=find(strcmp({report.rows.case_id},id{1}) & coarse); assert(isscalar(ix));
        assert(~report.rows(ix).new_numeric_pass && ...
            report.rows(ix).capacity_excess>cfg.check.capacity_tolerance);
    end
    ix=find(strcmp({report.rows.case_id},'E3') & coarse); assert(isscalar(ix));
    assert(strcmp(report.rows(ix).new_status,'unresolved_discrepancy') ...
        && ~report.rows(ix).new_agreement_pass,'tolerance:LostDiscrepancy', ...
        'E3 N=2000 must retain its unresolved cost discrepancy.');
    assertprotected(protected); report.phase='publishing_same_main_sources';
    main=cell(1,5);
    for k=1:5
        id=sprintf('E%d',k);
        ix=find(arrayfun(@(e) strcmp(e.case_id,id) && any(strcmp(e.groups,'main')),experiments));
        oldEntry=find(strcmp({oldManifest.entries.case_id},id)); assert(isscalar(ix) && isscalar(oldEntry));
        assert(strcmp(runs{ix}.run_id,oldManifest.entries(oldEntry).run_id)); main{k}=runs{ix};
    end
    newManifest=publish_numerical_selection(main,dataRoot, ...
        'Same five original run IDs and main_N; reassessed acceptance tolerances on 2026-10-10; no new optimization.');
    verifyselection(oldManifest,newManifest,dataRoot);
    report.phase='refreshing_current_summaries';
    writeMainSummary(main,cfg,revisionId);
    init=revision_group_summary(cfg,'initialization',experiments,runs);
    grid=revision_group_summary(cfg,'grid',experiments,runs);
    horizon=revision_group_summary(cfg,'horizon',experiments,runs);
    assert(numel(grid.rows)==15 && numel(grid.case_comparisons)==5 ...
        && grid.consistency_pass && all([grid.case_comparisons.event_comparison_evaluated]) ...
        && all([grid.case_comparisons.cost_comparison_evaluated]) ...
        && all([grid.case_comparisons.event_comparison_pass]) ...
        && all([grid.case_comparisons.cost_comparison_pass]), ...
        'tolerance:GridComparison','All five finest-pair comparisons must execute and pass.');
    threshold=revision_threshold_saved(cfg,main);
    report.group_status=struct('initialization',init.consistency_pass,'grid',grid.consistency_pass, ...
        'horizon',horizon.consistency_pass,'threshold',threshold.consistency_pass);
    assert(init.consistency_pass && horizon.consistency_pass && threshold.consistency_pass);
    report.phase='exporting_saved_results'; exported=export_numerical_latex(cfg);
    assert(exported.optimizer_executions==0 && exported.verified);
    assertprotected(protected);
    assert(numel(dir(fullfile(dataRoot,'runs','*.mat')))==35 ...
        && numel(dir(fullfile(dataRoot,'runs','*.solver.json')))==35);
    currentSolveSource=numerical_code_hash('solve');
    currentAssessmentSource=numerical_code_hash('assessment');
    assert(strcmp(solveSource.hash,currentSolveSource.hash));
    assert(strcmp(spec.code_hash,currentAssessmentSource.hash));
    assert(report.optimizer_executions==0 && report.solver_calls==0);
    assert(report.assessment_calls+report.reused_current_assessments==35);
    report.main_verified=exported.verified; report.protected_hashes_unchanged=true;
    report.protected_files=protected; report.status='completed'; report.phase='completed';
    report.finished_utc=numerical_utc(); numerical_write_json(reportPath,report);
    writetable(struct2table(report.rows),fullfile(here,'assessment_flag_comparison.csv'));
    fprintf('TOLERANCE_ASSESSMENT_REFRESH_OK optimizer=0 raw=35 assessment_calls=%d grid_pairs=5\n', ...
        report.assessment_calls);
catch exception
    report.status='failed'; report.failure=struct('identifier',exception.identifier,'message',exception.message);
    report.finished_utc=numerical_utc(); numerical_write_json(reportPath,report); rethrow(exception);
end
end

function mapping=sourceMapping(baseline,manifest,experiments)
mapping=cell(1,numel(experiments));
main=readjson(fullfile(baseline,'revision_checks','main_summary.json'));
for k=1:numel(main.rows)
    row=main.rows(k); ix=find(arrayfun(@(e) strcmp(e.case_id,row.case_id) ...
        && any(strcmp(e.groups,'main')),experiments)); assert(isscalar(ix));
    selected=find(strcmp({manifest.entries.case_id},row.case_id)); assert(isscalar(selected));
    assert(strcmp(row.run_id,manifest.entries(selected).run_id)); mapping{ix}=row.run_id;
end
for group={'initialization','grid','horizon'}
    summary=readjson(fullfile(baseline,'revision_checks',[group{1} '_summary.json']));
    assert(summary.schema_version==1 && strcmp(summary.group,group{1}) && summary.protocol_complete);
    for k=1:numel(summary.rows)
        row=summary.rows(k); ix=find(strcmp({experiments.configuration_id},row.configuration_id));
        assert(isscalar(ix)); e=experiments(ix);
        assert(strcmp(row.case_id,e.case_id) && row.T==e.solver_settings.T && row.N==e.solver_settings.N ...
            && strcmp(row.initialization,e.initialization.type) && ~isempty(row.run_id));
        if ~isempty(mapping{ix}), assert(strcmp(mapping{ix},row.run_id)); end
        mapping{ix}=row.run_id;
    end
end
assert(all(~cellfun(@isempty,mapping)));
end

function value=readjson(path)
assert(isfile(path),'tolerance:MissingBaseline','Missing captured baseline: %s.',path);
value=jsondecode(fileread(path));
end

function fingerprint=assessmentFingerprint(raw,spec)
fingerprint=numerical_sha256(struct('solve_fingerprint',raw.solve_fingerprint, ...
    'raw_output_hash',numerical_sha256(raw),'assessment',spec));
end

function [record,path]=readassessment(dataRoot,id,fingerprint)
files=dir(fullfile(dataRoot,'revision_checks','assessments',[id '_' fingerprint '_*.mat']));
assert(~isempty(files),'tolerance:MissingSavedAssessment','No saved assessment for %s.',id);
[~,ix]=max([files.datenum]); path=fullfile(files(ix).folder,files(ix).name);
loaded=load(path,'assessment_record'); record=loaded.assessment_record;
end

function verifyassessment(record,raw,spec,fingerprint)
assert(strcmp(record.run_id,raw.run_id) && strcmp(record.solve_fingerprint,raw.solve_fingerprint) ...
    && strcmp(record.assessment_fingerprint,fingerprint) ...
    && strcmp(record.assessment_provenance.code_hash,spec.code_hash) ...
    && isequaln(record.assessment_settings,spec.settings));
end

function view=attachassessment(raw,record)
view=raw; names={'reference','assessment','assessment_provenance','assessment_fingerprint','assessment_settings'};
for k=1:numel(names), view.(names{k})=record.(names{k}); end
end

function row=flagrow(e,old,new,oldPath,newPath)
row=struct('configuration_id',e.configuration_id,'case_id',e.case_id,'run_id',new.run_id, ...
    'solve_fingerprint',new.solve_fingerprint,'T',e.solver_settings.T,'N',e.solver_settings.N, ...
    'initialization',e.initialization.type,'old_numeric_pass',old.assessment.numeric_pass, ...
    'new_numeric_pass',new.assessment.numeric_pass,'old_agreement_pass',old.assessment.agreement_pass, ...
    'new_agreement_pass',new.assessment.agreement_pass,'old_status',old.assessment.status, ...
    'new_status',new.assessment.status,'J_openocl',new.J_openocl, ...
    'signed_cost_difference',new.assessment.signed_cost_difference, ...
    'relative_cost_difference',new.assessment.relative_cost_difference, ...
    'cost_agreement_pass',new.assessment.cost_agreement.passed, ...
    'capacity_excess',new.assessment.capacity_excess,'state_discrepancy',new.assessment.state_discrepancy, ...
    'old_numeric_failures',strjoin(failedchecks(old.assessment.numeric_checks),'; '), ...
    'new_numeric_failures',strjoin(failedchecks(new.assessment.numeric_checks),'; '), ...
    'old_assessment_fingerprint',old.assessment_fingerprint, ...
    'new_assessment_fingerprint',new.assessment_fingerprint,'old_assessment_file',oldPath,'new_assessment_file',newPath);
end

function names=failedchecks(checks)
names=fieldnames(checks); names=names(~structfun(@(v) logical(v),checks));
end

function out=counts(runs)
numeric=cellfun(@(r) r.assessment.numeric_pass,runs);
agreement=cellfun(@(r) r.assessment.agreement_pass,runs);
out=struct('records',numel(runs),'numeric_pass',sum(numeric),'agreement_pass',sum(agreement), ...
    'both_pass',sum(numeric & agreement));
end

function files=snapshot(dataRoot,baseline,here)
listing=[dir(fullfile(dataRoot,'runs','*.mat')); dir(fullfile(dataRoot,'runs','*.solver.json')); ...
    dir(fullfile(dataRoot,'revision_checks','assessments','*.mat')); dir(fullfile(baseline,'**','*'))];
listing=listing(~[listing.isdir]); paths=arrayfun(@(f) fullfile(f.folder,f.name),listing,'UniformOutput',false);
paths{end+1}=fullfile(dataRoot,'run_index.json');
for name={'baseline_numerical_cases_config.m','baseline_main.tex','baseline.json'}
    path=fullfile(here,name{1}); if isfile(path), paths{end+1}=path; end
end
paths=sort(unique(paths)); files=repmat(struct('path','','sha256',''),numel(paths),1);
for k=1:numel(paths), files(k)=struct('path',paths{k},'sha256',numerical_sha256(paths{k},'file')); end
end

function assertprotected(files)
for k=1:numel(files)
    assert(isfile(files(k).path) && strcmp(numerical_sha256(files(k).path,'file'),files(k).sha256), ...
        'tolerance:ProtectedFileChanged','Protected file changed: %s.',files(k).path);
end
end

function verifyselection(old,new,dataRoot)
for k=1:5
    before=old.entries(k); ix=find(strcmp({new.entries.case_id},before.case_id)); assert(isscalar(ix));
    after=new.entries(ix); names={'run_id','solve_fingerprint','raw_file','raw_sha256'};
    for j=1:numel(names), assert(strcmp(before.(names{j}),after.(names{j}))); end
    assert(~strcmp(before.assessment_fingerprint,after.assessment_fingerprint));
    archived=fullfile(dataRoot,'legacy_results',[before.case_id '_' before.compatibility_sha256 '.mat']);
    assert(isfile(archived) && strcmp(numerical_sha256(archived,'file'),before.compatibility_sha256));
end
load_selected_numerical_runs(dataRoot);
end

function writeMainSummary(runs,cfg,revisionId)
summary=struct('schema_version',1,'batch_id','','assessment_revision_id',revisionId, ...
    'source_kind','saved_raw_reassessment','optimizer_executions',0,'rows',[], ...
    'numeric_pass',false,'agreement_pass',false,'predeclared_parameters',cfg.parameters, ...
    'assessment_settings',cfg.check);
for k=1:5
    r=runs{k}; row=struct('case_id',r.case_id,'run_id',r.run_id,'solve_fingerprint',r.solve_fingerprint, ...
        'success',r.success,'return_status',r.return_status,'numeric_pass',r.assessment.numeric_pass, ...
        'agreement_pass',r.assessment.agreement_pass,'J_openocl',r.J_openocl, ...
        'J_reference',r.reference.J_reference,'observed_structure',r.assessment.observed_structure, ...
        'assessment',r.assessment,'reference_events',r.reference.events);
    if isempty(summary.rows), summary.rows=row; else, summary.rows(end+1)=row; end
end
summary.numeric_pass=all([summary.rows.numeric_pass]); summary.agreement_pass=all([summary.rows.agreement_pass]);
folder=fullfile(cfg.paths.data,'revision_checks');
numerical_write_json(fullfile(folder,'main_summary.json'),summary);
writetable(struct2table(rmfield(summary.rows,{'assessment','reference_events'})),fullfile(folder,'main_summary.csv'));
end
