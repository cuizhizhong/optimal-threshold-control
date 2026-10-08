# 第 0–2 步执行状态

本批仅执行 `ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md` 的第 0–2 步。第 3–11 步为 `not_started`。

| 步骤 | 状态 | 证据 |
|---|---|---|
| 0：冻结基准、环境预检 | completed | `BASELINE.json`、`preflight_report.json`、`preflight_tests.json`；四项回归通过 |
| 1：恢复独立解析检查点 | completed | `step1_python_tests.json`、`step1_matlab_tests.json`；Python/MATLAB 各六项通过 |
| 2：缓存与来源修复 | completed | `cache_unit_report.json`、`preparation_unit_report.json`；六项 mock 与构建接口通过 |

基准提交：`f078f41fda1a7e4b0fb495916210862a0f136558`。基础分支：`codex/integrate-theory-revision`。工作分支：`codex/numerical-reproducibility-revision`。

起始工作区无已跟踪文件修改，存在用户既有未跟踪材料，详见 `BASELINE.json`。创建分支未覆盖、移动或纳入这些材料。当前正文包含 167 个 label 和两组完整的 AUTO-GENERATED 标记；24 个历史数据、图和论文文件已记录 SHA-256。

MATLAB 沙箱启动尝试因 `PrefdirNotWritable` 失败，随后在获准运行环境执行成功。实际环境为 MATLAB `25.2.0.2998904 (R2025b)`、CasADi `3.4.5`，`has_nlpsol('ipopt')` 返回可用。OpenOCL/IPOPT 的版本无可确认接口时记为 `unknown`；实际依赖源码及二进制哈希另存。无持续阻断项。

本批真实优化调用为 0，真实成功/失败/缓存命中均为 0；默认矩阵为 0/35（`not_started`）。六项缓存测试使用 18 次 mock solver 调用，不计为科学实验。小型构建测试为 `T=1,N=4,d=2`，只构建 NLP 和初猜，不调用 solve。

本批未修改理论或 LaTeX。24 个历史数据、图和论文文件的 SHA-256 与基准一致，167 个 label 及两组生成块保持原样，见 `integrity_report.json`。主文与 TheoryOnly 本批未编译。

## 实际检查入口

从仓库根目录实际运行了：

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage02_integrity.py --write-report
```

实际通过 MATLAB `-batch` 调用了：

```matlab
revision_preflight();
verify_revision_preflight();
verify_numerical_reference();
verify_reference_dependency_tests();
verify_numerical_cache();
verify_numerical_preparation();
```

Python fixture 的 `--check` 前后 SHA-256 不变。MATLAB 解析交叉核查最大成本差为 `1.5543122344752192e-15`，最大解除时间差为 `5.9729998724833422e-14`。这些仅是解析实现之间的浮点差异，不是 NLP 精度或最优性结论。

`checkcode(...,'-id')` 已实际执行，无解析错误；原有及新增代码仍有少量可读性、未使用变量和抑制提示，见 `matlab_code_analyzer.json`，不将其描述为零警告。

## 文件和来源

共享输入和独立解析生成链位于本目录；MATLAB 配置、正式参考验证及依赖回归同步按 case_id 读取输入。求解构建、执行和评估分别由 `prepare_openocl_case.m`、`execute_numerical_run.m`、`assess_saved_numerical_run.m` 负责。

runner 不再在缓存命中时改写来源，也不按结果自动加密主网格。真实求解记录存于 `data/numerical_scenarios/runs/`，索引为 `run_index.json`；兼容副本只通过显式主选择 manifest 产生。图、正文导出和重新评估入口已改用独立来源与校验。历史 12 个 MAT 文件只在 `legacy_inventory.json` 标记为 `legacy_unverified`，原字节保留。

最终工作区求解源码哈希为 `32ab1ff9f71011b5caffa2e9abf696c15d5d0e4e925244fac76a00d1a7a613fe`，明细及独立评估/作图/导出哈希见 `source_fingerprints.json`。此哈希只表示源码检查，本批没有由它产生的优化结果；实际每次 solve_fingerprint 还必须加入参数、设置、实际网格、初猜与环境。

附加实验汇总尚未连接新 runs 索引，留待第 6/10 步。现有导出器拒绝历史附加 checks 作为新增通过证据，当前不能生成新的整体 verified 结论。新的评估/事件/调度/正文修改均为 `not_started`。

## 提交与独立检出

代码提交：`8446e1677fc55504d2bff74c5fb0e69b8262c058`。只按显式路径列表提交本批文件，未纳入原有未跟踪材料，也未 push。

从已提交索引通过 `git checkout-index` 导出独立目录，再实际通过 Python `--check`、六项 Python 测试、MATLAB 解析验证、六项依赖测试与六项缓存 mock 测试。fixture 前后字节不变，真实优化为 0。证据为 `clean_checkout_report.json`、`clean_checkout_python.log`、`clean_checkout_matlab_tests.json`、`clean_checkout_matlab.log`。

Git 的 `core.autocrlf=true` 在新检出时把四个历史文本文件及四个未改动 MATLAB 源文件从 LF 转为 CRLF。原工作区仍按原字节核对 24 个历史文件；跨检出核对只对文本规范 CRLF/LF，二进制仍按原字节比较，24 个文件内容一致。独立检出的求解源码原字节哈希为 `519f44278cd65db38e36b6545531d447a10ac6cc47f90c96c0b47bd4732a7592`，与工作区哈希分开记录，不把不同原字节来源当作同一次求解。

相关文件完整列表见 `CHANGED_FILES.txt`。第 0–2 步完成；第 3–11 步未开始。
