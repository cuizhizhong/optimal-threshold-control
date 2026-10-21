# 图2图例及 S2.7 实际导出

基准提交为 `54470c531e3214bdf379b073f69593ec47fecb6a`。仅将 `make_numerical_figures.m` 中 `s=h` 的灰色虚线改为点划线，删去三处 `(theory)`，并把图例移到 `s=h` 右侧、`i>K` 上方的空白区。其余区域判定、轨道、坐标与样式代码未改。

实际运行结果：

- `run_figure2_refresh` 依次实际执行 `make_numerical_figures(); r=export_numerical_latex(); assert(r.verified && r.optimizer_executions==0);`，退出0。正式正文在导出后与导出前原始字节相同，SHA256 为 `560af8a739625d0baccd3ae31d6876946a9cc0180fd931db41b6b85b70e61df5`；保存了当时快照，后续获授权图注修改不包含在这一时点的核对中。
- 随后另一次 MATLAB 入口执行 `run_s27_regression()`，退出0；`saved/revision/pending` 分别11、3、2项全部通过。回归中的故障注入仅作用于各测试自己的临时副本。
- 两次入口的优化器调用与新增OCP求解均为0。原有 `timepanels` 重绘 FigN2/N3 时仍按原流程调用 `analytic_reference` 的积分及 `ode45`，未另起ODE实验。
- 对比300个已有数据文件，只有当前导出来源记录 `figure_provenance.json`、`export_provenance.json` 改变。原始记录、评估、索引、选取清单、`numerical_checks.json` 和 `scenario_summary.csv` 的文件集合及字节保持不变。
- 图形来源记录绑定新的实际作图代码哈希 `aed6a807005715f7a2e7278b262f2f90495ef1f466a60c1deba6f8a7b79b463c` 及六个实际输出文件哈希，没有继承旧图哈希。

`FigN2_waiting` 与 `FigN3_boundary_tracking` 的 PNG 尺寸相同，分别仅1个像素不同，最大通道差26、4。150 dpi PDF渲染分别有1961、2274个像素差；逐图目视后确认控制阶段、跳跃、感染轨道、容量线、文字及布局均与基准内容一致。进一步检查 PDF 内容流：分别只有14、11个文字 `Td` 的水平位移改变1个绘图单位；内容流共12316、16689个操作，除上述文字位移外均相同，提取文字也相同；没有曲线或其他绘制指令变化。前后PDF、PNG、150 dpi渲染和并排图均留存。

完整命令在 `COMMANDS.md`，前后哈希在 `before_hashes.json`、`after_report.json`，实际回归结果在 `S2.7/regression_report.json`。`collect_after.py` 实际运行两次：第一次完成哈希及像素对比，第二次加入 PDF 内容流核对后再次通过；未再次运行MATLAB。

保留的说明性异常：MATLAB对三份矢量PDF给出 `MATLAB:print:ContentTypeImageSuggested` 性能提示，按既有代码继续矢量导出；没有改为位图或关闭警告。保存导出后正文快照时，首次 `Copy-Item` 在仓库根目录使用项目内相对路径，报找不到文件，随后在项目目录纠正并核实字节相同；未改变计算。旧验证报告未被覆盖。

`matlab_tmp/` 是本轮运行时目录，包含MATLAB启动缓存及已清理故障注入目录的残留运行文件，不提交。没有将整套原始MAT数据或回归副本放入提交。建议提交的精确清单见 `submission_paths.json`；两份PDF最终编译和主文图页核查由本轮总报告记录。
