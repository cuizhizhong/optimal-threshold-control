function report = revision_validation_dispatch(cfg,mode,force,hooks)
% 正式调度和无优化器mock共用此实现；hooks仅供隔离单元测试注入。
if nargin<4, hooks=struct(); end
mode=char(mode);
assert(ismember(mode,cfg.revision.allowed_modes),'revision:InvalidMode','Unknown revision mode: %s.',mode);
assert(isscalar(force) && (islogical(force) || ismember(force,[0 1])), ...
    'revision:InvalidForce','force must be a scalar logical.');
force=logical(force); hooks=defaults(hooks);
folder=fullfile(cfg.paths.data,'revision_checks'); if ~isfolder(folder), mkdir(folder); end
batchId=['batch_' strrep(char(java.util.UUID.randomUUID()),'-','')];
manifestFile=fullfile(folder,[batchId '_manifest.json']);
reportFile=fullfile(folder,[batchId '_report.json']);
experiments=cfg.revision.experiments;
selected=selection(experiments,mode);
if strcmp(mode,'extended'), experiments=cfg.revision.extended_experiments; selected=1:numel(experiments); end
source=numerical_code_hash('solve');
manifest=struct('schema_version',1,'batch_id',batchId,'created_utc',numerical_utc(), ...
    'mode',mode,'force',force,'status','frozen','protocol_version',cfg.revision.protocol_version, ...
    'protocol_hash',cfg.revision.protocol_hash,'solve_code_hash',source.hash, ...
    'solve_source_files',source.files,'default_unique_count',numel(cfg.revision.experiments), ...
    'default_experiments',cfg.revision.experiments,'selected_configuration_ids',{{}}, ...
    'configuration_count',numel(selected),'threshold_control',cfg.revision.threshold_control, ...
    'threshold_capacity',cfg.revision.threshold_capacity,'expected_fields_usage','comparison_only');
if ~isempty(selected), manifest.selected_configuration_ids={experiments(selected).configuration_id}; end
% 所有默认配置和本次选择先落盘；prepare、preflight和solver都在此语句之后。
numerical_write_json(manifestFile,manifest);
report=struct('schema_version',1,'batch_id',batchId,'mode',mode,'force',force, ...
    'status','implemented','started_utc',numerical_utc(),'finished_utc','', ...
    'manifest_file',manifestFile,'report_file',reportFile,'protocol_hash',cfg.revision.protocol_hash, ...
    'solve_code_hash',source.hash,'default_unique_count',35,'requested_unique_count',numel(selected), ...
    'attempted_count',0,'solver_calls',0,'cache_hits',0,'assessment_calls',0, ...
    'successful_count',0,'failed_count',0,'duplicate_reference_count',0, ...
    'numeric_pass_count',0,'agreement_pass_count',0,'selection_published',false, ...
    'protocol_complete',false,'consistency_pass',false,'rows',emptyrows(),'blockers',{{}});
