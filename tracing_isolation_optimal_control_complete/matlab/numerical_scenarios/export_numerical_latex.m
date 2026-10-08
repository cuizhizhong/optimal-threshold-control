function report = export_numerical_latex(cfg)
% 从实际保存数据导出；临时配置仅用于无优化器回归，失败时清除陈旧通过文本。
if nargin<1 || isempty(cfg), cfg=numerical_cases_config(); end
try
    report=export_selected_results(cfg);
catch exception
    invalidate_generated_results(cfg);
    rethrow(exception);
end
end

function report=export_selected_results(cfg)
[runs,selectionManifest]=load_selected_numerical_runs(cfg.paths.data);
assessmentSpec=numerical_assessment_spec(cfg);
mainVerification=numerical_main_verification(runs,cfg.cases,cfg.parameters,cfg.solve,assessmentSpec);
verified=mainVerification.verified;
[robustness,robustnessText]=saved_robustness(cfg,runs,assessmentSpec);
exitChecks=struct();
for k=[2 4]
    exitChecks.(sprintf('E%d',k))=capacity_exit_transition( ...
        runs{k}.assessment.arcs,runs{k}.reference.events.full_start);
end
summary=repmat(compact(runs{1}),1,5);
for k=1:5, summary(k)=compact(runs{k}); end
out=struct('verified',verified,'main_verification',mainVerification, ...
    'robustness',robustness,'cases',summary,'capacity_exit_checks',exitChecks);
writefile(fullfile(cfg.paths.data,'numerical_checks.json'),jsonencode(out,PrettyPrint=true));
rows=cell(5,12);
for k=1:5
    r=runs{k}; rows(k,:)={r.case_id,r.x0(1),r.x0(2),r.reference.region, ...
        cfg.cases(k).expected_structure,r.assessment.observed_structure, ...
        r.reference.J_reference,r.J_openocl,r.solver_settings.N, ...
        r.assessment.numeric_pass,r.assessment.agreement_pass,r.assessment.provenance_pass};
end
tab=cell2table(rows,'VariableNames',{'case_id','s0','i0','region','expected_structure', ...
    'observed_structure','J_reference','J_openocl','N','numeric_pass','agreement_pass','provenance_pass'});
writetable(tab,fullfile(cfg.paths.data,'scenario_summary.csv'));
suffix={'One','Two','Three','Four','Five'};
reference={'% MATLAB 解析公式评价；不含优化器结果。'};
pending={'% 从 data/numerical_scenarios 的真实结果生成；条件开关由 main.tex 定义。'};
if verified, pending{end+1}='\NumResultsVerifiedtrue'; else, pending{end+1}='\NumResultsVerifiedfalse'; end
if robustness.protocol_complete
    pending{end+1}='\NumRobustnessCompletetrue';
else
    pending{end+1}='\NumRobustnessCompletefalse';
end
pending{end+1}=renewmacro('NumRobustnessStatement',robustnessText);
pending{end+1}=macro('NumHorizon',sprintf('%g',runs{1}.solver_settings.T));
pending{end+1}=macro('NumIntervals',sprintf('%d',cfg.solve.N));
pending{end+1}=macro('NumDegree',sprintf('%d',runs{1}.solver_settings.d));
mesh={};
for k=1:5
    if runs{k}.solver_settings.N~=cfg.solve.N
        mesh{end+1}=sprintf('E%d 使用 $N=%d$',k,runs{k}.solver_settings.N); %#ok<AGROW>
    end
end
if isempty(mesh)
    pending{end+1}=macro('NumMeshDetails','五个主算例均使用上述网格。');
else
    pending{end+1}=macro('NumMeshDetails',['按预先指定设置，' strjoin(mesh,'，') ...
        '；其余算例保留基准网格。图表均采用各例最终保存的结果。']);
end
for k=1:5
    reference{end+1}=macro(['NumJRefE' suffix{k}],sprintf('%.6f',runs{k}.reference.J_reference)); %#ok<AGROW>
    if runs{k}.success && isfinite(runs{k}.J_openocl)
        pending{end+1}=macro(['NumJOclE' suffix{k}],sprintf('%.6f',runs{k}.J_openocl)); %#ok<AGROW>
    else
        pending{end+1}=macro(['NumJOclE' suffix{k}],'--'); %#ok<AGROW>
    end
