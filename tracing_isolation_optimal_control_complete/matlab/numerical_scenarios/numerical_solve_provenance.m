function provenance = numerical_solve_provenance(cfg)
% 版本从运行环境读取；无法读取时为 unknown，不按目录名推断。
source=numerical_code_hash('solve');
environment=struct('matlab',version,'matlab_release',version('-release'), ...
    'platform',computer,'openocl','unknown','openocl_path',which('ocl'), ...
    'casadi','unknown','casadi_path',which('casadi.MX'),'ipopt','unknown');
try, environment.casadi=char(casadi.CasadiMeta.version()); catch, end
% OpenOCL 无版本接口；保存实际依赖代码，而不把目录后缀当版本。
oclRoot=fileparts(which('ocl'));
if ~isempty(oclRoot)
    entries=dir(fullfile(oclRoot,'+ocl','**','*.m'));
    % 示例、测试和其他优化后端不参与当前CasADi/IPOPT问题。
    keep=true(size(entries));
    for k=1:numel(entries)
        relative=strrep(fullfile(entries(k).folder,entries(k).name),'\','/');
        keep(k)=isempty(regexp(relative,'/\+(examples|tests|acados)/','once'));
        if strcmp(entries(k).folder,fullfile(oclRoot,'+ocl'))
            keep(k)=ismember(entries(k).name,{'Problem.m','Stage.m','VarHandler.m', ...
                'DaeHandler.m','Cost.m','Constraint.m','Variable.m'});
        end
    end
    entries=entries(keep);
    oclFiles=repmat(struct('path','','sha256',''),1,numel(entries)+1);
    oclFiles(1)=struct('path','ocl.m','sha256',numerical_sha256(fullfile(oclRoot,'ocl.m'),'file'));
    for k=1:numel(entries)
        filename=fullfile(entries(k).folder,entries(k).name);
        oclFiles(k+1)=struct('path',strrep(filename(numel(oclRoot)+2:end),'\','/'), ...
            'sha256',numerical_sha256(filename,'file'));
    end
    [~,ix]=sort({oclFiles.path}); oclFiles=oclFiles(ix);
    environment.openocl_source_hash=numerical_sha256(oclFiles);
    environment.openocl_source_files=oclFiles;
else
    environment.openocl_source_hash='unknown'; environment.openocl_source_files=[];
end
casadiFile=which('casadiMEX');
environment.casadi_binary_path=casadiFile; environment.casadi_binary_hash='unknown';
if ~isempty(casadiFile), environment.casadi_binary_hash=numerical_sha256(casadiFile,'file'); end
environment.casadi_runtime_files=[];
if ~isempty(casadiFile)
    runtimeRoot=fileparts(casadiFile);
    runtime=[dir(fullfile(runtimeRoot,'+casadi','**','*.m'));dir(fullfile(runtimeRoot,'*.m'))];
    binaryEntries=[dir(fullfile(runtimeRoot,'*.dll'));dir(fullfile(runtimeRoot,'*.so*')); ...
        dir(fullfile(runtimeRoot,'*.dylib'))];
    for k=1:numel(binaryEntries)
        name=binaryEntries(k).name;
        % 当前后端需要core/IPOPT及公共runtime；其他conic/NLP插件不参与。
        if ~startsWith(name,'libcasadi_') || contains(name,'ipopt')
            runtime(end+1)=binaryEntries(k); %#ok<AGROW>
        end
    end
    runtimeFiles=repmat(struct('path','','sha256',''),1,numel(runtime));
    for k=1:numel(runtime)
        filename=fullfile(runtime(k).folder,runtime(k).name);
        runtimeFiles(k)=struct('path',strrep(filename(numel(runtimeRoot)+2:end),'\','/'), ...
            'sha256',numerical_sha256(filename,'file'));
    end
    [~,ix]=sort({runtimeFiles.path}); environment.casadi_runtime_files=runtimeFiles(ix);
end
% 保存实际IPOPT依赖库标识。不存在或版本API不可读时仍保持unknown版本。
environment.ipopt_binary_files=[];
if ~isempty(casadiFile)
    binaryRoot=fileparts(casadiFile);
    entries=[dir(fullfile(binaryRoot,'*ipopt*.dll'));dir(fullfile(binaryRoot,'*ipopt*.so*')); ...
        dir(fullfile(binaryRoot,'*ipopt*.dylib'))];
    binaries=repmat(struct('path','','sha256',''),1,numel(entries));
    for k=1:numel(entries)
        binaries(k)=struct('path',entries(k).name, ...
            'sha256',numerical_sha256(fullfile(entries(k).folder,entries(k).name),'file'));
    end
    environment.ipopt_binary_files=binaries;
end
[ok,commit]=system(sprintf('git -C "%s" rev-parse HEAD',cfg.paths.repo_root));
if ok~=0, commit='unknown'; end
[ok,dirty]=system(sprintf('git -C "%s" status --porcelain --untracked-files=all',cfg.paths.repo_root));
if ok~=0, dirty='unknown'; end
provenance=struct('solve_commit',strtrim(commit),'solve_code_hash',source.hash, ...
    'solve_source_files',source.files,'solve_dirty',~isempty(strtrim(dirty)), ...
    'solve_dirty_details',strtrim(dirty),'environment',environment, ...
    'environment_fingerprint',numerical_sha256(environment),'source_status','verified_record', ...
    'captured_utc',numerical_utc());
end
