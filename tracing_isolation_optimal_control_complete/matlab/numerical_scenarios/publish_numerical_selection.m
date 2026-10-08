function manifest = publish_numerical_selection(runs,dataRoot,reason)
% 显式选择产生兼容副本；原始runs文件永不修改。
assert(numel(runs)==5,'A main selection must contain E1--E5.');
index=jsondecode(fileread(fullfile(dataRoot,'run_index.json')));
entries=repmat(struct('case_id','','run_id','','solve_fingerprint','', ...
    'raw_file','','raw_sha256','','assessment_fingerprint','','compatibility_file','', ...
    'compatibility_sha256','','reason',''),1,5);
selectedUtc=numerical_utc();
for k=1:5
    run=runs{k}; id=sprintf('E%d',k);
    assert(strcmp(run.case_id,id) && run.success && strcmp(run.source_status,'verified_record'), ...
        'numerical:UntrustedSelection','Only trusted successful E1--E5 runs may be selected.');
    ix=find(strcmp({index.entries.run_id},run.run_id)); assert(isscalar(ix)); raw=index.entries(ix);
    assert(strcmp(raw.solve_fingerprint,run.solve_fingerprint) && raw.success);
    rawPath=fullfile(dataRoot,raw.raw_file);
    assert(strcmp(numerical_sha256(rawPath,'file'),raw.raw_sha256));
    run.selection_provenance=struct('selected_utc',selectedUtc,'reason',reason);
    compatibility=[id '.mat']; filename=fullfile(dataRoot,compatibility);
    % 替换旧兼容文件前按原始字节归档；无来源元数据的历史结果仍是legacy。
    if isfile(filename)
        legacy=fullfile(dataRoot,'legacy_results'); if ~isfolder(legacy), mkdir(legacy); end
        archived=fullfile(legacy,[id '_' numerical_sha256(filename,'file') '.mat']);
        if ~isfile(archived), copyfile(filename,archived); end
    end
    temporary=[tempname(dataRoot) '.mat']; save(temporary,'run','-v7');
    [ok,message]=movefile(temporary,filename,'f'); assert(ok,'%s',message);
    entries(k)=struct('case_id',id,'run_id',run.run_id,'solve_fingerprint',run.solve_fingerprint, ...
        'raw_file',raw.raw_file,'raw_sha256',raw.raw_sha256, ...
        'assessment_fingerprint',run.assessment_fingerprint,'compatibility_file',compatibility, ...
        'compatibility_sha256',numerical_sha256(filename,'file'),'reason',reason);
end
manifest=struct('schema_version',1,'selected_utc',selectedUtc,'selection_reason',reason,'entries',entries);
numerical_write_json(fullfile(dataRoot,'selection_manifest.json'),manifest);
load_selected_numerical_runs(dataRoot);
end
