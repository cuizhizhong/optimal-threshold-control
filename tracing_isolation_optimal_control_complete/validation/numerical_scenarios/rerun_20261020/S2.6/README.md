# S2.6：新 35 条记录的原判据重评

`refresh_original_criterion()` 实际完成，优化器/科学求解为 0，追加原判据评估 35 份。它先绑定已通过的 S2.5 新旧配对，再验证全部新 raw、当前修订 sidecar 和源码/请求来源；不重新选择、不刷新组摘要。

| 判据 | numeric_pass | agreement_pass | both_pass |
|---|---:|---:|---:|
| 原判据 | 29/35 | 29/35 | 28/35 |
| 修订判据 | 33/35 | 30/35 | 30/35 |

原判据只把状态/容量容差设为 `1e-6`、容量段控制容差设为 `2e-3`；其余设置不变。逐条确认参考解、重积分轨道和成本比较相同。旧 70 份评估、本批 35 份修订评估及全部既存数据哈希不变；现在共 70 raw、140 assessment，旧 35 条索引保持不变。

导出器的 `original_criterion_text` 改为读取本目录新报告，必须匹配当前 35 条记录集合和当前评估源码、设置与参考采样。来源路径及 SHA-256 进入导出报告的 `original_criterion_source`；不再把旧批计数当作新批结果。

实际 MATLAB `-batch` 入口先执行规定的数值代码 `addpath`，再把 `rerun_20261020` 加入路径，调用 `r=refresh_original_criterion(); assert(strcmp(r.status,'completed'));`。逐条原/现旗标、来源及保护文件清单见 `assessment_revision_report.json`，控制台见 `reassessment_console.log`。

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.6
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.6
```

主文实际四阶段编译通过，37 页，最终日志无错误、未定义引用或溢出。两套计数符合计划，没有触发停止条件；作图、重新导出与三项导出器回归留待 S2.7。
