function out = tail_diagnostic(t_control, q_control, sT, iT, par, T, tail_duration, tol, capacity_tol)
%TAIL_DIAGNOSTIC Post-processing check for a long finite-horizon run.
% This function does NOT impose a terminal constraint on the OCP.
% It only checks, after solving, whether the reported numerical trajectory
% has returned to an approximately zero-control tail and whether the final
% state admits a safe zero-control continuation in the constant-contact model.

validateattributes(t_control, {'numeric'}, {'real','finite','vector'}, mfilename, 't_control');
validateattributes(q_control, {'numeric'}, {'real','finite','vector'}, mfilename, 'q_control');
assert(numel(t_control) == numel(q_control), ...
    't_control and q_control must have the same length.');
validateattributes(T, {'numeric'}, {'real','finite','scalar','positive'}, mfilename, 'T');
validateattributes(tail_duration, {'numeric'}, {'real','finite','scalar','positive'}, mfilename, 'tail_duration');
validateattributes(tol, {'numeric'}, {'real','finite','scalar','nonnegative'}, mfilename, 'tol');
if nargin<9, capacity_tol=tol; end
validateattributes(capacity_tol,{'numeric'},{'real','finite','scalar','nonnegative'});

p = par.p; c = par.c; gamma = par.gamma; K = par.K;
h = gamma / (p*c);

left = max(0, T - tail_duration);
t_control = t_control(:);
q_control = q_control(:);
right_edges = [t_control(2:end); T];
assert(~isempty(t_control) && abs(t_control(1))<=1e-10 && all(right_edges>t_control), ...
    'numerical:TailIntervals','Tail diagnostic requires actual control intervals from zero to T.');
mask = right_edges(:) > left;
if any(mask)
    maxTailQ = max(abs(q_control(mask)));
else
    maxTailQ = NaN;
end

futurePeak = safe_peak(sT, iT, h);

out = struct();
out.tail_start_time = left;
out.max_abs_q_on_tail = maxTailQ;
out.control_returned_to_zero = isfinite(maxTailQ) && maxTailQ <= tol;
out.zero_control_future_peak = futurePeak;
out.zero_control_continuation_safe = isfinite(futurePeak) && futurePeak <= K + capacity_tol;
out.capacity = K;
out.tolerance = tol;
out.capacity_tolerance = capacity_tol;
out.terminal_state_source = 'original_control_reintegration';
out.tail_interval_indices = find(mask);
end
