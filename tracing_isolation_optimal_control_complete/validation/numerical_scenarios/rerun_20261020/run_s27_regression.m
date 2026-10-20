function report = run_s27_regression()
% S2.7规定的三项导出回归；故障注入只在各测试自己的临时目录内发生。
here=fileparts(mfilename('fullpath')); target=fullfile(here,'S2.7','regression_report.json');
report=struct('status','started','optimizer_calls',0,'scientific_solves',0);
try
    report.saved=verify_saved_result_exporter();
    report.revision=verify_revision_exporter();
    report.pending=verify_pending_result_exporter();
    report.status='completed'; numerical_write_json(target,report);
    fprintf('S2.7_EXPORT_REGRESSIONS_OK optimizer=0\n');
catch exception
    report.status='failed'; report.failure=struct('identifier',exception.identifier,'message',exception.message);
    numerical_write_json(target,report); rethrow(exception);
end
end
