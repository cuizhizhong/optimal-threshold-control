% 在候选临时检出内复核缓存、后处理与一个接口smoke；不把smoke计入科学结果。
v=fileparts(mfilename('fullpath'));
project=fileparts(fileparts(v));
repoRoot=fileparts(project); cd(repoRoot);
addpath(fullfile(project,'matlab','numerical_scenarios'));
cfg=numerical_cases_config();
preflight=revision_preflight();
numerical_write_json(fullfile(v,'step1011_clean_preflight.json'),preflight);
assert(preflight.passed,'stage1011:CleanPreflightFailed','Clean checkout preflight failed.');
unit=run_revision_validation('unit',false);
numerical_write_json(fullfile(v,'step1011_clean_unit_report.json'),unit);
savedRegression=verify_saved_result_exporter();
numerical_write_json(fullfile(v,'step1011_clean_saved_exporter_report.json'),savedRegression);
allReport=run_revision_validation('all',false);
numerical_write_json(fullfile(v,'step1011_clean_all_report.json'),allReport);
assert(allReport.solver_calls==0 && allReport.cache_hits==35, ...
    'stage1011:CacheMismatch','Expected 35 trusted caches and no new scientific solve.');
assert(allReport.protocol_complete && ~allReport.consistency_pass, ...
    'stage1011:UnexpectedConsistency','Completed protocol retains its measured failed consistency.');
make_numerical_figures();
first=export_numerical_latex();
mainHash=numerical_sha256(fullfile(cfg.paths.latex,'main.tex'),'file');
export_numerical_latex();
assert(strcmp(mainHash,numerical_sha256(fullfile(cfg.paths.latex,'main.tex'),'file')));
% 外部依赖只使用明确的 OPENOCL_ROOT；preflight 已实际检查接口。
addpath(cfg.paths.openocl_root,fullfile(cfg.paths.openocl_root,'Lib','casadi'));
setenv('OCL_CASADI_SETUP','true');
settings=cfg.solve; settings.T=1; settings.N=4;
initialization=struct('type','constant_control','control',.7);
prepared=prepare_openocl_case(cfg.parameters,cfg.safe_check.x0,settings,initialization);
smoke=solve_openocl_case(cfg.parameters,cfg.safe_check.x0,settings,initialization,prepared);
save(fullfile(v,'step1011_smoke_interface.mat'),'smoke','-v7');
numerical_write_json(fullfile(v,'step1011_smoke_report.json'),struct( ...
    'success',smoke.success,'return_status',smoke.return_status, ...
    'output_validation',smoke.output_validation,'T',1,'N',4,'d',settings.d, ...
    'optimizer_executions',1,'scientific_evidence',false, ...
    'purpose','Small interface smoke only; excluded from the 35 scientific configurations.'));
assert(smoke.success && smoke.output_validation.passed,'stage1011:SmokeFailed','Interface smoke solve failed.');
out=struct('status','completed','preflight_passed',preflight.passed, ...
    'unit_passed',unit.protocol_complete,'saved_exporter_regression',savedRegression, ...
    'scientific_optimizer_executions',allReport.solver_calls, ...
    'trusted_cache_hits',allReport.cache_hits,'protocol_complete',allReport.protocol_complete, ...
    'consistency_pass',allReport.consistency_pass,'successful_cached_runs',allReport.successful_count, ...
    'numeric_pass_count',allReport.numeric_pass_count,'agreement_pass_count',allReport.agreement_pass_count, ...
    'smoke_optimizer_executions',1,'smoke_passed',smoke.success, ...
    'postprocess_export',first,'export_idempotent',true,'checked_utc',numerical_utc());
numerical_write_json(fullfile(v,'step1011_clean_report.json'),out);
fprintf('STAGE1011_CLEAN_OK cache=%d scientific_optimizer=%d smoke_optimizer=1 consistency=%d\n', ...
    allReport.cache_hits,allReport.solver_calls,allReport.consistency_pass);
