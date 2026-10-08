# 第 8–9 步实际执行入口

从仓库根目录运行 MATLAB `execute_stage89.m`，实际依次调用：

```matlab
revision_preflight();
run_revision_validation('initialization',false);
run_revision_validation('grid',false);
run_revision_validation('horizon',false);
run_revision_validation('threshold',false);
```

实际本机启动命令及日志：

```powershell
& 'E:\software\Matlab\bin\matlab.exe' -wait -nosplash -nodesktop -logfile 'tracing_isolation_optimal_control_complete\validation\numerical_scenarios\step89_execution.log' -batch "run('tracing_isolation_optimal_control_complete/validation/numerical_scenarios/execute_stage89.m')"
& 'E:\software\Matlab\bin\matlab.exe' -wait -nosplash -nodesktop -logfile 'tracing_isolation_optimal_control_complete\validation\numerical_scenarios\step89_initialization_validation.log' -batch "run('tracing_isolation_optimal_control_complete/validation/numerical_scenarios/execute_stage89_initialization_check.m')"
python -u tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage89_integrity.py
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/summarize_stage89.py
```

以上入口均已实际执行并退出 0。MATLAB 第一个入口返回完整实验状态；grid 的诊断一致性失败如实写入报告，不因进程退出 0 就视作检查通过。第二个 MATLAB 入口及两个 Python 入口只复核或汇总保存记录，不调用优化器。Python 日志为 `step89_integrity_attempt1.log`、`step89_summary.log`。

本机执行前的受限启动使用了 `tmp/step89_matlab_prefs` 作为独立偏好目录；启动未进入脚本且日志为空，已中止并保留 `step89_execution_attempt1.log`、`step89_startup_attempts.json`，科学优化调用为 0。

当前提交沿用 `c23a5d6bdc7fd97ea53e32a485ca03996789831b`；本批没有新增 commit 或 push。原求解代码、协议和阈值已经在前批冻结，本批新结果保存真实 solve_commit、源码原字节哈希、环境和 dirty 状态。修改/新增文件清单为 `CHANGED_FILES_STAGE89.txt`。
