function report = verify_revision_scheduler()
% 调用正式dispatcher的mock回归；模拟调度调用数不等于真实优化次数。
cfg=revision_validation_config(); root=tempname; mkdir(root);
cleanup=onCleanup(@() cleanup_temporary(root)); %#ok<NASGU>
tests={}; experiments=cfg.revision.experiments;
assert(numel(experiments)==35 && numel(unique({experiments.configuration_fingerprint}))==35);
assert(count_group('main')==5 && count_group('initialization-constant')==5 && ...
    count_group('initialization-random')==5 && count_group('grid')==15 && count_group('horizon')==15);
for k=1:numel(experiments)
    e=experiments(k);
    assert(e.solver_settings.d==2 && isequal(e.parameters,cfg.parameters) && ...
        strcmp(e.solver_settings.terminal_constraint,'none') && ~e.solver_settings.controls_regularization);
    if any(strcmp(e.groups,'grid')), assert(e.solver_settings.T==300 && ismember(e.solver_settings.N,[2000 4000 8000])); end
    if any(strcmp(e.groups,'horizon')), assert(abs(e.solver_settings.T/e.solver_settings.N-.0375)<1e-14); end
end
tests{end+1}='35_unique_predeclared_configs_and_group_references';

stateBefore=rng; repeated=revision_validation_config(); stateAfter=rng;
assert(isequaln(stateBefore,stateAfter) && ...
    strcmp(cfg.revision.protocol_hash,repeated.revision.protocol_hash) && isequaln(experiments,repeated.revision.experiments));
tests{end+1}='configuration_is_deterministic_and_preserves_global_rng';
initialTests=verify_initial_guesses(cfg);
tests=[tests initialTests];

calls=0; prepares=0; units=0; published=0; thresholdCalls=0; forceValues=[];
sequence={}; fingerprints={}; failurePosition=0; fatalPosition=0; blocked=false;
thresholdStatus='completed'; thresholdConsistent=true; rawMockCalls=0;
activeCfg=isolated('all');
hooks=struct('unit',@unit,'preflight',@preflight,'setup',@setup, ...
    'provenance',@provenance,'prepare',@prepare,'execute',@execute,'publish',@publish, ...
    'threshold',@threshold,'verify_selection',@verify_selection,'summary',@summary);
allReport=revision_validation_dispatch(activeCfg,'all',true,hooks);
assert(strcmp(allReport.status,'completed') && allReport.protocol_complete && allReport.consistency_pass);
assert(calls==35 && prepares==35 && units==1 && published==1 && thresholdCalls==1);
assert(numel(unique(fingerprints))==35 && all(forceValues) && allReport.requested_unique_count==35);
assert(strcmp(sequence{1},'unit') && strcmp(sequence{2},'preflight') && strcmp(sequence{3},'setup'));
categories=cellfun(@first_group,{experiments.groups},'UniformOutput',false);
assert(isequal(categories(1:5),repmat({'main'},1,5)) && ...
    isequal(categories(6:10),repmat({'initialization-constant'},1,5)) && ...
    isequal(categories(11:15),repmat({'initialization-random'},1,5)));
publishIndex=find(strcmp(sequence,'publish')); thresholdIndex=find(strcmp(sequence,'threshold'));
verifyIndex=find(strcmp(sequence,'verify_selection'));
assert(isscalar(publishIndex) && isscalar(thresholdIndex) && publishIndex<thresholdIndex && verifyIndex<thresholdIndex);
tests{end+1}='all_order_full_manifest_first_force_unique_execution_and_main_publication';

reset(); activeCfg=isolated('duplicate_force');
e=experiments(1); e.groups={'grid'}; duplicate=e; duplicate.configuration_id='SYNTHETIC_DUPLICATE';
activeCfg.revision.experiments=[e duplicate];
duplicateReport=revision_validation_dispatch(activeCfg,'grid',true,hooks);
assert(calls==1 && prepares==2 && duplicateReport.solver_calls==1 && ...
    duplicateReport.duplicate_reference_count==1 && numel(duplicateReport.rows)==2);
