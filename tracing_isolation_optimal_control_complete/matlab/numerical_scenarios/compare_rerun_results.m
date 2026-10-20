function report = compare_rerun_results(cfg)
% S2.5：只读比较标签基线与本次35条保存结果，不求解、不生成或刷新评估。
% 本文件不属于任何求解、评估、作图或导出指纹清单。
if nargin<1, cfg=revision_validation_config(); end
reportRoot=fullfile(cfg.paths.report_root,'validation','numerical_scenarios','rerun_20261020');
reportPath=fullfile(reportRoot,'comparison_report.json');
tag='pre-code-rename';
protected=struct('path',{},'sha256',{});
report=struct('schema_version',1,'stage','S2.5','baseline_tag',tag, ...
    'baseline_commit','','status','started','passed',false, ...
    'started_utc',numerical_utc(),'finished_utc','', ...
    'optimizer_executions',0,'solver_calls',0,'assessment_calls',0, ...
    'expected_configuration_count',35,'compared_count',0,'passed_count',0, ...
    'cost_relative_tolerance',1e-10,'array_max_abs_tolerance',1e-8, ...
    'exact_comparisons',{{'return_status','iteration_count','time_grids', ...
        'event_intervals_and_candidates','observed_stage_structure', ...
        'numeric_pass','agreement_pass','numeric_checks'}}, ...
    'assessment_policy','Read saved revised-criterion sidecars only; never reassess.', ...
    'rows',[],'protected_files_unchanged',false,'protected_files',[], ...
    'blockers',{{}});
