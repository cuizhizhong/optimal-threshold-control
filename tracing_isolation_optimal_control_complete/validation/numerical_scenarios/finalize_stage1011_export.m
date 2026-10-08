% 对最终冻结的导出源码重导出；核对正文一致并更新导出指纹，不重跑已通过测试。
v=fileparts(mfilename('fullpath')); project=fileparts(fileparts(v));
addpath(fullfile(project,'matlab','numerical_scenarios'));
cfg=numerical_cases_config();
before=numerical_sha256(fullfile(cfg.paths.latex,'main.tex'),'file');
clear export_numerical_latex;
first=export_numerical_latex();
assert(strcmp(before,numerical_sha256(fullfile(cfg.paths.latex,'main.tex'),'file')), ...
    'stage1011:FinalExportChangedTex','Final exporter changed the compiled text.');
second=export_numerical_latex();
assert(strcmp(before,numerical_sha256(fullfile(cfg.paths.latex,'main.tex'),'file')));
numerical_write_json(fullfile(v,'step1011_final_export_report.json'),struct( ...
    'first',first,'second',second,'idempotent',true,'compiled_tex_unchanged',true, ...
    'optimizer_executions',0,'final_export_source',numerical_code_hash('export'), ...
    'checked_utc',numerical_utc()));
fprintf('STAGE1011_FINAL_EXPORT_OK optimizer=0 compiled_tex_unchanged=1\n');