end
g=build_theory_geometry(cfg.parameters); e=runs{1}.reference.events;
reference{end+1}=macro('NumSBRef',sprintf('%.8f',g.s_B));
reference{end+1}=macro('NumSwitchSEOneRef',sprintf('%.8f',e.full_state(1)));
reference{end+1}=macro('NumSwitchIEOneRef',sprintf('%.8f',e.full_state(2)));
reference{end+1}=macro('NumMaxReleaseRef',sprintf('%.8f',max(cellfun(@(r) r.reference.events.release,runs))));
waiting=sprintf('实际控制输出中，E1 和 E2 分别识别出 $%s$ 与 $%s$。', ...
    texstructure(runs{1}.assessment.observed_structure),texstructure(runs{2}.assessment.observed_structure));
waiting=[waiting event_summary(runs{1}) event_summary(runs{2})];
boundary=sprintf('E3、E4、E5 的实际阶段依次为 $%s$、$%s$ 和 $%s$。', ...
    texstructure(runs{3}.assessment.observed_structure),texstructure(runs{4}.assessment.observed_structure), ...
    texstructure(runs{5}.assessment.observed_structure));
boundary=[boundary event_summary(runs{3}) event_summary(runs{4}) event_summary(runs{5})];
if exitChecks.E2.supported && exitChecks.E4.supported
    boundary=[boundary 'E2、E4 的理论容量退出时刻均位于各自容量段与完全跟踪段之间的单网格过渡区间内，' ...
        '因此不将首个纯完全跟踪单元的起点直接等同于连续切换点。'];
else
    boundary=[boundary sprintf(['容量退出过渡区间的自动核查未全部支持单网格包含结论（E2: %s；E4: %s），' ...
        '不能据首个纯完全跟踪单元确定连续切换点。'], ...
        strrep(exitChecks.E2.status,'_','-'),strrep(exitChecks.E4.status,'_','-'))];
end
for k=[2 4]
    e=exitChecks.(sprintf('E%d',k));
    pending{end+1}=macro(sprintf('NumExitE%sStart',suffix{k}),finite_text(e.interval(1),'%.8f')); %#ok<AGROW>
    pending{end+1}=macro(sprintf('NumExitE%sEnd',suffix{k}),finite_text(e.interval(2),'%.8f')); %#ok<AGROW>
    reference{end+1}=macro(sprintf('NumExitE%sTheory',suffix{k}),sprintf('%.8f',e.theory_time)); %#ok<AGROW>
end
cap=max(cellfun(@(r) r.assessment.capacity_excess,runs));
state=max(cellfun(@(r) r.assessment.state_discrepancy,runs));
tail=max(cellfun(@(r) r.assessment.tail_max_q,runs));
checktext=sprintf(['对原始分段常数控制逐区间重积分后，五例最大容量超出量为 $\\num{%.2g}$，' ...
    '与配点状态的最大差异为 $\\num{%.2g}$；末尾 $20$ 个时间单位内最大控制幅值为 $\\num{%.2g}$。'],cap,state,tail);
if verified
    checktext=[checktext '各例终端状态均通过零控制安全延拓核查。' ...
        '这些浮点检查用于排查截断及离散问题，不是连续可行性的严格证明。'];
    finding=sprintf(['五例成本相对解析参考的最大差异约为 $%.3g\\%%$。' ...
        '计算结果支持这五个初值下的阶段顺序及切换位置预测；' ...
        '切换位置的偏差应结合控制区间宽度和过渡单元解释。'], ...
        100*max(cellfun(@(r) abs(r.assessment.relative_cost_difference),runs)));
else
    checktext=[checktext '五例主结果尚有数值接受或理论比较未通过，当前结果不标记为已验证；具体状态见配套核查文件。'];
    finding='当前数值验证尚未全部通过；成本列为实际求解输出，不以解析值填补或替换。';
