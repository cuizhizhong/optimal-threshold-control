function ensure_output_dirs(cfg)
%ENSURE_OUTPUT_DIRS Create the active run output directories.

dirs = {cfg.paths.run_dir, cfg.paths.output_csv, cfg.paths.figures, ...
    cfg.paths.tables, cfg.paths.logs};
for k = 1:numel(dirs)
    if ~exist(dirs{k}, 'dir')
        mkdir(dirs{k});
    end
end
end
