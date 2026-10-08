function summary = revision_group_summary(cfg,group,experiments,runs)
% 仅由保存的数值输出比较；失败和缺失参考都明确保留，不填入预期值。
summary=struct('schema_version',1,'group',group,'checked_utc',numerical_utc(), ...
    'status','completed','protocol_complete',true,'comparison_complete',true, ...
    'consistency_pass',false,'rows',[],'case_comparisons',[],'blockers',{{}});
selected=[];
for k=1:numel(experiments)
    groups=experiments(k).groups;
    yes=any(strcmp(groups,group));
    if strcmp(group,'initialization'), yes=any(ismember(groups,{'initialization-constant','initialization-random'})); end
    if yes, selected(end+1)=k; end %#ok<AGROW>
end
for ix=selected
    r=runs{ix}; e=experiments(ix);
    out=struct('case_id',e.case_id,'configuration_id',e.configuration_id,'run_id','', ...
        'solve_fingerprint','','T',e.solver_settings.T,'N',e.solver_settings.N, ...
        'initialization',e.initialization.type,'success',false,'return_status','not_available', ...
        'numeric_pass',false,'agreement_pass',false,'J_openocl',NaN, ...
        'capacity_excess',NaN,'state_discrepancy',NaN,'tail_max_q',NaN, ...
        'terminal_peak',NaN,'observed_structure','','event_intervals',[]);
    if isempty(r), summary.protocol_complete=false;
    else
        out.run_id=r.run_id; out.solve_fingerprint=r.solve_fingerprint;
        out.success=r.success; out.return_status=r.return_status;
        if isfield(r,'J_openocl'), out.J_openocl=r.J_openocl; end
        if isfield(r,'assessment')
            names={'numeric_pass','agreement_pass','capacity_excess','state_discrepancy', ...
                'tail_max_q','terminal_peak','observed_structure'};
            for j=1:numel(names)
                if isfield(r.assessment,names{j}), out.(names{j})=r.assessment.(names{j}); end
            end
            if isfield(r.assessment,'structured_events'), out.event_intervals=r.assessment.structured_events; end
        end
    end
    if isempty(summary.rows), summary.rows=out; else, summary.rows(end+1)=out; end
end
main={};
if strcmp(group,'initialization')
    main=mainSources(cfg,experiments,runs);
end
for k=1:5
    id=sprintf('E%d',k); indices=selected(strcmp({experiments(selected).case_id},id));
    chosen=runs(indices);
    out=struct('case_id',id,'status','failed_or_incomplete','consistency_pass',false, ...
        'source_run_ids',{{}},'reference_run_id','','cost_absolute_difference',[], ...
        'finest_relative_cost_difference',NaN,'cost_absolute_span',NaN, ...
        'event_comparisons',[],'common_window_comparisons',[],'reasons',{{}});
    valid=~cellfun(@isempty,chosen);
    out.source_run_ids=cellfun(@(r) r.run_id,chosen(valid),'UniformOutput',false);
    if ~all(valid)
        out.reasons={'missing scheduled record'}; summary.comparison_complete=false;
    elseif strcmp(group,'initialization')
        base=main{k};
        if isempty(base)
            out.reasons={'current predeclared main reference missing or untrusted'};
            summary.comparison_complete=false;
        else
            out.reference_run_id=base.run_id;
            gaps=NaN(1,numel(chosen)); matches=false(1,numel(chosen)); comps=cell(1,numel(chosen));
            for j=1:numel(chosen)
                if usable(base) && usable(chosen{j})
                    gaps(j)=chosen{j}.J_openocl-base.J_openocl;
                    [matches(j),comps{j}]=eventsAgree(base,chosen{j});
                end
            end
            out.cost_absolute_difference=abs(gaps); out.event_comparisons=comps;
            out.consistency_pass=all(matches) && all(abs(gaps)<=cfg.revision.initialization_cost_absolute_tolerance);
        end
    elseif strcmp(group,'grid')
        Ns=[experiments(indices).solver_settings]; Ns=[Ns.N];
        [~,order]=sort(Ns); chosen=chosen(order);
        if numel(chosen)>=2 && usable(chosen{end}) && usable(chosen{end-1})
            base=chosen{end}; second=chosen{end-1}; out.reference_run_id=base.run_id;
            out.finest_relative_cost_difference=abs(base.J_openocl-second.J_openocl)/max(abs(base.J_openocl),1e-12);
            [pass,comp]=eventsAgree(base,second); out.event_comparisons=comp;
            out.consistency_pass=pass && out.finest_relative_cost_difference<=cfg.revision.grid_cost_relative_tolerance;
        end
    elseif strcmp(group,'horizon')
        settings=[experiments(indices).solver_settings]; [~,order]=sort([settings.T]); chosen=chosen(order);
        if numel(chosen)==3 && all(cellfun(@usable,chosen))
            base=chosen{end}; out.reference_run_id=base.run_id;
            costs=cellfun(@(r) r.J_openocl,chosen); out.cost_absolute_span=max(costs)-min(costs);
            matches=true(1,numel(chosen)); comps=cell(1,numel(chosen)); windows=cell(1,numel(chosen));
            for j=1:numel(chosen)
                [matches(j),comps{j}]=eventsAgree(base,chosen{j});
                windows{j}=windowCompare(base,chosen{j},cfg.check.grid_time_tolerance);
                matches(j)=matches(j) && windows{j}.same_control_step;
            end
            out.event_comparisons=comps; out.common_window_comparisons=windows;
            out.consistency_pass=all(matches) && out.cost_absolute_span<=cfg.revision.horizon_cost_absolute_span_tolerance;
        end
    end
    if out.consistency_pass, out.status='passed';
    elseif isempty(out.reasons), out.reasons={'numeric diagnostics, structure, event comparison or cost tolerance not satisfied'}; end
    if isempty(summary.case_comparisons), summary.case_comparisons=out;
    else, summary.case_comparisons(end+1)=out; end
