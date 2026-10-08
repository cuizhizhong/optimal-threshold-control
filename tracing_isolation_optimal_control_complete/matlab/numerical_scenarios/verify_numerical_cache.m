function report = verify_numerical_cache()
% 六项缓存来源测试使用mock，优化器调用次数始终为0。
root=tempname; mkdir(root); cleanup=onCleanup(@() cleanupTemporary(root));
sourceRoot=fullfile(root,'source'); mkdir(sourceRoot);
source=numerical_code_hash('solve');
for k=1:numel(source.files), write(fullfile(sourceRoot,source.files(k).path),'original'); end
write(fullfile(sourceRoot,'make_numerical_figures.m'),'figure original');
write(fullfile(sourceRoot,'main.tex'),'paper original');
source=numerical_code_hash('solve',sourceRoot);
provenance=struct('solve_commit','commit_A','solve_code_hash',source.hash, ...
    'solve_dirty',false,'environment',struct('matlab','mock','ipopt','mock'), ...
    'environment_fingerprint','mock_environment','source_status','verified_record');
request=struct('case_id','E1','parameters',struct('p',0.5,'c',2,'gamma',0.3,'K',0.15), ...
    'x0',[0.75;0.01],'solver_settings',struct('T',1,'N',2,'d',2), ...
    'actual_solver_settings',struct('T',1,'N',2,'d',2,'tol',1e-9), ...
    'actual_grid',struct('t_state',[0;0.5;1],'t_control',[0;0.5]), ...
    'initialization',struct('type','constant_control','control',0.7,'seed',[], ...
    'knot_times',[],'knot_values',[],'actual_control_guess',[0.7;0.7]), ...
    'initial_guess',struct('node_states',[.75 .01;.74 .01;.73 .01], ...
    'integrator_states',[.745 .01;.735 .01],'control',[0.7;0.7]));
