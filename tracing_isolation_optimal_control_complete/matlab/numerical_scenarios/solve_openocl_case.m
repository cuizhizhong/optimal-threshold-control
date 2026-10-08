function run = solve_openocl_case(par,x0,opts,guess,prepared)
% 原直接配点问题；复用缓存检查阶段构建的实际问题和初猜。
if nargin<5, prepared=prepare_openocl_case(par,x0,opts,guess); end
solveClock=tic;
try
    [solution,times,info]=prepared.problem.solve(prepared.ig);
catch exception
    % 求解异常时尽量取得真实接口快照；不把不可读的 info 填成成功或零残差。
    elapsedSeconds=toc(solveClock); info=[];
    infoReason='problem.solve 抛出异常，未返回 info；见 failure 中的原始异常。';
    try
        info=prepared.problem.solver.info();
        infoReason='求解异常后读取的 solver.info 快照未包含此字段；见 failure。';
    catch infoException
        infoReason=[infoReason ' solver.info 也不可读：' infoException.message];
    end
    run=failedRun(prepared,exception,info,elapsedSeconds,infoReason);
    return
end
elapsedSeconds=toc(solveClock);
diagnostics=numerical_solver_diagnostics(info,elapsedSeconds);
solverSuccess=strcmp(diagnostics.success.status,'available') && logical(diagnostics.success.value);
returnStatus='not_available';
if strcmp(diagnostics.return_status.status,'available'), returnStatus=diagnostics.return_status.value; end
run=struct('parameters',par,'x0',x0(:),'solver_settings',prepared.solver_settings, ...
    'actual_solver_settings',prepared.actual_solver_settings,'actual_grid',prepared.actual_grid, ...
    'initialization',prepared.initialization,'initial_guess',prepared.initial_guess, ...
    'success',solverSuccess,'solver_success',solverSuccess, ...
    'return_status',returnStatus,'solver_info',info,'solver_elapsed_seconds',elapsedSeconds, ...
    'solver_info_origin','returned','solver_diagnostics',diagnostics);
run.output_validation=struct('passed',false,'status','failed','reason','');
run.J_openocl=NaN;
try
    run.t_state=reshape(times.states.value,[],1);
    run.s_state=reshape(solution.states.S.value,[],1);
    run.i_state=reshape(solution.states.I.value,[],1);
    run.t_control=reshape(times.controls.value,[],1);
    run.q_control=reshape(solution.controls.q.value,[],1);
    % 与重积分评估器共用同一网格断言，检查时间值及完整数组而非只比较长度。
    grid=validate_numerical_run_grid(run);
    run.dt_control=grid.dt;
    run.J_openocl=par.p*par.c*sum(run.q_control.*grid.dt);
    run.output_validation=struct('passed',true,'status','passed','reason','');
catch exception
    % 已返回的原控制、状态、info 均保留；验证失败不能丢失求解输出。
    run.success=false;
    run.output_validation=struct('passed',false,'status','failed','reason',exception.message, ...
        'failure',failureRecord(exception));
end
% 来源由execute_numerical_run在不可覆盖原始文件中记录。
end

function run=failedRun(prepared,exception,info,elapsedSeconds,infoReason)
diagnostics=numerical_solver_diagnostics(info,elapsedSeconds,infoReason);
infoOrigin='not_returned';
if isstruct(info) && isscalar(info), infoOrigin='exception_snapshot'; end
returnStatus='exception';
if strcmp(diagnostics.return_status.status,'available'), returnStatus=diagnostics.return_status.value; end
solverSuccess=strcmp(diagnostics.success.status,'available') && logical(diagnostics.success.value);
run=struct('parameters',prepared.parameters,'x0',prepared.x0, ...
    'solver_settings',prepared.solver_settings,'actual_solver_settings',prepared.actual_solver_settings, ...
    'actual_grid',prepared.actual_grid,'initialization',prepared.initialization, ...
    'initial_guess',prepared.initial_guess,'success',false,'solver_success',solverSuccess, ...
    'return_status',returnStatus, ...
    'solver_info',info,'solver_elapsed_seconds',elapsedSeconds, ...
    'solver_info_origin',infoOrigin,'solver_info_note',infoReason,'solver_diagnostics',diagnostics, ...
    'failure',failureRecord(exception),'J_openocl',NaN, ...
    'output_validation',struct('passed',false,'status','not_available', ...
    'reason','求解异常，未取得可验证的时间与状态控制数组。'));
end

function record=failureRecord(exception)
record=struct('message',exception.message,'identifier',exception.identifier, ...
    'stack',exception.stack,'report',getReport(exception,'extended','hyperlinks','off'));
end
