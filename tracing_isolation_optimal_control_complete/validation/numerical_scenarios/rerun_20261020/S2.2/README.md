# S2.2：代码字段迁移与历史参数适配

作者于本轮确认 `code_rename_inventory.md`，授权继续 S2.2–S2.9。本步未执行优化器。

- 19 个 MATLAB 文件共 106 处纯符号替换；逐文件逆映射并规范化 Git 换行后，与 `pre-code-rename` 全文一致。同步更名的注释、参数错误提示和测试标签也参与逆映射。
- 生成器、Python 测试与共享 JSON 已同步改名；两份 Python 逆映射 AST、JSON 与标签完全一致。解析检查点本步未生成，留待 S2.3。
- 新增 `numerical_normalize_parameters.m`，只规范化参数计算副本；双键冲突、缺键时报错，不丢弃其他字段。raw/payload 原结构及哈希检查保留。
- 评估、图、导出和参数整体比较采用该副本；新辅助函数已登记到实际调用它的 assessment / figure / export 指纹依赖中。
- 评估入口先执行原结构来源检查，再创建副本，并验证适配前后的来源判定完全一致。适配测试注册进统一 unit 入口，使后续套件包含 13 组；本步只单独运行其中的 9 项适配测试。
- `verify_numerical_parameters()` 的 9 项适配/冲突/真实旧记录防篡改核对通过，MATLAB 退出 0，优化器 0 次。
- 141 个旧 raw/solver/assessment 保护文件 SHA-256 不变，旧索引仍为 35 条。`record_baseline.json` 保存本轮不可覆盖基准。
- 主文实际 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，4/4 命令退出 0，37 页，最终日志无错误、未定义引用或溢出。未改变理论或论文源文件。

实际命令（仓库根目录）：

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py capture --step S2.2
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.2
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.2
```

MATLAB 使用 `E:\software\Matlab\bin\matlab.exe -batch`，先执行计划规定的 `addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'))`，再执行 `verify_numerical_parameters()`，并写出本目录的 `compatibility_report.json`；实际控制台见 `compatibility_console.log`。

没有改变任何运算、运算顺序、参数值、初值、求解设置或判据，没有触发停止条件。当前源码与旧保存数据字段不同，这是后续重跑前的预期状态；尚未刷新选择或旧评估。