runs=cell(1,numel(experiments)); seenFingerprints={}; seenIndices=[];
saveReport();
try
    if ismember(mode,{'unit','all'})
        report.unit=hooks.unit();
        assert(isfield(report.unit,'passed') && report.unit.passed, ...
            'revision:UnitFailed','Revision unit suite did not pass; no optimization started.');
        if strcmp(mode,'unit')
            report.status='tested'; report.protocol_complete=true; report.consistency_pass=true;
            finish(); return;
        end
    end
    if strcmp(mode,'threshold')
        report.threshold=hooks.threshold(cfg,{});
        report.status=report.threshold.status;
        report.protocol_complete=strcmp(report.threshold.status,'completed');
        report.consistency_pass=isfield(report.threshold,'consistency_pass') && report.threshold.consistency_pass;
        finish(); return;
    end
    if isempty(selected)
        report.status='not_started';
        report.blockers={'extended requires explicitly declared additional configurations and reasons; no automatic escalation'};
        finish(); return;
    end
    report.preflight=hooks.preflight(cfg);
    if ~report.preflight.passed
        report.status='blocked'; report.blockers=report.preflight.blockers; finish(); return;
    end
    oldSetup=getenv('OCL_CASADI_SETUP');
    setupCleanup=onCleanup(@() setenv('OCL_CASADI_SETUP',oldSetup)); %#ok<NASGU>
    hooks.setup(cfg);
    provenance=hooks.provenance(cfg);
    assert(strcmp(provenance.solve_code_hash,source.hash),'revision:SolveSourceChanged', ...
        'Solve source changed after manifest freeze.');
    manifest.environment_fingerprint=provenance.environment_fingerprint;
    manifest.solve_provenance=provenance; manifest.status='running';
    numerical_write_json(manifestFile,manifest);
    for position=1:numel(selected)
        ix=selected(position); experiment=experiments(ix);
        current=numerical_code_hash('solve');
        assert(strcmp(current.hash,source.hash),'revision:SolveSourceChanged','Solve source changed during the batch.');
        prepared=hooks.prepare(experiment,cfg);
        current=numerical_code_hash('solve');
        assert(strcmp(current.hash,source.hash),'revision:SolveSourceChanged', ...
            'Solve source changed while constructing the actual request.');
        request=prepared;
        if isfield(request,'problem'), request=rmfield(request,'problem'); end
        if isfield(request,'ig'), request=rmfield(request,'ig'); end
        request.case_id=experiment.case_id;
        fingerprint=solveFingerprint(request,provenance);
        request.expected_solve_fingerprint=fingerprint;
        planRecord=struct('configuration_id',experiment.configuration_id,'case_id',experiment.case_id, ...
            'groups',{experiment.groups},'solve_fingerprint',fingerprint, ...
            'actual_solver_settings',request.actual_solver_settings,'actual_grid',request.actual_grid, ...
            'initialization',request.initialization,'initial_guess',request.initial_guess);
        numerical_write_json(fullfile(folder,[batchId '_' experiment.configuration_id '_request.json']),planRecord);
        previous=find(strcmp(seenFingerprints,fingerprint),1);
        if ~isempty(previous)
            original=seenIndices(previous); run=runs{original};
            activity=struct('cache_hit',false,'solver_called',false,'assessment_called',false);
            report.duplicate_reference_count=report.duplicate_reference_count+1;
            rowStatus='duplicate_reference';
        else
            seenFingerprints{end+1}=fingerprint; seenIndices(end+1)=ix; %#ok<AGROW>
            fprintf('REVISION START %s %s T=%g N=%d initialization=%s\n', ...
                experiment.configuration_id,experiment.case_id,experiment.solver_settings.T, ...
                experiment.solver_settings.N,experiment.initialization.type);
            [run,activity]=hooks.execute(request,provenance,prepared,cfg,force);
            report.attempted_count=report.attempted_count+1;
            report.solver_calls=report.solver_calls+double(activity.solver_called);
            report.cache_hits=report.cache_hits+double(activity.cache_hit);
            report.assessment_calls=report.assessment_calls+double(activity.assessment_called);
            rowStatus='completed'; if ~run.success, rowStatus='failed'; end
        end
        runs{ix}=run;
        report.rows(end+1)=row(experiment,run,activity,rowStatus);
        if run.success, report.successful_count=report.successful_count+1;
        else, report.failed_count=report.failed_count+1; end
        report.numeric_pass_count=report.numeric_pass_count+double(report.rows(end).numeric_pass);
        report.agreement_pass_count=report.agreement_pass_count+double(report.rows(end).agreement_pass);
        saveReport();
        % 原始记录已由execute保存；接口、源码、基础依赖错误现在立即停。
        failOnCodeError(run);
        clear prepared request;
        if ismember(mode,{'main','all'}) && allMainVisited(experiments,runs)
            if ~isfield(report,'main_publication_checked')
                report.main_publication_checked=true;
                mainRuns=orderedMain(experiments,runs);
                report.main_summary=writeMain(mainRuns,cfg,folder,batchId);
                if all(cellfun(@(r) ~isempty(r) && r.success,mainRuns))
                    report.selection=hooks.publish(mainRuns,cfg); report.selection_published=true;
                else
                    report.selection_published=false;
                    report.selection_reason='本批主算例存在失败；不发布新的selection。';
                end
                saveReport();
            end
        end
    end
    if ismember(mode,{'initialization','grid','horizon','all'})
        summaryGroups={mode}; if strcmp(mode,'all'), summaryGroups={'initialization','grid','horizon'}; end
        for j=1:numel(summaryGroups)
            report.(summaryGroups{j})=hooks.summary(cfg,summaryGroups{j},experiments,runs);
        end
    end
    if strcmp(mode,'all')
        if report.selection_published
            hooks.verify_selection(cfg);
            report.threshold=hooks.threshold(cfg,orderedMain(experiments,runs));
        else
            report.threshold=struct('status','blocked','consistency_pass',false, ...
                'reason','Current batch main selection was not published; old selection cannot substitute.');
        end
    end
    report.protocol_complete=true;
    report.consistency_pass=report.failed_count==0 && ...
        report.numeric_pass_count==numel(selected) && report.agreement_pass_count==numel(selected);
    if ismember(mode,{'initialization','grid','horizon','all'})
        for j=1:numel(summaryGroups)
            report.protocol_complete=report.protocol_complete && report.(summaryGroups{j}).protocol_complete;
            report.consistency_pass=report.consistency_pass && report.(summaryGroups{j}).consistency_pass;
        end
    end
    if strcmp(mode,'all')
        report.protocol_complete=report.protocol_complete && strcmp(report.threshold.status,'completed');
        report.consistency_pass=report.consistency_pass && report.threshold.consistency_pass;
    end
    report.status='completed'; if ~report.consistency_pass, report.status='failed'; end
    finish();
