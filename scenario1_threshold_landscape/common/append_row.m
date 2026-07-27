function rows = append_row(rows, row, idx)
%APPEND_ROW Append a scalar struct to a struct array by index.

if idx == 1
    rows = row;
else
    rows(idx) = row;
end
end