assert(strcmp(duplicateReport.rows(1).run_id,duplicateReport.rows(2).run_id) && ...
    strcmp(duplicateReport.rows(2).status,'duplicate_reference') && all(forceValues));
tests{end+1}='force_deduplicates_identical_actual_fingerprints_with_distinct_ids';

reset(); activeCfg=isolated('duplicate_failed_force'); activeCfg.revision.experiments=[e duplicate];
failurePosition=1; duplicateFailure=revision_validation_dispatch(activeCfg,'grid',true,hooks);
assert(calls==1 && duplicateFailure.failed_count==2 && duplicateFailure.duplicate_reference_count==1 && ...
    strcmp(duplicateFailure.status,'failed') && ...
    strcmp(duplicateFailure.rows(1).run_id,duplicateFailure.rows(2).run_id));
tests{end+1}='failed_fingerprint_is_not_retried_in_the_same_force_batch';

for thresholdCase={'completed','blocked'}
    reset(); activeCfg=isolated(['all_threshold_' thresholdCase{1}]);
    thresholdStatus=thresholdCase{1}; thresholdConsistent=false;
    aggregate=revision_validation_dispatch(activeCfg,'all',false,hooks);
    assert(~strcmp(aggregate.status,'completed') && ~aggregate.consistency_pass && calls==35);
    if strcmp(thresholdStatus,'blocked'), assert(~aggregate.protocol_complete);
    else, assert(aggregate.protocol_complete); end
    tests{end+1}=['all_cannot_pass_after_threshold_' thresholdCase{1} '_disagreement']; %#ok<AGROW>
end

reset(); activeCfg=isolated('main_failure'); failurePosition=2;
failureReport=revision_validation_dispatch(activeCfg,'main',false,hooks);
assert(calls==5 && failureReport.failed_count==1 && failureReport.successful_count==4 && ...
    ~failureReport.selection_published && published==0 && strcmp(failureReport.status,'failed'));
assert(numel(failureReport.rows)==5 && strcmp(failureReport.rows(2).status,'failed') && ...
    strcmp(failureReport.rows(2).return_status,'Maximum_Iterations_Exceeded'));
tests{end+1}='NLP_failure_preserved_and_remaining_main_cases_continue';

reset(); activeCfg=isolated('main_code_error'); fatalPosition=1; caught=false;
try, revision_validation_dispatch(activeCfg,'main',false,hooks);
catch exception, caught=strcmp(exception.identifier,'revision_unit:DeliberateCodeError'); end
latest=jsondecode(fileread(fullfile(activeCfg.paths.data,'revision_checks','latest_main_report.json')));
assert(caught && calls==1 && prepares==1 && strcmp(latest.status,'failed') && ...
    strcmp(latest.failure.identifier,'revision_unit:DeliberateCodeError'));
tests{end+1}='code_error_stops_immediately_with_saved_failure_report';

reset(); activeCfg=isolated('persisted_assessment_failure');
activeCfg.check=rmfield(activeCfg.check,'ode_rel_tol'); activeCfg.plot.reference_samples=7;
productionExecute=rmfield(hooks,'execute'); productionExecute.prepare=@prepare_for_persisted_failure;
caught=false;
try, revision_validation_dispatch(activeCfg,'main',false,productionExecute);
catch exception, caught=strcmp(exception.identifier,'revision:ExecutionCodeFailure'); end
latest=jsondecode(fileread(fullfile(activeCfg.paths.data,'revision_checks','latest_main_report.json')));
index=jsondecode(fileread(fullfile(activeCfg.paths.data,'run_index.json')));
saved=load(fullfile(activeCfg.paths.data,index.entries(1).raw_file),'run');
assert(caught && rawMockCalls==1 && latest.solver_calls==1 && latest.attempted_count==1 && ...
    numel(latest.rows)==1 && numel(index.entries)==1 && strcmp(latest.status,'failed'));
