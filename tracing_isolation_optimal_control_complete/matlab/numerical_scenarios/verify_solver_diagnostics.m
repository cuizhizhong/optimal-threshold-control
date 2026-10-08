function report = verify_solver_diagnostics()
% 接口与保存路径测试使用 mock；不建立或调用任何 NLP 优化器。
stats=struct('return_status','Solve_Succeeded','success',true,'iter_count',3, ...
    't_wall_my_solver',0.12,'iterations',struct('inf_pr',[1e-2 1e-7 2e-9], ...
    'inf_du',[1e-1 1e-6 3e-8],'mu',[1e-1 1e-5 1e-10], ...
    'alpha_pr',[0.1 0.9 1],'alpha_du',[0.2 0.8 1],'d_norm',[1 0.1 1e-9]));
info=struct('success',true,'timeMeasures',struct('solveTotal',0.14,'solveCasadi',0.13), ...
    'ipopt_stats',stats);
originalInfo=info;
diag=numerical_solver_diagnostics(info,0.15);
assert(isequal(info,originalInfo));
assert(diag.success.value && strcmp(diag.return_status.value,'Solve_Succeeded'));
assert(diag.iteration_count.value==3 && diag.elapsed_seconds.value==0.15);
assert(diag.openocl_solve_total_seconds.value==0.14 && diag.openocl_casadi_solve_seconds.value==0.13);
assert(diag.plugin_wall_seconds.value==0.12);
assert(diag.primal_infeasibility.value==2e-9 && diag.dual_infeasibility.value==3e-8);
assert(isnan(diag.complementarity.value) && strcmp(diag.complementarity.status,'not_available'));
assert(isnan(diag.kkt_residual.value) && strcmp(diag.kkt_certificate_status,'not_available'));
assert(contains(jsonencode(diag.complementarity),'"value":null'));
tests={'known_return_fields_and_final_iteration','raw_info_unmodified', ...
    'barrier_and_step_lengths_not_residuals','missing_values_json_null_with_reason'};

missing=numerical_solver_diagnostics([],NaN,'deliberately absent info');
assert(isnan(missing.iteration_count.value) && strcmp(missing.iteration_count.reason,'deliberately absent info'));
assert(isnan(missing.elapsed_seconds.value) && strcmp(missing.elapsed_seconds.status,'not_available'));
badInfo=info; badInfo.ipopt_stats.iterations.inf_du=[2e-9 NaN];
last=numerical_solver_diagnostics(badInfo,0.15);
assert(isnan(last.dual_infeasibility.value) && strcmp(last.dual_infeasibility.status,'not_available'));
badInfo.ipopt_stats.iterations.inf_pr=[];
last=numerical_solver_diagnostics(badInfo,0.15);
assert(isnan(last.primal_infeasibility.value));
tests{end+1}='absent_or_nonfinite_final_iteration_not_fabricated';

par=struct('p',.5,'c',2,'gamma',.3,'K',.15);
settings=struct('T',1,'N',2,'d',2);
grid=struct('t_state',[0;.2;1],'t_control',[0;.2], ...
    'control_interval_edges',[0;.2;1],'dt_control',[.2;.8]);
initialization=struct('type','mock_interface');
initialGuess=struct('control',[.2;1]);
prepared=struct('problem',struct('solve',@mockOpenOCL),'ig',[], ...
    'parameters',par,'x0',[.75;.01],'solver_settings',settings, ...
    'actual_solver_settings',settings,'actual_grid',grid, ...
    'initialization',initialization,'initial_guess',initialGuess);
run=solve_openocl_case(par,prepared.x0,settings,initialization,prepared);
assert(run.success && run.output_validation.passed && abs(run.J_openocl-.84)<1e-14);
assert(isequal(run.solver_info,info) && isequal(run.dt_control,[.2;.8]));
assert(run.solver_elapsed_seconds>=0 && isfinite(run.solver_elapsed_seconds));
badPrepared=prepared; badPrepared.actual_grid.t_state=[0;.3;1];
badRun=solve_openocl_case(par,prepared.x0,settings,initialization,badPrepared);
assert(~badRun.success && ~badRun.output_validation.passed && isnan(badRun.J_openocl));
assert(isequal(badRun.solver_info,info) && isequal(badRun.q_control,[.2;1]));
assert(isequal(badRun.t_state,[0;.2;1]));
tests{end+1}='nonuniform_interval_cost_and_output_grid_check';
tests{end+1}='invalid_output_retains_original_arrays_and_info';

throwPrepared=prepared;
throwPrepared.problem=struct('solve',@throwingOpenOCL, ...
    'solver',struct('info',@failureInfo));
