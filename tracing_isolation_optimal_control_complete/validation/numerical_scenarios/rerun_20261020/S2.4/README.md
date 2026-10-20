# S2.4：实际完成 35 次新求解

正式批次：`batch_489a22dd23b64763a9a163f1390ca080`。完整入口为上一级 `run_s24.m`，没有重跑或补跑矩阵。

| 项目 | 实测 |
|---|---:|
| 科学求解调用 | 35 |
| 缓存命中 | 0 |
| 评估调用 | 35 |
| 求解成功 / 失败 | 35 / 0 |
| 修订判据 numeric / agreement / both | 33 / 30 / 30（总数 35） |
| `all,false` 调用总耗时 | 2157.5074708 秒 |
| 当前索引 / raw / assessment 数 | 70 / 70 / 105 |
| 旧保护文件 SHA-256 | 141/141 不变；旧 35 条索引逐项不变 |

该耗时包含 `all` 内部的 unit、预检、来源记录、准备、求解、评估和组摘要，不冒充 35 个优化器内部计时的简单求和。计划中的约 22 分钟为旧求解耗时参考，未将其写成本轮计时。

预检实际确认 MATLAB R2025b、CasADi 3.4.5 和 IPOPT 可用。`run_revision_validation('unit',false)` 及 `all,false` 内部的同一套件各实际通过 13 组；其中 mock 调用在日志明确标为 `actual_optimizer=0`，不计入 35 次科学求解。

调度器 `status='failed'` 表示并非全部 35 条都通过 numeric/agreement；本批 `protocol_complete=true`、求解失败为 0、同时通过 30/35。它符合计划保留原有诊断失败的参照，不能据此重复求解。

实际从仓库根目录运行 `E:\software\Matlab\bin\matlab.exe -logfile <本目录 matlab_console.log> -batch`，内容为：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','numerical_scenarios','rerun_20261020'));
run_s24();
```

入口依次执行计划的 `revision_preflight()`、`run_revision_validation('unit',false)`、`run_revision_validation('all',false)`，分别保存本目录的预检、unit、all 和执行计数报告。

本步结束后实际运行：

```powershell
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/preserve_records.py check --step S2.4
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/numerical_scenarios/rerun_20261020/build_step.py S2.4
```

主文四阶段编译 4/4 退出 0，37 页，最终日志无错误、未定义引用或溢出。本步尚未执行 S2.5 严格比较、原判据重评、作图或正文重新导出。

首次暂存遇到 Windows 的 `Filename too long`，未写入暂存区；随后提交尝试因暂存区为空而没有创建提交。保留原文件名和目录，后续 Git 文件操作使用单次命令的 `-c core.longpaths=true` 后完成暂存与提交，不移动、缩短或改写任何评估文件。
