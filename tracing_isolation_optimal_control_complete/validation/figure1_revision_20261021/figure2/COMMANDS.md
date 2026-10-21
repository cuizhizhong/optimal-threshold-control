# 图2刷新及 S2.7 导出回归

基准：`54470c531e3214bdf379b073f69593ec47fecb6a`。本目录只记录本轮运行，不覆盖历史 S2.7 报告。

从项目目录执行基准备份：

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/figure2/capture_before.py
```

从仓库根目录执行以下 MATLAB 入口。`run_figure2_refresh` 实际依次调用用户指定的 `make_numerical_figures(); r=export_numerical_latex(); assert(r.verified && r.optimizer_executions==0);`，随后核对正式 `main.tex` 内容未变，并将本轮报告写在这里。

```powershell
$taskTemp='E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete/validation/figure1_revision_20261021/figure2/matlab_tmp'
New-Item -ItemType Directory -Path $taskTemp -Force | Out-Null
$env:TEMP=$taskTemp
$env:TMP=$taskTemp
& 'E:/software/Matlab/bin/matlab.exe' -logfile 'E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete/validation/figure1_revision_20261021/figure2/refresh_console.log' -batch "addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios')); addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','figure1_revision_20261021','figure2')); run_figure2_refresh();"
```

前一入口完成后，另一次入口加上本轮报告目录并调用 `run_s27_regression()`。本轮驱动是旧驱动的**字节相同副本**；它使用 `mfilename('fullpath')` 定位输出，因此输出落在本目录的 `S2.7/regression_report.json`，历史报告保持原样。故障注入临时目录由原驱动各测试自己的清理函数删除，不构成科学结果。

先从项目目录保存刚完成导出的 `main_after_export.tex` 快照，再运行回归；此快照和导出前正文逐字相同，允许并行工作随后只修改获授权的图注。首次误在仓库根目录以项目内相对路径执行 `Copy-Item`，提示找不到 `latex/main.tex`；已在项目目录立即纠正，未改变 MATLAB 命令或计算结果。

```powershell
Copy-Item -LiteralPath 'latex/main.tex' -Destination 'validation/figure1_revision_20261021/figure2/main_after_export.tex'
```

```powershell
$env:TEMP='E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete/validation/figure1_revision_20261021/figure2/matlab_tmp'
$env:TMP=$env:TEMP
& 'E:/software/Matlab/bin/matlab.exe' -logfile 'E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete/validation/figure1_revision_20261021/figure2/regression_console.log' -batch "addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios')); addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','figure1_revision_20261021','figure2')); run_s27_regression();"
```

从项目目录执行导出后核对。PDF 比较实际调用 `pdftoppm -r 150 -png -singlefile`，完整路径与退出码写入 JSON；PNG 比较不重采样。

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/figure2/collect_after.py
```

限制：没有运行任何优化器、OCP 求解或历史重跑入口。现有 `timepanels` 为重绘 FigN2/N3 仍按原流程调用 `analytic_reference` 的积分与 `ode45`；没有另起 ODE 实验。
