# 第10–11步命令与实际证据

本记录只说明本批实际调用及其保存证据。科学结果使用已有35条记录；不得把下面的调用、计划中的预期数值或接口smoke作为新科学结果。是否完成以对应报告及退出码为准。

## 原工作区后处理

工作目录：`E:\work\optimal-threshold-control`。实际使用本机 MATLAB R2025b 和原仓库内已跟踪的依赖：

```powershell
$env:OPENOCL_ROOT='E:\work\optimal-threshold-control\optimal\OpenOCL-master 0104'
& 'E:\software\Matlab\bin\matlab.exe' -wait -nosplash -nodesktop -logfile 'E:\work\optimal-threshold-control\tracing_isolation_optimal_control_complete\validation\numerical_scenarios\step1011_postprocess.log' -batch "run('tracing_isolation_optimal_control_complete/validation/numerical_scenarios/execute_stage1011.m')"
```

入口实际调用 `revision_preflight()`、`verify_revision_validation_unit()`、`verify_revision_exporter()`、`verify_saved_result_exporter()`、两次 `export_numerical_latex()`、`make_numerical_figures()`。结果是12组unit、3项故障清空、当时8项保存数据回归；科学优化0次。首次错误目录的运行与日志保留为 `step1011_postprocess_attempt1.log`，随后使用 `mfilename('fullpath')` 修复定位。

另实际调用 `verify_pending_result_exporter()`，其2项临时 missing/blocked 输入不产生科学证据，核实旧通过宏被清空且不输出 NaN。日志、报告为 `step1011_pending_exporter.log`、`step1011_pending_exporter_report.json`。

最终 exporter 修改后实际重新导出两次：

```powershell
& 'E:\software\Matlab\bin\matlab.exe' -wait -nosplash -nodesktop -logfile 'E:\work\optimal-threshold-control\tracing_isolation_optimal_control_complete\validation\numerical_scenarios\step1011_final_export.log' -batch "run('tracing_isolation_optimal_control_complete/validation/numerical_scenarios/finalize_stage1011_export.m')"
```

`step1011_final_export_report.json` 记录两次导出均 verified、字节相同、编译源未改变、优化0次及最终实际来源指纹。来源旧快照另存 `step1011_source_fingerprints_postprocess.json`，当前快照逐文件核对并刷新最终 export 指纹。

