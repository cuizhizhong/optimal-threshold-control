function results = run_numerical_scenarios(mode,force)
% 默认运行五例及附加复核；'neutral_E2' 只运行 E2 常值初猜。
if nargin<1, mode='all'; end
if nargin<2, force=false; end
cfg=numerical_cases_config(); addpath(cfg.paths.openocl_root); ocl;
if ~isfolder(cfg.paths.data), mkdir(cfg.paths.data); end
verify_numerical_reference();
provenance=numerical_solve_provenance(cfg); assessmentSpec=numerical_assessment_spec(cfg);
results=struct();
if ~ismember(mode,{'checks','neutral_E2'})
    ids=cfg.run_order;
    if ~ismember(mode,{'all','main'}), ids={mode}; end
    for j=1:numel(ids)
        opts=cfg.solve;
        ix=find(strcmp({cfg.cases.id},ids{j})); assert(isscalar(ix),'Unknown case ID.');
        opts.N=cfg.cases(ix).main_N;
        results.(ids{j})=runone(ids{j},opts,struct('type','analytic_reference'));
    end
    if ismember(mode,{'main','all'})
        selected=cell(1,5);
        for k=1:5, selected{k}=results.(sprintf('E%d',k)); end
        publish_numerical_selection(selected,cfg.paths.data, ...
            'Predeclared main_N and analytic_reference initialization; no result-dependent refinement.');
    end
end
if ismember(mode,{'all','checks'})
    opts=cfg.solve; opts.N=cfg.check.refine_N;
    results.refined=runone(cfg.check.refine_case_id,opts,struct('type','analytic_reference'));
    results.neutral=runone(cfg.check.neutral_guess_case_id,cfg.solve, ...
        struct('type','constant_control','control',cfg.check.neutral_control));
end
if ismember(mode,{'all','checks','neutral_E2'})
    opts=cfg.solve; opts.N=cfg.check.refine_N;
    results.neutral_E2=runone('E2',opts, ...
        struct('type','constant_control','control',cfg.check.neutral_control));
end
if strcmp(mode,'all'), load_selected_numerical_runs(cfg.paths.data); end
    function run=runone(id,opts,guess)
        opts.initialization=guess.type;
        ix=find(strcmp({cfg.cases.id},id)); assert(isscalar(ix),'Unknown case ID.');
        x0=cfg.cases(ix).x0;
        fprintf('START %s N=%d guess=%s\n',id,opts.N,guess.type);
        runProvenance=numerical_solve_provenance(cfg);
        prepared=prepare_openocl_case(cfg.parameters,x0,opts,guess);
        currentSource=numerical_code_hash('solve');
        assert(strcmp(currentSource.hash,provenance.solve_code_hash), ...
            'numerical:SolveSourceChanged','Solve source changed during this batch; restart with the new fingerprint.');
        request=rmfield(prepared,{'problem','ig'}); request.case_id=id;
        solver=@(~) solve_openocl_case(cfg.parameters,x0,opts,guess,prepared);
        [run,activity]=execute_numerical_run(request,runProvenance,cfg.paths.data,solver, ...
            @(raw) numerical_assessment_view(raw,cfg),assessmentSpec,force);
        fprintf('RUN %s id=%s cache=%d solver=%d assessment=%d\n', ...
            id,run.run_id,activity.cache_hit,activity.solver_called,activity.assessment_called);
        if ~run.success
            fprintf('FAILED %s return_status=%s; immutable record retained.\n',id,run.return_status);
            return;
        end
        fprintf('RESULT %s status=%s J=%.12f ref=%.12f cap=%.3g state=%.3g tail=%.3g pass=%d structure=%s\n', ...
            id,run.return_status,run.J_openocl,run.reference.J_reference, ...
            run.assessment.capacity_excess,run.assessment.state_discrepancy, ...
            run.assessment.tail_max_q,run.assessment.passed,run.assessment.observed_structure);
    end
end