end
% 旧 E2 常值宏保留兼容定义；值仅取自新协议的真实常值初猜记录。
pending{end+1}=macro('NumNeutralETwoCostDifference',robustness.neutral_E2_cost_difference);
gap=runs{4}.J_openocl-runs{4}.reference.J_reference;
pending{end+1}=macro('NumEFourSignedCostDifference',finite_text(gap,'%.12g'));
pending{end+1}=macro('NumEFourCapacityExcess',finite_text(runs{4}.assessment.capacity_excess,'%.12g'));
pending{end+1}=macro('NumFindingWaiting',waiting);
for k=1:numel(runs)
    r=runs{k}; signedGap=r.J_openocl-r.reference.J_reference;
    if isfinite(signedGap) && signedGap<0
        finding=[finding sprintf('%s 的离散成本比解析参考低 $\\num{%.3g}$，',r.case_id,-signedGap)]; %#ok<AGROW>
        if r.assessment.capacity_excess>0
            finding=[finding sprintf(['重积分轨道仍有 $\\num{%.3g}$ 的容量超出；' ...
                '即使满足浮点接受容差，也不能称为低于解析最优值的严格连续时间可行控制。'], ...
                r.assessment.capacity_excess)]; %#ok<AGROW>
        else
            finding=[finding '现有浮点诊断不构成严格连续时间可行性证书，该负差需结合离散误差解释。']; %#ok<AGROW>
        end
    end
    if strcmp(r.assessment.status,'unresolved_discrepancy')
        finding=[finding r.case_id ' 的成本差超过预定比较尺度且现有诊断未能解释，标为 unresolved-discrepancy，保留原记录待查。']; %#ok<AGROW>
    end
    if ~strcmp(r.assessment.observed_structure,cfg.cases(k).expected_structure)
        finding=[finding sprintf('%s 的实际识别结构 $%s$ 与表中理论结构不一致。', ...
            r.case_id,texstructure(r.assessment.observed_structure))]; %#ok<AGROW>
    end
end
pending{end+1}=macro('NumFindingTrackingBoundary',boundary);
pending{end+1}=macro('NumCheckStatement',checktext);
pending{end+1}=macro('NumOverallFinding',finding);
mainPath=fullfile(cfg.paths.latex,'main.tex');
text=fileread(mainPath);
text=replace_generated_block(text, ...
    '% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES', ...
    '% END AUTO-GENERATED NUMERICAL REFERENCE VALUES',strjoin(reference,newline));
text=replace_generated_block(text, ...
    '% BEGIN AUTO-GENERATED NUMERICAL RESULTS', ...
    '% END AUTO-GENERATED NUMERICAL RESULTS',strjoin(pending,newline));
atomic_write(mainPath,text);
numerical_export_provenance('export',selectionManifest,cfg.paths.data);
report=struct('verified',verified,'status',mainVerification.status, ...
    'optimizer_executions',0,'selection_manifest',selectionManifest,'robustness',robustness);
fprintf('NUMERICAL_LATEX_EXPORTED verified=%d\n',verified);
end

function invalidate_generated_results(cfg)
% 输入缺失、失败或来源不匹配时不能继承上次生成块中的 true 和通过段落。
filename=fullfile(cfg.paths.latex,'main.tex');
text=fileread(filename);
body={'% 当前选定结果不可用；本块不包含新优化结果。', ...
    '\NumResultsVerifiedfalse','\NumRobustnessCompletefalse',renewmacro('NumRobustnessStatement','')};
body{end+1}=macro('NumHorizon',sprintf('%g',cfg.solve.T));
body{end+1}=macro('NumIntervals',sprintf('%d',cfg.solve.N));
body{end+1}=macro('NumDegree',sprintf('%d',cfg.solve.d));
body{end+1}=macro('NumMeshDetails','');
suffix={'One','Two','Three','Four','Five'};
for k=1:numel(suffix)
    body{end+1}=macro(['NumJOclE' suffix{k}],'--'); %#ok<AGROW>
end
names={'NumFindingWaiting','NumFindingTrackingBoundary','NumCheckStatement','NumOverallFinding'};
for k=1:numel(names), body{end+1}=macro(names{k},''); end %#ok<AGROW>
names={'NumExitETwoStart','NumExitETwoEnd','NumExitEFourStart','NumExitEFourEnd', ...
    'NumNeutralETwoCostDifference','NumEFourSignedCostDifference','NumEFourCapacityExcess'};
for k=1:numel(names), body{end+1}=macro(names{k},'--'); end %#ok<AGROW>
text=replace_generated_block(text, ...
    '% BEGIN AUTO-GENERATED NUMERICAL RESULTS', ...
    '% END AUTO-GENERATED NUMERICAL RESULTS',strjoin(body,newline));
atomic_write(filename,text);
end

