# G4：独立补充材料与投稿前清理

基准：`671c6cda42dcb0d0cc6c7b116bf715ada89664c6`，分支 `codex/numerical-reproducibility-revision`。
作者于 2026-10-22 授权精简方案：补充材料只保留三节，完整复现档案留在仓库；原第 2297 行不动；完成后本地独立提交，不推送。

## 改动范围

- 主文第 1–11 节、附录 A–F、全部 5 图和 4 表保留；末尾原补充材料 S 独立为 `latex/supplementary.tex`。
- 补充材料恰含 S1 附加数值设置、S2 附加核对结果、S3 误差判据与残差说明，共三张表。保留粗网格异常和两套判据，完整日志、逐条评估、原始数组、来源指纹及复现命令留在仓库。
- 两个自动生成块及其开关声明集中到 `latex/generated/numerical_values.tex`，两份文稿各加载一次。导出器成功和失败清空路径均已适配，三套现有回归继续使用临时目录。
- 仅更新生成文字中的“复现附录”称谓和开关注释；数值与计算公式不变。导出后 `numerical_checks.json`、`scenario_summary.csv` 与基准字节相同，`export_provenance.json` 记录新导出源码哈希和时间。
- 主文对旧附录 G 的引用改为独立补充材料 S1–S3；清空作者栏、日期和 PDF 作者占位；删除合并基线及插入位置的开发注释。
- 更新双文稿构建入口、阅读入口和清单。没有恢复 TheoryOnly。

原第 2297 行逐字保留：

> 其来源是跟踪隔离对两条流量的不同作用：完全跟踪在阻止新感染的同时让社区易感者继续减少，用一段短时完全跟踪替代纯容量填充末端漫长的低强度维持更省（第\ref{sec:switching-mechanism}节）。

## 实际验证

- `run_export_g4.m`：保存数据导出通过；既有导出器回归 **16/16**（11+3+2），见 `matlab_report.json`、`matlab_console.log`。
- `verify_new_notation.py`：原 28 条符号恒等式 **28/28**，见 `notation_checks.log`。这项检查是代数核对，不是新 OCP 求解。
- `audit_g4.py`：19 项保护检查通过，见 `audit_report.json`。基线覆盖 6692 个跟踪文件，全部旧数据、图形与历史验证记录字节不变；35 个定理类环境、32 个证明环境、公式及附录 A–F 与基准一致。
- `build_g4.py 3`：从新隔离目录执行主文 XeLaTeX→BibTeX→XeLaTeX×2、补充材料 XeLaTeX×3，全部进程退出 0，最终日志无错误、警告、未定义引用、缺字或溢出。
- `check_build_entry.py`：在隔离副本实际执行更新后的 Windows `build.bat`，退出 0，主文 **43 页**、补充材料 **2 页**，两份最终日志零诊断。Linux/macOS 的 `build.sh` 仅静态检查，未在本机执行。
- `render_g4.py`：将最终两份 PDF 的全部 **45 页**按 100 dpi 渲染；逐页目视记录见 `visual_qa.json`，源 PDF 哈希见 `render_manifest.json`。
- 补充材料三张表及 E3 残差与保存来源对应，见 `source_map.json`。E3 容量放宽值下降引用已保存导出宏，不伪称为新评估或新科学结果。

本批优化器调用 **0**、新增 OCP 求解 **0**、重新评估 **0**、图形重新导出 **0**。MATLAB 仅运行保存数据导出与既有回归。

## 实际入口

从仓库根目录执行（本批已实际运行）：

```powershell
& 'E:/software/Matlab/bin/matlab.exe' -batch "addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios')); addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','g4_supplement_20261022')); run_export_g4();" -logfile 'tracing_isolation_optimal_control_complete/validation/g4_supplement_20261022/matlab_console.log'
python -X utf8 tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
```

隔离构建、渲染、来源保护使用本目录的 `build_g4.py`、`check_build_entry.py`、`render_g4.py`、`audit_g4.py`；实际命令、工作目录、每次退出码与输入哈希保存在各 JSON 中。已有 attempt 不覆盖；重做时应新设编号和输出目录。

## 保留的失败与修复

1. 默认沙箱中的 MATLAB 在执行入口之前因 `PrefdirNotWritable` 退出，见 `matlab_sandbox_failure.log`；随后在授权环境运行同一入口成功，没有修改科学配置。
2. `attempt1` 的补充材料第二遍编译因缺少 `xcolor` 报 `Undefined color blue!55!black`；补齐宏包后重建。
3. `attempt2` 两份文稿均完成编译，但补充材料的时域配置长公式导致 48.81659 pt 溢出及数条 underfull，未验收；将元组分开并让表格列左对齐后，`attempt3` 通过。

最终源文件/PDF 哈希与交付状态见 `acceptance_report.json`，准确提交文件清单见 `staging_paths.json`。本批完成后交作者审阅；没有推送。
