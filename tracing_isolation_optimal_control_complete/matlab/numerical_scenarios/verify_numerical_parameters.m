function report = verify_numerical_parameters()
% 字段兼容、冲突拒绝以及原始指纹保护；不调用优化器、不保存评估。
old=struct('p',0.5,'c',2,'gamma',0.3,'K',0.15);
current=struct('beta',0.5,'c',2,'gamma',0.3,'K',0.15);
assert(isequaln(numerical_normalize_parameters(old),current));
assert(isequaln(numerical_normalize_parameters(current),current));
both=old; both.beta=0.5;
assert(isequaln(numerical_normalize_parameters(both),current));
extra=old; extra.extra=struct('p',17,'r',23);
converted=numerical_normalize_parameters(extra);
assert(isequaln(converted.extra,extra.extra) && isequaln(old.p,0.5));
both.beta=0.6;
mustFail(@() numerical_normalize_parameters(both),'numerical:ConflictingProbability');
mustFail(@() numerical_normalize_parameters(rmfield(old,'p')),'numerical:MissingProbability');
cfg=numerical_cases_config();
index=jsondecode(fileread(fullfile(cfg.paths.data,'run_index.json')));
% 必须使用真正的历史记录，检验新参数计算副本不影响raw/payload自洽校验。
for k=1:numel(index.entries)
    entry=index.entries(k); loaded=load(fullfile(cfg.paths.data,entry.raw_file),'run');
    if isfield(loaded.run.parameters,'p'), raw=loaded.run; break; end
end
assert(exist('raw','var')==1,'Missing historical raw fixture.');
before=numerical_sha256(raw);
out=numerical_run_consistency(raw,current,cfg.check.grid_time_tolerance);
assert(out.provenance_pass && out.problem_pass);
assert(strcmp(before,numerical_sha256(raw)) && isfield(raw.parameters,'p') ...
    && ~isfield(raw.parameters,'beta'));
tampered=raw; tampered.parameters.p=0.6;
out=numerical_run_consistency(tampered,current,cfg.check.grid_time_tolerance);
assert(~out.problem_pass && any(strcmp(out.reasons,'request_does_not_match_output_record')));
report=struct('passed',true,'tests',9,'optimizer_calls',0);
fprintf('NUMERICAL_PARAMETER_COMPATIBILITY_OK tests=9 optimizer=0\n');
end

function mustFail(callback,identifier)
try
    callback();
catch exception
    assert(strcmp(exception.identifier,identifier)); return;
end
error('numerical:ExpectedRejection','Expected rejection: %s.',identifier);
end
