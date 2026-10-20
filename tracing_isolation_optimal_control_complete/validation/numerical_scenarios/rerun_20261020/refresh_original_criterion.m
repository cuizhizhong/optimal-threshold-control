function report = refresh_original_criterion()
% S2.6：只对本次35个新raw追加原判据评估；不求解、不再选择或刷新摘要。
here=fileparts(mfilename('fullpath'));
reportRoot=fileparts(fileparts(fileparts(here)));
addpath(fullfile(reportRoot,'matlab','numerical_scenarios'));
cfg=revision_validation_config(); dataRoot=cfg.paths.data;
folder=fullfile(here,'S2.6'); if ~isfolder(folder), mkdir(folder); end
reportPath=fullfile(folder,'assessment_revision_report.json');
originalCfg=cfg;
originalCfg.check.state_tolerance=1e-6;
originalCfg.check.capacity_tolerance=1e-6;
originalCfg.check.capacity_control_tolerance=2e-3;
currentSpec=numerical_assessment_spec(cfg);
originalSpec=numerical_assessment_spec(originalCfg);
solveSource=numerical_code_hash('solve');
report=struct('schema_version',1,'revision_id','code_rename_20261020_original_criterion', ...
    'status','started','phase','checking_sources','checked_utc',numerical_utc(), ...
    'optimizer_executions',0,'solver_calls',0,'assessment_calls',0, ...
    'reused_original_assessments',0,'source_run_count',0,'rows',[], ...
    'original_settings',originalCfg.check,'current_settings',cfg.check, ...
    'original_spec',originalSpec,'current_spec',currentSpec, ...
    'original_counts',emptycounts(),'current_counts',emptycounts(), ...
    'expected_original_both_pass',28,'expected_current_both_pass',30);
