# S2.7：刷新图表、导出和回归

实际执行 `make_numerical_figures(); r=export_numerical_latex();`，导出 `verified=true`，优化器和科学求解均为 0。三幅图的 PDF/PNG 已刷新，六个文件的 SHA-256 与 `figure_provenance.json` 一致，选用的五个新 run_id 与 `selection_manifest.json` 一致。原判据来源绑定 S2.6 新报告及其 SHA-256。

实际运行三项回归：`verify_saved_result_exporter` 11 项、`verify_revision_exporter` 3 项、`verify_pending_result_exporter` 2 项，16 项全部通过。测试中的缺文件、失败摘要及来源变动均为故障注入分支；原论文未被测试夹具修改。驱动为 `../run_s27_regression.m`，保存报告为 `regression_report.json`。

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/verify_exported_macros.py
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.7
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.7 --publish
```

两个正文生成块（`NUMERICAL REFERENCE VALUES`、`NUMERICAL RESULTS`）与重跑前逐字相同，块外文字也相同，见 `macro_comparison_report.json`。旧 141 个保护文件字节不变，旧 35 条索引不变；现有 70 raw、140 assessment。

主文按 XeLaTeX → BibTeX → XeLaTeX × 2 实际编译成功，37 页，最终日志无错误、未定义引用、缺字或溢出。正式 `latex/main.pdf` 已更新。实际目视检查三幅 PNG，并用 `pdftoppm` 渲染后检查主文数值图表所在的第 28–30 页：图表、数学式、图注及分页正常，沿用既有布局。本步没有逐页目视检查其余 34 页。检查记录及页面图像哈希见 `visual_qa.json`。

MATLAB 图形导出留下三条 `MATLAB:print:ContentTypeImageSuggested` 性能提醒；保留向量 PDF 与原日志，没有因此改成栅格输出。没有触发计划停止条件。
