function cfg = scenario1_params(mode)
%SCENARIO1_PARAMS Shared parameters and run-directory state.

if nargin < 1 || isempty(mode)
    mode = 'current';
end

base_dir = fileparts(fileparts(mfilename('fullpath')));
state_file = fullfile(base_dir, 'current_run.mat');
current_dir = fullfile(base_dir, 'current_run');
archive_dir = fullfile(base_dir, 'archive_runs');

cfg.beta = 0.155;
cfg.gamma = 0.3504;
cfg.q0 = 0.01526;
cfg.N = 763;
cfg.S0 = 762;
cfg.I0 = 1;
cfg.c0_base = 10;

cfg.eta_frac_list = 0.002:0.0002:0.020;
cfg.eta_list = cfg.eta_frac_list * cfg.N;
cfg.eta_percent_list = 100 * cfg.eta_frac_list;
cfg.c0_list = 6:0.1:14;

cfg.selected_eta_frac = [0.002, 0.005, 0.010, 0.020];
cfg.c0_response_eta_frac = [0.002, 0.010, 0.020];
cfg.selected_c0 = [6, 10, 14];
cfg.baseline_eta_frac = [0.020, 0.002];

cfg.paths.base_dir = base_dir;
cfg.paths.state_file = state_file;

switch lower(string(mode))
    case {"new", "create"}
        run_id = datestr(now, 'yyyymmdd_HHMMSS');
        if exist(current_dir, 'dir')
            archived_run = archive_existing_run(current_dir, archive_dir, run_id);
            fprintf('Archived previous current_run to:\n%s\n', archived_run);
        end
        run_dir = current_dir;
        cfg.run_id = run_id;
        cfg.paths = fill_run_paths(cfg.paths, run_dir);
        save(state_file, 'run_dir', 'run_id');
        write_current_run_text(base_dir, run_dir);

    case {"current", "read"}
        if exist(current_dir, 'dir')
            run_dir = current_dir;
            run_id = "current";
            cfg.run_id = run_id;
            save(state_file, 'run_dir', 'run_id');
            write_current_run_text(base_dir, run_dir);
        elseif exist(state_file, 'file')
            S = load(state_file, 'run_dir', 'run_id');
            run_dir = S.run_dir;
            if isfield(S, 'run_id')
                cfg.run_id = S.run_id;
            else
                cfg.run_id = get_run_id_from_dir(run_dir);
            end
        else
            run_dir = current_dir;
            run_id = "current";
            cfg.run_id = run_id;
            save(state_file, 'run_dir', 'run_id');
            write_current_run_text(base_dir, run_dir);
        end
        cfg.paths = fill_run_paths(cfg.paths, run_dir);

    otherwise
        error('Unknown scenario1_params mode: %s', mode);
end
end

function paths = fill_run_paths(paths, run_dir)
paths.run_dir = run_dir;
paths.output_csv = fullfile(run_dir, 'output_csv');
paths.figures = fullfile(run_dir, 'figures');
paths.tables = fullfile(run_dir, 'tables');
paths.logs = fullfile(run_dir, 'logs');
end

function run_id = get_run_id_from_dir(run_dir)
[~, name] = fileparts(run_dir);
run_id = erase(name, 'run_');
end

function archived_run = archive_existing_run(current_dir, archive_dir, run_id)
if ~exist(archive_dir, 'dir')
    mkdir(archive_dir);
end
archived_run = fullfile(archive_dir, ['run_' run_id]);
suffix = 0;
while exist(archived_run, 'dir')
    suffix = suffix + 1;
    archived_run = fullfile(archive_dir, sprintf('run_%s_%02d', run_id, suffix));
end
[ok, message] = movefile(current_dir, archived_run, 'f');
if ~ok
    [status, output] = system(sprintf([ ...
        'powershell -NoProfile -ExecutionPolicy Bypass -Command ', ...
        '"Move-Item -LiteralPath ''%s'' -Destination ''%s'' -Force"'], ...
        escape_single_quotes(current_dir), escape_single_quotes(archived_run)));
    if status ~= 0
        [copy_ok, copy_message] = copyfile(current_dir, archived_run, 'f');
        if ~copy_ok
            error(['Failed to archive current_run: %s ', ...
                'PowerShell fallback: %s Copy fallback: %s'], ...
                message, output, copy_message);
        end
        fprintf(['Could not move current_run because of file permissions. ', ...
            'Copied it to archive_runs and will overwrite current_run in place.\n']);
    end
end
end

function value = escape_single_quotes(value)
value = strrep(value, '''', '''''');
end

function write_current_run_text(base_dir, run_dir)
fid = fopen(fullfile(base_dir, 'current_run.txt'), 'w');
if fid >= 0
    cleaner = onCleanup(@() fclose(fid)); %#ok<NASGU>
    fprintf(fid, '%s\n', run_dir);
end
end
