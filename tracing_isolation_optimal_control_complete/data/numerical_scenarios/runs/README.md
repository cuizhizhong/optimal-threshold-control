# 原始求解记录

每次真实求解（包括失败和 force 重试）使用独立 `run_id`，保存到 `<run_id>.mat`。已保存记录不覆盖；`../run_index.json` 保存来源指纹、attempt 和原始文件 SHA-256。

求解来源保存于 `provenance`，缓存命中、重新评估、选择兼容副本及作图均不得重写它。评估只写入 `../revision_checks/assessments/`。

本目录目前没有新增优化结果。既有 `E1.mat`–`E5.mat` 等文件的核查状态见 `../legacy_inventory.json`，不自动迁入新缓存或当作新实验的通过证据。