try
    [ok,commit]=system(sprintf('git -C "%s" rev-parse "%s^{commit}"',cfg.paths.repo_root,tag));
    assert(ok==0,'rerun:MissingBaselineTag','Cannot resolve baseline tag %s: %s',tag,commit);
    report.baseline_commit=strtrim(commit);
    experiments=cfg.revision.experiments;
    assert(numel(experiments)==35 && numel(unique({experiments.configuration_id}))==35, ...
        'rerun:InvalidMatrix','Expected exactly 35 distinct configuration_id values.');
    oldIndex=tagJson(fullfile(cfg.paths.data,'run_index.json'));
    currentIndex=readJson(fullfile(cfg.paths.data,'run_index.json'));
    assert(oldIndex.schema_version==1 && numel(oldIndex.entries)==35 && currentIndex.schema_version==1, ...
        'rerun:InvalidRunIndex','Baseline must contain exactly 35 indexed raw records.');
    oldTolerance=tagJson(fullfile(cfg.paths.report_root,'validation','numerical_scenarios', ...
        'tolerance_revision_20261010','assessment_revision_report.json'));
    assert(strcmp(oldTolerance.status,'completed') && oldTolerance.source_run_count==35 ...
        && numel(oldTolerance.rows)==35 && isequaln(oldTolerance.current_settings,cfg.check), ...
        'rerun:InvalidBaselineAssessment','Baseline revised-criterion assessment settings do not match.');
    oldMapping=sourceMapping(true,experiments);
    newMapping=sourceMapping(false,experiments);
    assert(numel(unique(oldMapping))==35 && numel(unique(newMapping))==35 ...
        && isempty(intersect(oldMapping,newMapping)), ...
        'rerun:NotNewSolves','Expected 35 distinct new run IDs, all different from the baseline.');
    spec=numerical_assessment_spec(cfg);
    report.current_assessment_code_hash=spec.code_hash;
    report.current_assessment_settings=spec.settings;
    for ix=1:35
        e=experiments(ix); item=emptyRow(e,oldMapping{ix},newMapping{ix});
        try
            [old,oldEntry]=readRaw(oldIndex,item.old_run_id);
            [new,newEntry]=readRaw(currentIndex,item.new_run_id);
            item.old_raw_file=oldEntry.raw_file; item.new_raw_file=newEntry.raw_file;
            item.old_raw_sha256=oldEntry.raw_sha256; item.new_raw_sha256=newEntry.raw_sha256;
            assert(strcmp(old.case_id,e.case_id) && strcmp(new.case_id,e.case_id), ...
                'rerun:CaseMismatch','Raw case_id does not match %s.',e.configuration_id);
            assert(isequaln(currentParameters(old.parameters),e.parameters) ...
                && isequaln(new.parameters,e.parameters) ...
                && isequaln(old.x0(:),e.x0(:)) && isequaln(new.x0(:),e.x0(:)) ...
                && isequaln(old.solver_settings,e.solver_settings) ...
                && isequaln(new.solver_settings,e.solver_settings), ...
                'rerun:RequestMismatch','Parameters, initial state or settings differ for %s.',e.configuration_id);
            original=find(strcmp({oldTolerance.rows.configuration_id},e.configuration_id));
            assert(isscalar(original) && strcmp(oldTolerance.rows(original).run_id,old.run_id), ...
                'rerun:BaselineMappingMismatch','Historical tolerance report disagrees with the tagged summaries.');
            oldFingerprint=oldTolerance.rows(original).new_assessment_fingerprint;
            newFingerprint=numerical_sha256(struct('solve_fingerprint',new.solve_fingerprint, ...
                'raw_output_hash',numerical_sha256(new),'assessment',spec));
            [oa,oldPath]=readAssessment(old,oldFingerprint,oldTolerance.current_settings,'');
            [na,newPath]=readAssessment(new,newFingerprint,spec.settings,spec.code_hash);
            item.old_assessment_file=relativePath(oldPath); item.new_assessment_file=relativePath(newPath);
            item.old_assessment_fingerprint=oldFingerprint; item.new_assessment_fingerprint=newFingerprint;
            assert(isequaln(oa.assessment.numeric_pass,oldTolerance.rows(original).new_numeric_pass) ...
                && isequaln(oa.assessment.agreement_pass,oldTolerance.rows(original).new_agreement_pass), ...
                'rerun:HistoricalFlagsMismatch','Saved revised assessment does not match its tagged report.');
            item.old_return_status=old.return_status; item.new_return_status=new.return_status;
            item.old_iteration_count=iterationCount(old); item.new_iteration_count=iterationCount(new);
            item.old_J_openocl=old.J_openocl; item.new_J_openocl=new.J_openocl;
            assert(isfinite(old.J_openocl) && isscalar(old.J_openocl) ...
                && isfinite(new.J_openocl) && isscalar(new.J_openocl), ...
                'rerun:InvalidCost','Both saved objective values must be finite scalars.');
            item.cost_relative_difference=abs(new.J_openocl-old.J_openocl)/max(abs(old.J_openocl),1e-12);
            item.control_max_abs_difference=arrayDifference(old.q_control,new.q_control);
            item.s_state_max_abs_difference=arrayDifference(old.s_state,new.s_state);
            item.i_state_max_abs_difference=arrayDifference(old.i_state,new.i_state);
            item.state_max_abs_difference=max(item.s_state_max_abs_difference,item.i_state_max_abs_difference);
            item.old_numeric_pass=oa.assessment.numeric_pass; item.new_numeric_pass=na.assessment.numeric_pass;
            item.old_agreement_pass=oa.assessment.agreement_pass; item.new_agreement_pass=na.assessment.agreement_pass;
            item.old_observed_structure=oa.assessment.observed_structure;
            item.new_observed_structure=na.assessment.observed_structure;
            item.old_events=eventView(oa.assessment.structured_events);
            item.new_events=eventView(na.assessment.structured_events);
            item.checks=struct('success',isequaln(old.success,new.success), ...
                'return_status',strcmp(old.return_status,new.return_status), ...
                'iteration_count',isequaln(item.old_iteration_count,item.new_iteration_count), ...
                'objective',item.cost_relative_difference<=report.cost_relative_tolerance, ...
                'control_array',item.control_max_abs_difference<=report.array_max_abs_tolerance, ...
                'state_arrays',item.state_max_abs_difference<=report.array_max_abs_tolerance, ...
                'time_grids',isequaln(old.t_control,new.t_control) && isequaln(old.t_state,new.t_state) ...
                    && isequaln(old.dt_control,new.dt_control), ...
                'actual_grid',isequaln(old.actual_grid,new.actual_grid), ...
                'actual_solver_settings',isequaln(old.actual_solver_settings,new.actual_solver_settings), ...
                'observed_structure',strcmp(item.old_observed_structure,item.new_observed_structure), ...
                'stage_arcs',isequaln(oa.assessment.arcs,na.assessment.arcs), ...
                'stage_cell_labels',isequaln(oa.assessment.event_detection.cell_labels,na.assessment.event_detection.cell_labels), ...
                'observed_sequence',strcmp(oa.assessment.event_detection.observed_sequence,na.assessment.event_detection.observed_sequence), ...
                'event_intervals',isequaln(item.old_events,item.new_events), ...
                'numeric_pass',isequaln(item.old_numeric_pass,item.new_numeric_pass), ...
                'agreement_pass',isequaln(item.old_agreement_pass,item.new_agreement_pass), ...
                'numeric_checks',isequaln(oa.assessment.numeric_checks,na.assessment.numeric_checks));
            names=fieldnames(item.checks);
            item.reasons=names(~structfun(@(v) logical(v),item.checks))';
            item.comparison_completed=true; item.passed=isempty(item.reasons);
            item.status='compared'; if ~item.passed, item.status='mismatch'; end
        catch exception
            item.status='failed'; item.passed=false;
            item.reasons{end+1}=sprintf('[%s] %s',exception.identifier,exception.message);
            item.failure=struct('identifier',exception.identifier,'message',exception.message);
        end
        if isempty(report.rows), report.rows=item; else, report.rows(end+1)=item; end
        fprintf('RERUN COMPARISON %s %d/35 passed=%d status=%s\n', ...
            e.configuration_id,ix,item.passed,item.status);
    end
    report.compared_count=sum([report.rows.comparison_completed]); report.passed_count=sum([report.rows.passed]);
    report.old_counts=counts(report.rows,'old'); report.new_counts=counts(report.rows,'new');
    report.passed=report.compared_count==35 && report.passed_count==35;
    if ~report.passed, report.blockers={'At least one of the 35 comparisons failed; do not refresh scientific outputs.'}; end
