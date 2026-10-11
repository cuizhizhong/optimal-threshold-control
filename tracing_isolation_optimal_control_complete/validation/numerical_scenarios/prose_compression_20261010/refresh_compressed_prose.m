function report=refresh_compressed_prose()
% 仅从当前保存结果导出正文，并运行临时副本中的既有导出回归。
cfg=revision_validation_config();
folder=fileparts(mfilename('fullpath'));
revision=jsondecode(fileread(fullfile(cfg.paths.report_root,'validation', ...
    'numerical_scenarios','tolerance_revision_20261010','assessment_revision_report.json')));
assert(strcmp(revision.status,'completed') && revision.optimizer_executions==0);
exported=export_numerical_latex(cfg);
assert(exported.optimizer_executions==0 && exported.verified);
saved=verify_saved_result_exporter();
failure=verify_revision_exporter();
pending=verify_pending_result_exporter();
assert(saved.passed && failure.passed && pending.passed);
report=struct('passed',true,'optimizer_executions',0, ...
    'assessment_executions_this_task',0,'compatibility_publications_this_task',0, ...
    'main_verified',exported.verified, ...
    'recorded_configurations',exported.robustness.recorded_configuration_count, ...
    'numeric_and_agreement_pass_count',exported.robustness.numeric_and_agreement_pass_count, ...
    'saved_exporter',saved,'failure_exporter',failure,'pending_exporter',pending);
numerical_write_json(fullfile(folder,'matlab_report.json'),report);
fprintf('PROSE_COMPRESSION_EXPORT_OK optimizer=0 reassessment=0 main_verified=1\n');
end
