function report=verify_saved_result_exporter()
% 复制已有数据到临时目录做导出回归；修改仅为故障注入，不作为科学证据。
cfg=numerical_cases_config(); source=cfg.paths.data; sourceTex=fullfile(cfg.paths.latex,'main.tex'); root=tempname; mkdir(root);
cleanup=onCleanup(@() cleanup_temporary(root)); %#ok<NASGU>
cfg.paths.data=fullfile(root,'data'); cfg.paths.latex=fullfile(root,'latex'); mkdir(cfg.paths.latex);
copyfile(source,cfg.paths.data);
tex=fullfile(cfg.paths.latex,'main.tex'); copyfile(sourceTex,tex);
before=fileread(tex); report1=export_numerical_latex(cfg); first=fileread(tex);
report2=export_numerical_latex(cfg); second=fileread(tex);
assert(strcmp(first,second),'Saved-data re-export changed LaTeX bytes.');
assert(report1.optimizer_executions==0 && report2.optimizer_executions==0);
assert(report1.verified && report1.robustness.protocol_complete && ~report1.robustness.consistency_pass);
assert(report1.robustness.recorded_configuration_count==report1.robustness.expected_configuration_count);
assert(contains(first,'\NumResultsVerifiedtrue') && contains(first,'\NumRobustnessCompletetrue'));
assert(contains(first,'\renewcommand{\NumRobustnessStatement}{') && ...
    contains(first,'E2、E4 未通过') && ~contains(first,'NaN'));
assert(strcmp(without_blocks(before),without_blocks(first)),'Exporter changed non-generated text.');
tests={'saved_data_reexport_identical','independent_protocol_and_consistency','no_NaN_or_legacy_neutral_claim', ...
    'non_generated_text_unchanged'};
% 缺少附加组时保留主结果状态，独立附加开关刷新为 false。
summaryPath=fullfile(cfg.paths.data,'revision_checks','grid_summary.json'); saved=fileread(summaryPath);
delete(summaryPath); partial=export_numerical_latex(cfg); text=fileread(tex);
assert(partial.verified && ~partial.robustness.protocol_complete && ...
    contains(text,'\NumRobustnessCompletefalse') && contains(text,'尚无结果的组为 \texttt{grid}'));
write_text(summaryPath,saved); tests{end+1}='missing_robustness_keeps_main_independent';
% 已完成初猜组故障不得继承上一轮的全通过说明。
path=fullfile(cfg.paths.data,'revision_checks','initialization_summary.json'); savedInit=fileread(path);
value=jsondecode(savedInit); value.consistency_pass=false; value.status='failed';
value.case_comparisons(1).consistency_pass=false;
numerical_write_json(path,value); failed=export_numerical_latex(cfg); text=fileread(tex);
assert(failed.robustness.protocol_complete && ~failed.robustness.consistency_pass && ...
    contains(text,'初猜复核未全部支持一致性') && ~contains(text,'五例常值和固定种子随机初猜的阶段一致'));
write_text(path,savedInit); tests{end+1}='failed_summary_removes_old_pass_claim';
% 故意修改摘要的来源，必须报错且原 true 和所有结论被清除。
value=jsondecode(savedInit); value.rows(1).solve_fingerprint='deliberately_wrong_source';
numerical_write_json(path,value); caught=false;
try, export_numerical_latex(cfg);
catch exception, caught=strcmp(exception.identifier,'numerical:RevisionSourceMismatch'); end
text=fileread(tex);
assert(caught && contains(text,'\NumResultsVerifiedfalse') && ...
    contains(text,'\NumRobustnessCompletefalse') && ~contains(text,'五例常值'));
write_text(path,savedInit); tests{end+1}='changed_summary_origin_clears_stale_success';
% blocked 摘要尚无实验行：清除旧附加结论，五例主结果仍独立验证。
groups={'initialization','grid','horizon','threshold'}; savedSummaries=cell(size(groups));
for k=1:numel(groups)
    path=fullfile(cfg.paths.data,'revision_checks',[groups{k} '_summary.json']);
    savedSummaries{k}=fileread(path);
    numerical_write_json(path,struct('schema_version',1,'status','blocked','rows',[], ...
        'consistency_pass',false,'protocol_complete',false));
end
pending=export_numerical_latex(cfg); text=fileread(tex);
assert(pending.verified && ~pending.robustness.protocol_complete && ...
    contains(text,'\NumRobustnessCompletefalse') && ...
    contains(text,'\renewcommand{\NumRobustnessStatement}{}') && ~contains(text,'NaN'));
for k=1:numel(groups)
    write_text(fullfile(cfg.paths.data,'revision_checks',[groups{k} '_summary.json']),savedSummaries{k});
end
tests{end+1}='blocked_empty_rows_keep_new_results_empty';
% 原始证据被改写时，即使主兼容文件仍存在也不能导出通过。
manifest=jsondecode(fileread(fullfile(cfg.paths.data,'selection_manifest.json')));
raw=fullfile(cfg.paths.data,manifest.entries(1).raw_file);
fid=fopen(raw,'a'); assert(fid>=0); fwrite(fid,uint8(1),'uint8'); fclose(fid);
caught=false; try, export_numerical_latex(cfg); catch, caught=true; end
assert(caught && contains(fileread(tex),'\NumResultsVerifiedfalse'));
tests{end+1}='changed_raw_hash_clears_stale_success';
report=struct('passed',true,'tests',{tests},'test_count',numel(tests), ...
    'actual_optimizer_calls',0,'formal_tex_modified',false, ...
    'recorded_configurations',report1.robustness.recorded_configuration_count, ...
    'numeric_and_agreement_pass_count',report1.robustness.numeric_and_agreement_pass_count);
fprintf('SAVED_RESULT_EXPORTER_TESTS_OK tests=%d actual_optimizer=0\n',numel(tests));
end

function text=without_blocks(text)
for marker={'NUMERICAL REFERENCE VALUES','NUMERICAL RESULTS'}
    begin=['% BEGIN AUTO-GENERATED ' marker{1}]; ending=['% END AUTO-GENERATED ' marker{1}];
    first=strfind(text,begin); last=strfind(text,ending); assert(isscalar(first) && isscalar(last));
    text=[text(1:first-1) text(last+numel(ending):end)];
end
end
function write_text(path,text)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); fprintf(fid,'%s',text); fclose(fid);
end
function cleanup_temporary(root)
resolved=char(java.io.File(root).getCanonicalPath()); parent=char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