catch exception
    report.failure=struct('identifier',exception.identifier,'message',exception.message);
    report.blockers{end+1}=sprintf('[%s] %s',exception.identifier,exception.message);
    report.passed=false;
end
% 不改写raw、sidecar、索引、selection或组摘要；连异常分支也检查已读取文件的原字节。
changed={};
for k=1:numel(protected)
    try
        unchanged=isfile(protected(k).path) ...
            && strcmp(numerical_sha256(protected(k).path,'file'),protected(k).sha256);
    catch exception
        unchanged=false;
        report.blockers{end+1}=sprintf('Cannot verify saved input [%s]: %s',exception.identifier,exception.message);
    end
    if ~unchanged
        changed{end+1}=protected(k).path; %#ok<AGROW>
    end
end
report.protected_files_unchanged=isempty(changed); report.protected_files=protected;
if ~isempty(changed)
    report.passed=false; report.blockers{end+1}='A read-only comparison input changed during comparison.';
    report.changed_input_files=changed;
end
report.status='completed'; if ~report.passed, report.status='failed'; end
report.finished_utc=numerical_utc();
% 失败证据必须先完整落盘，再抛出停止错误；这里没有评估或优化调用。
numerical_write_json(reportPath,report);
writeReadme(reportRoot,report);
if ~report.passed
    error('rerun:ComparisonFailed','S2.5 stopped: %d/35 comparisons passed. Read %s.',report.passed_count,reportPath);
