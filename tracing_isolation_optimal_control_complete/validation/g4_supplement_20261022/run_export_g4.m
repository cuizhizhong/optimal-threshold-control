function report = run_export_g4()
% G4 只运行保存数据导出及既有导出器回归，不求解或重评。
here=fileparts(mfilename('fullpath'));
report=struct('status','started','optimizer_calls',0,'new_ocp_solves',0, ...
    'assessment_calls',0,'figure_exports',0);
try
    report.export=export_numerical_latex();
    report.saved=verify_saved_result_exporter();
    report.revision=verify_revision_exporter();
    report.pending=verify_pending_result_exporter();
    report.status='completed';
    numerical_write_json(fullfile(here,'matlab_report.json'),report);
    fprintf('G4_EXPORT_REGRESSIONS_OK optimizer=0 new_ocp=0\n');
catch exception
    report.status='failed';
    report.failure=struct('identifier',exception.identifier,'message',exception.message);
    numerical_write_json(fullfile(here,'matlab_report.json'),report);
    rethrow(exception);
end
end
