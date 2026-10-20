function par = numerical_normalize_parameters(par)
% 旧记录中的p表示传播概率；只规范化计算副本，不改raw或其指纹载荷。
assert(isstruct(par) && isscalar(par),'numerical:InvalidParameters', ...
    'Parameters must be a scalar structure.');
old=isfield(par,'p'); current=isfield(par,'beta');
assert(old || current,'numerical:MissingProbability', ...
    'Parameters must contain beta or the historical probability field p.');
if old && current
    assert(isequaln(par.p,par.beta),'numerical:ConflictingProbability', ...
        'Historical probability p and beta must agree when both are present.');
    par=rmfield(par,'p');
elseif old
    names=fieldnames(par); names(strcmp(names,'p'))={'beta'};
    par=cell2struct(struct2cell(par),names,1);
end
end
