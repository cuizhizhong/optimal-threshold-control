# S2 实际执行命令

工作目录为 `E:\work\optimal-threshold-control`。本页汇总已执行入口，不是再次求解的指令。优化器仅在 S2.4 实际执行一次完整 35 配置矩阵。Python 实际解释器为 `E:\anaconda\python.exe`，下文用 `python` 表示。

## S2.1–S2.3

S2.1 精确命令、初次页数解析问题及主文/TheoryOnly 构建见 `../../code_rename_s21_20261020/README.md`。实际标签为：

```powershell
git tag pre-code-rename 051099fba63cd6d326f2344d2bf4322c1f651282
git rev-parse pre-code-rename
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py capture --step S2.2
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -X utf8 tracing_isolation_optimal_control_complete/validation/numerical_scenarios/test_analytic_checkpoints.py
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/verify_checkpoint_migration.py --report tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/S2.3/checkpoint_migration_report.json
```

## MATLAB 实际入口

每次通过 `E:\software\Matlab\bin\matlab.exe -logfile <各步控制台日志> -batch <内容>` 执行，内容先执行计划规定的：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
```

S2.2 随后执行 `verify_numerical_parameters()` 并保存报告，9 项通过。

S2.4：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','numerical_scenarios','rerun_20261020'));
run_s24();
```

驱动依次实际执行 `revision_preflight()`、`run_revision_validation('unit',false)`、`run_revision_validation('all',false)`；记录 35 次求解、0 缓存、计时和两个 13 组 unit 结果。已有执行报告时拒绝重复入口。

S2.5：`r=compare_rerun_results(); assert(r.passed);`。

S2.6 先加与 S2.4 相同的报告目录路径，再执行 `r=refresh_original_criterion(); assert(strcmp(r.status,'completed'));`。

S2.7 先执行 `make_numerical_figures(); r=export_numerical_latex(); assert(r.verified && r.optimizer_executions==0);`，另一次入口加报告目录路径后调用 `run_s27_regression()`。驱动实际调用 `verify_saved_result_exporter`、`verify_revision_exporter`、`verify_pending_result_exporter`，11+3+2 项通过。

控制台与 JSON 分别保存于 S2.2、S2.4–S2.7 目录。

## 正文、页面与最终核对

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/verify_exported_macros.py
pdftotext -layout tracing_isolation_optimal_control_complete/latex/main.pdf tracing_isolation_optimal_control_complete/tmp/rerun_20261020/S2.7/main_published.txt
```

三幅 PNG 通过图片查看器实际检查。`pdftoppm -f <页> -l <页> -singlefile -scale-to 1800 -png` 实际渲染主文第 28、29、30 页后逐页查看；页面路径和 SHA-256 记在 S2.7/visual_qa.json。

S2.2–S2.9 每一步实际执行下面两条命令，`<步骤>` 分别取 S2.2 至 S2.9；S2.7、S2.9 构建额外使用 `--publish`：

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py <步骤>
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step <步骤>
```

构建实际运行 XeLaTeX → BibTeX → XeLaTeX × 2。绝对路径、工作目录、退出码、日志、37 页及最终检查均在各步 build_report.json。S2.1 实际双稿构建另有独立报告。

S2.9 汇总入口为 `python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/finalize_report.py`，只核对已存证据并写汇总清单，不运行 MATLAB。另用 `pdftotext -layout` 比较 S2.9 最终 PDF 与 S2.7 已目视 PDF 的文字。

各步按 JSON 精确路径清单用 `git -c core.longpaths=true -c core.safecrlf=false add -- <路径列表>` 暂存，核对范围与非日志空白后独立提交，未执行 push。工具原始日志的行尾空白保留。
