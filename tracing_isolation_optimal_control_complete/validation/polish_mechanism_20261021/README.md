# 图1、安全集和机制节打磨

基准：`6b48cc6b0bb4b222415853bf575c8f7ccc48e561`，分支 `codex/numerical-reproducibility-revision`。按作者本轮14项要求修改，独立本地提交，不推送。

## 修改范围

- 图1：放大图新增安全边界与切换曲线共同端点的空心圆和 `s_e` 标注，上限由0.166收至0.153，E1/E2使用正体及同行数字。主图选区框上沿仍为0.166，继续避开 `s_B`；只有放大图的实际显示上限收窄。原轨道、配色、尺寸、其他标注不变。新脚本以 `figure1_layout_20261021` 版为底稿，旧脚本及旧记录不改。
- 第3节：说明物理状态可直接写属于安全集；三类集合区分只归于AFG，FG另述可行性；定理3.1仅陈述存在性、全控制类下U=V及唯一性，新增命题3.2承接阶段结构和提前离开容量。表1和图1紧随其后。
- 第15节：保留两条指定成本与等待公式，新增成本一形式及其外微分、两类积分边际公式和h的端点驻点解释。Green比较明确围域条件和方向，边际说明限于可行的一维策略比较，全局最优性仍由验证定理保证。仅保留Angulo不变量坐标的方法致谢，不声称其使用Green公式，不新增文献。
- 第20节：改名为“模型假设与理论边界”，删除两句越界因果说明，改引命题3.2和机制节。保留理想化完美追踪及适用范围限定。
- 引言仅同步两处定理/命题引用归属。其他节及模型、已有定理证明、数值块未改。

## 实际执行与结果

以下为仓库根目录的入口写法；双编译和渲染的逐条绝对argv、cwd、退出码另存JSON。

```powershell
& 'E:/anaconda/python.exe' tracing_isolation_optimal_control_complete/validation/polish_mechanism_20261021/make_optimal_partition.py --attempt 1
& 'E:/anaconda/python.exe' tracing_isolation_optimal_control_complete/validation/polish_mechanism_20261021/check_mechanism.py
& 'E:/anaconda/python.exe' tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/polish_mechanism_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/polish_mechanism_20261021/render_requested_pages.py
& 'E:/anaconda/python.exe' tracing_isolation_optimal_control_complete/validation/polish_mechanism_20261021/audit_scope.py
git diff --check
git diff --cached --check -- '*.tex' '*.py' '*.md' '*.json'
```

PDF编辑标记实际执行一次，`operation-kind=edit`、`expected-output-count=3`。本轮MATLAB、优化器、新增OCP求解、ODE积分均为0次；使用的是解析公式求值、数值积分、网格扫描及标量方程求根。

- 原有符号检查28/28通过；新增SymPy检查9/9残差为零。
- 几何检查点最大差1.11e-16，切换点Theta残差3.55e-15；新增s_e安全边界/切换端点方程最大残差9.71e-17。原几何、E1/E2轨道端点及成本数据与上一版逐键完全一致。图1覆盖前后SHA256在 `analytic_checks.json`。
- E2容量路径20001点扫描只有一个内点导数变号，方程求根给出s_B=0.5476951246795451；最小成本1.5295111601514724，维持至h成本1.5783855039561376。以维持成本为分母节省3.0964769812%，四舍五入3.10%；反向相对最优高出3.1954225%，不混用分母。h右侧三个样点导数均负且趋零。B/D共9条弧的积分边际公式最大归一化残差3.97e-14；详见 `mechanism_checks.json`，不将本轮公式核对称为新增OCP结果。
- 主文与TheoryOnly各实际执行XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，共8个进程退出0。最终页数为42、32，分别较基准增加1页。最终log/blg无错误、警告、未定义引用、缺字或溢出；报告及完整过程日志在 `attempt1/`。
- 实际150dpi渲染并逐页查看12页：主文6–8、27–28、34–35；TheoryOnly5–7、26–27。包括第3节、图1、两版本第15节及主文第20节。标签、公式、跨页、图表及引用均通过；TheoryOnly无第20节悬空引用。渲染命令和SHA见 `render_manifest.json`，分项目视记录由 `visual_review_summary.json` 汇总。
- 范围检查确认两个自动生成数值块逐字不变；除第3/15/20节及引言两处授权引用外，所有其他节源码逐字不变。1547个既有保护文件SHA256不变，包括FigN1_regions、FigN2、FigN3、MATLAB源码、原始数据和旧验证记录；完整结果见 `audit_report.json`。

本轮审计脚本首次因日志编码识别错误退出1，修复新脚本的UTF-8/UTF-16识别后重新运行退出0；没有修改数学判据或验收标准，记录在 `workflow_notes.json`。未触发数学或编译停止条件，无需作者另作技术决定。完整提交文件清单见 `changed_files.txt`。完成提交后暂停，等待作者审阅。
