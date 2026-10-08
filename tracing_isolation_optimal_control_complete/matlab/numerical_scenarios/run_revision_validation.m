function report = run_revision_validation(mode,force)
% 正式入口；unit不加载优化依赖，threshold只读取已保存的主结果。
if nargin<1 || isempty(mode), mode='all'; end
if nargin<2, force=false; end
report=revision_validation_dispatch(revision_validation_config(),mode,force);
end
