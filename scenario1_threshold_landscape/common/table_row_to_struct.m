function row = table_row_to_struct(T)
%TABLE_ROW_TO_STRUCT Convert one readtable row to a scalar struct.

if height(T) ~= 1
    error('Expected exactly one table row.');
end
row = struct();
names = T.Properties.VariableNames;
for k = 1:numel(names)
    value = T.(names{k})(1);
    if iscell(value)
        value = value{1};
    end
    row.(names{k}) = value;
end
if ~isfield(row, 'status_code')
    row.status_code = "ok";
end
end
