# 实际命令

工作目录为 `E:/work/optimal-threshold-control/tracing_isolation_optimal_control_complete`；PDF标记与Git从仓库根目录运行。

PDF技能编辑标记实际运行一次：

```powershell
node 'C:/Users/cui/.codex/plugins/cache/openai-primary-runtime/pdf/26.1015.12040/skills/pdf/container_tools/mark_artifact_operation_started.mjs' --operation-kind edit --expected-output-count 3 --output-format pdf
```

符号核对实际命令及退出码另存notation_command.json，stdout为notation_checks.log：

```powershell
& 'E:/anaconda/python.exe' ai/claude_revision_plan/checks/verify_new_notation.py
```

新图脚本实际运行第1–7轮；第4轮标签框检查失败未替换产品，第7轮为最终。各轮JSON与迭代说明保留：

```powershell
& 'E:/anaconda/python.exe' validation/mainline_focus_20261021/make_optimal_partition.py --attempt 7
```

旧图仅删除作者指定的两个产品文件。Python在删除前确认绝对父目录为项目figures/numerical_scenarios，读取SHA256，再逐个unlink；精确路径与哈希见authorized_deletions.json。旧脚本及历史记录没有删除。

双稿实际各编译两轮：

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/build_revision.py --attempt 2
```

每轮为主文和TheoryOnly各XeLaTeX→BibTeX→XeLaTeX→XeLaTeX。合计16个实际进程均退出0。各条绝对命令、工作目录和退出码均在对应build_report.json，第二轮同时绑定当前所有图形SHA256，使用原子替换同步PDF，未用旧构建文件交付。

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/audit_mainline.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/render_pages.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/render_pages.py --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/mainline_focus_20261021/verify_acceptance.py
git diff --check
git diff --cached --check -- '*.tex' '*.bib' '*.py' '*.md' '*.json'
```

pdftoppm逐条实际命令含-r 150、页码与退出码，保存在render_manifest_attempt1.json与最终render_manifest.json。主文6–11页、TheoryOnly5–10页；实际目视及相同像素复用边界见visual_qa.json。

MATLAB调用0；优化器调用0；新增OCP求解0；ODE积分0。Brent法只求解析标量方程根，未优化目标泛函。没有导出器重跑或数值图重生成。
