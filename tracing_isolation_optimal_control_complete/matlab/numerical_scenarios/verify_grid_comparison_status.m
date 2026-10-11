function report = verify_grid_comparison_status()
% 合成汇总回归：不调用优化器，所有产物仅写入独立临时目录。
root=[tempname(tempdir) '_grid_comparison_status']; mkdir(root);
cleanup=onCleanup(@() cleanupSynthetic(root)); %#ok<NASGU>
cfg=struct('paths',struct('data',root),'revision',struct('grid_cost_relative_tolerance',1e-4));
[experiments,runs]=syntheticGrid();

% 次细级未被数值接受，即使事件原本可一致，也不得执行严格比较。
changed=runs; changed{2}.assessment.numeric_pass=false;
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'not_evaluated_due_to_numeric_failure'));
assert(c.fine_numeric_pass && ~c.coarse_numeric_pass && c.fine_N==8000 && c.coarse_N==4000);
assert(strcmp(c.fine_run_id,'synthetic_E1_N8000') && strcmp(c.coarse_run_id,'synthetic_E1_N4000'));
assert(any(strcmp(c.reasons,'coarse N=4000 numeric_pass=false')));
assertSkipped(c); assert(strcmp(s.status,'failed') && s.protocol_complete && s.comparison_complete);

% 事件真的不一致时保留已执行状态及成本比较的独立结果。
changed=runs; changed{2}.assessment.structured_events.full_start.interval=[3 3.1];
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'evaluated_failed'));
assert(c.event_comparison_evaluated && c.cost_comparison_evaluated);
assert(~c.event_comparison_pass && c.cost_comparison_pass && ~c.consistency_pass);
assert(~c.event_comparisons.full_start.passed && c.finest_relative_cost_difference==0);

% 成本差超限与事件比较通过分别保存。
changed=runs; changed{2}.J_openocl=1.01;
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'evaluated_failed'));
assert(c.event_comparison_evaluated && c.cost_comparison_evaluated);
assert(c.event_comparison_pass && ~c.cost_comparison_pass && ~c.consistency_pass);
assert(abs(c.finest_relative_cost_difference-.01)<1e-14);

% 两类比较通过，仍保持原 summary/status 判定。
s=revision_group_summary(cfg,'grid',experiments,runs); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'evaluated_passed'));
assert(c.event_comparison_evaluated && c.cost_comparison_evaluated);
assert(c.event_comparison_pass && c.cost_comparison_pass && c.consistency_pass);
assert(strcmp(c.status,'passed') && strcmp(s.status,'completed') && s.consistency_pass);
assert(s.schema_version==1);

% 其他前提缺失与缺求解记录有独立状态，且都不填入比较结果。
changed=runs; changed{2}.assessment=rmfield(changed{2}.assessment,'event_detection');
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'not_evaluated_due_to_comparison_prerequisite_failure'));
assert(c.fine_numeric_pass && c.coarse_numeric_pass); assertSkipped(c);
changed=runs; changed{2}=[];
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'not_evaluated_due_to_missing_record'));
assert(isempty(c.coarse_numeric_pass) && isempty(c.coarse_run_id)); assertSkipped(c);
assert(strcmp(s.status,'blocked') && ~s.protocol_complete && ~s.comparison_complete);

% 最细级数值失败也必须明确指向该级，而非声称事件不一致。
changed=runs; changed{3}.assessment.numeric_pass=false;
s=revision_group_summary(cfg,'grid',experiments,changed); c=s.case_comparisons(1);
assert(strcmp(c.comparison_status,'not_evaluated_due_to_numeric_failure'));
assert(any(strcmp(c.reasons,'fine N=8000 numeric_pass=false'))); assertSkipped(c);
report=struct('passed',true,'tests',{{'numeric_gate_skips_comparable_events', ...
    'evaluated_event_failure','evaluated_cost_failure','evaluated_pass', ...
    'missing_prerequisite','missing_record','fine_numeric_failure'}},'actual_optimizer_calls',0);
fprintf('GRID_COMPARISON_STATUS_OK tests=%d actual_optimizer=0\n',numel(report.tests));
end

function cleanupSynthetic(root)
% 递归清理前确认目标仍是本测试在系统临时目录内创建的独立目录。
targetFile=javaObject('java.io.File',root); parentFile=javaObject('java.io.File',tempdir);
targetPath=char(targetFile.getCanonicalPath()); parentPath=char(parentFile.getCanonicalPath());
assert(~strcmpi(targetPath,parentPath) && ...
    startsWith(targetPath,[parentPath filesep],'IgnoreCase',ispc) && ...
    endsWith(targetPath,'_grid_comparison_status'));
if isfolder(targetPath), rmdir(targetPath,'s'); end
end

function assertSkipped(c)
assert(~c.event_comparison_evaluated && ~c.cost_comparison_evaluated);
assert(~c.event_comparison_pass && ~c.cost_comparison_pass && ~c.consistency_pass);
assert(isnan(c.finest_relative_cost_difference) && isempty(c.event_comparisons) && isempty(c.reference_run_id));
end

function [experiments,runs]=syntheticGrid()
experiments=struct([]); runs={}; levels=[2000 4000 8000];
for k=1:5
    for j=1:numel(levels)
        id=sprintf('E%d',k); N=levels(j); ix=numel(runs)+1;
        row=struct('case_id',id,'configuration_id',sprintf('synthetic_%s_N%d',id,N), ...
            'groups',{{'grid'}},'solver_settings',struct('T',300,'N',N), ...
            'initialization',struct('type','synthetic'));
        if isempty(experiments), experiments=row; else, experiments(ix)=row; end
        event=struct('candidate_count',1,'interval',[1 1.1],'local_max_cell_width',.1);
        assessment=struct('numeric_pass',true,'agreement_pass',true,'observed_structure','0 -> 1 -> 0', ...
            'structured_events',struct('full_start',event), ...
            'event_detection',struct('diagnostics',struct('passed',true)), ...
            'event_comparison',struct('diagnostic_pass',true));
        runs{ix}=struct('run_id',sprintf('synthetic_%s_N%d',id,N),'solve_fingerprint','synthetic', ...
            'success',true,'return_status','synthetic_success','J_openocl',1,'assessment',assessment);
    end
end
end
