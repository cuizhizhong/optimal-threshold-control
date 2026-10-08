function [runs,manifest] = load_selected_numerical_runs(dataRoot)
% 图/导出入口严格核对manifest、兼容副本和不可覆盖原始记录。
filename=fullfile(dataRoot,'selection_manifest.json');
assert(isfile(filename),'numerical:MissingSelectionManifest', ...
    'Missing %s. Historical files are legacy_unverified; run main only after code freeze.',filename);
manifest=jsondecode(fileread(filename));
assert(manifest.schema_version==1 && numel(manifest.entries)==5,'Invalid main selection manifest.');
runs=cell(1,5);
for k=1:5
    id=sprintf('E%d',k); ix=find(strcmp({manifest.entries.case_id},id)); assert(isscalar(ix));
    entry=manifest.entries(ix); compatibility=fullfile(dataRoot,[id '.mat']);
    assert(strcmp(entry.compatibility_file,[id '.mat']) && isfile(compatibility),'Missing selected compatibility copy: %s',id);
    assert(strcmp(numerical_sha256(compatibility,'file'),entry.compatibility_sha256), ...
        'numerical:SelectionMismatch','Compatibility file does not match selection manifest: %s',id);
    d=load(compatibility,'run'); run=d.run;
    assert(strcmp(run.case_id,id) && run.success && isfield(run,'source_status') && strcmp(run.source_status,'verified_record') && ...
        strcmp(run.run_id,entry.run_id) && strcmp(run.solve_fingerprint,entry.solve_fingerprint) && ...
        strcmp(run.assessment_fingerprint,entry.assessment_fingerprint),'Untrusted selected run: %s',id);
    rawPath=fullfile(dataRoot,entry.raw_file); assert(isfile(rawPath),'Missing immutable raw run: %s',entry.run_id);
    assert(strcmp(numerical_sha256(rawPath,'file'),entry.raw_sha256),'Selected raw run was modified.');
    d=load(rawPath,'run'); raw=d.run;
    assert(strcmp(raw.run_id,run.run_id) && strcmp(raw.solve_fingerprint,run.solve_fingerprint) && ...
        isequal(raw.provenance,run.provenance),'Solve provenance was changed in compatibility copy.');
    % 同时核对全部原始求解字段；reference/assessment/selection另有来源。
    fields=fieldnames(raw);
    for j=1:numel(fields)
        assert(isfield(run,fields{j}) && isequaln(raw.(fields{j}),run.(fields{j})), ...
            'numerical:RawOutputMismatch','Selected raw output differs at %s.',fields{j});
    end
    runs{k}=run;
end
end
