function report = verify_reference_dependency_tests()
% 验证 JSON 顺序无关性及缺失、重复、篡改 fixture 时的严格失败。
cfg = numerical_cases_config();
testRoot = fullfile(cfg.paths.report_root,'validation','numerical_scenarios');
taskDir = tempname(testRoot); mkdir(taskDir);
cleanup = onCleanup(@() cleanupTestFiles(taskDir)); %#ok<NASGU>
fixture = jsondecode(fileread(cfg.paths.analytic_checkpoints));
fixture.cases = fixture.cases(end:-1:1);
path = fullfile(taskDir,'reversed_fixture.json'); writeJson(path,fixture);
baseline = verify_numerical_reference();
reversed = verify_numerical_reference(path);
assert(baseline.verified && reversed.verified && baseline.case_count == reversed.case_count);

inputs = jsondecode(fileread(cfg.paths.scenario_inputs));
inputs.cases = inputs.cases(end:-1:1);
inputPath = fullfile(taskDir,'reversed_inputs.json'); writeJson(inputPath,inputs);
other = numerical_cases_config(inputPath);
assert(isequal(cfg.parameters,other.parameters) && isequal(cfg.cases,other.cases) && ...
    isequal(cfg.safe_check,other.safe_check));

missingPath = fullfile(taskDir,'missing_fixture.json');
try
    verify_numerical_reference(missingPath);
    error('verify_reference_dependency_tests:UnexpectedSuccess','Missing fixture passed.');
catch err
    assert(strcmp(err.identifier,'verify_numerical_reference:MissingFixture'));
    assert(contains(err.message,missingPath) && contains(err.message,'generate_analytic_checkpoints.py --write'));
end
bad = fixture; bad.cases(1).case_id = bad.cases(2).case_id;
path = fullfile(taskDir,'duplicate_fixture.json'); writeJson(path,bad);
assertFailure(path,'verify_numerical_reference:FixtureCases');
bad = fixture; index = find(strcmp({bad.cases.case_id},'E1'));
bad.cases(index).s0 = bad.cases(index).s0+1e-5;
path = fullfile(taskDir,'changed_initial.json'); writeJson(path,bad);
assertFailure(path,'verify_numerical_reference:FixtureMismatch');
bad = fixture; bad.cases(index).J_reference = bad.cases(index).J_reference+1e-5;
path = fullfile(taskDir,'changed_cost.json'); writeJson(path,bad);
assertFailure(path,'verify_numerical_reference:FixtureMismatch');
report = struct('passed',true,'test_count',6,'optimizer_executions',0, ...
    'max_cost_error',baseline.max_cost_error,'max_release_time_error',baseline.max_release_time_error);
fprintf('REFERENCE_DEPENDENCY_TESTS_OK tests=%d optimizer_executions=0\n',report.test_count);
end

function assertFailure(path,id)
try
    verify_numerical_reference(path);
    error('verify_reference_dependency_tests:UnexpectedSuccess','Changed fixture passed.');
catch err
    assert(strcmp(err.identifier,id),'Unexpected failure: %s',err.message);
end
end

function writeJson(path,value)
fid = fopen(path,'w'); assert(fid >= 0); close = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value));
end

function cleanupTestFiles(path)
% 只删除本函数明确创建的临时文件，不递归删除目录。
files = {'reversed_fixture.json','reversed_inputs.json','duplicate_fixture.json', ...
    'changed_initial.json','changed_cost.json'};
for k = 1:numel(files)
    file = fullfile(path,files{k});
    if isfile(file), delete(file); end
end
if isfolder(path), rmdir(path); end
end
