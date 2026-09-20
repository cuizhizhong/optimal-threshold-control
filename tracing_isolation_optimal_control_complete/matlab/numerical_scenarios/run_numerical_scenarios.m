function results = run_numerical_scenarios(mode,force)
% 默认运行五例及两项独立复核；可传 'main'、'checks' 或单个算例 ID。
if nargin<1, mode='all'; end
if nargin<2, force=false; end
cfg=numerical_cases_config(); addpath(cfg.paths.openocl_root); ocl;
if ~isfolder(cfg.paths.data), mkdir(cfg.paths.data); end
geom=build_theory_geometry(cfg.parameters); verify_numerical_reference();
results=struct();
if ~strcmp(mode,'checks')
    ids=cfg.run_order;
    if ~ismember(mode,{'all','main'}), ids={mode}; end
    for j=1:numel(ids)
        results.(ids{j})=runone(ids{j},cfg.solve,struct('type','analytic_reference'),cfg.paths.data);
    end
end
if ismember(mode,{'all','checks'})
    folder=fullfile(cfg.paths.data,'checks'); if ~isfolder(folder), mkdir(folder); end
    opts=cfg.solve; opts.N=cfg.check.refine_N;
    results.refined=runone(cfg.check.refine_case_id,opts,struct('type','analytic_reference'),folder);
    results.neutral=runone(cfg.check.neutral_guess_case_id,cfg.solve, ...
        struct('type','constant_control','control',cfg.check.neutral_control),folder);
end
    function run=runone(id,opts,guess,folder)
        ix=find(strcmp({cfg.cases.id},id)); assert(isscalar(ix),'Unknown case ID.');
        x0=cfg.cases(ix).x0;
        fprintf('START %s N=%d guess=%s\n',id,opts.N,guess.type);
        filename=fullfile(folder,[id '.mat']);
        cached=false;
        if ~force && isfile(filename)
            d=load(filename,'run');
            cached=isequal(d.run.parameters,cfg.parameters) && isequal(d.run.x0,x0) && ...
                isequal(d.run.solver_settings,opts) && isequal(d.run.initialization,guess);
            if cached, run=d.run; end
        end
        if ~cached
            run=solve_openocl_case(cfg.parameters,x0,opts,guess); run.case_id=id;
        end
        [~,sha]=system(sprintf('git -C "%s" rev-parse HEAD',cfg.paths.repo_root));
        run.source_commit=strtrim(sha);
        % 保存真实输出后才做后处理，即使后处理失败也能追溯。
        save(filename,'run','-v7');
        run.reference=analytic_reference(cfg.parameters,x0,geom, ...
            unique([linspace(0,18,cfg.plot.reference_samples)';run.t_state]));
        run.assessment=assess_numerical_case(run,run.reference,cfg.parameters,cfg.check);
        run.assessment_settings=cfg.check;
        save(filename,'run','-v7');
        if strcmp(folder,cfg.paths.data) && run.success && ~run.assessment.passed && ...
                (run.assessment.capacity_excess>cfg.check.capacity_tolerance || ...
                 run.assessment.state_discrepancy>cfg.check.state_tolerance)
            archive=fullfile(cfg.paths.data,'coarse'); if ~isfolder(archive), mkdir(archive); end
            save(fullfile(archive,[id '.mat']),'run','-v7');
            fprintf('REFINE %s: capacity/state check requires N=%d\n',id,cfg.check.refine_N);
            opts.N=cfg.check.refine_N;
            run=solve_openocl_case(cfg.parameters,x0,opts,guess); run.case_id=id;
            run.source_commit=strtrim(sha); save(filename,'run','-v7');
            run.reference=analytic_reference(cfg.parameters,x0,geom, ...
                unique([linspace(0,18,cfg.plot.reference_samples)';run.t_state]));
            run.assessment=assess_numerical_case(run,run.reference,cfg.parameters,cfg.check);
            run.assessment_settings=cfg.check;
            save(filename,'run','-v7');
            if strcmp(id,cfg.check.refine_case_id)
                checkfolder=fullfile(cfg.paths.data,'checks'); if ~isfolder(checkfolder), mkdir(checkfolder); end
                save(fullfile(checkfolder,[id '.mat']),'run','-v7');
            end
        end
        fprintf('RESULT %s status=%s J=%.12f ref=%.12f cap=%.3g state=%.3g tail=%.3g pass=%d structure=%s\n', ...
            id,run.return_status,run.J_openocl,run.reference.J_reference, ...
            run.assessment.capacity_excess,run.assessment.state_discrepancy, ...
            run.assessment.tail_max_q,run.assessment.passed,run.assessment.observed_structure);
    end
end
