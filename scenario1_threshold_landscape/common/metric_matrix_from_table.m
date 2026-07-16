function Z = metric_matrix_from_table(T, c0_list, eta_frac_list, metric_name)
%METRIC_MATRIX_FROM_TABLE Reshape a metric into c0-by-eta grid order.

Z = nan(numel(c0_list), numel(eta_frac_list));
for j = 1:numel(c0_list)
    for i = 1:numel(eta_frac_list)
        idx = abs(T.c0 - c0_list(j)) < 1e-10 & ...
            abs(T.eta_frac - eta_frac_list(i)) < 1e-10;
        if any(idx)
            found = find(idx, 1);
            Z(j, i) = T.(metric_name)(found);
        end
    end
end
end
