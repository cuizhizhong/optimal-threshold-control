# 评估、批次与附加复核记录

`assessments/` 保存与原始 `run_id` 对应的独立评估 sidecar；原始记录在上一级的 `runs/`。`assessment_fingerprint` 包含原始输出、评估源码和设置，改变评估器只触发重新评估，不改变求解来源。

`batch_*_manifest.json` 保存冻结协议，`batch_*_Cxx_request.json` 保存实际请求和初猜数组，`batch_*_report.json` 保存真实调用/缓存/诊断及失败。`latest_*_report.json` 只是最新报告指针式副本，历史批次不覆盖。`selection_manifest.json` 位于上一级目录，三张主图与一个成本表只取其指定的五例。第 8–9 步附加实验保持第 6–7 步主选择原字节；第 11 步 all 缓存复核可重新发布同一 run_id 的主兼容副本，发布时刻不等于新求解时刻。

`initialization / grid / horizon / threshold` 各有 CSV/JSON 摘要。JSON 保留完整识别和比较；`*_detailed_summary.csv` 逐行列出事件、实际初猜容量超出、种子、成本差与失败分量。原始数组不裁剪、不平滑、不替换为解析参考。

科学矩阵覆盖 35/35；第 6–7 步 5 次主求解、第 8–9 步新增 30 次求解均成功，后批缓存引用 10 次。numeric 和 agreement 各通过 29/35，同时通过为 28/35。七条至少一旗标失败记录为 E1/N2000、E2/N2000/4000、E3/N2000、E4/N2000/4000、E5/N2000（均 T=300、analytic_reference），详见 `../../../validation/numerical_scenarios/step89_results.md`。

原严格 grid 的 `protocol_complete=true`、`consistency_pass=false`、`status=failed` 保留。另列的最细两级计划建议比较不覆盖它，不使次细级容量违规成为可行控制。E2/E4 的粗网格出现 11/8 单元中间控制块，实际识别结构分别为 `0 -> 1 -> 0` 和 `1 -> 0`；未通过事件/结构诊断如实保存。阈值复核 45/45 次识别全部保留，优化调用 0。

`protocol_complete` 仅表示全部预定配置有尝试和记录；`consistency_pass` 表示该组既定比较通过；`numeric_pass`/`agreement_pass` 是逐条浮点诊断。不能互相替代。无记录结果为缺失/未完成，数值输出不填 0。smoke solve 仅验证接口，单独保存于隔离检出证据，不纳入科学矩阵。

本轮第 10–11 步已实际完成当前工作区的图表/宏、重复导出、12 组 unit 及 3/8/2 项导出回归，科学优化调用 0。main 34 页、TheoryOnly 26 页实际编译成功，最终日志零问题。干净候选也通过 12 组 unit、9 项保存数据回归、Python fixture检查及 6 项测试、双版本编译；all,false 实测缓存 35、科学优化 0、assessment 0，协议完成 true、一致性 false，两旗标各 29/35、双通过 28/35。独立小型接口 smoke 成功 1 次，不纳入科学矩阵。

首次 11.08316pt 附录溢出、Windows 长路径展开失败及长路径 assessment 漏拷贝导致的 `No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a` 均保留。原数据完整，源/目标复制与 MANIFEST 用长路径枚举修复。候选 35 个 raw/solver、35 个 assessment、输入/fixture 字节相同；兼容副本只更新选择时间及哈希，科学字段/数组相同。PNG 时间戳及极少像素差有记录，视觉未见实际变化。15 类操作异常及失败日志见 `../../../validation/numerical_scenarios/step1011_operational_anomalies.json`。N=16000、T=600与额外初猜未运行，不生成结果。

证据见 `../../../validation/numerical_scenarios/REVISION_STATUS.md` 及 `step1011_*`。求解、评估和导出分别记来源；重复导出或重评估不冒充重新优化。第 8–9 步历史完整性报告仅评价当批基准，正文更新后不重新写成历史通过。
