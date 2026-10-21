# 图1重绘与图2图例返修

基准 `54470c531e3214bdf379b073f69593ec47fecb6a`。本任务只修改两幅相图、两处图注及规定的图形重导出；不改模型、证明或数值结果。独立提交，不推送，完成后等待作者审阅。

## 完成内容

图1由本目录 `make_figure1.py` 生成，旧 `validation/geometry_proofs_20261021/make_two_layer_phase.py` 的字节保持不变。实测正文宽度469.47049 TeX pt，成图16.5000006×6.9 cm；PDF由 `width=\linewidth` 按原尺寸插入，比例为1。刻度8 pt、轴标签9 pt、区域标签9–10 pt；Times New Roman与STIX数学字体。删除旧参数标题、英文面板标题及单独图例，图内仅保留数学记号、数值和(a)(b)。

左图画qbar=0、0.1、0.2、0.4四条解析包络，按物理约束截断并直接标号，在容量线标出四个切点。右图使用与图2相同的区域底色和曲线线型；纵轴上限0.17，两主图横轴均0.15–1.01。E2示例轨道使用解析自然轨道、容量直线和完全跟踪特征线连接，不积分ODE。角区放大图放在右侧主图下方，覆盖[0.42,0.60]×[0.10,0.16]，不遮挡主图；Gamma_K印刷跨度2.1978 cm。省略可选“维持至s=h”对照段，以保留标注空间。

图2只改变s=h点划线、图例位置及三处(theory)。图例位于s=h右侧且i>K的空白处，保留OpenOCL(E1–E5)。坐标、分区、轨道及N2/N3绘图函数未改。两份当前provenance按实际图形代码/输出哈希与导出时间更新；原始、评估、选取清单和旧验证记录不改写。

## 覆盖前后SHA256

图1覆盖前后完整SHA256见 `hashes_before_after.json`；同样存于 `analytic_checks.json` 的baseline_outputs_sha256与outputs_sha256。基准两份旧图保存在本目录，图2/N2/N3旧图在 `figure2/before/`。图2/N2/N3前后哈希见 `figure2/after_report.json`。

## 实际命令与结果

精确命令及工作目录见 `COMMANDS.md`、`figure2/COMMANDS.md`。

| 实际入口/检查 | 结果 |
|---|---|
| make_figure1.py --attempt 5（最终） | checkpoint最大差1.1102230246251565e-16；Theta最大残差4.440892098500626e-15；四包络切点值/导数残差为0；三段端点残差小于2e-11 |
| 独立解析复核 | 60位计算通过，见analytic_independent_review.json；102757个内点的新旧分区分类完全一致 |
| MATLAB图形+导出入口 | 实际退出0；verified=true；正式导出后的整个main.tex与导出前字节相同 |
| run_s27_regression() | 第二个实际MATLAB入口退出0；saved/revision/pending分别11/3/2项全通过 |
| audit_scope.py | 18/18；正文除两处图注外相同，两自动生成块相同；438数据、785旧validation、60其他保护文件SHA不变 |
| build_revision.py --attempt 2 | 最终双稿各XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，8/8退出0；43/33页；最终日志无错误、警告、未定义引用、缺字或溢出 |
| build_revision.py --attempt 2 --publish-existing | Windows直接覆盖报OSError22后，核对成功编译原产物及源/图哈希，原子同步恢复；未增加TeX进程，原失败报告另存 |
| render_pages.py | 实际150dpi渲染主文8、31页与TheoryOnly7页；逐页目视通过 |
| verify_acceptance.py | 17/17汇总验收通过；绑定最终PDF、图形、脚本和页面哈希 |
| 调用次数 | MATLAB入口2次；优化器0、新增OCP求解0；图1 ODE积分0 |

FigN2与FigN3的PNG分别仅差1个像素，最大通道差26、4。150dpi PDF渲染前后逐幅目视内容一致；内容流只有14/11个文字水平位移改变1个绘图单位，内容流共12316/16689个操作，其余相同，提取文字也相同，曲线及数值内容不变。

原有N2/N3图形流程仍含analytic_reference的积分/ode45，属于本次获准重绘；没有另外启动ODE实验，因此不把整个任务的ODE调用次数写成0。`brentq`仅解解析标量方程，不是控制优化；`quad`仅核对完整物理域内的面积，不积分轨道。不可行面积份额40.2178%、31.7492%、21.2198%、3.89462%对应完整D，不是横轴从0.15开始的显示窗口占比。

## 验收差异、异常与停止事项

页数相对基准43/33未变，模型、证明、其他正文、两自动生成块、数据记录及数值口径均未变。放大图改为外置，满足尺寸且避免遮挡；按可选授权省略维持至h的对照段。

实际保留两轮双编译：首轮8进程成功，随后根据图形目视微调标签，再作最终一轮8进程；合计16个TeX/BibTeX进程，均退出0。最终同步的PDF来自第二轮。准备期的路径/依赖/Mathtext错误、直接覆盖错误及修复见 `execution_history.json`，未删除失败记录；图1attempt2/4为通过但被最终标签版本取代，最终为attempt5。

MATLAB保留三条矢量导出性能提示ContentTypeImageSuggested，没有关闭提示或改成位图；它们与最终LaTeX日志无警告分别记录。未触发计划的数学/数值停止条件，没有放宽验收。没有后续研究、仓库可见性或历史处理，没有push。

完整提交清单见 `changed_files.txt`。运行期缓存、回归故障注入临时副本、探针辅助文件与图1尝试目录中的重复输出均留在本轮目录并由局部.gitignore排除提交，不混入旧原始/评估目录。
