# S2.5：35 条新旧求解严格比较通过

`compare_rerun_results()` 实际读取标签 `pre-code-rename` 与当前三组摘要，按 `configuration_id` 完整配对 35 项；旧评估取标签容差报告中的修订判据 sidecar，新评估取本次当前源码/设置对应的保存 sidecar。

- 35/35 完成且通过；成本最大相对差 **0**、控制数组最大绝对差 **0**、状态数组最大绝对差 **0**。
- 求解状态、实际 IPOPT 迭代数、时间网格、事件区间/候选/节点索引、阶段结构、numeric/agreement 及分项旗标完全一致。
- 旧/新修订判据均为 numeric=33、agreement=30、both=30（总数 35）。
- 比较只读，不产生新求解或新评估；已读取输入的原始字节不变。完整逐条结果及旧/新 run_id 见上一级 `comparison_report.json`。
- `checkcode` 未报告语法错误；唯一 MSNU 提示为不必要的消息抑制标记，不影响执行。实际函数完整执行退出 0。
- 141 个旧保护文件不变，旧 35 条索引不变；主文四阶段编译通过，37 页，最终日志无错误、未定义引用或溢出。

实际 MATLAB `-batch` 命令先按计划 addpath，再执行 `r=compare_rerun_results(); assert(r.passed);`，控制台见 `comparison_console.log`。该比较函数没有加入任何指纹清单。

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.5
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.5
```

通过标准保持成本相对差 `1e-10`、数组最大差 `1e-8`，没有放宽，也没有触发停止条件。
