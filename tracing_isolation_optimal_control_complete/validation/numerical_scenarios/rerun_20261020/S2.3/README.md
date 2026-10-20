# S2.3：重新生成并逐项核对解析检查点

- `generate_analytic_checkpoints.py --write` 实际完成，随后 `--check` 通过。
- `test_analytic_checkpoints.py` 实际 9 项全部通过，耗时 14.379 秒。
- 独立 `verify_checkpoint_migration.py` 从 `pre-code-rename` 读取旧输入和检查点，逆映射后比较全部字段：105 个数值项（含 16 个零值）相同，最大相对差 **0**，满足 `1e-12`。除对应键名外，唯一不同的元数据为经新旧输入各自重算验证的 `generator.input_sha256`。
- 141 个旧保护文件字节未变；索引仍为 35 条，科学求解和优化器调用均为 0。
- 本步主文四阶段实际编译通过，37 页，最终日志无错误、未定义引用或溢出。

实际命令均从仓库根目录执行：

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -X utf8 tracing_isolation_optimal_control_complete/validation/numerical_scenarios/test_analytic_checkpoints.py
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/verify_checkpoint_migration.py --report tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/S2.3/checkpoint_migration_report.json
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.3
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.3
```

首次给测试文件也加上 `-I`，因隔离模式移除了同目录模块搜索路径，在测试开始前出现 `ModuleNotFoundError`；保留 `python_tests.log`。按该文件的原有同目录导入方式移除 `-I` 后，9 项正式测试通过，详见 `python_tests_corrected.log`。未修改测试逻辑或放宽核对标准，未触发科学停止条件。
