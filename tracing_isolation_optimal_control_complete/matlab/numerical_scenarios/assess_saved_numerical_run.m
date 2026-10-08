function [view,called] = assess_saved_numerical_run(run,dataRoot,assessor,spec,force)
% 评估单独保存；不得重新保存或改写runs中的原始记录。
if nargin<5, force=false; end
if ~isfield(run,'run_id') || ~isfield(run,'provenance') || ~isfield(run,'solve_fingerprint')
    run.source_status='legacy_unverified';
    run.run_id=['legacy_' numerical_sha256(run)];
    run.solve_fingerprint='legacy_unverified';
    run.provenance=struct('source_status','legacy_unverified','solve_commit','unknown', ...
        'solve_started_utc','unknown','solve_code_hash','unknown','solve_dirty','unknown');
end
fingerprint=numerical_sha256(struct('solve_fingerprint',run.solve_fingerprint, ...
    'raw_output_hash',numerical_sha256(run),'assessment',spec));
folder=fullfile(dataRoot,'revision_checks','assessments'); if ~isfolder(folder), mkdir(folder); end
prefix=[run.run_id '_' fingerprint '_'];
files=dir(fullfile(folder,[prefix '*.mat'])); called=false;
if ~force && ~isempty(files)
    [~,ix]=max([files.datenum]); record=load(fullfile(files(ix).folder,files(ix).name),'assessment_record');
    record=record.assessment_record;
    assert(strcmp(record.run_id,run.run_id) && strcmp(record.assessment_fingerprint,fingerprint));
else
    called=true; view=assessor(run);
    % 回调只允许返回reference和assessment；不会污染求解来源。
    assert(isfield(view,'reference') && isfield(view,'assessment'),'Assessment callback must return reference and assessment.');
    provenance=struct('code_hash',spec.code_hash,'checked_utc',numerical_utc(), ...
        'assessment_fingerprint',fingerprint,'settings',spec.settings,'source_status',run.source_status);
    record=struct('run_id',run.run_id,'solve_fingerprint',run.solve_fingerprint, ...
        'reference',view.reference,'assessment',view.assessment,'assessment_provenance',provenance, ...
        'assessment_fingerprint',fingerprint,'assessment_settings',spec.settings);
    if isfield(spec,'source_files'), record.assessment_provenance.source_files=spec.source_files; end
    assessment_record=record; %#ok<NASGU>
    filename=fullfile(folder,[prefix strrep(char(java.util.UUID.randomUUID()),'-','') '.mat']);
    assert(~isfile(filename)); save(filename,'assessment_record','-v7');
end
view=run; view.reference=record.reference; view.assessment=record.assessment;
view.assessment_provenance=record.assessment_provenance;
view.assessment_fingerprint=record.assessment_fingerprint;
view.assessment_settings=record.assessment_settings;
end