function c=compact(r)
c=struct('case_id',r.case_id,'x0',r.x0,'parameters',r.parameters, ...
    'solver_settings',r.solver_settings,'initialization',r.initialization, ...
    'success',r.success,'return_status',r.return_status,'J_reference',r.reference.J_reference, ...
    'J_openocl',r.J_openocl,'reference_events',r.reference.events, ...
    'assessment',rmfield(r.assessment,'reintegration'));
end
function s=texstructure(s)
s=strrep(s,' -> ','\to ');
end
function text=event_summary(run)
% 每句话取自唯一数值候选；缺失/多个候选不输出预期阶段或NaN时刻。
events=run.assessment.structured_events;
names={'intervention','capacity_enter','capacity_exit','full_start','release'};
titles={'初次干预','容量进入','容量退出','完全跟踪开始','解除'};
parts={};
for k=1:numel(names)
    e=events.(names{k});
    if e.candidate_count==1 && all(isfinite(e.interval))
        parts{end+1}=sprintf('%s的检测区间为 $[%.6g,%.6g]$',titles{k},e.interval(1),e.interval(2)); %#ok<AGROW>
    elseif e.candidate_count>1
        parts{end+1}=sprintf('%s存在 %d 个候选，尚不能唯一定位',titles{k},e.candidate_count); %#ok<AGROW>
    end
end
if isempty(parts), text=[run.case_id ' 未检测到付费阶段事件。'];
else, text=[run.case_id '：' strjoin(parts,'；') '。']; end
end
function s=macro(name,value)
s=['\providecommand{\' name '}{' value '}'];
end
function s=renewmacro(name,value)
s=['\renewcommand{\' name '}{' value '}'];
end
function s=finite_text(value,format)
if isscalar(value) && isfinite(value), s=sprintf(format,value); else, s='--'; end
end

function [out,text]=saved_robustness(cfg,main,spec)
% 只读新协议摘要、不可覆盖原始记录及已有评估；不重求解、不重新评估。
if ~isfield(cfg,'revision')
    protocol=revision_validation_config(cfg.paths.scenario_inputs);
    cfg.revision=protocol.revision;
end
groups={'initialization','grid','horizon','threshold'};
out=struct('protocol_complete',false,'consistency_pass',false,'groups',struct(), ...
    'recorded_configuration_count',0,'expected_configuration_count',numel(cfg.revision.experiments), ...
    'numeric_and_agreement_pass_count',0,'source_files',[], ...
    'neutral_E2_cost_difference','--');
records=struct('configuration_id',{},'run_id',{},'numeric_pass',{},'agreement_pass',{});
views=containers.Map('KeyType','char','ValueType','any');
source=numerical_code_hash('solve'); indexPath=fullfile(cfg.paths.data,'run_index.json');
hasSummary=any(cellfun(@(g) isfile(fullfile(cfg.paths.data,'revision_checks',[g '_summary.json'])),groups));
text=''; if ~hasSummary, return; end
assert(isfile(indexPath),'numerical:MissingRunIndex','Saved robustness summaries require run_index.json.');
index=jsondecode(fileread(indexPath));
for k=1:numel(main)
    r=main{k}; ix=find(arrayfun(@(e) strcmp(e.case_id,r.case_id) && any(strcmp(e.groups,'main')),cfg.revision.experiments));
    assert(isscalar(ix));
    add_record(cfg.revision.experiments(ix).configuration_id,r);
