function [T, cfg] = read_landscape_table(mode)
%READ_LANDSCAPE_TABLE Read the active run landscape summary.

if nargin < 1 || isempty(mode)
    mode = 'current';
end

cfg = scenario1_params(mode);
filename = fullfile(cfg.paths.output_csv, 'landscape_summary.csv');
if ~exist(filename, 'file')
    error('Missing landscape summary: %s', filename);
end
T = readtable(filename);
end
