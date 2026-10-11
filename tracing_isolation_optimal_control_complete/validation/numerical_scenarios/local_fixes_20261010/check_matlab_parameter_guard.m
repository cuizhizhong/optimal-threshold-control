function check_matlab_parameter_guard()
% 只调用配置入口，核对参数拒绝行为，不加载求解器或运行优化。
repoRoot = 'E:\work\optimal-threshold-control';
scenarioRoot = fullfile(repoRoot, 'tracing_isolation_optimal_control_complete');
sourceRoot = fullfile(scenarioRoot, 'matlab', 'numerical_scenarios');
testRoot = fullfile(repoRoot, 'tmp', 'local_fixes_20261010');
inputRoot = fullfile(testRoot, 'matlab_parameter_inputs');
if ~isfolder(inputRoot), mkdir(inputRoot); end
addpath(sourceRoot);
inputPath = fullfile(scenarioRoot, 'validation', 'numerical_scenarios', 'scenario_inputs.json');
inputText = fileread(inputPath);
cfg = numerical_cases_config(inputPath);
assert(isequal([cfg.parameters.p cfg.parameters.c cfg.parameters.gamma cfg.parameters.K], ...
    [0.5 2.0 0.3 0.15]));
assert(strcmp(cfg.status, 'configured') && numel(cfg.cases) == 5);
fprintf('PASS: current shared configuration loads without optimization.\n');

fields = {'p', 'c', 'gamma', 'K'};
nonfiniteLabels = {'NaN', 'positive_Inf', 'negative_Inf'};
candidateTokens = {{'NaN', '[null]'}, {'Infinity', '1e999'}, {'-Infinity', '-1e999'}};
selectedTokens = cell(size(candidateTokens));
for kind = 1:numel(candidateTokens)
    for candidate = candidateTokens{kind}
        try
            probe = jsondecode(['{"value":' candidate{1} '}']);
            value = probe.value;
            matches = isnumeric(value) && isscalar(value) && ...
                ((kind == 1 && isnan(value)) || ...
                 (kind == 2 && isinf(value) && value > 0) || ...
                 (kind == 3 && isinf(value) && value < 0));
            if matches, selectedTokens{kind} = candidate{1}; break; end
        catch
            % 尝试下一个能由当前 MATLAB 解码为对应浮点值的 JSON 表达。
        end
    end
    assert(~isempty(selectedTokens{kind}), 'No supported JSON token for %s.', nonfiniteLabels{kind});
    fprintf('JSON token for %s: %s\n', nonfiniteLabels{kind}, selectedTokens{kind});
end

tested = 0;
for field = fields
    for kind = 1:numel(selectedTokens)
        testInput(field{1}, selectedTokens{kind}, nonfiniteLabels{kind});
    end
end
boundaryFields = {'p', 'p', 'p', 'p', 'c', 'c', 'gamma', 'gamma', 'K', 'K', 'K', 'K'};
boundaryValues = {'0', '1', '-0.1', '1.1', '0', '-1', '0', '-1', '0', '1', '-0.1', '1.1'};
for k = 1:numel(boundaryFields)
    testInput(boundaryFields{k}, boundaryValues{k}, ['boundary_' num2str(k)]);
end
fprintf('PASS: all %d invalid parameter inputs rejected with numerical_cases_config:InvalidParameters.\n', tested);

messages = checkcode(fullfile(sourceRoot, 'numerical_cases_config.m'), '-id');
fprintf('CHECKCODE: %d message(s).\n', numel(messages));
for k = 1:numel(messages)
    fprintf('line %d: %s\n', messages(k).line, messages(k).message);
end
baselinePath = fullfile(testRoot, 'baseline', 'matlab', 'numerical_scenarios', 'numerical_cases_config.m');
baselineMessages = checkcode(baselinePath, '-id');
assert(isequal({messages.message}, {baselineMessages.message}));
fprintf('PASS: CHECKCODE message text is unchanged from the pre-edit baseline (%d message(s)).\n', ...
    numel(baselineMessages));
save(fullfile(testRoot, 'matlab_parameter_guard_results.mat'), ...
    'selectedTokens', 'tested', 'messages', 'baselineMessages');

    function testInput(field, token, label)
        pattern = ['"' field '"\s*:\s*[-+0-9.eE]+'];
        replacedText = regexprep(inputText, pattern, ['"' field '": ' token], 'once');
        assert(~strcmp(replacedText, inputText), 'Fixture replacement failed for %s.', field);
        fixturePath = fullfile(inputRoot, [field '_' label '.json']);
        fid = fopen(fixturePath, 'w', 'n', 'UTF-8');
        assert(fid >= 0, 'Cannot create test fixture.');
        cleanup = onCleanup(@() fclose(fid));
        fwrite(fid, replacedText, 'char');
        clear cleanup;
        try
            numerical_cases_config(fixturePath);
        catch err
            assert(strcmp(err.identifier, 'numerical_cases_config:InvalidParameters'), ...
                'Wrong error for %s=%s: %s', field, token, err.identifier);
            assert(contains(err.message, 'must be finite and satisfy 0<p<1, c>0, gamma>0, and 0<K<1.'));
            fprintf('PASS: %s=%s -> %s\n', field, token, err.identifier);
            tested = tested + 1;
            return;
        end
        error('Parameter %s=%s was not rejected.', field, token);
    end
end