failure=solve_openocl_case(par,prepared.x0,settings,initialization,throwPrepared);
assert(~failure.success && strcmp(failure.return_status,'Maximum_Iterations_Exceeded'));
assert(strcmp(failure.failure.identifier,'mock:OpenOCLFailure'));
assert(isequal(failure.solver_info,failureInfo()) && failure.solver_elapsed_seconds>=0);
tests{end+1}='solver_exception_retains_available_info_snapshot';

temporaryRoot=tempname; mkdir(temporaryRoot);
cleanup=onCleanup(@() cleanupTemporary(temporaryRoot)); %#ok<NASGU>
request=struct('case_id','mock_case','parameters',par,'x0',prepared.x0, ...
    'solver_settings',settings,'actual_solver_settings',settings,'actual_grid',grid, ...
    'initialization',initialization,'initial_guess',initialGuess);
provenance=struct('solve_commit','mock_commit','solve_code_hash','mock_hash', ...
    'solve_dirty',false,'environment',struct('matlab','mock'), ...
    'environment_fingerprint','mock_environment');
spec=struct('code_hash','mock_assessment','settings',struct());
mockCalls=0;
[saved,activity]=execute_numerical_run(request,provenance,temporaryRoot,@mockCallable,@mockAssessment,spec,false);
assert(activity.solver_called && saved.success && mockCalls==1);
sidecar=fullfile(temporaryRoot,saved.solver_diagnostics_file);
raw=fullfile(temporaryRoot,'runs',[saved.run_id '.mat']);
sidecarHash=numerical_sha256(sidecar,'file'); rawHash=numerical_sha256(raw,'file');
decoded=jsondecode(fileread(sidecar));
assert(strcmp(decoded.run_id,saved.run_id) && decoded.solver_diagnostics.iteration_count.value==3);
assert(contains(fileread(sidecar),'"value": null'));
assert(saved.execution_elapsed_seconds>=0);
[cached,activity]=execute_numerical_run(request,provenance,temporaryRoot,@mockCallable,@mockAssessment,spec,false);
assert(activity.cache_hit && ~activity.solver_called && mockCalls==1);
assert(strcmp(cached.run_id,saved.run_id) && strcmp(rawHash,numerical_sha256(raw,'file')));
assert(strcmp(sidecarHash,numerical_sha256(sidecar,'file')));
tests{end+1}='diagnostic_sidecar_and_cache_preserve_original_timing';

try
    execute_numerical_run(request,provenance,temporaryRoot,@throwingCallable,@mockAssessment,spec,true);
    error('mock:TestFailed','Missing deliberate callable exception.');
catch exception
    assert(strcmp(exception.identifier,'mock:CallableFailure'));
end
index=jsondecode(fileread(fullfile(temporaryRoot,'run_index.json')));
assert(numel(index.entries)==2 && ~index.entries(2).success);
loaded=load(fullfile(temporaryRoot,index.entries(2).raw_file),'run');
assert(strcmp(loaded.run.failure.identifier,'mock:CallableFailure'));
assert(loaded.run.execution_elapsed_seconds>=0 && isnan(loaded.run.solver_diagnostics.iteration_count.value));
assert(isfile(fullfile(temporaryRoot,loaded.run.solver_diagnostics_file)));
tests{end+1}='thrown_callable_saved_with_elapsed_time_before_rethrow';
report=struct('passed',true,'tests',{tests},'tests_passed',numel(tests), ...
    'actual_optimizer_calls',0,'mock_callable_calls',mockCalls,'checked_utc',numerical_utc(),'matlab',version);
fprintf('SOLVER_DIAGNOSTIC_TESTS_OK tests=%d actual_optimizer=0\n',numel(tests));

    function [solution,times,outInfo]=mockOpenOCL(~)
        solution=struct('states',struct('S',struct('value',[.75 .74 .73]), ...
            'I',struct('value',[.01 .01 .01])),'controls',struct('q',struct('value',[.2 1])));
        times=struct('states',struct('value',[0 .2 1]),'controls',struct('value',[0 .2]));
        outInfo=info;
    end
    function [solution,times,outInfo]=throwingOpenOCL(~) %#ok<STOUT>
        error('mock:OpenOCLFailure','Deliberate OpenOCL interface exception.');
    end
    function outInfo=failureInfo()
        outInfo=info; outInfo.success=false;
        outInfo.ipopt_stats.success=false; outInfo.ipopt_stats.return_status='Maximum_Iterations_Exceeded';
    end
    function out=mockCallable(~)
        mockCalls=mockCalls+1; out=run;
    end
    function out=throwingCallable(~) %#ok<STOUT>
        error('mock:CallableFailure','Deliberate execute interface exception.');
    end
    function out=mockAssessment(~)
        out=struct('reference',struct('J_reference',.84),'assessment',struct('passed',true));
    end
end

function cleanupTemporary(root)
% 只清理本测试创建且已确认位于 tempdir 内的目录。
resolved=char(java.io.File(root).getCanonicalPath());
parent=char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