catch exception
    report.status='failed';
    if dependencyError(exception.identifier), report.status='blocked'; end
    report.failure=struct('identifier',exception.identifier,'message',exception.message, ...
        'stack',exception.stack,'report',getReport(exception,'extended','hyperlinks','off'));
    finish(); rethrow(exception);
end

    function saveReport()
        numerical_write_json(reportFile,report);
        numerical_write_json(fullfile(folder,['latest_' mode '_report.json']),report);
    end
    function finish()
        report.finished_utc=numerical_utc(); saveReport();
    end
end

function out=defaults(out)
fallback=struct('unit',@() verify_revision_validation_unit(), ...
    'preflight',@(cfg) revision_preflight(cfg.paths.openocl_root),'setup',@setup, ...
    'provenance',@(cfg) numerical_solve_provenance(cfg),'prepare',@prepare, ...
    'execute',@execute,'publish',@(runs,cfg) publish_numerical_selection(runs,cfg.paths.data, ...
        'Predeclared main_N and analytic_reference; no result-dependent selection.'), ...
    'threshold',@(cfg,runs) revision_threshold_saved(cfg,runs), ...
    'summary',@(cfg,group,experiments,runs) revision_group_summary(cfg,group,experiments,runs), ...
    'verify_selection',@(cfg) load_selected_numerical_runs(cfg.paths.data));
names=fieldnames(fallback);
for k=1:numel(names), if ~isfield(out,names{k}), out.(names{k})=fallback.(names{k}); end, end
end
function setup(cfg)
addpath(cfg.paths.openocl_root,fullfile(cfg.paths.openocl_root,'Lib','casadi'));
% preflight已验证本地依赖；不调用ocl.m的自动下载/安装入口。
setenv('OCL_CASADI_SETUP','true');
end
function prepared=prepare(experiment,cfg)
prepared=prepare_openocl_case(cfg.parameters,experiment.x0,experiment.solver_settings,experiment.initialization);
end
function [run,activity]=execute(request,provenance,prepared,cfg,force)
solver=@(~) solve_openocl_case(request.parameters,request.x0,request.solver_settings,request.initialization,prepared);
indexPath=fullfile(cfg.paths.data,'run_index.json'); before={};
if isfile(indexPath)
    old=jsondecode(fileread(indexPath)); if ~isempty(old.entries), before={old.entries.run_id}; end
end
try
    [run,activity]=execute_numerical_run(request,provenance,cfg.paths.data,solver, ...
        @(raw) numerical_assessment_view(raw,cfg),numerical_assessment_spec(cfg),force);
catch exception
    % execute可能已保存原始失败后rethrow，或在成功原始记录的评估阶段报错。
    % 从真实索引核对本次新增记录，不能把已执行的失败统计为零次。
    [run,activity]=reconcileSavedFailure(indexPath,before,request,cfg,exception,force);
    if isempty(run), rethrow(exception); end
