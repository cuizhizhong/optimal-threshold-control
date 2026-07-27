function logfid = open_log(cfg, name)
%OPEN_LOG Open a per-script log file under the run's logs directory.

logfid = fopen(fullfile(cfg.paths.logs, name), 'w');
if logfid < 0
    error('Cannot open log file: %s', name);
end
end
