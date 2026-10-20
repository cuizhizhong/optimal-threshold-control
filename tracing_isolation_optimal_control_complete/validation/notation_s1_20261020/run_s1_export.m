function report = run_s1_export(mode)
% 仅执行既有导出回归和保存结果重导出；不调用求解入口。
if nargin<1, mode='regression'; end
assert(ismember(mode,{'export','regression'}));
codeRoot=fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios');
addpath(codeRoot);
root=fileparts(mfilename('fullpath'));
report=struct('mode',mode,'optimizer_calls',0,'scientific_solves',0);
if strcmp(mode,'regression')
    report.saved=verify_saved_result_exporter();
    report.revision=verify_revision_exporter();
    report.pending=verify_pending_result_exporter();
    assert(report.saved.passed && report.revision.passed && report.pending.passed);
    assert(report.saved.actual_optimizer_calls==0 && report.revision.actual_optimizer_calls==0 && ...
        report.pending.actual_optimizer_calls==0);
end
report.export=export_numerical_latex();
assert(report.export.verified && report.export.optimizer_executions==0);
assert(report.export.robustness.recorded_configuration_count==35 && ...
    report.export.robustness.numeric_and_agreement_pass_count==30);
numerical_write_json(fullfile(root,[mode '_report.json']),report);
fprintf('S1_EXPORT_OK mode=%s recorded=35 combined_pass=30 optimizer=0 solves=0\n',mode);
end
