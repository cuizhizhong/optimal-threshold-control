# C1–C4 作者审阅返修

基线 `a2909a8a2988ba471180549969852bbcd43075ab`；本报告所在提交为独立 C 返修提交。不进入 D，不推送。

## 修正内容

1. 主文数值节恢复 `FigN1_regions.pdf`，现为图2（主文第31页），图中 E1–E5 的初始点与 OpenOCL 轨道仍叠加于原理论分区。两层理论相图继续作为图1。没有重画旧 N1、改动轨道或重新生成数值图；TheoryOnly 条件块继续排除数值章节及图2。
2. 常接触率约定改为“本节及第5–14节”，用节标签生成编号，排除允许时变 c(t) 的第4节适定性定理。第15节机制说明单独声明采用常接触率假设。适定性定理的原陈述未变。
3. 概览中提前给出 Phi=i+s−h ln s，并说明它是零控制自然轨道的标签；原正式定义式整体前移，没有重复定义或改变公式。补明 Gamma_K、辅助条带中的(s_B,K)、Phi_B=Phi(s_B,K)与Q*的角色，精确构造继续前引后文。阶段表分为五行，加入自然语言策略列，分别解释A、T∪Gamma_K、W_Gamma、W_K、B，并明确B仅为i=K、s>s_B的容量平台，临界自然轨道Phi=Phi_B的容量段为零。
4. 八处水平集性质补上式 `eq:ac-level-set` 的定位。安全不变性引理去掉重复的V0/V1端点陈述和证明，只保留前向不变性及A0=A；端点计算集中保留在受限能力命题，概览相应分别引用。原最大零控制安全集命题仍处理其安全含义与零成本唯一性。

图1的生成流程、字体和英文标签留到已计划的F/G阶段统一。本轮未修改作者栏、旧日期、图件或数值记录。

## 实际命令及结果

从项目目录执行：

```powershell
node 'C:/Users/cui/.codex/plugins/cache/openai-primary-runtime/pdf/26.1015.12040/skills/pdf/container_tools/mark_artifact_operation_started.mjs' --operation-kind edit --expected-output-count 2 --output-format pdf
python ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/geometry_review_20261021/build_revision.py --attempt 1
python validation/geometry_review_20261021/audit_revision.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/geometry_review_20261021/render_qa.py
git diff --check
```

| 检查 | 结果 |
|---|---|
| 返修范围、原公式、条件编译与保存文件审计 | 27/27，见 `audit_report.json` |
| 既有符号恒等式 | 28/28为True，见 `notation_checks.log` |
| 原公式 | 118个既有公式标签对应环境逐字相同；Phi定义仅搬移 |
| C3与附录 | 受限能力一节及正则性完整证明逐字相同 |
| 两份最终编译 | 各实际执行XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，8/8进程退出0 |
| 最终页数 | 主文43页、TheoryOnly33页 |
| 最终日志 | 无错误、警告、未定义引用、缺字或溢出 |
| 实际目视 | 主文6、7、8、9、11、28、30、31、32页；TheoryOnly5、6、7、8、10、27页 |
| 原始记录与图件 | 535个既有保护文件及两层新图的哈希不变；两块生成数值不变 |
| 本轮新增计算 | 优化器0、OCP0、ODE积分0、MATLAB0；未重跑C3或S2 |

源文件与双PDF哈希、逐条编译命令和退出码见 `attempt1/build_report.json`。本轮编译目录的main.aux含图2，TheoryOnly辅助文件无该图标签，见 `page_map.json`，未用latex根目录陈旧辅助文件作判断。最终主文第31页已实际目视确认五条轨道和初始点；概览五行表及常接触率范围均正常。独立复核见 `read_only_review.md`、`visual_theory_review.md`，页面与PNG哈希见 `render_manifest.json`。未声称目视全部43/33页。

## 参照差异、停止条件与仓库事项

相对C初稿42/33页，本轮为43/33页，主文增加的一页来自恢复数值相图及其排版；TheoryOnly页数不变。没有数学结论或数值结果变化。未触发编译、公式或范围停止条件。完整改动清单见 `changed_files.txt`。

仓库事项与论文返修分开：作者本轮指出仓库为public，已推送的b039bdc含21份ref PDF；本地树对象再次核对了这21份文件的存在。它们与尚未推送的80074ec所新增全文提取是两个不同范围。先前“未推送”的结论只覆盖后者，不能据此推断既有ref从未公开。记录见 `repository_issue.json`。

本轮没有改变仓库可见性，没有移除任何参考文献、提取文件或历史提交，也没有执行push、force-push、历史清理或许可证判断。仓库处理留待作者另行决定；论文修正不依赖该决定。已有未跟踪的Morris/Kretzschmar参考副本也未纳入本次提交。
