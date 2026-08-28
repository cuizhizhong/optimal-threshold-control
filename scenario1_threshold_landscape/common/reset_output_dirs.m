function reset_output_dirs(cfg)
%RESET_OUTPUT_DIRS Clear previous outputs so no stale files linger.
%   Removes and recreates output_csv/figures/tables/logs. Call this once at
%   the start of a full run (run_all). Do NOT call it when rerunning a single
%   plot script, or you will wipe the other outputs.

dirs = {cfg.paths.output_csv, cfg.paths.figures, cfg.paths.tables, cfg.paths.logs};
for k = 1:numel(dirs)
    if exist(dirs{k}, 'dir')
        [ok, msg] = rmdir(dirs{k}, 's');
        if ~ok
            warning('reset_output_dirs:cannotClear', ...
                'Could not clear %s (%s). Close any open file there and rerun.', ...
                dirs{k}, msg);
        end
    end
end
ensure_output_dirs(cfg);
end