assert(saved.run.success && ~isfield(saved.run,'scheduler_failure'));
tests{end+1}='production_execute_reconciles_saved_raw_run_after_assessment_exception';

reset(); activeCfg=isolated('main_blocked'); blocked=true;
blockedReport=revision_validation_dispatch(activeCfg,'main',false,hooks);
assert(strcmp(blockedReport.status,'blocked') && calls==0 && prepares==0 && ~isempty(blockedReport.blockers));
tests{end+1}='missing_environment_is_blocked_and_never_prepare_or_execute';

reset(); activeCfg=isolated('threshold');
thresholdReport=revision_validation_dispatch(activeCfg,'threshold',false,hooks);
assert(strcmp(thresholdReport.status,'completed') && calls==0 && prepares==0 && thresholdCalls==1 && units==0);
tests{end+1}='threshold_mode_does_not_call_optimizer_or_preparation';

reset(); activeCfg=isolated('threshold_no_saved_data');
withoutThreshold=rmfield(hooks,'threshold');
missingThreshold=revision_validation_dispatch(activeCfg,'threshold',false,withoutThreshold);
assert(strcmp(missingThreshold.status,'blocked') && calls==0 && prepares==0 && ...
    missingThreshold.threshold.optimizer_calls==0 && ~isempty(missingThreshold.threshold.blockers));
tests{end+1}='production_threshold_missing_data_stays_blocked_without_optimizer';

reset(); activeCfg=isolated('unit');
unitReport=revision_validation_dispatch(activeCfg,'unit',false,hooks);
assert(strcmp(unitReport.status,'tested') && units==1 && calls==0 && prepares==0);
tests{end+1}='unit_mode_never_starts_optimizer';
report=struct('passed',true,'tests',{tests},'test_count',numel(tests), ...
    'default_unique_configuration_count',35,'mock_all_execute_calls',allReport.solver_calls, ...
    'actual_optimizer_calls',0,'checked_utc',numerical_utc());