end

    function value=tagJson(path)
        relative=relativePath(path);
        [status,body]=system(sprintf('git -C "%s" show "%s:%s"',cfg.paths.repo_root,tag,relative));
        assert(status==0,'rerun:MissingTaggedInput','Cannot read %s:%s: %s',tag,relative,body);
        value=jsondecode(body);
    end

    function value=readJson(path)
        guard(path); value=jsondecode(fileread(path));
    end

    function guard(path)
        assert(isfile(path),'rerun:MissingInput','Missing saved comparison input: %s',path);
        if isempty(protected) || ~any(strcmp({protected.path},path))
            protected(end+1)=struct('path',path,'sha256',numerical_sha256(path,'file'));
        end
    end

    function relative=relativePath(path)
        root=strrep(cfg.paths.repo_root,'\','/'); full=strrep(path,'\','/');
        assert(startsWith(lower(full),[lower(root) '/']),'rerun:OutsideRepository', ...
            'Comparison input must be inside the repository: %s',path);
        relative=full(numel(root)+2:end);
    end

    function mapping=sourceMapping(fromTag,experiments)
        mapping=cell(1,numel(experiments));
        for group={'initialization','grid','horizon'}
            path=fullfile(cfg.paths.data,'revision_checks',[group{1} '_summary.json']);
            if fromTag, summary=tagJson(path); else, summary=readJson(path); end
            assert(summary.schema_version==1 && strcmp(summary.group,group{1}) && summary.protocol_complete, ...
                'rerun:IncompleteSummary','Incomplete %s summary (baseline=%d).',group{1},fromTag);
            for j=1:numel(summary.rows)
                saved=summary.rows(j); match=find(strcmp({experiments.configuration_id},saved.configuration_id));
                assert(isscalar(match),'rerun:UnknownConfiguration','Unknown summary configuration_id.');
                e=experiments(match);
                assert(strcmp(saved.case_id,e.case_id) && saved.T==e.solver_settings.T ...
                    && saved.N==e.solver_settings.N && strcmp(saved.initialization,e.initialization.type) ...
                    && ~isempty(saved.run_id),'rerun:SummaryMismatch','Summary metadata differs for %s.',e.configuration_id);
                if ~isempty(mapping{match})
                    assert(strcmp(mapping{match},saved.run_id),'rerun:InconsistentSummary', ...
                        'Overlapping summaries disagree for %s.',e.configuration_id);
                end
                mapping{match}=saved.run_id;
            end
        end
        assert(all(~cellfun(@isempty,mapping)),'rerun:MissingConfiguration','Summaries do not cover all 35 configurations.');
    end

    function [raw,entry]=readRaw(index,id)
        match=find(strcmp({index.entries.run_id},id)); assert(isscalar(match),'rerun:MissingRun','No unique indexed run %s.',id);
        entry=index.entries(match); path=fullfile(cfg.paths.data,entry.raw_file); guard(path);
        assert(strcmp(numerical_sha256(path,'file'),entry.raw_sha256),'rerun:RawRecordModified','Raw hash differs for %s.',id);
        loaded=load(path,'run'); raw=loaded.run;
        assert(strcmp(raw.run_id,id) && strcmp(raw.solve_fingerprint,entry.solve_fingerprint) ...
            && strcmp(raw.source_status,'verified_record') && entry.success==raw.success, ...
            'rerun:UntrustedRaw','Saved raw provenance does not match its index for %s.',id);
        diagnosticPath=fullfile(cfg.paths.data,raw.solver_diagnostics_file);
        diagnostic=readJson(diagnosticPath);
        assert(strcmp(diagnostic.run_id,id) && strcmp(diagnostic.return_status,raw.return_status) ...
            && isequaln(diagnostic.solver_diagnostics.iteration_count,raw.solver_diagnostics.iteration_count), ...
            'rerun:DiagnosticsMismatch','Solver sidecar differs from its saved raw record for %s.',id);
    end

    function [record,path]=readAssessment(raw,fingerprint,settings,codeHash)
        files=dir(fullfile(cfg.paths.data,'revision_checks','assessments',[raw.run_id '_' fingerprint '_*.mat']));
        assert(~isempty(files),'rerun:MissingSavedAssessment','No saved revised assessment for %s.',raw.run_id);
        [~,order]=max([files.datenum]); path=fullfile(files(order).folder,files(order).name); guard(path);
        loaded=load(path,'assessment_record'); record=loaded.assessment_record;
        assert(strcmp(record.run_id,raw.run_id) && strcmp(record.solve_fingerprint,raw.solve_fingerprint) ...
            && strcmp(record.assessment_fingerprint,fingerprint) ...
            && strcmp(record.assessment_provenance.assessment_fingerprint,fingerprint) ...
            && isequaln(record.assessment_settings,settings) ...
            && isequaln(record.assessment_provenance.settings,settings), ...
            'rerun:AssessmentMismatch','Saved assessment provenance/settings differ for %s.',raw.run_id);
        if ~isempty(codeHash)
            assert(strcmp(record.assessment_provenance.code_hash,codeHash),'rerun:StaleAssessment', ...
                'New run %s has no current-source revised assessment.',raw.run_id);
        end
    end
end

function par=currentParameters(par)
% 只归一化内存中的旧参数副本，不改写raw及其求解指纹。
if isfield(par,'p')
    assert(~isfield(par,'beta'),'rerun:AmbiguousParameters','Historical parameters contain both p and beta.');
    par.beta=par.p; par=rmfield(par,'p');
end
end

function value=iterationCount(raw)
assert(isfield(raw,'solver_info') && isstruct(raw.solver_info) ...
    && isfield(raw.solver_info,'ipopt_stats') && isfield(raw.solver_info.ipopt_stats,'iter_count'), ...
    'rerun:MissingIterations','Missing actual IPOPT iteration count for %s.',raw.run_id);
value=raw.solver_info.ipopt_stats.iter_count;
assert(isnumeric(value) && isscalar(value) && isfinite(value) && value>=0 && value==fix(value) ...
    && strcmp(raw.solver_diagnostics.iteration_count.status,'available') ...
    && isequaln(value,raw.solver_diagnostics.iteration_count.value), ...
    'rerun:InvalidIterations','Raw iteration count and diagnostic sidecar disagree for %s.',raw.run_id);
end

function value=arrayDifference(first,second)
assert(isnumeric(first) && isnumeric(second) && isequal(size(first),size(second)) ...
    && ~isempty(first) && all(isfinite(first(:))) && all(isfinite(second(:))), ...
    'rerun:ArrayShapeOrValues','Saved output arrays must have equal sizes and finite values.');
value=max(abs(first(:)-second(:)));
end

function projected=eventView(events)
% 区间、候选、单元索引及阶段标志完全比较；端点状态/跨度遵守状态数组的数值容差。
projected=events; names=fieldnames(projected);
for k=1:numel(names)
    item=projected.(names{k});
    item=rmfield(item,intersect(fieldnames(item),{'numerical_endpoint_states','state_span'}));
    if isfield(item,'candidates') && isstruct(item.candidates)
        item.candidates=rmfield(item.candidates,intersect(fieldnames(item.candidates), ...
            {'numerical_endpoint_states','state_span'}));
    end
    projected.(names{k})=item;
end
end

function item=emptyRow(e,oldId,newId)
item=struct('configuration_id',e.configuration_id,'case_id',e.case_id,'groups',{e.groups}, ...
    'T',e.solver_settings.T,'N',e.solver_settings.N,'initialization',e.initialization.type, ...
    'old_run_id',oldId,'new_run_id',newId,'status','not_compared','comparison_completed',false,'passed',false, ...
    'old_raw_file','','new_raw_file','','old_raw_sha256','','new_raw_sha256','', ...
    'old_assessment_file','','new_assessment_file','','old_assessment_fingerprint','','new_assessment_fingerprint','', ...
    'old_return_status','','new_return_status','','old_iteration_count',[],'new_iteration_count',[], ...
    'old_J_openocl',[],'new_J_openocl',[],'cost_relative_difference',[], ...
    'control_max_abs_difference',[],'s_state_max_abs_difference',[],'i_state_max_abs_difference',[], ...
    'state_max_abs_difference',[],'old_numeric_pass',[],'new_numeric_pass',[], ...
    'old_agreement_pass',[],'new_agreement_pass',[],'old_observed_structure','','new_observed_structure','', ...
    'old_events',[],'new_events',[],'checks',struct(),'reasons',{{}},'failure',[]);
end

function out=counts(rows,prefix)
complete=[rows.comparison_completed]; rows=rows(complete);
numeric=[rows.([prefix '_numeric_pass'])]; agreement=[rows.([prefix '_agreement_pass'])];
out=struct('records',numel(rows),'numeric_pass',sum(numeric),'agreement_pass',sum(agreement),'both_pass',sum(numeric & agreement));
end

function writeReadme(folder,report)
path=fullfile(folder,'README.md'); fid=fopen(path,'w','n','UTF-8');
assert(fid>=0,'rerun:CannotWriteReport','Cannot write %s.',path); cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'# S2.5 新旧求解逐条比较\n\n');
fprintf(fid,'基线：`%s`（`%s`）。按 `configuration_id` 从标签及当前初始化、网格、时域三组摘要配对。\n\n', ...
    report.baseline_tag,report.baseline_commit);
fprintf(fid,'状态：**%s**；完成比较 %d/35，逐项通过 %d/35。优化器调用 0 次，新评估 0 次。\n\n', ...
    report.status,report.compared_count,report.passed_count);
fprintf(fid,['比较保存的真实 `return_status`、IPOPT 迭代次数、成本及原控制/状态数组。成本相对差限值 `1e-10`，' ...
    '数组最大绝对差限值 `1e-8`；时间网格、事件区间与候选、阶段结构、`numeric_pass`、`agreement_pass` 必须完全一致。\n\n']);
fprintf(fid,['旧评估取标签容差报告中的修订判据指纹，新评估取当前源码/设置及原始输出指纹对应的保存 sidecar。' ...
    '不执行重积分、重新评估、结果选择或求解。历史参数 `p` 只在内存副本中映射为 `beta`。\n\n']);
fprintf(fid,'已读取输入的原始字节保持不变：%d。逐条差值、失败项及来源见 `comparison_report.json`。\n', ...
    report.protected_files_unchanged);
for k=1:numel(report.blockers), fprintf(fid,'\n- %s\n',report.blockers{k}); end
if ~report.passed
    fprintf(fid,'\n已触发 S2.5 停止条件；不应据此刷新图表或论文产物。\n');
end
end
