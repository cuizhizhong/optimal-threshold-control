function report = verify_revision_preflight()
% 回归检查参数/环境变量优先级、路径恢复和无优化执行。
cfg = numerical_cases_config();
originalPath = path;
originalEnv = getenv('OPENOCL_ROOT');
restoreEnv = onCleanup(@() setenv('OPENOCL_ROOT',originalEnv)); %#ok<NASGU>
setenv('OPENOCL_ROOT','');
ready = revision_preflight();
assert(ready.passed,'默认预检失败：%s',jsonencode(ready.blockers));
assert(~ready.optimization_started);
assert(strcmp(path,originalPath),'预检未恢复 MATLAB path。');
invalidRoot = fullfile(tempdir,'revision-preflight-absent-openocl');
assert(~isfolder(invalidRoot),'测试专用缺失路径意外存在。');
setenv('OPENOCL_ROOT',invalidRoot);
missing = revision_preflight();
assert(~missing.passed && ~missing.checks.openocl.passed);
assert(strcmp(missing.openocl_root,invalidRoot));
assert(~missing.optimization_started && strcmp(path,originalPath));
explicit = revision_preflight(cfg.paths.openocl_root);
assert(explicit.passed && strcmp(explicit.openocl_root,cfg.paths.openocl_root), ...
    '显式参数没有优先于 OPENOCL_ROOT。');
assert(~explicit.optimization_started && strcmp(path,originalPath));
% 模拟干净检出缺少输入及 fixture：入口仍返回报告，不抛出配置读取错误。
isolatedRoot = tempname;
aliasDir = fullfile(isolatedRoot,'project','matlab','numerical_scenarios');
mkdir(aliasDir);
restoreTemporary = onCleanup(@() cleanupTemporary(isolatedRoot,aliasDir)); %#ok<NASGU>
source = fileread(which('revision_preflight'));
source = strrep(source,'function report = revision_preflight(openoclRoot)', ...
    'function report = isolated_revision_preflight(openoclRoot)');
filename = fullfile(aliasDir,'isolated_revision_preflight.m');
fid = fopen(filename,'w','n','UTF-8'); assert(fid >= 0);
fprintf(fid,'%s',source); fclose(fid);
addpath(aliasDir,'-begin');
missingInput = isolated_revision_preflight(cfg.paths.openocl_root);
assert(~missingInput.passed && ~missingInput.checks.inputs.passed && ...
    ~missingInput.checks.checkpoints.passed && ~missingInput.optimization_started);
assert(contains(missingInput.checks.inputs.detail,'scenario_inputs.json') && ...
    contains(missingInput.checks.checkpoints.detail,'--write'));
rmpath(aliasDir);
report = struct('status','tested','tests',4,'optimization_calls',0, ...
    'default_environment',ready.environment,'passed',true);
fprintf('REVISION_PREFLIGHT_TESTS_OK tests=4 optimization_calls=0\n');
end

function cleanupTemporary(root,aliasDir)
if contains([path pathsep],[aliasDir pathsep]), rmpath(aliasDir); end
resolved = char(java.io.File(root).getCanonicalPath());
parent = char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