try
    assert(cfg.check.state_tolerance==1e-5 && cfg.check.capacity_tolerance==1e-5 ...
        && cfg.check.capacity_control_tolerance==3e-3, ...
        'rerun:UnexpectedCurrentCriterion','Current acceptance tolerances differ from the approved revision.');
    expected=originalCfg.check; expected.state_tolerance=1e-5;
    expected.capacity_tolerance=1e-5; expected.capacity_control_tolerance=3e-3;
    assert(isequaln(expected,cfg.check),'rerun:UnexpectedCriterionChange', ...
        'Only state, capacity and capacity-control acceptance tolerances may differ.');
    [~,projectName]=fileparts(reportRoot);
    baselineIndexPath=strrep(fullfile(projectName,'data','numerical_scenarios','run_index.json'),'\','/');
    oldIndex=jsondecode(gitread(cfg.paths.repo_root, ...
        sprintf('show "pre-code-rename:%s"',baselineIndexPath)));
    report.baseline_ref='pre-code-rename';
    report.baseline_commit=strtrim(gitread(cfg.paths.repo_root,'rev-parse pre-code-rename'));
    assert(isfield(oldIndex,'entries') && ~isempty(oldIndex.entries));
    oldIds={oldIndex.entries.run_id};
    index=readjson(fullfile(dataRoot,'run_index.json'));
    experiments=cfg.revision.experiments; assert(numel(experiments)==35);
    [mapping,sources,sourceRows]=sourceMapping(dataRoot,experiments);
    assert(numel(unique(mapping))==35 && ~any(ismember(mapping,oldIds)), ...
        'rerun:NotNewRunMatrix','The matrix must contain 35 distinct runs absent from pre-code-rename.');
    comparisonPath=fullfile(here,'comparison_report.json'); comparison=readjson(comparisonPath);
    assert(strcmp(comparison.status,'completed') && comparison.passed ...
        && comparison.compared_count==35 && comparison.passed_count==35, ...
        'rerun:S25NotPassed','The saved S2.5 comparison must pass all 35 records before S2.6.');
    for ix=1:35
        hit=find(strcmp({comparison.rows.configuration_id},experiments(ix).configuration_id));
        assert(isscalar(hit) && strcmp(comparison.rows(hit).new_run_id,mapping{ix}), ...
            'rerun:S25SourceMismatch','Current summary source differs from the passed S2.5 matrix.');
    end
    report.s25_comparison_file=comparisonPath;
    report.s25_comparison_sha256=numerical_sha256(comparisonPath,'file');
    report.source_run_count=numel(mapping);
    protected=snapshot(dataRoot);
    report.protected_file_count=numel(protected);
    raws=cell(1,35); currents=cell(1,35); originals=cell(1,35);
    currentPaths=cell(1,35); rawPaths=cell(1,35);
    % 先验证全部raw及当前sidecar；此循环不产生任何新评估文件。
    for ix=1:35
        e=experiments(ix); hit=find(strcmp({index.entries.run_id},mapping{ix}));
        assert(isscalar(hit),'rerun:MissingRunIndexEntry','Expected one entry for %s.',mapping{ix});
        entry=index.entries(hit); rawPaths{ix}=fullfile(dataRoot,entry.raw_file);
        assert(isfile(rawPaths{ix}) && strcmp(numerical_sha256(rawPaths{ix},'file'),entry.raw_sha256), ...
            'rerun:RawRecordModified','Raw hash differs for %s.',mapping{ix});
        loaded=load(rawPaths{ix},'run'); raw=loaded.run;
        assert(strcmp(raw.run_id,entry.run_id) && strcmp(raw.solve_fingerprint,entry.solve_fingerprint) ...
            && entry.success && strcmp(entry.source_status,'verified_record') ...
            && strcmp(entry.case_id,e.case_id) && strcmp(raw.source_status,'verified_record') && raw.success ...
            && strcmp(raw.provenance.solve_code_hash,solveSource.hash), ...
            'rerun:UntrustedNewRun','Untrusted current solve source for %s.',e.configuration_id);
        assert(isfield(raw.parameters,'beta') && ~isfield(raw.parameters,'p') ...
            && strcmp(raw.case_id,e.case_id) && isequaln(raw.parameters,e.parameters) ...
            && isequaln(raw.x0(:),e.x0(:)) && isequaln(raw.solver_settings,e.solver_settings), ...
            'rerun:ConfigurationMismatch','Raw request differs for %s.',e.configuration_id);
        names=fieldnames(e.initialization);
        for j=1:numel(names)
            name=names{j}; assert(isfield(raw.initialization,name) ...
                && isequaln(raw.initialization.(name),e.initialization.(name)));
        end
        consistency=numerical_run_consistency(raw,cfg.parameters,cfg.check.grid_time_tolerance);
        assert(consistency.provenance_pass && consistency.problem_pass, ...
            'rerun:InvalidProvenance','Raw/payload provenance differs for %s.',e.configuration_id);
        fingerprint=assessmentFingerprint(raw,currentSpec);
        [record,currentPaths{ix}]=readassessment(dataRoot,raw.run_id,fingerprint);
        verifyassessment(record,raw,currentSpec,fingerprint);
        for j=1:numel(sourceRows{ix})
            row=sourceRows{ix}{j};
            assert(strcmp(row.solve_fingerprint,raw.solve_fingerprint) ...
                && isequaln(row.success,raw.success) && isequaln(row.J_openocl,raw.J_openocl) ...
                && isequaln(row.numeric_pass,record.assessment.numeric_pass) ...
                && isequaln(row.agreement_pass,record.assessment.agreement_pass), ...
                'rerun:SummaryAssessmentMismatch', ...
                'Current summary differs from current sidecar for %s.',e.configuration_id);
        end
        currents{ix}=attachassessment(raw,record); raws{ix}=raw;
    end
    report.phase='appending_original_criterion_assessments';
    for ix=1:35
        raw=raws{ix};
        [originals{ix},called]=assess_saved_numerical_run(raw,dataRoot, ...
            @(saved) numerical_assessment_view(saved,originalCfg),originalSpec,false);
        report.assessment_calls=report.assessment_calls+double(called);
        report.reused_original_assessments=report.reused_original_assessments+double(~called);
        fingerprint=assessmentFingerprint(raw,originalSpec);
        [record,originalPath]=readassessment(dataRoot,raw.run_id,fingerprint);
        verifyassessment(record,raw,originalSpec,fingerprint);
        original=originals{ix}; current=currents{ix};
        assert(~strcmp(original.assessment_fingerprint,current.assessment_fingerprint));
        sameReference=isequaln(original.reference,current.reference);
        sameReintegration=isequaln(original.assessment.reintegration,current.assessment.reintegration);
        sameCost=isequaln(original.assessment.cost_agreement,current.assessment.cost_agreement);
        item=flagrow(experiments(ix),original,current,rawPaths{ix},sources{ix}, ...
            originalPath,currentPaths{ix},sameReference,sameReintegration,sameCost,called);
        if isempty(report.rows), report.rows=item; else, report.rows(end+1)=item; end
        report.completed_assessment_count=ix;
        assert(sameReference,'rerun:ReferenceChanged', ...
            'Changing acceptance tolerances changed reference for %s.',item.configuration_id);
        assert(sameReintegration,'rerun:ReintegrationChanged', ...
            'Changing acceptance tolerances changed reintegration for %s.',item.configuration_id);
        assert(sameCost,'rerun:CostCalculationChanged', ...
            'Changing acceptance tolerances changed cost comparison for %s.',item.configuration_id);
        fprintf('ORIGINAL_CRITERION %s %d/35 original=%d/%d current=%d/%d\n', ...
            item.configuration_id,ix,item.original_numeric_pass,item.original_agreement_pass, ...
            item.current_numeric_pass,item.current_agreement_pass);
        if mod(ix,5)==0
            report.updated_utc=numerical_utc(); numerical_write_json(reportPath,report);
        end
    end
    report.original_counts=counts(originals); report.current_counts=counts(currents);
    report.reference_unchanged=all([report.rows.reference_unchanged]);
    report.reintegration_unchanged=all([report.rows.reintegration_unchanged]);
    report.cost_calculation_unchanged=all([report.rows.cost_calculation_unchanged]);
    assertprotected(protected);
    report.protected_hashes_unchanged=true; report.protected_files=protected;
    nowSolve=numerical_code_hash('solve'); nowAssessment=numerical_assessment_spec(cfg);
    assert(isequaln(solveSource,nowSolve) && isequaln(currentSpec,nowAssessment), ...
        'rerun:SourceChangedDuringAssessment','Solve or assessment source changed during S2.6.');
    assert(report.assessment_calls+report.reused_original_assessments==35);
    assert(report.original_counts.records==35 && report.current_counts.records==35 ...
        && report.original_counts.both_pass==28 && report.current_counts.both_pass==30, ...
        'rerun:OriginalCriterionCountChanged', ...
        'Expected original/current both-pass counts 28/30, observed %d/%d; retain records and stop.', ...
        report.original_counts.both_pass,report.current_counts.both_pass);
    report.status='completed'; report.phase='completed'; report.finished_utc=numerical_utc();
    numerical_write_json(reportPath,report);
    fprintf('ORIGINAL_CRITERION_REFRESH_OK source_runs=35 original_both=28 current_both=30 optimizer=0\n');
catch exception
    report.status='failed'; report.failure=struct('identifier',exception.identifier,'message',exception.message);
    if exist('protected','var')
        report.protected_files=protected;
        try
            assertprotected(protected); report.protected_hashes_unchanged=true;
        catch protectionException
            report.protected_hashes_unchanged=false;
            report.protection_failure=struct('identifier',protectionException.identifier, ...
                'message',protectionException.message);
        end
    end
    report.finished_utc=numerical_utc(); numerical_write_json(reportPath,report); rethrow(exception);
end
end

function [mapping,sources,sourceRows]=sourceMapping(dataRoot,experiments)
mapping=cell(1,numel(experiments)); sources=cell(1,numel(experiments));
sourceRows=cell(1,numel(experiments));
for group={'initialization','grid','horizon'}
    path=fullfile(dataRoot,'revision_checks',[group{1} '_summary.json']);
    summary=readjson(path);
    assert(summary.schema_version==1 && strcmp(summary.group,group{1}) && summary.protocol_complete, ...
        'rerun:IncompleteSummary','Summary is incomplete: %s.',path);
    expected=15; if strcmp(group{1},'initialization'), expected=10; end
    assert(numel(summary.rows)==expected && numel(unique({summary.rows.configuration_id}))==expected, ...
        'rerun:InvalidSummaryMatrix','Missing or duplicated configuration in %s.',path);
    for k=1:numel(summary.rows)
        row=summary.rows(k); ix=find(strcmp({experiments.configuration_id},row.configuration_id));
        assert(isscalar(ix),'rerun:UnexpectedConfiguration','Unexpected configuration %s.',row.configuration_id);
        e=experiments(ix);
        belongs=any(strcmp(e.groups,group{1}));
        if strcmp(group{1},'initialization')
            belongs=any(ismember(e.groups,{'initialization-constant','initialization-random'}));
        end
        assert(belongs && strcmp(row.case_id,e.case_id) && row.T==e.solver_settings.T ...
            && row.N==e.solver_settings.N && strcmp(row.initialization,e.initialization.type) ...
            && ~isempty(row.run_id),'rerun:SummaryConfigurationMismatch', ...
            'Summary request differs for %s.',e.configuration_id);
        if ~isempty(mapping{ix})
            assert(strcmp(mapping{ix},row.run_id),'rerun:ConflictingSummarySource', ...
                'Summaries disagree on source run for %s.',e.configuration_id);
        end
        mapping{ix}=row.run_id;
        if isempty(sources{ix})
            sources{ix}={path}; sourceRows{ix}={row};
        else
            sources{ix}{end+1}=path; sourceRows{ix}{end+1}=row;
        end
    end
end
assert(all(~cellfun(@isempty,mapping)),'rerun:IncompleteRunMatrix','The three summaries do not cover C01-C35.');
end

function value=readjson(path)
assert(isfile(path),'rerun:MissingSource','Missing source: %s.',path);
value=jsondecode(fileread(path));
end

function text=gitread(repository,arguments)
[status,text]=system(sprintf('git -C "%s" %s',repository,arguments));
assert(status==0,'rerun:MissingBaselineTag','Cannot read pre-code-rename: %s.',text);
end

function fingerprint=assessmentFingerprint(raw,spec)
fingerprint=numerical_sha256(struct('solve_fingerprint',raw.solve_fingerprint, ...
    'raw_output_hash',numerical_sha256(raw),'assessment',spec));
end

function [record,path]=readassessment(dataRoot,id,fingerprint)
files=dir(fullfile(dataRoot,'revision_checks','assessments',[id '_' fingerprint '_*.mat']));
assert(~isempty(files),'rerun:MissingSavedAssessment','No saved assessment for %s.',id);
[~,ix]=max([files.datenum]); path=fullfile(files(ix).folder,files(ix).name);
loaded=load(path,'assessment_record'); record=loaded.assessment_record;
end

function verifyassessment(record,raw,spec,fingerprint)
assert(strcmp(record.run_id,raw.run_id) && strcmp(record.solve_fingerprint,raw.solve_fingerprint) ...
    && strcmp(record.assessment_fingerprint,fingerprint) ...
    && strcmp(record.assessment_provenance.assessment_fingerprint,fingerprint) ...
    && strcmp(record.assessment_provenance.code_hash,spec.code_hash) ...
    && strcmp(record.assessment_provenance.source_status,raw.source_status) ...
    && isequaln(record.assessment_settings,spec.settings) ...
    && isequaln(record.assessment_provenance.settings,spec.settings) ...
    && isequaln(record.assessment_provenance.source_files,spec.source_files), ...
    'rerun:InvalidSavedAssessment','Saved assessment source/settings differ for %s.',raw.run_id);
end

function view=attachassessment(raw,record)
view=raw; names={'reference','assessment','assessment_provenance','assessment_fingerprint','assessment_settings'};
for k=1:numel(names), view.(names{k})=record.(names{k}); end
end

function row=flagrow(e,original,current,rawPath,sources,originalPath,currentPath,sameRef,sameReintegration,sameCost,called)
row=struct('configuration_id',e.configuration_id,'configuration_fingerprint',e.configuration_fingerprint, ...
    'case_id',e.case_id,'run_id',current.run_id,'solve_fingerprint',current.solve_fingerprint, ...
    'solve_commit',current.provenance.solve_commit,'solve_code_hash',current.provenance.solve_code_hash, ...
    'source_status',current.source_status,'source_raw_file',rawPath,'source_summaries',{sources}, ...
    'T',e.solver_settings.T,'N',e.solver_settings.N,'initialization',e.initialization.type, ...
    'original_numeric_pass',original.assessment.numeric_pass, ...
    'original_agreement_pass',original.assessment.agreement_pass, ...
    'original_both_pass',original.assessment.numeric_pass && original.assessment.agreement_pass, ...
    'current_numeric_pass',current.assessment.numeric_pass, ...
    'current_agreement_pass',current.assessment.agreement_pass, ...
    'current_both_pass',current.assessment.numeric_pass && current.assessment.agreement_pass, ...
    'original_status',original.assessment.status,'current_status',current.assessment.status, ...
    'J_openocl',current.J_openocl,'J_reference',current.reference.J_reference, ...
    'capacity_excess',current.assessment.capacity_excess, ...
    'state_discrepancy',current.assessment.state_discrepancy, ...
    'original_numeric_failures',{failedchecks(original.assessment.numeric_checks)}, ...
    'current_numeric_failures',{failedchecks(current.assessment.numeric_checks)}, ...
    'original_assessment_fingerprint',original.assessment_fingerprint, ...
    'current_assessment_fingerprint',current.assessment_fingerprint, ...
    'original_assessment_file',originalPath,'current_assessment_file',currentPath, ...
    'original_assessment_called',logical(called),'reference_unchanged',sameRef, ...
    'reintegration_unchanged',sameReintegration,'cost_calculation_unchanged',sameCost);
end

function names=failedchecks(checks)
names=fieldnames(checks); names=names(~structfun(@(v) logical(v),checks));
end

function out=emptycounts()
out=struct('records',0,'numeric_pass',0,'agreement_pass',0,'both_pass',0);
end

function out=counts(runs)
numeric=cellfun(@(r) logical(r.assessment.numeric_pass),runs);
agreement=cellfun(@(r) logical(r.assessment.agreement_pass),runs);
out=struct('records',numel(runs),'numeric_pass',sum(numeric),'agreement_pass',sum(agreement), ...
    'both_pass',sum(numeric & agreement));
end

function files=snapshot(dataRoot)
listing=dir(fullfile(dataRoot,'**','*')); listing=listing(~[listing.isdir]);
paths=arrayfun(@(f) fullfile(f.folder,f.name),listing,'UniformOutput',false);
paths=sort(unique(paths)); files=repmat(struct('path','','sha256',''),numel(paths),1);
for k=1:numel(paths), files(k)=struct('path',paths{k},'sha256',numerical_sha256(paths{k},'file')); end
end

function assertprotected(files)
for k=1:numel(files)
    assert(isfile(files(k).path) && strcmp(numerical_sha256(files(k).path,'file'),files(k).sha256), ...
        'rerun:ProtectedFileChanged','Existing source was changed: %s.',files(k).path);
end
end
