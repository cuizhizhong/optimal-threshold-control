function provenance = numerical_export_provenance(kind,manifest,dataRoot)
% 导出时间与源码单独记录，不代替solve_started_utc。
source=numerical_code_hash(kind);
provenance=struct('kind',kind,'code_hash',source.hash,'source_files',source.files, ...
    'exported_utc',numerical_utc(),'selection_manifest_hash',numerical_sha256(manifest), ...
    'selected_run_ids',{{manifest.entries.run_id}});
numerical_write_json(fullfile(dataRoot,[kind '_provenance.json']),provenance);
end