## 实际双版本编译与页面检查

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& 'E:\anaconda\python.exe' 'tracing_isolation_optimal_control_complete/validation/numerical_scenarios/build_stage1011.py'
```

脚本在 `latex` 目录对 `main`、`theory_only` 分别实际执行以下四个进程；每一步退出码、完整输出及最终LaTeX日志均保存：

```text
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error theory_only.tex
bibtex theory_only
xelatex -interaction=nonstopmode -halt-on-error theory_only.tex
xelatex -interaction=nonstopmode -halt-on-error theory_only.tex
```

主文首次编译的11.08316pt溢出保留为 `step1011_main_attempt1_final.log`；修复只涉及附录换段。重编后主文34页、TheoryOnly26页，最终日志问题列表为空。包名/Info筛选的首次误报保留于 `step1011_build_attempt1_report.json`。当前真实结果见 `step1011_build_report.json`。

`pdftoppm -png -r 110 -f <页> -l <页> -singlefile main.pdf <输出前缀>` 实际渲染第5、25–30、33页；逐页人工检查8页和三张原始PNG，当前PDF SHA绑定于 `step1011_pdf_qa.json`。

## 候选成果的干净检出

```powershell
& 'E:\anaconda\python.exe' 'tracing_isolation_optimal_control_complete/validation/numerical_scenarios/prepare_stage1011_checkout.py'
```

该脚本从原HEAD的 `git archive` 加明确成果目录建立独立临时Git候选快照，原仓库不提交。实际候选 `E:\work\optimal-threshold-control\tmp\s12`，初始 `git status --porcelain=v1` 为空；显式排除ai、pending_deletion、tmp、Python缓存及LaTeX中间产物。源与目标均使用Windows长路径前缀，核实35条assessment完整复制。首次tar失败和漏复制长文件的候选均保留。

工作目录改为 `E:\work\optimal-threshold-control\tmp\s12`，显式 `OPENOCL_ROOT` 保持上述原依赖绝对路径和记录的环境指纹：

```powershell
$env:OPENOCL_ROOT='E:\work\optimal-threshold-control\optimal\OpenOCL-master 0104'
& 'E:\software\Matlab\bin\matlab.exe' -wait -nosplash -nodesktop -logfile 'E:\work\optimal-threshold-control\tracing_isolation_optimal_control_complete\validation\numerical_scenarios\step1011_clean_execution.log' -batch "run('tracing_isolation_optimal_control_complete/validation/numerical_scenarios/execute_stage1011_clean.m')"
```

入口实际调用 preflight、`run_revision_validation('unit',false)`、保存数据9项回归、`run_revision_validation('all',false)`、绘图和重复导出；再运行独立 `T=1,N=4,d=2` 的一个接口smoke。all模式只允许可信缓存复用，禁止把新增优化冒充缓存；smoke原始文件和报告与35条科学配置分开。

依赖限制：本候选复核使用当前机器内已跟踪且哈希匹配的OpenOCL/CasADi/MEX/DLL文件，不声称另一台机器的全新环境安装成功。

在候选项目目录还实际执行：

```powershell
& 'E:\anaconda\python.exe' 'validation/numerical_scenarios/generate_analytic_checkpoints.py' --check
& 'E:\anaconda\python.exe' -m unittest discover -s 'validation/numerical_scenarios' -p 'test_analytic_checkpoints.py'
```

6项测试通过，generator退出0、unittest退出0，fixture SHA未变；见 `step1011_clean_python_report.json`。

候选入口已实际退出0，可信缓存35、科学优化0、重新评估0、独立smoke成功1。严格一致性仍为false。随后在候选目录实际运行同一 `build_stage1011.py`，两个版本编译均成功、最终日志问题为空；保存为 `step1011_clean_build_report.json` 和带 `clean_` 前缀的8个过程日志/2个最终日志。

原工作区再实际运行：

```powershell
& 'E:\anaconda\python.exe' 'tracing_isolation_optimal_control_complete/validation/numerical_scenarios/compare_stage1011_candidate.py'
& 'E:\anaconda\python.exe' 'tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage1011.py'
```

候选对比确认35条raw/solver、35条assessment、输入和fixture字节不变；主TeX字节相同，7个当前入口/导出/图形源码与候选相同。兼容文件所有科学字段和数组相同，只有选择时间戳更新，相应兼容文件哈希及selection_manifest刷新。PNG时间戳均变化，像素实际差异数分别为3、1、0，已逐图视觉检查，不宣称图像字节相同。

完整性检查实际退出0，保护93个基准文件，完整冻结solve/assessment清单、三图精确来源、35条真实记录、28条双通过、未运行扩展留空及两份编译报告均已核对。第一次检查把 `NumTheoryRef` 定义中的 `#1` 误识别为标签，输出保留于 `step1011_integrity_attempt1.log`，仅修正检查器后再执行成功。

以上实际报告核对成功后，实际执行以下登记入口，退出0并输出 `STAGE1011_DELIVERY_REGISTERED`：

```powershell
& 'E:\anaconda\python.exe' 'tracing_isolation_optimal_control_complete/validation/numerical_scenarios/finalize_stage1011.py'
```

此入口先断言最终导出幂等且编译源未变、当前PDF与视觉QA的SHA绑定、clean双版编译成功、Python6tests/fixture检查成功、候选科学内容比较成功，再登记第10–11步完成。原Git HEAD未提交、未push。说明与MANIFEST是执行完毕后的交付文档，不用于替代实验记录。

## 执行异常

任何受限MATLAB偏好目录失败、目录定位失败、控制台编码失败、编译溢出、Windows长路径失败、漏复制评估文件、矢量导出提醒与Git换行提示均保留，最终清单为 `step1011_operational_anomalies.json`。科学上的7条诊断失败、E2/E4原严格grid一致性失败、主E4有符号成本差和容量超出另在 `step1011_results.md` 与 `step1011_validation_report.json` 中逐项保留。