spec=struct('code_hash','assessment_A','settings',struct('tolerance',1e-6));
solverCalls=0; assessmentCalls=0; failNext=false; throwNext=false;
dataRoot=fullfile(root,'same');
[first,a]=execute_numerical_run(request,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
assert(a.solver_called && ~a.cache_hit && a.assessment_called);
rawPath=fullfile(dataRoot,'runs',[first.run_id '.mat']); rawHash=numerical_sha256(rawPath,'file');
later=provenance; later.solve_commit='commit_B'; later.solve_dirty=true;
[second,a]=execute_numerical_run(request,later,dataRoot,@mockSolver,@mockAssessment,spec,false);
assert(a.cache_hit && ~a.solver_called && ~a.assessment_called && solverCalls==1);
assert(isequal(first.provenance,second.provenance) && strcmp(second.provenance.solve_commit,'commit_A'));
assert(strcmp(rawHash,numerical_sha256(rawPath,'file')));
tests={'same_fingerprint_preserves_solve_provenance'};

% 动力学/初猜源码、实际设置/网格/初猜及环境均须使缓存失效。
before=solverCalls;
write(fullfile(sourceRoot,'prepare_openocl_case.m'),'changed dynamics');
changed=provenance; changed.solve_code_hash=numerical_code_hash('solve',sourceRoot).hash;
execute_numerical_run(request,changed,dataRoot,@mockSolver,@mockAssessment,spec,false);
write(fullfile(sourceRoot,'analytic_reference.m'),'changed initializer');
changed.solve_code_hash=numerical_code_hash('solve',sourceRoot).hash;
execute_numerical_run(request,changed,dataRoot,@mockSolver,@mockAssessment,spec,false);
modified=request; modified.actual_solver_settings.tol=2e-9;
execute_numerical_run(modified,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
modified=request; modified.actual_grid.t_state=[0;.4;1];
execute_numerical_run(modified,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
modified=request; modified.initialization.seed=123;
execute_numerical_run(modified,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
modified=request; modified.initial_guess.control=[.6;.7];
execute_numerical_run(modified,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
changed=provenance; changed.environment_fingerprint='changed_environment';
execute_numerical_run(request,changed,dataRoot,@mockSolver,@mockAssessment,spec,false);
assert(solverCalls==before+7);
tests{end+1}='solve_dependencies_and_actual_request_invalidate_cache';

before=solverCalls; beforeAssessment=assessmentCalls;
newSpec=spec; newSpec.code_hash='assessment_B';
[third,a]=execute_numerical_run(request,provenance,dataRoot,@mockSolver,@mockAssessment,newSpec,false);
assert(a.cache_hit && ~a.solver_called && a.assessment_called && solverCalls==before && assessmentCalls==beforeAssessment+1);
assert(isequal(first.provenance,third.provenance) && strcmp(rawHash,numerical_sha256(rawPath,'file')));
tests{end+1}='assessment_change_only_reassesses';

beforeHash=numerical_code_hash('solve',sourceRoot).hash;
write(fullfile(sourceRoot,'main.tex'),'changed paper');
write(fullfile(sourceRoot,'make_numerical_figures.m'),'changed figure');
assert(strcmp(beforeHash,numerical_code_hash('solve',sourceRoot).hash));
before=solverCalls;
[~,a]=execute_numerical_run(request,provenance,dataRoot,@mockSolver,@mockAssessment,spec,false);
assert(a.cache_hit && solverCalls==before);
tests{end+1}='paper_and_figure_do_not_invalidate_solve';

legacyRoot=fullfile(root,'legacy'); mkdir(legacyRoot);
run=rmfield(first,{'run_id','provenance','solve_fingerprint','solve_fingerprint_payload','source_status'}); %#ok<NASGU>
legacyPath=fullfile(legacyRoot,'E1.mat'); save(legacyPath,'run','-v7');
legacyHash=numerical_sha256(legacyPath,'file'); before=solverCalls;
[~,a]=execute_numerical_run(request,provenance,legacyRoot,@mockSolver,@mockAssessment,spec,false);
assert(~a.cache_hit && solverCalls==before+1 && strcmp(legacyHash,numerical_sha256(legacyPath,'file')));
[legacyView,~]=assess_saved_numerical_run(run,legacyRoot,@mockAssessment,spec,false);
assert(strcmp(legacyView.source_status,'legacy_unverified'));
tests{end+1}='legacy_result_never_reused_as_new_evidence';

failureRoot=fullfile(root,'failure'); failNext=true;
[failed,a]=execute_numerical_run(request,provenance,failureRoot,@mockSolver,@mockAssessment,spec,false);
assert(~failed.success && a.solver_called && ~a.assessment_called);
failurePath=fullfile(failureRoot,'runs',[failed.run_id '.mat']); failureHash=numerical_sha256(failurePath,'file');
[retry,a]=execute_numerical_run(request,provenance,failureRoot,@mockSolver,@mockAssessment,spec,false);
assert(retry.success && ~a.cache_hit && retry.attempt==2 && ~strcmp(failed.run_id,retry.run_id));
assert(strcmp(failureHash,numerical_sha256(failurePath,'file')));
index=jsondecode(fileread(fullfile(failureRoot,'run_index.json'))); assert(numel(index.entries)==2);
% 异常同样先保存原始失败记录，再抛给调用方。
throwNext=true;
try
    execute_numerical_run(request,provenance,failureRoot,@mockSolver,@mockAssessment,spec,true);
    error('Mock exception was not rethrown.');
catch exception, assert(strcmp(exception.identifier,'mock:Failure')); end
index=jsondecode(fileread(fullfile(failureRoot,'run_index.json'))); assert(numel(index.entries)==3 && ~index.entries(3).success);
tests{end+1}='failed_attempt_retained_and_retry_has_new_run_id';

% 附加：force独立attempt、manifest/兼容副本校验。
[forced,a]=execute_numerical_run(request,provenance,dataRoot,@mockSolver,@mockAssessment,spec,true);
assert(a.solver_called && ~strcmp(first.run_id,forced.run_id));
selectionRoot=fullfile(root,'selection'); selected=cell(1,5);
for k=1:5
    modified=request; modified.case_id=sprintf('E%d',k);
    selected{k}=execute_numerical_run(modified,provenance,selectionRoot,@mockSolver,@mockAssessment,spec,false);
end
manifest=publish_numerical_selection(selected,selectionRoot,'mock selection test');
loaded=load_selected_numerical_runs(selectionRoot); assert(strcmp(loaded{1}.run_id,selected{1}.run_id));
bad=manifest; bad.entries(1).case_id='E2'; bad.entries(2).case_id='E1';
numerical_write_json(fullfile(selectionRoot,'selection_manifest.json'),bad);
try, load_selected_numerical_runs(selectionRoot); error('Bad manifest accepted.');
catch exception, assert(~strcmp(exception.message,'Bad manifest accepted.')); end
report=struct('passed',true,'tests',{tests},'required_tests_passed',numel(tests), ...
    'mock_solver_calls',solverCalls,'mock_assessment_calls',assessmentCalls, ...
    'actual_optimizer_calls',0,'checked_utc',numerical_utc(),'matlab',version);
fprintf('NUMERICAL_CACHE_TESTS_OK tests=%d mock_solver=%d actual_optimizer=0\n',numel(tests),solverCalls);
    function raw=mockSolver(~)
        solverCalls=solverCalls+1;
        if throwNext, throwNext=false; error('mock:Failure','Deliberate solver exception.'); end
        raw=struct('success',~failNext,'return_status','mock','solver_info',struct('mock',true), ...
            't_state',[0;.5;1],'t_control',[0;.5],'s_state',[.75;.74;.73], ...
            'i_state',[.01;.01;.01],'q_control',[.7;.7],'J_openocl',.7);
        failNext=false;
    end
    function view=mockAssessment(~)
        assessmentCalls=assessmentCalls+1;
        view=struct('reference',struct('J_reference',.7),'assessment',struct('passed',true));
    end
end

function write(filename,content)
fid=fopen(filename,'w'); assert(fid>=0); cleanup=onCleanup(@() fclose(fid)); fprintf(fid,'%s',content);
end
function cleanupTemporary(root)
% 只删除本测试创建且位于tempdir下的唯一目录。
resolved=char(java.io.File(root).getCanonicalPath());
parent=char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