end
for gi=1:numel(groups)
    group=groups{gi}; path=fullfile(cfg.paths.data,'revision_checks',[group '_summary.json']);
    status=struct('available',false,'protocol_complete',false,'consistency_pass',false, ...
        'passed_cases',{{}},'failed_cases',{{}},'record_count',0,'summary_sha256','');
    if ~isfile(path), out.groups.(group)=status; continue; end
    summary=jsondecode(fileread(path));
    assert(summary.schema_version==1 && isfield(summary,'rows') && isfield(summary,'consistency_pass'), ...
        'numerical:InvalidRevisionSummary','Invalid saved %s summary.',group);
    status.available=true; status.summary_sha256=numerical_sha256(path,'file');
    add_source(fullfile('revision_checks',[group '_summary.json']),status.summary_sha256);
    rows=summary.rows; status.record_count=numel(rows);
    if isempty(rows)
        % blocked 摘要仅是状态记录；尚未产生实验行时不生成结果结论。
        status.available=false; out.groups.(group)=status; continue;
    end
    if strcmp(group,'threshold')
        expectedCount=numel(main)*numel(cfg.revision.threshold_control)*numel(cfg.revision.threshold_capacity);
        keys={};
        for j=1:numel(rows)
            row=rows(j); k=find(cellfun(@(r) strcmp(r.case_id,row.case_id),main));
            assert(isscalar(k) && strcmp(row.run_id,main{k}.run_id) && ...
                strcmp(row.solve_fingerprint,main{k}.solve_fingerprint), ...
                'numerical:RevisionSourceMismatch','Threshold source differs from selected main result.');
            assert(ismember(row.control_threshold,cfg.revision.threshold_control) && ...
                ismember(row.capacity_threshold,cfg.revision.threshold_capacity), ...
                'numerical:RevisionSourceMismatch','Threshold settings differ from the frozen protocol.');
            keys{end+1}=sprintf('%s/%.12g/%.12g',row.case_id,row.control_threshold,row.capacity_threshold); %#ok<AGROW>
            assert(strcmp(row.observed_structure,row.detection.observed_structure), ...
                'numerical:RevisionSourceMismatch','Threshold summary and saved detection differ.');
        end
        assert(numel(unique(keys))==numel(keys),'numerical:InvalidRevisionSummary','Duplicated threshold rows.');
        status.protocol_complete=numel(rows)==expectedCount && strcmp(summary.status,'completed');
        status.consistency_pass=status.protocol_complete && summary.consistency_pass && all([rows.consistency_pass]);
        for k=1:numel(main)
            local=rows(strcmp({rows.case_id},main{k}.case_id));
            pass=numel(local)==expectedCount/numel(main) && all([local.consistency_pass]);
            if pass, status.passed_cases{end+1}=main{k}.case_id;
            else, status.failed_cases{end+1}=main{k}.case_id; end
        end
    else
        assert(strcmp(summary.group,group) && isfield(summary,'protocol_complete') && ...
            isfield(summary,'case_comparisons'),'numerical:InvalidRevisionSummary','Incomplete %s summary.',group);
        scheduled=cfg.revision.experiments(arrayfun(@(e) belongs(e,group),cfg.revision.experiments));
        assert(numel(unique({rows.configuration_id}))==numel(rows), ...
            'numerical:InvalidRevisionSummary','Duplicated %s configuration.',group);
        recorded=true(1,numel(rows));
        for j=1:numel(rows)
            row=rows(j); ix=find(strcmp({scheduled.configuration_id},row.configuration_id));
            assert(isscalar(ix),'numerical:RevisionSourceMismatch','Unscheduled %s configuration.',group);
            e=scheduled(ix);
            assert(strcmp(row.case_id,e.case_id) && row.T==e.solver_settings.T && ...
                row.N==e.solver_settings.N && strcmp(row.initialization,e.initialization.type), ...
                'numerical:RevisionSourceMismatch','Summary configuration differs from the frozen protocol.');
            if isempty(row.run_id), recorded(j)=false; continue; end
            view=saved_view(row,e); add_record(row.configuration_id,view);
            if strcmp(group,'initialization') && strcmp(row.case_id,'E2') && strcmp(row.initialization,'constant_control')
                out.neutral_E2_cost_difference=finite_text(abs(view.J_openocl-main{2}.J_openocl),'%.12g');
            end
        end
        status.protocol_complete=summary.protocol_complete && numel(rows)==numel(scheduled) && all(recorded);
        comparison=summary.case_comparisons;
        assert(numel(comparison)==numel(main) && numel(unique({comparison.case_id}))==numel(main), ...
            'numerical:InvalidRevisionSummary','Missing or duplicated case comparisons in %s.',group);
        for k=1:numel(main)
            ix=find(strcmp({comparison.case_id},main{k}.case_id)); assert(isscalar(ix)); item=comparison(ix);
            local=rows(strcmp({rows.case_id},item.case_id));
            ids=cellstr(item.source_run_ids);
            assert(isequal(sort(ids(:)),sort({local(~cellfun(@isempty,{local.run_id})).run_id}')), ...
                'numerical:RevisionSourceMismatch','%s comparison uses different source runs.',group);
            if strcmp(group,'initialization') && ~isempty(item.reference_run_id)
                assert(strcmp(item.reference_run_id,main{k}.run_id), ...
                    'numerical:RevisionSourceMismatch','Initialization comparison uses a different main reference.');
            end
            if item.consistency_pass, status.passed_cases{end+1}=item.case_id;
            else, status.failed_cases{end+1}=item.case_id; end
        end
        status.consistency_pass=status.protocol_complete && summary.consistency_pass && all([comparison.consistency_pass]);
    end
    out.groups.(group)=status;
end
out.recorded_configuration_count=numel(records);
out.numeric_and_agreement_pass_count=sum([records.numeric_pass] & [records.agreement_pass]);
out.protocol_complete=out.recorded_configuration_count==out.expected_configuration_count && ...
    all(cellfun(@(g) out.groups.(g).protocol_complete,groups));
out.consistency_pass=out.protocol_complete && all(cellfun(@(g) out.groups.(g).consistency_pass,groups));
if ~any(cellfun(@(g) out.groups.(g).available,groups)), return; end
text=sprintf(['默认协议已记录 %d/%d 个不同配置，其中 %d 个同时通过数值接受与理论比较。' ...
    '协议是否完成与比较是否一致分别记录。'],out.recorded_configuration_count, ...
    out.expected_configuration_count,out.numeric_and_agreement_pass_count);
init=out.groups.initialization;
if init.available
    summary=jsondecode(fileread(fullfile(cfg.paths.data,'revision_checks','initialization_summary.json')));
    values=[];
    for k=1:numel(summary.case_comparisons)
        values=[values; summary.case_comparisons(k).cost_absolute_difference(:)]; %#ok<AGROW>
    end
    if init.consistency_pass
        text=[text sprintf('五例常值和固定种子随机初猜的阶段一致，成本最大绝对差为 $\\num{%.3g}$。',max(values))];
    else
        text=[text '初猜复核未全部支持一致性，未通过案例为 ' strjoin(init.failed_cases,'、') '。'];
    end
end
grid=out.groups.grid;
if grid.available
    text=[text '固定时域网格比较通过 ' strjoin(grid.passed_cases,'、') '；'];
    if ~isempty(grid.failed_cases)
        text=[text strjoin(grid.failed_cases,'、') ' 未通过预定数值及事件比较，不能作五例整体网格稳定结论。'];
    else
        text=[text '五例主要事件在对应网格尺度内一致。'];
    end
end
if out.groups.horizon.available
    if out.groups.horizon.consistency_pass, text=[text '固定步长时域复核五例通过。'];
    else, text=[text '固定步长时域复核未通过案例为 ' strjoin(out.groups.horizon.failed_cases,'、') '。']; end
end
if out.groups.threshold.available
    if out.groups.threshold.consistency_pass, text=[text '阈值复核通过。'];
    else, text=[text '阈值复核未全部通过。']; end
end
missing=groups(~cellfun(@(g) out.groups.(g).available,groups));
if ~isempty(missing), text=[text '尚无结果的组为 \texttt{' strjoin(missing,', ') '}。']; end
text=[text '全部记录见配套文件；有限样本与浮点诊断不替代解析证明。'];

    function add_record(configuration,r)
        ix=find(strcmp({records.configuration_id},configuration));
        entry=struct('configuration_id',configuration,'run_id',r.run_id, ...
            'numeric_pass',logical(r.assessment.numeric_pass),'agreement_pass',logical(r.assessment.agreement_pass));
        if isempty(ix), records(end+1)=entry;
        else
            assert(isscalar(ix) && isequal(records(ix),entry), ...
                'numerical:RevisionSourceMismatch','One configuration points to conflicting saved results.');
        end
    end
    function add_source(path,hash)
        entry=struct('path',strrep(path,'\','/'),'sha256',hash);
        if isempty(out.source_files), out.source_files=entry;
        elseif ~any(strcmp({out.source_files.path},entry.path)), out.source_files(end+1)=entry; end
    end
    function view=saved_view(row,e)
        if isKey(views,row.run_id), view=views(row.run_id);
        else
            ix=find(strcmp({index.entries.run_id},row.run_id));
            assert(isscalar(ix),'numerical:RevisionSourceMismatch','Run not found in index: %s.',row.run_id);
            entry=index.entries(ix); rawPath=fullfile(cfg.paths.data,entry.raw_file);
            assert(isfile(rawPath) && strcmp(numerical_sha256(rawPath,'file'),entry.raw_sha256), ...
                'numerical:RawRecordModified','Missing or modified robustness raw run: %s.',row.run_id);
            data=load(rawPath,'run'); raw=data.run;
            assert(strcmp(raw.run_id,row.run_id) && strcmp(raw.solve_fingerprint,row.solve_fingerprint) && ...
                strcmp(raw.source_status,'verified_record') && strcmp(raw.provenance.solve_code_hash,source.hash), ...
                'numerical:RevisionSourceMismatch','Untrusted robustness solve provenance: %s.',row.run_id);
            fingerprint=numerical_sha256(struct('solve_fingerprint',raw.solve_fingerprint, ...
                'raw_output_hash',numerical_sha256(raw),'assessment',spec));
            files=dir(fullfile(cfg.paths.data,'revision_checks','assessments',[raw.run_id '_' fingerprint '_*.mat']));
            assert(~isempty(files),'numerical:RevisionSourceMismatch','No current saved assessment: %s.',row.run_id);
            [~,latest]=max([files.datenum]); assessmentPath=fullfile(files(latest).folder,files(latest).name);
            data=load(assessmentPath,'assessment_record'); record=data.assessment_record;
            assert(strcmp(record.run_id,raw.run_id) && strcmp(record.solve_fingerprint,raw.solve_fingerprint) && ...
                strcmp(record.assessment_fingerprint,fingerprint) && ...
                strcmp(record.assessment_provenance.code_hash,spec.code_hash) && isequaln(record.assessment_settings,spec.settings), ...
                'numerical:RevisionSourceMismatch','Saved assessment provenance mismatch: %s.',row.run_id);
            view=raw; view.assessment=record.assessment; view.reference=record.reference;
            views(row.run_id)=view;
            add_source(entry.raw_file,entry.raw_sha256);
            add_source(fullfile('revision_checks','assessments',files(latest).name),numerical_sha256(assessmentPath,'file'));
        end
        assert(strcmp(view.solve_fingerprint,row.solve_fingerprint) && ...
            strcmp(view.case_id,e.case_id) && isequaln(view.parameters,e.parameters) && ...
            isequaln(view.x0(:),e.x0(:)) && isequaln(view.solver_settings,e.solver_settings) && ...
            strcmp(view.initialization.type,e.initialization.type) && view.success==row.success && ...
            strcmp(view.return_status,row.return_status) && isequaln(view.J_openocl,row.J_openocl), ...
            'numerical:RevisionSourceMismatch','Summary does not match original solve: %s.',row.run_id);
        names={'numeric_pass','agreement_pass','capacity_excess','state_discrepancy', ...
            'tail_max_q','terminal_peak','observed_structure'};
        for ni=1:numel(names)
            assert(isequaln(view.assessment.(names{ni}),row.(names{ni})), ...
                'numerical:RevisionSourceMismatch','Summary differs from saved assessment at %s: %s.',names{ni},row.run_id);
        end
    end
end

function yes=belongs(experiment,group)
if strcmp(group,'initialization')
    yes=any(ismember(experiment.groups,{'initialization-constant','initialization-random'}));
else
    yes=any(strcmp(experiment.groups,group));
end
end
function writefile(path,text)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cleaner=onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',text);
end

function text=replace_generated_block(text,beginMarker,endMarker,body)
% 在内存核对两个完整生成块后一次写入，防止混合导出版本。
begins=strfind(text,beginMarker); ends=strfind(text,endMarker);
assert(isscalar(begins) && isscalar(ends) && begins<ends, ...
    'Generated block markers are missing or duplicated: %s',beginMarker);
if contains(text,sprintf('\r\n'))
    nl=sprintf('\r\n');
else
    nl=sprintf('\n');
end
body=strrep(body,sprintf('\r\n'),sprintf('\n'));
body=strrep(body,sprintf('\n'),nl);
replacement=[beginMarker nl body nl endMarker];
text=[text(1:begins-1) replacement text(ends+length(endMarker):end)];
end

function atomic_write(filename,text)
temporary=[tempname(fileparts(filename)) '.tex'];
cleaner=onCleanup(@() cleanup_file(temporary)); %#ok<NASGU>
fid=fopen(temporary,'w','n','UTF-8'); assert(fid>=0);
fprintf(fid,'%s',text);
assert(fclose(fid)==0,'export_numerical_latex:WriteFailure','Cannot close temporary export.');
[ok,message]=movefile(temporary,filename,'f');
assert(ok,'export_numerical_latex:PublishFailure','Cannot publish export: %s',message);
end

function cleanup_file(filename)
if isfile(filename), delete(filename); end
end
