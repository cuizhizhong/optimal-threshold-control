function log_line(logfid, message)
%LOG_LINE Print a timestamped line to the console and an optional log file.

line = sprintf('[%s] %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), message);
fprintf('%s', line);
if ~isempty(logfid) && logfid > 0
    fprintf(logfid, '%s', line);
end
end
