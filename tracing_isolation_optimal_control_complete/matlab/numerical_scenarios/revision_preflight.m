function report = revision_preflight(openoclRoot)
% 仅检查依赖和写权限；不初始化 OpenOCL、不下载依赖、不构建或求解 NLP。
% 预检不依赖配置成功读取，使输入缺失时仍返回结构化报告。
here = fileparts(mfilename('fullpath'));
reportRoot = fileparts(fileparts(here));
repoRoot = fileparts(reportRoot);
cfg.paths.report_root = reportRoot;
cfg.paths.openocl_root = fullfile(repoRoot,'optimal','OpenOCL-master 0104');
cfg.paths.data = fullfile(reportRoot,'data','numerical_scenarios');
if nargin < 1 || isempty(openoclRoot)
    openoclRoot = getenv('OPENOCL_ROOT');
    if isempty(openoclRoot), openoclRoot = cfg.paths.openocl_root; end
end
openoclRoot = char(openoclRoot);
oldPath = path;
restorePath = onCleanup(@() path(oldPath)); %#ok<NASGU>
report = struct('schema_version',1,'status','blocked','passed',false, ...
    'optimization_started',false,'checked_utc',utcNow(), ...
    'openocl_root',openoclRoot,'checks',struct(),'blockers',{{}});
report.environment = struct('matlab',version,'matlab_release',version('-release'), ...
    'platform',computer,'openocl','unknown','casadi','unknown','ipopt','unknown');
report.checks.matlab = check(true,version,'');
oclFile = fullfile(openoclRoot,'ocl.m');
hasOcl = isfile(oclFile) && isfolder(fullfile(openoclRoot,'+ocl'));
report.checks.openocl = check(hasOcl,oclFile,'revision:MissingOpenOCL');
if hasOcl
    addpath(openoclRoot);
    report.environment.openocl_path = which('ocl');
    casadiRoot = fullfile(openoclRoot,'Lib','casadi');
    if isfolder(casadiRoot), addpath(casadiRoot); end
else
    report.environment.openocl_path = 'unknown';
end
try
    report.environment.casadi = casadi.CasadiMeta.version();
    report.environment.casadi_path = which('casadi.MX');
    % 建立符号对象也不调用优化器；同时检验 MEX 能否加载。
    probe = casadi.MX.sym('preflight_probe'); %#ok<NASGU>
    clear probe % 在恢复 path 之前销毁 CasADi 对象，保证其析构方法可访问。
    report.checks.casadi = check(true,report.environment.casadi,'');
catch ex
    report.environment.casadi_path = 'unknown';
    report.checks.casadi = check(false,ex.message,ex.identifier);
end
try
    available = logical(casadi.has_nlpsol('ipopt'));
    report.checks.ipopt = check(available, ...
        'casadi.has_nlpsol(''ipopt'')；未建立或调用求解器。','revision:MissingIPOPT');
catch ex
    report.checks.ipopt = check(false,ex.message,ex.identifier);
end
report.environment.ipopt_version_note = ...
    '当前接口未提供已查询的 IPOPT 版本；不从安装目录名推测。';
validationRoot = fullfile(cfg.paths.report_root,'validation','numerical_scenarios');
inputsPath = fullfile(validationRoot,'scenario_inputs.json');
fixturePath = fullfile(validationRoot,'analytic_checkpoints.json');
report.checks.inputs = jsonCheck(inputsPath,'parameters');
report.checks.checkpoints = jsonCheck(fixturePath,'cases');
targets = {validationRoot,fullfile(cfg.paths.data,'runs'), ...
    fullfile(cfg.paths.data,'revision_checks')};
writeChecks = repmat(struct('path','','passed',false,'detail',''),numel(targets),1);
for k = 1:numel(targets)
    writeChecks(k).path = targets{k};
    try
        if ~isfolder(targets{k}), mkdir(targets{k}); end
        probePath = [tempname(targets{k}) '.preflight'];
        fid = fopen(probePath,'w');
        if fid < 0, error('revision:NotWritable','不能写入 %s',targets{k}); end
        fclose(fid);
        delete(probePath);
        writeChecks(k).passed = true;
        writeChecks(k).detail = '临时文件写入和删除成功。';
    catch ex
        writeChecks(k).detail = ex.message;
    end
end
report.write_checks = writeChecks;
report.checks.write_access = check(all([writeChecks.passed]), ...
    'validation、runs 和 revision_checks 的临时写入测试。','revision:NotWritable');
names = fieldnames(report.checks);
for k = 1:numel(names)
    item = report.checks.(names{k});
    if ~item.passed
        report.blockers{end+1} = struct('check',names{k}, ...
            'identifier',item.identifier,'detail',item.detail); %#ok<AGROW>
    end
end
report.passed = isempty(report.blockers);
if report.passed, report.status = 'completed'; end
if nargout == 0, disp(jsonencode(report,'PrettyPrint',true)); end
end

function out = check(passed,detail,identifier)
if passed, identifier = ''; end
out = struct('passed',logical(passed),'detail',char(detail),'identifier',identifier);
end

function out = jsonCheck(filename,requiredField)
if ~isfile(filename)
    if strcmp(requiredField,'cases')
        detail = [filename ' 缺失；请运行 generate_analytic_checkpoints.py --write。'];
    else
        detail = [filename ' 缺失；请从当前提交恢复 scenario_inputs.json 原始输入源。'];
    end
    out = check(false,detail, ...
        'revision:MissingInput');
    return
end
try
    data = jsondecode(fileread(filename));
    assert(isfield(data,requiredField),'revision:InvalidInput', ...
        'JSON 缺少字段 %s：%s',requiredField,filename);
    if strcmp(requiredField,'parameters')
        numerical_cases_config(filename); % 检查共享输入的参数、case_id 和初值。
    else
        assert(isstruct(data.cases) && ~isempty(data.cases) && ...
            all(isfield(data.cases,{'case_id','J_reference'})), ...
            'revision:InvalidInput','解析检查点案例字段无效：%s',filename);
    end
    out = check(true,filename,'');
catch ex
    out = check(false,ex.message,ex.identifier);
end
end

function value = utcNow()
value = char(datetime('now','TimeZone','UTC','Format',"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"));
end
