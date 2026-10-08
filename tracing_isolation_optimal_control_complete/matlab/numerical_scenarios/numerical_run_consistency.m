function out = numerical_run_consistency(run,par,tol)
% 核查记录自身的来源和原OCP声明；不要求历史求解源码等于当前评估源码。
out=struct('provenance_pass',false,'problem_pass',false,'reasons',{{}});
needed={'run_id','provenance','solve_fingerprint','solve_fingerprint_payload','source_status'};
if ~all(isfield(run,needed)) || ~strcmp(run.source_status,'verified_record')
    out.reasons{end+1}='legacy_or_missing_provenance'; return;
end
p=run.provenance; payload=run.solve_fingerprint_payload;
fields={'solve_commit','solve_code_hash','solve_dirty','solve_started_utc','environment_fingerprint'};
if ~all(isfield(p,fields)) || ~islogical(p.solve_dirty) || ...
        isempty(p.solve_code_hash) || strcmp(p.solve_code_hash,'unknown') || ...
        isempty(p.solve_started_utc) || strcmp(p.solve_started_utc,'unknown')
    out.reasons{end+1}='incomplete_solve_provenance'; return;
end
out.provenance_pass=strcmp(run.solve_fingerprint,numerical_sha256(payload)) && ...
    isfield(payload,'solve_code_hash') && strcmp(p.solve_code_hash,payload.solve_code_hash) && ...
    isfield(payload,'environment_fingerprint') && strcmp(p.environment_fingerprint,payload.environment_fingerprint);
if ~out.provenance_pass, out.reasons{end+1}='fingerprint_or_source_mismatch'; end
fields={'case_id','parameters','x0','solver_settings','actual_solver_settings','actual_grid', ...
    'initialization','initial_guess'};
consistent=all(isfield(run,fields)) && all(isfield(payload,fields));
if consistent
    for k=1:numel(fields), consistent=consistent && isequaln(run.(fields{k}),payload.(fields{k})); end
end
if ~consistent, out.reasons{end+1}='request_does_not_match_output_record'; end
settingsOK=false;
if isfield(run,'actual_solver_settings')
    a=run.actual_solver_settings;
    needed={'controls_regularization','terminal_constraint','terminal_cost','grid_constraints', ...
        'grid_costs','state_lower_bounds','state_upper_bounds','control_lower_bound','control_upper_bound','initial_state','T','N'};
    if all(isfield(a,needed))
        settingsOK=~a.controls_regularization && strcmp(a.terminal_constraint,'none') && ...
            strcmp(a.terminal_cost,'none') && strcmp(a.grid_constraints,'none') && strcmp(a.grid_costs,'none') && ...
            isequal(a.state_lower_bounds,[0 0]) && isequal(a.state_upper_bounds,[1 par.K]) && ...
            a.control_lower_bound==0 && a.control_upper_bound==1 && ...
            isequal(a.initial_state(:),run.x0(:)) && abs(a.T-run.t_state(end))<=tol && a.N==numel(run.q_control);
    end
end
out.problem_pass=consistent && settingsOK && isequal(run.parameters,par);
if ~out.problem_pass, out.reasons{end+1}='problem_parameters_bounds_or_horizon_mismatch'; end
end
