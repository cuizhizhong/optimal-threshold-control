function [run,activity] = execute_numerical_run(request,provenance,dataRoot,solver,assessor,assessmentSpec,force)
% 缓存只从索引中的可信成功原始记录读取。mock测试使用同一实现。
% solver(request)返回原始输出；assessor(run)返回reference/assessment视图。
if nargin<7, force=false; end
assert(isfield(provenance,'solve_code_hash') && isfield(provenance,'environment_fingerprint'));
payload=struct('case_id',request.case_id,'parameters',request.parameters,'x0',request.x0(:), ...
    'solver_settings',request.solver_settings,'actual_solver_settings',request.actual_solver_settings, ...
    'actual_grid',request.actual_grid,'initialization',request.initialization, ...
    'initial_guess',request.initial_guess,'solve_code_hash',provenance.solve_code_hash, ...
    'environment_fingerprint',provenance.environment_fingerprint);
fingerprint=numerical_sha256(payload);
folder=fullfile(dataRoot,'runs'); if ~isfolder(folder), mkdir(folder); end
indexFile=fullfile(dataRoot,'run_index.json');
index=readindex(indexFile);
activity=struct('cache_hit',false,'solver_called',false,'assessment_called',false);
if ~force
    for k=numel(index.entries):-1:1
        entry=index.entries(k);
        if ~entry.success || ~strcmp(entry.source_status,'verified_record') || ...
                ~strcmp(entry.solve_fingerprint,fingerprint), continue; end
        filename=fullfile(dataRoot,entry.raw_file);
        if ~isfile(filename), continue; end
        assert(strcmp(numerical_sha256(filename,'file'),entry.raw_sha256), ...
            'numerical:RawRecordModified','Immutable raw record has changed: %s',filename);
        loaded=load(filename,'run'); candidate=loaded.run;
        if trusted(candidate,fingerprint) && strcmp(candidate.run_id,entry.run_id)
            run=candidate; activity.cache_hit=true; break;
        end
    end
end
if ~activity.cache_hit
    attempt=1;
    for k=1:numel(index.entries)
        if strcmp(index.entries(k).solve_fingerprint,fingerprint), attempt=max(attempt,index.entries(k).attempt+1); end
    end
    runId=['run_' strrep(char(java.util.UUID.randomUUID()),'-','')];
    provenance.solve_started_utc=numerical_utc();
    thrown=[]; activity.solver_called=true;
    try
        run=solver(request);
    catch exception
        thrown=exception;
        run=struct('success',false,'return_status','exception','solver_info',[], ...
            'failure',struct('message',exception.message,'identifier',exception.identifier, ...
            'stack',exception.stack));
    end
    % 这些字段来自实际求解请求，不能由solver或后处理改写来源。
    fields={'case_id','parameters','x0','solver_settings','actual_solver_settings', ...
        'actual_grid','initialization','initial_guess'};
    for k=1:numel(fields), run.(fields{k})=request.(fields{k}); end
    run.run_id=runId; run.attempt=attempt; run.solve_fingerprint=fingerprint;
    run.solve_fingerprint_payload=payload; run.provenance=provenance;
    run.provenance.solve_finished_utc=numerical_utc();
    run.source_status='verified_record';
    run.environment=provenance.environment;
    rawFile=fullfile('runs',[runId '.mat']); filename=fullfile(dataRoot,rawFile);
    assert(~isfile(filename),'numerical:RunCollision','Refusing to overwrite raw run: %s',filename);
    save(filename,'run','-v7');
    entry=struct('run_id',runId,'attempt',attempt,'case_id',request.case_id, ...
        'solve_fingerprint',fingerprint,'success',logical(run.success), ...
        'source_status',run.source_status,'raw_file',strrep(rawFile,'\','/'), ...
        'raw_sha256',numerical_sha256(filename,'file'), ...
        'solve_started_utc',provenance.solve_started_utc);
    if isempty(index.entries), index.entries=entry; else, index.entries(end+1)=entry; end
    numerical_write_json(indexFile,index);
    if ~isempty(thrown), rethrow(thrown); end
end
if run.success
    [run,activity.assessment_called]=assess_saved_numerical_run(run,dataRoot,assessor,assessmentSpec,false);
end
end

function yes=trusted(run,fingerprint)
yes=isfield(run,'run_id') && isfield(run,'provenance') && ...
    isfield(run,'source_status') && strcmp(run.source_status,'verified_record') && ...
    isfield(run,'solve_fingerprint') && strcmp(run.solve_fingerprint,fingerprint) && ...
    isfield(run.provenance,'solve_started_utc') && isfield(run.provenance,'solve_commit') && ...
    isfield(run.provenance,'solve_code_hash') && isfield(run.provenance,'solve_dirty') && run.success;
end

function index=readindex(filename)
index=struct('schema_version',1,'entries',[]);
if isfile(filename)
    index=jsondecode(fileread(filename));
    assert(index.schema_version==1,'Unsupported run index schema.');
end
end
