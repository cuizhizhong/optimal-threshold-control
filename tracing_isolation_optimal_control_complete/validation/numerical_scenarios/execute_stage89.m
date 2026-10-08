% 第 8–9 步真实执行入口；不导出正文、图表，不替换主选择。
repoRoot=fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
addpath(fullfile(repoRoot,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
set(0,'DefaultFigureVisible','off');
cfg=revision_validation_config();
evidenceRoot=fullfile(cfg.paths.report_root,'validation','numerical_scenarios');
preflight=revision_preflight();
numerical_write_json(fullfile(evidenceRoot,'step89_preflight.json'),preflight);
assert(preflight.passed,'revision:Stage89Preflight','Stage 8–9 preflight failed.');
source=struct('solve',numerical_code_hash('solve'),'assessment',numerical_code_hash('assessment'), ...
    'protocol_hash',cfg.revision.protocol_hash);
numerical_write_json(fullfile(evidenceRoot,'step89_source_fingerprints.json'),source);
modes={'initialization','grid','horizon','threshold'};
for modeIndex=1:numel(modes)
    mode=modes{modeIndex};
    fprintf('STAGE89 MODE START %s\n',mode);
    report=run_revision_validation(mode,false);
    numerical_write_json(fullfile(evidenceRoot,['step89_' mode '_report.json']),report);
    fprintf('STAGE89 MODE END %s status=%s calls=%d cache=%d success=%d failed=%d numeric=%d agreement=%d\n', ...
        mode,report.status,report.solver_calls,report.cache_hits,report.successful_count, ...
        report.failed_count,report.numeric_pass_count,report.agreement_pass_count);
    clear report;
end
fprintf('STAGE89 DEFAULT EXECUTION FINISHED\n');