fprintf('REVISION_SCHEDULER_TESTS_OK tests=%d mock_all_execute=%d actual_optimizer=0\n',numel(tests),allReport.solver_calls);

    function n=count_group(group)
        n=sum(arrayfun(@(e) any(strcmp(e.groups,group)),experiments));
    end
    function out=isolated(name)
        out=cfg; out.paths.data=fullfile(root,name); mkdir(out.paths.data);
    end
    function reset()
        calls=0; prepares=0; units=0; published=0; thresholdCalls=0; forceValues=[];
        sequence={}; fingerprints={}; failurePosition=0; fatalPosition=0; blocked=false;
        thresholdStatus='completed'; thresholdConsistent=true; rawMockCalls=0;
    end
    function out=unit()
        units=units+1; sequence{end+1}='unit'; assert_manifest();
        out=struct('passed',true,'actual_optimizer_calls',0);
    end
    function out=preflight(~)
        sequence{end+1}='preflight'; assert_manifest();
        out=struct('passed',~blocked,'status','tested','blockers',{{}});
        if blocked, out.status='blocked'; out.blockers={'deliberately absent test environment'}; end
    end
    function setup(~), sequence{end+1}='setup'; assert_manifest(); end
    function out=provenance(~)
        sequence{end+1}='provenance'; source=numerical_code_hash('solve');
        out=struct('solve_code_hash',source.hash,'environment_fingerprint','synthetic_scheduler_test', ...
            'environment',struct('matlab','synthetic_unit_test'), ...
            'solve_commit','synthetic_test_only','solve_dirty',true);
    end
    function out=prepare(e,~)
        prepares=prepares+1; sequence{end+1}=['prepare_' e.configuration_id]; assert_manifest();
        t=[0;e.solver_settings.T/2;e.solver_settings.T];
        grid=struct('t_state',t,'t_control',t(1:end-1),'dt_control',diff(t));
        out=struct('case_id',e.case_id,'parameters',e.parameters,'x0',e.x0, ...
            'solver_settings',e.solver_settings,'actual_solver_settings',e.solver_settings, ...
            'actual_grid',grid,'initialization',e.initialization, ...
            'initial_guess',struct('synthetic_scheduler_mock',true));
    end
    function [run,activity]=execute(request,~,~,~,force)
        calls=calls+1; sequence{end+1}=['execute_' request.case_id];
        forceValues(end+1)=force; fingerprints{end+1}=request.expected_solve_fingerprint;
        if calls==fatalPosition, error('revision_unit:DeliberateCodeError','Deliberate code failure in scheduler mock.'); end
        success=calls~=failurePosition; status='Solve_Succeeded';
        if ~success, status='Maximum_Iterations_Exceeded'; end
        run=struct('case_id',request.case_id,'run_id',sprintf('synthetic_scheduler_%d',calls), ...
            'solve_fingerprint',request.expected_solve_fingerprint,'success',success,'return_status',status, ...
            'assessment',struct('numeric_pass',success,'agreement_pass',success,'status','synthetic_unit_test'), ...
            'J_openocl',NaN);
        activity=struct('cache_hit',false,'solver_called',true,'assessment_called',success);
    end
    function out=prepare_for_persisted_failure(e,currentCfg)
        out=prepare(e,currentCfg);
        out.ig=[]; out.problem=struct('solve',@raw_output);
    end
    function [sol,times,info]=raw_output(~)
        rawMockCalls=rawMockCalls+1;
        state=cfg.cases(1).x0; t=[0;150;300];
        sol=struct('states',struct('S',struct('value',repmat(state(1),1,3)), ...
            'I',struct('value',repmat(state(2),1,3))), ...
            'controls',struct('q',struct('value',[0 0])));
        times=struct('states',struct('value',t'),'controls',struct('value',t(1:end-1)'));
        info=struct('success',true,'ipopt_stats',struct('success',true,'return_status','Solve_Succeeded'));
    end
    function out=publish(runs,~)
        published=published+1; sequence{end+1}='publish';
        assert(numel(runs)==5 && isequal(cellfun(@(r) r.case_id,runs,'UniformOutput',false),{'E1','E2','E3','E4','E5'}));
        out=struct('synthetic_unit_test',true);
    end
    function verify_selection(~), sequence{end+1}='verify_selection'; end
    function out=threshold(~,~)
        thresholdCalls=thresholdCalls+1; sequence{end+1}='threshold';
        out=struct('status',thresholdStatus,'consistency_pass',thresholdConsistent,'optimizer_calls',0);
    end
    function out=summary(~,group,~,~)
        sequence{end+1}=['summary_' group];
        out=struct('status','completed','protocol_complete',true,'consistency_pass',true);
    end
    function assert_manifest()
        files=dir(fullfile(activeCfg.paths.data,'revision_checks','*_manifest.json'));
        assert(numel(files)==1,'verify_revision_scheduler:ManifestOrder','Full manifest must exist before hooks run.');
        frozen=jsondecode(fileread(fullfile(files(1).folder,files(1).name)));
        expectedCount=numel(activeCfg.revision.experiments);
        expectedUnique=numel(unique({activeCfg.revision.experiments.configuration_fingerprint}));
        assert(numel(frozen.default_experiments)==expectedCount && frozen.default_unique_count==expectedCount && ...
            numel(unique({frozen.default_experiments.configuration_fingerprint}))==expectedUnique);
    end
end

function out=first_group(groups), out=groups{1}; end