end
summary.consistency_pass=summary.protocol_complete && summary.comparison_complete && all([summary.case_comparisons.consistency_pass]);
if ~summary.protocol_complete || ~summary.comparison_complete, summary.status='blocked';
elseif ~summary.consistency_pass, summary.status='failed'; end
folder=fullfile(cfg.paths.data,'revision_checks');
numerical_write_json(fullfile(folder,[group '_summary.json']),summary);
table=struct2table(rmfield(summary.rows,'event_intervals'));
writetable(table,fullfile(folder,[group '_summary.csv']));
end

function main=mainSources(cfg,experiments,runs)
main=cell(1,5); source=numerical_code_hash('solve'); saved={}; spec=numerical_assessment_spec(cfg);
for k=1:5
    id=sprintf('E%d',k);
    ix=find(arrayfun(@(e) strcmp(e.case_id,id) && any(strcmp(e.groups,'main')),experiments));
    if isscalar(ix) && ~isempty(runs{ix}), main{k}=runs{ix}; end
end
if any(cellfun(@isempty,main))
    try, saved=load_selected_numerical_runs(cfg.paths.data);
    catch exception
        if ~strcmp(exception.identifier,'numerical:MissingSelectionManifest'), rethrow(exception); end
    end
end
for k=1:5
    if isempty(main{k}) && ~isempty(saved), main{k}=saved{k}; end
    r=main{k}; if isempty(r), continue; end
    ix=find(strcmp({cfg.cases.id},sprintf('E%d',k))); opts=cfg.solve;
    opts.N=cfg.cases(ix).main_N; opts.initialization='analytic_reference';
    required={'provenance','solver_settings','initialization','parameters','x0'};
    if ~all(isfield(r,required)) || ~strcmp(r.provenance.solve_code_hash,source.hash) || ...
            ~isequaln(r.solver_settings,opts) || ~strcmp(r.initialization.type,'analytic_reference') || ...
            ~isequal(r.parameters,cfg.parameters) || ~isequal(r.x0(:),cfg.cases(ix).x0(:))
        main{k}=[];
        continue;
    end
    current=isfield(r,'assessment_provenance') && isfield(r,'assessment_settings') && ...
        strcmp(r.assessment_provenance.code_hash,spec.code_hash) && isequaln(r.assessment_settings,spec.settings);
    if ~current
        index=jsondecode(fileread(fullfile(cfg.paths.data,'run_index.json')));
        entry=find(strcmp({index.entries.run_id},r.run_id)); assert(isscalar(entry));
        rawPath=fullfile(cfg.paths.data,index.entries(entry).raw_file);
        assert(strcmp(numerical_sha256(rawPath,'file'),index.entries(entry).raw_sha256), ...
            'numerical:RawRecordModified','Main comparison raw record changed.');
        loaded=load(rawPath,'run');
        [main{k},~]=assess_saved_numerical_run(loaded.run,cfg.paths.data, ...
            @(raw) numerical_assessment_view(raw,cfg),spec,false);
    end
end
end
function yes=usable(r)
yes=~isempty(r) && r.success && isfield(r,'J_openocl') && isfinite(r.J_openocl) && ...
    isfield(r,'assessment') && all(isfield(r.assessment,{'numeric_pass','observed_structure', ...
    'structured_events','event_detection','event_comparison'})) && r.assessment.numeric_pass && ...
    r.assessment.event_detection.diagnostics.passed && r.assessment.event_comparison.diagnostic_pass;
end
function [yes,comparison]=eventsAgree(a,b)
yes=usable(a) && usable(b); comparison=struct(); if ~yes, return; end
yes=strcmp(a.assessment.observed_structure,b.assessment.observed_structure);
names=fieldnames(a.assessment.structured_events);
for k=1:numel(names)
    first=a.assessment.structured_events.(names{k}); second=b.assessment.structured_events.(names{k});
    distance=NaN; allowed=NaN;
    if first.candidate_count==1 && second.candidate_count==1
        distance=max([first.interval(1)-second.interval(2),second.interval(1)-first.interval(2),0]);
        allowed=max(first.local_max_cell_width,second.local_max_cell_width);
        pass=distance<=allowed+1e-10;
    else
        pass=first.candidate_count==0 && second.candidate_count==0;
    end
    comparison.(names{k})=struct('passed',pass,'reference_interval',first.interval, ...
        'other_interval',second.interval,'distance_between_intervals',distance,'allowed_cell_width',allowed);
    yes=yes && pass;
end
end
function out=windowCompare(a,b,tol)
ta=a.assessment.reintegration.t; tb=b.assessment.reintegration.t;
ia=find(ta<=18+tol); ib=find(tb<=18+tol);
out=struct('interval',[0 18],'same_control_step',false, ...
    'state_max_abs_difference',NaN,'control_max_abs_difference',NaN, ...
    'sampling','common original control starts and reintegrated state nodes; no interpolation');
out.same_control_step=numel(ia)==numel(ib) && max(abs(ta(ia)-tb(ib)))<=tol;
if out.same_control_step
    xa=[a.assessment.reintegration.s(ia) a.assessment.reintegration.i(ia)];
    xb=[b.assessment.reintegration.s(ib) b.assessment.reintegration.i(ib)];
    out.state_max_abs_difference=max(abs(xa-xb),[],'all');
    ca=find(a.t_control<=18+tol); cb=find(b.t_control<=18+tol);
    out.control_max_abs_difference=max(abs(a.q_control(ca)-b.q_control(cb)));
end
end
