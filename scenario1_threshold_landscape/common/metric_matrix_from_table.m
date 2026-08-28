function Z = metric_matrix_from_table(T, c0_list, eta_frac_list, metric_name)
%METRIC_MATRIX_FROM_TABLE Reshape a metric into c0-by-eta grid order.

Z = nan(numel(c0_list), numel(eta_frac_list));
[found_c0, c0_index] = ismembertol(T.c0(:), c0_list(:), 1e-10, ...
    'DataScale', 1);
[found_eta, eta_index] = ismembertol(T.eta_frac(:), eta_frac_list(:), 1e-10, ...
    'DataScale', 1);
found = found_c0 & found_eta;
linear_index = sub2ind(size(Z), c0_index(found), eta_index(found));
values = T.(metric_name);
Z(linear_index) = values(found);
end
