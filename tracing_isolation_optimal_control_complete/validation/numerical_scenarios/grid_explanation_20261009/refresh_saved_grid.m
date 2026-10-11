function report=refresh_saved_grid()
% 仅刷新网格解释和正文导出；只加载既有评估，不调用求解或重评估入口。
cfg=revision_validation_config(); experiments=cfg.revision.experiments;
folder=fileparts(mfilename('fullpath'));
old=jsondecode(fileread(fullfile(cfg.paths.data,'revision_checks','grid_summary.json')));
assert(strcmp(old.group,'grid') && numel(old.rows)==15);
source=numerical_code_hash('solve'); spec=numerical_assessment_spec(cfg);
index=jsondecode(fileread(fullfile(cfg.paths.data,'run_index.json')));
runs=cell(1,numel(experiments));
selected=find(arrayfun(@(e) any(strcmp(e.groups,'grid')),experiments));
assert(numel(selected)==15);
for ix=selected
    e=experiments(ix); j=find(strcmp({old.rows.configuration_id},e.configuration_id));
    assert(isscalar(j)); row=old.rows(j);
    assert(strcmp(row.case_id,e.case_id) && row.T==e.solver_settings.T && row.N==e.solver_settings.N);
    j=find(strcmp({index.entries.run_id},row.run_id)); assert(isscalar(j)); entry=index.entries(j);
    rawPath=fullfile(cfg.paths.data,entry.raw_file);
    assert(strcmp(numerical_sha256(rawPath,'file'),entry.raw_sha256));
    loaded=load(rawPath,'run'); raw=loaded.run;
    assert(strcmp(raw.run_id,row.run_id) && strcmp(raw.solve_fingerprint,row.solve_fingerprint) && ...
        strcmp(raw.source_status,'verified_record') && strcmp(raw.provenance.solve_code_hash,source.hash));
    assert(strcmp(raw.case_id,e.case_id) && isequaln(raw.parameters,e.parameters) && ...
        isequaln(raw.x0(:),e.x0(:)) && isequaln(raw.solver_settings,e.solver_settings) && ...
        strcmp(raw.initialization.type,e.initialization.type));
    fingerprint=numerical_sha256(struct('solve_fingerprint',raw.solve_fingerprint, ...
        'raw_output_hash',numerical_sha256(raw),'assessment',spec));
    files=dir(fullfile(cfg.paths.data,'revision_checks','assessments',[raw.run_id '_' fingerprint '_*.mat']));
    assert(~isempty(files),'No existing current assessment; stop without reassessment.');
    [~,latest]=max([files.datenum]);
    saved=load(fullfile(files(latest).folder,files(latest).name),'assessment_record'); record=saved.assessment_record;
    assert(strcmp(record.run_id,raw.run_id) && strcmp(record.solve_fingerprint,raw.solve_fingerprint) && ...
        strcmp(record.assessment_fingerprint,fingerprint) && strcmp(record.assessment_provenance.code_hash,spec.code_hash) && ...
        isequaln(record.assessment_settings,spec.settings));
    view=raw; view.reference=record.reference; view.assessment=record.assessment;
    view.assessment_provenance=record.assessment_provenance;
    view.assessment_fingerprint=record.assessment_fingerprint; view.assessment_settings=record.assessment_settings;
    names={'numeric_pass','agreement_pass','capacity_excess','state_discrepancy','tail_max_q','terminal_peak','observed_structure'};
    for j=1:numel(names), assert(isequaln(view.assessment.(names{j}),row.(names{j}))); end
    assert(isequaln(view.J_openocl,row.J_openocl)); runs{ix}=view;
end
unit=verify_grid_comparison_status();
summary=revision_group_summary(cfg,'grid',experiments,runs);
% JSON 读回会改变嵌套向量方向；全字段内容另由 validate_scope.py 核对。
assert(numel(old.rows)==numel(summary.rows) && ...
    ~summary.consistency_pass && strcmp(summary.status,'failed'));
assert(isequal([old.case_comparisons.consistency_pass],[summary.case_comparisons.consistency_pass]));
for id={'E2','E4'}
    item=summary.case_comparisons(strcmp({summary.case_comparisons.case_id},id{1}));
    assert(strcmp(item.comparison_status,'not_evaluated_due_to_numeric_failure') && ...
        item.fine_numeric_pass && ~item.coarse_numeric_pass && ...
        ~item.event_comparison_evaluated && ~item.cost_comparison_evaluated);
end
exported=export_numerical_latex(cfg);
assert(exported.optimizer_executions==0 && exported.verified && ...
    exported.robustness.recorded_configuration_count==35 && ...
    exported.robustness.numeric_and_agreement_pass_count==28 && ~exported.robustness.consistency_pass);
savedExporter=verify_saved_result_exporter();
failureExporter=verify_revision_exporter();
assert(unit.passed && savedExporter.passed && failureExporter.passed);
report=struct('passed',true,'grid_rows_loaded',numel(selected), ...
    'optimizer_executions',0,'assessment_executions',0,'compatibility_publications',0, ...
    'strict_grid_status',summary.status,'strict_grid_consistency_pass',summary.consistency_pass, ...
    'grid_unit',unit,'saved_exporter',savedExporter,'failure_exporter',failureExporter, ...
    'recorded_configurations',exported.robustness.recorded_configuration_count, ...
    'numeric_and_agreement_pass_count',exported.robustness.numeric_and_agreement_pass_count);
numerical_write_json(fullfile(folder,'matlab_report.json'),report);
fprintf('GRID_EXPLANATION_REFRESH_OK records=%d optimizer=0 assessment=0 strict_consistency=0\n',numel(selected));
end
