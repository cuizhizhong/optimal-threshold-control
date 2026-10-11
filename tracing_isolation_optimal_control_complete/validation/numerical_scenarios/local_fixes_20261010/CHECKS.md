# 第四步两个局部小修

日期：2026-10-10。Git HEAD：`f5ee536712947e4b86a12497698aa8b911405911`。

本轮修改限定为复合绝对连续引理中的局部延拓措辞、MATLAB/Python 参数入口及 Python 非法输入回归测试。工作区已有其他修订，执行期间也有摘要、成本措辞和数值自动生成块的并发更新，均予保留。本轮没有调用数值求解、重评或正文数据导出，也没有调整数值接受容差。`task_changes.diff` 只列本轮源文件修改，其中主 TeX 仅提取该引理的差异。

## 修改

- `lem:ac-composition` 中将 $C^1$ 局部表达式定义为环境开邻域上的局部延拓，链式法则使用该延拓的梯度，并说明不同延拓沿轨道的梯度内积一致。原有假设、绝对连续结论及其他证明保持原样。
- `numerical_cases_config.m` 与 `Geometry.__init__` 在计算后续几何量前，检查四参数全部有限，并要求 `0<p<1, c>0, gamma>0, 0<K<1`。
- `test_analytic_checkpoints.py` 新增三项非法输入回归测试。

## 实际验证

1. Python `--check` 返回 `ANALYTIC_CHECKPOINTS_CHECK_OK`，六例解析结果与原 fixture 一致，优化调用为零。详见 `python_check.log`。
2. Python unittest 共 9 项通过，新增测试覆盖 24 个非法参数组合。详见 `python_unittest.log`。
3. 真实 MATLAB 配置入口检查通过。当前合法配置被接受，各参数 NaN/正负无穷的 12 项及非法边界/负值的 12 项全部以 `numerical_cases_config:InvalidParameters` 拒绝。没有加载 OpenOCL、创建 NLP 或调用优化器。`checkcode` 仅保留修改前已有的一条 `sort` 输入转置提示，未新增消息。详见 `matlab_parameter_guard.log` 和 `check_matlab_parameter_guard.m`。
4. 主文和 TheoryOnly 均实际执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，各命令退出码为 0。最终主文 37 页、理论版 29 页；最终日志未发现 Warning、未定义引用、重复标签、缺字或 Overfull/Underfull。精确命令及最终日志见 `main_build_commands.json`、`theory_only_build_commands.json`、`main_final.log`、`theory_only_final.log`。
5. 已渲染检查主文第 6、7 页及理论版第 6 页，局部延拓定义、梯度公式、中文和分页正常。`pdf_check.json` 保存最终页数和 PDF 哈希。
6. 原有 177 个标签及 163 次交叉引用列表保持一致。四个本轮源文件的 `git diff --check` 通过。
7. 相对执行前基线，原始 runs/solver 文件、图形、共享输入和解析 fixture 哈希未变。其余数值摘要、兼容副本等文件存在并发更新，不能将整个工作区的差异归为本轮操作。详见 `protected_check.json`。

编译在临时副本中完成；正式 PDF 更新前已核对全部六个编译输入与当前工作区一致。37/29 页反映当前完整工作区及同期其他修订，不将页数变化单独归因于本轮局部小修。执行期间未提交或推送。

## 命令

从仓库根目录执行 Python 检查：

```powershell
& 'E:\anaconda\python.exe' -B tracing_isolation_optimal_control_complete\validation\numerical_scenarios\generate_analytic_checkpoints.py --check
```

在 `validation/numerical_scenarios` 中执行 Python 回归：

```powershell
& 'E:\anaconda\python.exe' -B -m unittest -v test_analytic_checkpoints
```

实际成功 MATLAB 调用：

```powershell
& 'E:\software\Matlab\bin\matlab.exe' -batch "addpath('E:/work/optimal-threshold-control/tmp/local_fixes_20261010'); check_matlab_parameter_guard" -logfile 'E:\work\optimal-threshold-control\tmp\local_fixes_20261010\matlab_parameter_guard.log'
```

首次 MATLAB 沙箱启动失败，重定向首选项目录后的一次启动被中止；同一无优化批处理在获准环境重试后退出码为 0。`latexmk` 的 Perl 启动受沙箱限制，随后使用上述原生四步编译流程成功。因并发正文更新，交付前重新同步并编译最新源码；未将旧快照覆盖当前正式 PDF。
