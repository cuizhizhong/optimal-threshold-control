% 第10--11步：只重新测试、后处理、导出，不重新优化科学结果。
v=fileparts(mfilename('fullpath'));
project=fileparts(fileparts(v));
repoRoot=fileparts(project); cd(repoRoot);
addpath(fullfile(project,'matlab','numerical_scenarios'));
cfg=numerical_cases_config();
preflight=revision_preflight();
numerical_write_json(fullfile(v,'step1011_preflight.json'),preflight);
assert(preflight.passed,'stage1011:PreflightFailed','Preflight failed.');
source=numerical_code_hash('solve');
numerical_write_json(fullfile(v,'step1011_source_fingerprints.json'),struct( ...
    'solve',source,'assessment',numerical_code_hash('assessment'), ...
    'figure',numerical_code_hash('figure'),'export',numerical_code_hash('export')));
unit=verify_revision_validation_unit();
numerical_write_json(fullfile(v,'step1011_unit_report.json'),unit);
regression=verify_revision_exporter();
numerical_write_json(fullfile(v,'step1011_exporter_report.json'),regression);
savedRegression=verify_saved_result_exporter();
numerical_write_json(fullfile(v,'step1011_saved_exporter_report.json'),savedRegression);
mainPath=fullfile(cfg.paths.latex,'main.tex');
before=fileread(mainPath);
first=export_numerical_latex();
once=fileread(mainPath); firstHash=numerical_sha256(mainPath,'file');
second=export_numerical_latex();
assert(strcmp(firstHash,numerical_sha256(mainPath,'file')), ...
    'stage1011:NonIdempotentExport','Repeated main.tex export changed its bytes.');
strip=@(x) regexprep(x,'(?s)% BEGIN AUTO-GENERATED NUMERICAL (REFERENCE VALUES|RESULTS).*?% END AUTO-GENERATED NUMERICAL (REFERENCE VALUES|RESULTS)','');
assert(strcmp(strip(before),strip(once)), ...
    'stage1011:UnexpectedTexEdit','Exporter changed text outside generated blocks.');
make_numerical_figures();
out=struct('status','completed','optimizer_executions',0,'preflight',preflight, ...
    'unit_groups_passed',unit.group_count,'exporter_regression',regression, ...
    'saved_exporter_regression',savedRegression, ...
    'first_export',first,'second_export',second,'export_idempotent',true, ...
    'export_preserves_nongenerated_text',true,'main_tex_sha256',firstHash, ...
    'solve_code_hash',source.hash,'checked_utc',numerical_utc());
numerical_write_json(fullfile(v,'step1011_postprocess_report.json'),out);
fprintf('STAGE1011_POSTPROCESS_OK optimizer=0\n');