end
assert(strcmp(run.solve_fingerprint,request.expected_solve_fingerprint), ...
    'revision:FingerprintMismatch','Saved run does not match the manifest request fingerprint.');
end
function [run,activity]=reconcileSavedFailure(indexPath,before,request,cfg,exception,force)
run=[]; activity=struct('cache_hit',false,'solver_called',false,'assessment_called',false);
if ~isfile(indexPath), return; end
index=jsondecode(fileread(indexPath)); if isempty(index.entries), return; end
matches=find(strcmp({index.entries.solve_fingerprint},request.expected_solve_fingerprint));
stackNames={exception.stack.name};
assessmentReached=any(strcmp(stackNames,'assess_saved_numerical_run'));
assessorCalled=any(strcmp(stackNames,'numerical_assessment_view')) || ...
    any(strcmp(stackNames,'assess_numerical_case'));
for k=fliplr(matches(:)')
    entry=index.entries(k); isNew=~ismember(entry.run_id,before);
    if ~isNew && ~entry.success, continue; end
    if ~isNew && (force || ~assessmentReached), continue; end
    filename=fullfile(cfg.paths.data,entry.raw_file);
    if ~isfile(filename) || ~strcmp(numerical_sha256(filename,'file'),entry.raw_sha256), continue; end
    loaded=load(filename,'run'); candidate=loaded.run;
    if ~strcmp(candidate.run_id,entry.run_id) || ~strcmp(candidate.solve_fingerprint,request.expected_solve_fingerprint), continue; end
    run=candidate; run.scheduler_failure=struct('identifier',exception.identifier, ...
        'message',exception.message,'stack',exception.stack, ...
        'report',getReport(exception,'extended','hyperlinks','off'));
    activity.solver_called=isNew; activity.cache_hit=~isNew;
    activity.assessment_called=assessorCalled; return;
end
end
function ix=selection(experiments,mode)
ix=[];
for k=1:numel(experiments)
    groups=experiments(k).groups;
    yes=strcmp(mode,'all') || any(strcmp(groups,mode));
    if strcmp(mode,'initialization'), yes=any(ismember(groups,{'initialization-constant','initialization-random'})); end
    if ismember(mode,{'unit','threshold','extended'}), yes=false; end
    if yes, ix(end+1)=k; end %#ok<AGROW>
end
end
function hash=solveFingerprint(request,provenance)
payload=struct('case_id',request.case_id,'parameters',request.parameters,'x0',request.x0(:), ...
    'solver_settings',request.solver_settings,'actual_solver_settings',request.actual_solver_settings, ...
    'actual_grid',request.actual_grid,'initialization',request.initialization, ...
    'initial_guess',request.initial_guess,'solve_code_hash',provenance.solve_code_hash, ...
    'environment_fingerprint',provenance.environment_fingerprint);
hash=numerical_sha256(payload);
end
function rows=emptyrows()
rows=struct('configuration_id',{},'case_id',{},'groups',{},'run_id',{},'solve_fingerprint',{}, ...
    'status',{},'success',{},'return_status',{},'cache_hit',{},'solver_called',{}, ...
    'numeric_pass',{},'agreement_pass',{},'J_openocl',{},'observed_structure',{},'assessment_status',{});
end
function out=row(experiment,run,activity,status)
out=struct('configuration_id',experiment.configuration_id,'case_id',experiment.case_id,'groups',{experiment.groups}, ...
    'run_id',run.run_id,'solve_fingerprint',run.solve_fingerprint,'status',status, ...
    'success',logical(run.success),'return_status',run.return_status, ...
    'cache_hit',logical(activity.cache_hit),'solver_called',logical(activity.solver_called), ...
    'numeric_pass',false,'agreement_pass',false,'J_openocl',NaN,'observed_structure','','assessment_status','not_available');
if isfield(run,'J_openocl'), out.J_openocl=run.J_openocl; end
if isfield(run,'assessment')
    fields={'numeric_pass','agreement_pass','observed_structure'};
    for k=1:numel(fields), if isfield(run.assessment,fields{k}), out.(fields{k})=run.assessment.(fields{k}); end, end
    if isfield(run.assessment,'status'), out.assessment_status=run.assessment.status; end
end
end
function yes=allMainVisited(experiments,runs)
ix=find(arrayfun(@(e) any(strcmp(e.groups,'main')),experiments));
yes=numel(ix)==5 && all(~cellfun(@isempty,runs(ix)));
end
function selected=orderedMain(experiments,runs)
selected=cell(1,5);
for k=1:5
    ix=find(arrayfun(@(e) strcmp(e.case_id,sprintf('E%d',k)) && any(strcmp(e.groups,'main')),experiments));
    assert(isscalar(ix),'revision:InvalidMainMatrix','Main matrix must contain E1--E5 exactly once.');
    selected{k}=runs{ix};
end
end
function summary=writeMain(runs,cfg,folder,batchId)
summary=struct('schema_version',1,'batch_id',batchId,'rows',[],'numeric_pass',false,'agreement_pass',false);
for k=1:5
    r=runs{k}; out=struct('case_id',sprintf('E%d',k),'run_id',r.run_id,'solve_fingerprint',r.solve_fingerprint, ...
        'success',logical(r.success),'return_status',r.return_status,'numeric_pass',false,'agreement_pass',false, ...
        'J_openocl',NaN,'J_reference',NaN,'observed_structure','','assessment',[],'reference_events',[]);
    if isfield(r,'J_openocl'), out.J_openocl=r.J_openocl; end
    if isfield(r,'assessment')
        out.assessment=r.assessment;
        if isfield(r.assessment,'numeric_pass'), out.numeric_pass=r.assessment.numeric_pass; end
        if isfield(r.assessment,'agreement_pass'), out.agreement_pass=r.assessment.agreement_pass; end
        if isfield(r.assessment,'observed_structure'), out.observed_structure=r.assessment.observed_structure; end
    end
    if isfield(r,'reference')
        out.J_reference=r.reference.J_reference;
        if isfield(r.reference,'events'), out.reference_events=r.reference.events; end
    end
    if isempty(summary.rows), summary.rows=out; else, summary.rows(end+1)=out; end
end
summary.numeric_pass=all([summary.rows.numeric_pass]); summary.agreement_pass=all([summary.rows.agreement_pass]);
summary.predeclared_parameters=cfg.parameters;
numerical_write_json(fullfile(folder,[batchId '_main_summary.json']),summary);
numerical_write_json(fullfile(folder,'main_summary.json'),summary);
table=struct2table(rmfield(summary.rows,{'assessment','reference_events'}));
writetable(table,fullfile(folder,'main_summary.csv'));
end
function failOnCodeError(run)
if isfield(run,'scheduler_failure')
    failure=run.scheduler_failure;
    if dependencyError(failure.identifier)
        error('revision:DependencyFailure','Saved run %s raised [%s]: %s',run.run_id,failure.identifier,failure.message);
    end
    error('revision:ExecutionCodeFailure','Saved run %s raised [%s]: %s',run.run_id,failure.identifier,failure.message);
end
if isfield(run,'output_validation') && strcmp(run.output_validation.status,'failed')
    error('revision:InvalidSolverOutput','Saved raw run %s failed output validation: %s', ...
        run.run_id,run.output_validation.reason);
end
if isfield(run,'failure')
    identifier=run.failure.identifier;
    ordinary={'Maximum_Iterations_Exceeded','Restoration_Failed','Infeasible_Problem_Detected', ...
        'Search_Direction_Becomes_Too_Small','Diverging_Iterates','Maximum_CpuTime_Exceeded'};
    % 仅有真实正常IPOPT失败状态且没有代码/依赖标识的求解异常可继续。
    if isempty(identifier) && ismember(run.return_status,ordinary), return; end
    if dependencyError(identifier)
        error('revision:DependencyFailure','Saved raw run %s encountered a dependency error [%s]: %s', ...
            run.run_id,identifier,run.failure.message);
    end
    error('revision:ExecutionCodeFailure','Saved raw run %s contains an unexpected execution exception [%s]: %s', ...
        run.run_id,identifier,run.failure.message);
end
end
function yes=dependencyError(identifier)
yes=ismember(identifier,{'revision:DependencyFailure','revision:MissingOpenOCL','revision:MissingIPOPT', ...
    'revision:MissingInput','revision:NotWritable'}) || ...
    contains(identifier,'InvalidMEXFile') || contains(identifier,'MissingDependency');
end
