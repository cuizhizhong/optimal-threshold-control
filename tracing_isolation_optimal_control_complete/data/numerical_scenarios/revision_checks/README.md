# 独立后处理记录

`assessments/` 保存与原始 `run_id` 对应的评估 sidecar。其 `assessment_fingerprint` 包含原始输出、评估源码及设置；修改评估器只要求重新评估，不重新优化。

`selection_manifest.json` 位于上一级目录，只有执行主算例并明确选择结果后才生成。本批没有主算例求解，不预填 selection manifest 或科学结果汇总。

本批无优化器测试证据位于 `../../../validation/numerical_scenarios/`。后续第 3–11 步尚未执行。
