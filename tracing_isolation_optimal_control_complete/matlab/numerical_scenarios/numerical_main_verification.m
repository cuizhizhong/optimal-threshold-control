function out = numerical_main_verification(runs,cases,parameters,settings,assessmentSpec)
% 五例主结果和附加实验的状态分开；缺失新评估旗标时拒绝沿用旧passed。
out=struct('verified',false,'case_pass',false(1,numel(cases)),'status','incomplete');
if nargin<5 || numel(runs)~=numel(cases), return; end
for k=1:numel(cases)
    r=runs{k};
    needed={'case_id','success','assessment','x0','parameters','solver_settings','initialization', ...
        'assessment_provenance','assessment_settings'};
    if ~all(isfield(r,needed)) || ~all(isfield(r.assessment,{'numeric_pass','agreement_pass'})), continue; end
    expectedSettings=settings; expectedSettings.N=cases(k).main_N; expectedSettings.initialization='analytic_reference';
    requestOK=isequal(r.x0(:),cases(k).x0(:)) && isequal(r.parameters,parameters) && ...
        isequaln(r.solver_settings,expectedSettings) && strcmp(r.initialization.type,'analytic_reference');
    assessmentCurrent=isfield(r.assessment_provenance,'code_hash') && ...
        strcmp(r.assessment_provenance.code_hash,assessmentSpec.code_hash) && ...
        isequaln(r.assessment_settings,assessmentSpec.settings);
    out.case_pass(k)=strcmp(r.case_id,cases(k).id) && r.success && ...
        requestOK && assessmentCurrent && r.assessment.numeric_pass && r.assessment.agreement_pass && ...
        strcmp(r.assessment.observed_structure,cases(k).expected_structure);
end
out.verified=all(out.case_pass);
if out.verified, out.status='passed'; else, out.status='failed_or_incomplete'; end
end
