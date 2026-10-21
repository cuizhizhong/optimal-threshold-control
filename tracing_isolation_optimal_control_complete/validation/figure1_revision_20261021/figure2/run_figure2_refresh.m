function report=run_figure2_refresh()
% 本轮只执行图形重导出和已有数据的 LaTeX 导出；不调用求解入口。
here=fileparts(mfilename('fullpath'));
target=fullfile(here,'refresh_report.json');
assert(~isfile(target),'This recorded figure refresh must not be overwritten.');
cfg=numerical_cases_config();
before=fileread(fullfile(here,'before','latex','main.tex'));
make_numerical_figures();
r=export_numerical_latex();
assert(r.verified && r.optimizer_executions==0);
after=fileread(fullfile(cfg.paths.latex,'main.tex'));
assert(strcmp(before,after),'Figure refresh changed formal LaTeX content.');
source=numerical_code_hash('figure');
report=struct('status','completed','verified',r.verified, ...
    'optimizer_executions',r.optimizer_executions,'scientific_solves',0, ...
    'formal_latex_content_unchanged',true,'figure_code_hash',source.hash, ...
    'selected_run_ids',{{r.selection_manifest.entries.run_id}});
numerical_write_json(target,report);
fprintf('FIGURE2_REFRESH_OK verified=1 optimizer=0 scientific_solves=0 latex_unchanged=1\n');
end
