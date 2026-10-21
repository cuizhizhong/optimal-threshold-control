# 本轮实际执行入口

除特别说明外，工作目录为 `E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete`。

在仓库根目录实际运行PDF编辑标记一次：

```powershell
node 'C:/Users/cui/.codex/plugins/cache/openai-primary-runtime/pdf/26.1015.12040/skills/pdf/container_tools/mark_artifact_operation_started.mjs' --operation-kind edit --expected-output-count 6 --output-format pdf
```

正文宽度探针通过Python subprocess参数列表运行XeLaTeX，精确argv、退出码见 `measure_linewidth_command.json` 与console日志。以现稿完整前导区编译，typeout得到469.47049pt。探针首轮的交叉引用警告不是最终主文日志；最终双稿分别实际四阶段编译。

图1脚本使用 `E:/anaconda/python.exe`（已有matplotlib/scipy/numpy）。实际尝试1、2、3、4、5；1/3在覆盖前失败，2/4通过后根据目视调整，5为最终。各次解析记录和异常见 `execution_history.json`：

```powershell
& 'E:/anaconda/python.exe' validation/figure1_revision_20261021/make_figure1.py --attempt 5
```

独立核对使用已有mpmath作60位解析计算，记录于 `analytic_independent_review.json`；没有ODE或优化调用。

图2两个实际MATLAB入口的完整命令、日志路径与退出码见 `figure2/COMMANDS.md`；先图形重导出，再run_s27_regression。回归驱动与旧版本字节相同，复制到新报告目录后按mfilename位置产生新S2.7记录，旧报告不覆盖。

双稿编译实际运行两轮，最终使用第二轮产物：

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/build_revision.py --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/build_revision.py --attempt 2 --publish-existing
```

各轮每稿4条xelatex/bibtex绝对argv、cwd与退出码见attempt1/attempt2中的build_report.json。第二轮8进程全过；首次向latex/main.pdf直接同步报OSError22，最后一条只检查源/图/已生成PDF哈希并原子同步，不重新编译。原报告保存在build_report_before_publication_recovery.json。

实际渲染与核对：

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/render_pages.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/audit_scope.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_revision_20261021/verify_acceptance.py
git diff --check
git diff --cached --check -- '*.tex' '*.m' '*.py' '*.md' '*.json'
```

150dpi的pdftoppm逐条argv在render_manifest.json；逐页目视见visual_qa.json。优化器与新增OCP求解均0，历史35配置的保存结果不称为本轮新求解。
