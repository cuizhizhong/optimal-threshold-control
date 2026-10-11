# E2/E4 网格复核解释修订

本轮仅修正网格汇总的原因分类和正文对应解释。基准为 `f5ee536712947e4b86a12497698aa8b911405911`，未修改模型、成本、证明、参数、接受阈值或求解器，未运行新的优化或重新评估。

## 修订结果

- 网格汇总增加 `comparison_status`、最细/次细网格的记录标识、网格数及数值接受标志，另存成本和事件比较是否实际执行及其独立结果。
- E2/E4 的 `N=4000` 数值接受失败，因此原严格判据下的最细两级成本与事件比较未执行。对应状态为 `not_evaluated_due_to_numeric_failure`，比较数值仍为空，未填入假失败或假通过。
- E2 的该级解析比较通过；E4 的该级容量控制比较未通过，但单项解析事件时间比较通过。正文分别说明这两种结果。
- 测试网格上的容量超出下降、`N=8000` 低于既定容差，以及 `N=2000` 长中间控制块和阶段识别异常均保留。
- E1/E3/E5 通过的是原严格判据下最细两级的成本与事件区间比较。整个严格网格组仍为 `status=failed`、`consistency_pass=false`。
- 历史“计划建议判定”报告保持原样，本轮没有使用它替换原严格判定。

## 实际验证

- `matlab_report.json` 记录 7 个网格分类合成回归、9 个保存数据导出回归及 3 个失败清空回归，共 19 项通过。脚本从 15 条现有网格记录加载当前保存评估，科学优化、重新评估和兼容副本发布次数均为 0。
- `scope_report.json` 记录 147 个受保护文件 SHA-256 不变。其中包括 35 个原始 MAT、35 个 solver JSON、35 个评估 MAT、五例兼容副本、选择清单、索引、图及求解/评估源码。
- 15 条网格科学结果、原比较数值和事件区间保持一致；五例主结果及原 35 个配置、28 个双通过统计保持一致。正文除 `NumRobustnessStatement` 外逐字不变。
- `build_report.json` 记录两份文档各自 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX 的实际成功执行。主文 34 页，TheoryOnly 26 页，最终日志未发现警告、缺字、未定义引用或溢出。
- `pdf_qa.json` 记录主文第 26、27、29 页及 TheoryOnly 第 25 页的实际渲染和目视检查。修订文字在主文第 26 页，未见裁切、重叠或分页异常。

## 执行中修复的问题

初次 MATLAB 沙箱启动受默认预设目录权限限制；最终在可正常启动的环境中完成验证。第一次实际合成回归发现空结构体初始化问题，已修复并通过全部七项回归。后续验证脚本因 JSON 读回改变 MATLAB 嵌套向量方向而误报数据差异，改由 Python 逐字段比较 JSON 内容，实际科学数据始终未变。失败日志 `matlab.log`、`matlab_attempt2.log`、`matlab_attempt3.log` 均保留，最终成功日志为 `matlab_attempt4.log`。

直接覆盖 PDF 的前两次编译遇到文件访问限制。主文最终在本项目临时目录完成全部编译后原子替换正式 PDF；TheoryOnly 完成正常编译。初次失败日志保存在 `build_attempt1/`、`build_attempt2/`，最终命令、退出码及 PDF 哈希见 `build_report.json`。

## 复核入口

从仓库根目录执行以下只读范围核查：

```powershell
python -B tracing_isolation_optimal_control_complete/validation/numerical_scenarios/grid_explanation_20261009/validate_scope.py verify
```

MATLAB 中以下入口只重做保存数据汇总、正文导出及临时目录回归，不进行优化或重新评估：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','numerical_scenarios','grid_explanation_20261009'));
refresh_saved_grid();
```

`baseline.json` 是本轮修订前快照，复核时保留，不重新执行 `capture`。
