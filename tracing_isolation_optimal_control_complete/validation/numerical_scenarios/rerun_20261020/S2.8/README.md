# S2.8：文档与历史字段对照

项目 README 改为“历史数据字段对照”，说明 `pre-code-rename` 标签及旧 JSON/MAT 的字段含义；MATLAB README 改用当前 `beta/p/s_e/s_A`，说明指纹变动后的 35 次实际求解。历史第 6–11 步的缓存次数、测试数和页数保留，并明确其历史口径。

`REVIEW_GUIDE.md` 登记五个新主选择 run_id、35 项新旧对照、原判据报告和两套诊断计数。`MANIFEST.txt` 保留旧条目，补齐历史漏列的 35 份评估，并登记本批新 raw、solver sidecar、评估和报告。S2.1 清单更新作者确认与执行状态，改名前行号和映射依据保留。

实际运行：

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.8
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.8
```

主文四阶段编译通过，37 页，最终日志零问题。保护检查通过：旧 141 个文件字节不变，旧 35 条索引不变；现有 70 raw、140 assessment。优化器调用和科学求解均为 0。本步只整理文档，没有修改模型、算法、判据或数值结果。最终总报告与清单将在 S2.9 补齐。
