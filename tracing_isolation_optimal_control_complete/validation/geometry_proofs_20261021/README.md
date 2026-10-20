# 第四批 C1–C4：几何与证明整理

基线为 B 作者审阅修订 `e86ec62094f72c2aa56c05191c0ecaf5166d3cf6`，分支 `codex/numerical-reproducibility-revision`。本报告所在提交独立完成 C1–C4，不推送，不进入 C5、D、F 或 G。

## 正文修改

**C1 两层分区。** 在模型节后先定义物理域、未来峰值、零控制安全集 A、所有可测允许控制均安全的 A^0，以及存在受限可行控制的 V_qbar。全称控制类没有预先限制为可行类，避免循环定义。旧安全不变性引理补出 A^0=A=V0、V1=D；成本最优分区在可行性层之后。新增理论两层相图左示可行性、右示成本分区，s=h点线与s+i=1虚线分别列入图例。

**C2 主结果前置。** 模型后新增第3节“主结果与两层几何”，总定理3.1合并后文全局验证、唯一性及分区综合的已证结论，附阶段表和图1。定理没有作为后续证明的前提，未形成循环依赖。引言第一项贡献改引总定理。绝对连续水平集与Lipschitz复合改为标准事实及Fremlin教材引用，保留二维相对局部版本的局部化说明；容量时间集、横穿和容量延续的专门证明保留。命题12.3的完整正则性证明逐字符移至附录C，未删计算，正文保留结果与证明路线。

**C3 受限能力命题。** 命题5.2给出V_qbar的精确包络：充分性使用恒定最大控制，必要性在s≥h_qbar≥h>p上使用F_qbar单调性，并证明任意受限控制有限时间到达切点。采用符号表#13/#20的varpi_qbar、nu_qbar、d_qbar、h_qbar和花体I_qbar。另处理qbar=0/1、包络非正、物理总量截断、灭绝轴和h_qbar≥1−K时整个物理域可行的退化。此命题只判定可行性，没有声称受限能力的最低成本或简单截断反馈的可行性。

**C4 机制说明。** 第15节给出beta*c*q*dt=−beta*dPhi/[i(s−p)]，把Theta匹配解释为免费等待后完全跟踪成本的一阶变分为零。独立审阅后将免费等待的适用域明确收紧为x∈E∩D且i<K，并要求短自然轨道仍留在定义域；容量线上使用完整C_B+W成本变分。容量线上单位Phi削减成本随s下降而上升仅作直观线索，未替代严格验证。方法归功于Angulo的不变量坐标。

## 实际命令与结果

从项目目录执行的主要命令：

```powershell
python validation/geometry_proofs_20261021/apply_geometry.py
python validation/geometry_proofs_20261021/audit_revision.py
python ai/claude_revision_plan/checks/verify_new_notation.py
python validation/geometry_proofs_20261021/c3_check.py
python validation/geometry_proofs_20261021/make_two_layer_phase.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/geometry_proofs_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/geometry_proofs_20261021/build_revision.py --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/geometry_proofs_20261021/render_qa.py
git diff --check -- '*.tex' '*.bib' '*.py' '*.md' '*.json'
```

其中C3脚本由独立任务从仓库根目录以带项目目录前缀的等价路径执行，未重复运行。相图任务的实际生成入口和数据源另见 `two_layer_phase_README.md`。逐条构建命令、绝对路径、退出码与源/PDF哈希见 `attempt1/`、`attempt2/` 的构建报告；`apply_geometry.py` 为一次性集成入口，当前源码和源片段保留最终修正，`content_movement.json` 记录首次集成时的指纹，最终源指纹以 `attempt2/build_report.json` 为准。

| 验收 | 实际结果 |
|---|---|
| 范围、公式、标签与保护文件审计 | 21/21，通过 `audit_report.json` |
| 既有符号恒等式 | 28/28为True，见 `notation_checks.log` |
| 既有公式与生成数值 | 106个公式标签对应环境不变；两块自动数值内容不变 |
| C3不变量导数 | SymPy残差精确为0 |
| C3常控制IVP | 27次，最大峰值误差1.231209578733683e−12，低于预设2e−10 |
| C3物理截断 | 6组×500个截面核对通过 |
| 相图解析检查 | 几何检查点最大差1.11e−16；701点Theta残差最大3.55e−15；6个初值分类一致 |
| 最终主文构建 | XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，4/4退出0，42页 |
| 最终TheoryOnly构建 | 同一四阶段流程，4/4退出0，33页 |
| 最终日志 | 无错误、警告、未定义引用、缺字或溢出 |
| 页面目视 | 主文19页、TheoryOnly18页，共37页，详见下文与 `visual_qa.json` |
| 保护文件 | 535个已有原始数据、评估、代码和图形文件哈希不变 |
| 优化器 / 新增OCP / MATLAB | 0 / 0 / 0 |

27次IVP为已知常值控制下的ODE初值问题核对，不是OCP优化，也没有重跑S2的35次求解。几何标量求根只评价解析曲线，没有优化策略。检查和有限样本仿真不能替代正文解析证明。

## 构建诊断、页面与差异

首次构建实际完成主文四阶段，但最终日志检出数值节一段21.99733pt溢出，构建脚本因此阻断，未替换交付PDF，TheoryOnly尚未启动。原因是未来峰值前置后，原数值段落仍带旧章节前引且断行过长。删除过时章节号、将终端处理说明另起段后，完整重编两稿，最终8个进程全部退出0。首次日志原样保留，没有放宽验收标准。C阶段实际编译进程合计12次，最终交付取attempt2。

C3第一次抽样将“包络上方”扰动选到初值约束之外，触发样本合法性断言；修正抽样幅度后27个IVP全部通过，公式与通过阈值未变，见 `c3_README.md`。独立数学审阅发现的免费等待定义域问题已在最终编译前修正，见 `c_integration_readonly_review.md`。

实际目视主文1–11、22、28、29、36–38、41、42页；TheoryOnly1–10、21、27–33页。覆盖新增主结果、集合、阶段表、相图、教材引用、受限可行域、正则性正文与附录、机制以及参考文献，未声称目视全部42/33页。三个独立任务及主任务的记录分别保存在 `visual_main_front.md`、`visual_theory_front.md`、`visual_theory_back.md` 与 `visual_qa.json`。公式、引用和跨页无可见缺陷。作者栏/旧日期及目录末页留白作为G阶段整理项记录，没有在本轮改变。

与B修订38/29页相比，最终为42/33页；增长来自主结果概览、可行域证明和机制说明。按计划将N1改为两层呈现时，采用新文件名 `FigN1_two_layers.pdf/.png`，旧N1及既有figure_provenance字节不变；正文概览使用新图，数值节去掉重复单层图并前引概览。此处理保留旧图来源，不改写历史评估。完整改动路径见 `changed_files.txt`。

## 批次结论与剩余范围

C1–C4已完成，无尚未解决的公式、编译或排版阻断；首次构建的验收阻断及其修复如上保留。受限能力的成本最优综合不属于本批结论。没有开展C5、D的渐近/量级扫描、F重写或G全文定稿，也未改变模型、运行新优化或发布远程。

本轮B审阅修订为e86ec62；C为本报告所在的独立提交。两者均只在本地。公开仓库与B全文提取尚未发布的核查依据见上一提交的 `validation/intro_review_20261021/remote_visibility.json`；本轮没有清理或重写80074ec这段未推送历史。
