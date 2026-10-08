function passed = numerical_additional_verification(r,cfg,kind,spec)
% 附加旗标对应预定请求；文件名或来源标签本身不能证明复核组已完成。
passed=false;
required={'case_id','parameters','x0','solver_settings','initialization','success','source_status', ...
    'assessment','assessment_provenance','assessment_settings'};
if ~all(isfield(r,required)) || ~all(isfield(r.assessment,{'numeric_pass','agreement_pass'})), return; end
if strcmp(kind,'grid')
    id=cfg.check.refine_case_id; N=cfg.check.refine_N; guess='analytic_reference';
elseif strcmp(kind,'neutral')
    id=cfg.check.neutral_guess_case_id; N=cfg.solve.N; guess='constant_control';
else
    error('numerical:UnknownCheckKind','Unknown additional check kind: %s',kind);
end
ix=find(strcmp({cfg.cases.id},id)); assert(isscalar(ix));
guessOK=strcmp(r.initialization.type,guess);
if strcmp(guess,'constant_control')
    guessOK=guessOK && isfield(r.initialization,'control') && r.initialization.control==cfg.check.neutral_control;
end
expectedSettings=cfg.solve; expectedSettings.N=N; expectedSettings.initialization=guess;
passed=strcmp(r.source_status,'verified_record') && r.success && ...
    strcmp(r.case_id,id) && isequal(r.parameters,cfg.parameters) && isequal(r.x0(:),cfg.cases(ix).x0(:)) && ...
    isequaln(r.solver_settings,expectedSettings) && ...
    guessOK && r.assessment.numeric_pass && r.assessment.agreement_pass && ...
    isfield(r.assessment_provenance,'code_hash') && strcmp(r.assessment_provenance.code_hash,spec.code_hash) && ...
    isequaln(r.assessment_settings,spec.settings);
end
