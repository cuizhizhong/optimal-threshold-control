function peak = safe_peak(s, i, h)
%SAFE_PEAK Future peak under zero tracing for the constant-contact model.
% Numeric post-processing only; not the symbolic OpenOCL callback.
% s and i must have the same shape, or one must be scalar.
validateattributes(s, {'numeric'}, {'real', 'finite', 'nonnegative'}, mfilename, 's');
validateattributes(i, {'numeric'}, {'real', 'finite', 'nonnegative'}, mfilename, 'i');
validateattributes(h, {'numeric'}, {'real', 'finite', 'scalar', 'positive'}, mfilename, 'h');
assert(isequal(size(s), size(i)) || isscalar(s) || isscalar(i), ...
    's and i must have matching sizes, or one must be scalar.');
m = max(s, h);
% 先计算易感部分，避免 s<=h 时把极小正感染数与 h 相加后消去。
peak = i + (m - h - h .* log(m ./ h));
end
