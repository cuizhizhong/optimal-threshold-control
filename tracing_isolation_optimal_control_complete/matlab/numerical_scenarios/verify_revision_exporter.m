function report = verify_revision_exporter()
% 每个失败场景只写临时 tex/data；断言清除旧通过内容，不触碰正式正文和原始结果。
cfg=numerical_cases_config(); root=tempname; mkdir(root);
cleanup=onCleanup(@() cleanup_temporary(root)); %#ok<NASGU>
cfg.paths.data=fullfile(root,'data'); mkdir(cfg.paths.data);
cfg.paths.latex=fullfile(root,'latex'); mkdir(cfg.paths.latex);
tex=fullfile(cfg.paths.latex,'main.tex'); tests={};
for scenario={'missing','failed','provenance_changed'}
    write_stale(tex);
    if ~strcmp(scenario{1},'missing'), write_selection(cfg.paths.data,scenario{1}); end
    before=fileread(tex); caught=false;
    try
        export_numerical_latex(cfg);
    catch exception
        if strcmp(scenario{1},'missing')
            caught=strcmp(exception.identifier,'numerical:MissingSelectionManifest');
        elseif strcmp(scenario{1},'failed')
            caught=contains(exception.message,'Untrusted selected run: E1');
        else
            caught=contains(exception.message,'Solve provenance was changed in compatibility copy.');
        end
    end
    after=fileread(tex);
    assert(caught && contains(after,'\NumResultsVerifiedfalse') && ...
        ~contains(after,'\NumResultsVerifiedtrue') && ~contains(after,'OLD_PASSED_SENTINEL'));
    assert(contains(after,'\providecommand{\NumJOclEOne}{--}') && ...
        contains(after,'\providecommand{\NumOverallFinding}{}'));
    assert(contains(after,'UNTOUCHED_THEORY_SENTINEL') && ...
        contains(after,'UNCHANGED_REFERENCE_SENTINEL') && contains(before,sprintf('\r\n')) && ...
        contains(after,sprintf('\r\n')));
    tests{end+1}=['export_failure_clears_stale_pass_' scenario{1}]; %#ok<AGROW>
end
report=struct('passed',true,'tests',{tests},'test_count',numel(tests), ...
    'actual_optimizer_calls',0,'formal_tex_modified',false);
fprintf('REVISION_EXPORTER_TESTS_OK tests=%d actual_optimizer=0\n',numel(tests));
end

function write_stale(filename)
nl=sprintf('\r\n');
text=strjoin({'UNTOUCHED_THEORY_SENTINEL', ...
    '% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES','UNCHANGED_REFERENCE_SENTINEL', ...
    '% END AUTO-GENERATED NUMERICAL REFERENCE VALUES', ...
    '% BEGIN AUTO-GENERATED NUMERICAL RESULTS','\NumResultsVerifiedtrue', ...
    '\providecommand{\NumOverallFinding}{OLD_PASSED_SENTINEL}', ...
    '% END AUTO-GENERATED NUMERICAL RESULTS','UNTOUCHED_THEORY_SENTINEL'},nl);
fid=fopen(filename,'w','n','UTF-8'); assert(fid>=0); fprintf(fid,'%s',text); fclose(fid);
end

function write_selection(dataRoot,scenario)
rawRoot=fullfile(dataRoot,'runs'); if ~isfolder(rawRoot), mkdir(rawRoot); end
entries=struct([]);
for k=1:5
    id=sprintf('E%d',k); run=struct('case_id',id,'success',true, ...
        'source_status','verified_record','run_id',['synthetic_export_' id], ...
        'solve_fingerprint',['synthetic_solve_' id], ...
        'assessment_fingerprint',['synthetic_assessment_' id], ...
        'provenance',struct('solve_commit','synthetic_test_only'));
    rawFile=fullfile('runs',[run.run_id '.mat']);
    save(fullfile(dataRoot,rawFile),'run','-v7');
    if k==1
        if strcmp(scenario,'failed'), run.success=false;
        else, run.provenance.solve_commit='deliberately_changed_solve_origin'; end
    end
    compatibility=[id '.mat']; save(fullfile(dataRoot,compatibility),'run','-v7');
    row=struct('case_id',id,'run_id',run.run_id, ...
        'solve_fingerprint',run.solve_fingerprint,'assessment_fingerprint',run.assessment_fingerprint, ...
        'compatibility_file',compatibility,'raw_file',rawFile, ...
        'compatibility_sha256',numerical_sha256(fullfile(dataRoot,compatibility),'file'), ...
        'raw_sha256',numerical_sha256(fullfile(dataRoot,rawFile),'file'));
    if isempty(entries), entries=row; else, entries(k)=row; end %#ok<AGROW>
end
numerical_write_json(fullfile(dataRoot,'selection_manifest.json'),struct('schema_version',1,'entries',entries));
end

function cleanup_temporary(root)
resolved=char(java.io.File(root).getCanonicalPath()); parent=char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
