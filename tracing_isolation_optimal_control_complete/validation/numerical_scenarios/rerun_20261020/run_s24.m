function summary = run_s24()
% S2.4正式入口；只运行一次完整矩阵，不因既有数值诊断失败而重跑。
here=fileparts(mfilename('fullpath')); folder=fullfile(here,'S2.4');
if ~isfolder(folder), mkdir(folder); end
output=fullfile(folder,'execution_report.json');
assert(~isfile(output),'rerun:ExistingExecution','S2.4 execution report already exists; do not repeat solves.');
summary=struct('stage','S2.4','status','started','started_utc',numerical_utc(), ...
    'finished_utc','','solver_calls',0,'cache_hits',0,'assessment_calls',0);
numerical_write_json(output,summary);
try
    preflight=revision_preflight();
    numerical_write_json(fullfile(folder,'preflight_report.json'),preflight);
    assert(preflight.passed,'rerun:PreflightFailed','停止条件：OpenOCL/CasADi预检未通过。');
    unit=run_revision_validation('unit',false);
    numerical_write_json(fullfile(folder,'unit_report.json'),unit);
    assert(unit.protocol_complete && unit.unit.passed,'rerun:UnitFailed','Unit suite did not pass.');
    timer=tic;
    report=run_revision_validation('all',false);
    summary.elapsed_seconds=toc(timer);
    numerical_write_json(fullfile(folder,'all_report.json'),report);
    summary.batch_id=report.batch_id;
    summary.solver_calls=report.solver_calls; summary.cache_hits=report.cache_hits;
    summary.assessment_calls=report.assessment_calls;
    summary.successful_count=report.successful_count; summary.failed_count=report.failed_count;
    summary.protocol_complete=report.protocol_complete; summary.scheduler_status=report.status;
    summary.numeric_pass_count=report.numeric_pass_count;
    summary.agreement_pass_count=report.agreement_pass_count;
    summary.both_pass_count=sum([report.rows.numeric_pass] & [report.rows.agreement_pass]);
    assert(report.solver_calls==35 && report.cache_hits==0 && report.attempted_count==35, ...
        'rerun:WrongSolveCount','停止条件：实际求解必须为35次，且缓存命中必须为0。');
    assert(report.protocol_complete && report.failed_count==0,'rerun:IncompleteSolves', ...
        '停止条件：35条科学记录没有全部完成并返回求解成功。');
    assert(summary.both_pass_count==30,'rerun:RevisedCountChanged', ...
        '停止条件：修订判据同时通过数不再是30/35。');
    summary.status='completed'; summary.finished_utc=numerical_utc();
    numerical_write_json(output,summary);
    fprintf('S2.4_COMPLETED solves=%d cache=%d assessments=%d both=%d/35 elapsed=%.3f\n', ...
        summary.solver_calls,summary.cache_hits,summary.assessment_calls, ...
        summary.both_pass_count,summary.elapsed_seconds);
catch exception
    summary.status='failed'; summary.finished_utc=numerical_utc();
    summary.failure=struct('identifier',exception.identifier,'message',exception.message);
    numerical_write_json(output,summary); rethrow(exception);
end
end