function tests=verify_initial_guesses(cfg)
par=cfg.parameters; x0=cfg.cases(1).x0; T=6;
edges=[0;.2;1;2.5;6]; tc=edges(1:end-1); ti=sort([tc+.2*diff(edges);tc+.7*diff(edges)]);
grid=struct('t_state',edges,'t_control',tc,'t_integrator',ti,'control_interval_edges',edges);
stateBefore=rng;
[constant,c]=revision_initial_guess(par,x0,T,grid,struct('type','constant_control','control',.7));
assert(all(c.control==.7) && isequal(c.control,constant.actual_control_guess));
guess=struct('type','seeded_random','seed',20261009);
[random,r]=revision_initial_guess(par,x0,T,grid,guess);
[repeated,again]=revision_initial_guess(par,x0,T,grid,random);
other=guess; other.seed=guess.seed+1; [~,different]=revision_initial_guess(par,x0,T,grid,other);
assert(isequaln(r,again) && isequaln(random,repeated) && ~isequal(r.control,different.control));
assert(all(r.control>=.15 & r.control<=.85) && random.knot_times(1)==0 && random.knot_times(end)==T);
stream=RandStream('mt19937ar','Seed',guess.seed); values=.15+.70*rand(stream,numel(random.knot_times),1);
assert(isequal(values,random.knot_values) && ...
    isequal(interp1(random.knot_times,values,tc,'linear'),r.control) && isequaln(stateBefore,rng));
reintegrated=reconstruct(par,x0,grid,r.control);
assert(max(abs(reintegrated.node_states-r.node_states),[],'all')<1e-12 && ...
    max(abs(reintegrated.integrator_states-r.integrator_states),[],'all')<1e-12);
assert(all(r.node_states(:)>0) && max(diff(sum(r.node_states,2)))<=1e-12);
bad=random; bad.knot_values(1)=bad.knot_values(1)+.01; caught=false;
try, revision_initial_guess(par,x0,T,grid,bad);
catch exception, caught=strcmp(exception.identifier,'revision:RandomDefinitionMismatch'); end
assert(caught);
[~,violating]=revision_initial_guess(par,[.99;.01],20, ...
    struct('t_state',[0;10;20],'t_control',[0;10],'t_integrator',[2;5;12;15], ...
    'control_interval_edges',[0;10;20]),struct('type','constant_control','control',0));
assert(violating.capacity_excess>0 && max(violating.node_states(:,2))>par.K);
tests={'actual_constant_point_seven_input_array', ...
    'random_seed_knots_values_reconstruction_and_rng_preservation', ...
    'state_node_and_integrator_guesses_follow_actual_piecewise_control', ...
    'tampered_random_definition_rejected', ...
    'infeasible_initial_guess_capacity_excess_recorded_without_clipping'};
end

function out=reconstruct(par,x0,grid,q)
ns=nan(numel(grid.t_state),2); ni=nan(numel(grid.t_integrator),2); y=x0;
for k=1:numel(q)
    rhs=@(~,x) [-par.c*(par.p+(1-par.p)*q(k))*x(1)*x(2); ...
        (par.p*par.c*(1-q(k))*x(1)-par.gamma)*x(2)];
    span=grid.control_interval_edges(k:k+1);
    sol=ode45(rhs,span,y,odeset('RelTol',2e-10,'AbsTol',1e-13));
    j=find(grid.t_state>=span(1) & grid.t_state<=span(2));
    l=find(grid.t_integrator>=span(1) & grid.t_integrator<=span(2));
    ns(j,:)=deval(sol,grid.t_state(j)')'; ni(l,:)=deval(sol,grid.t_integrator(l)')';
    y=deval(sol,span(2));
end
out=struct('node_states',ns,'integrator_states',ni);
end

function cleanup_temporary(root)
resolved=char(java.io.File(root).getCanonicalPath()); parent=char(java.io.File(tempdir).getCanonicalPath());
assert(startsWith(lower(resolved),[lower(parent) filesep]) && ~strcmpi(resolved,parent));
if isfolder(resolved), rmdir(resolved,'s'); end
end
