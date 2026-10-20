# A1 作者返修：无回流五仓室模型与二维约化

本轮落实作者的新决定：当前论文只研究无回流模型的最优控制，有回流情形的数值研究留待未来独立开展。基线为 `e40c8971692a97feba6faea38bef6bae7167b941`，未进入 B 或后续阶段。

## 正文与计划修改

第2节现分为“基本模型”和“二维约化与控制问题”。先说明五个仓室与追踪分流，给出带 `SI/N` 的计数五式，交代移出仓室的聚合含义、参数单位、初值、人口守恒及无回流假设；再说明前两式不依赖其余仓室，归一化后引出原二维最优控制问题。

删除前稿的回流率、总易感回流变量、五维值函数及独立等价命题，也删除关于修订过程和来源误读的工作说明。摘要和结论只作研究对象的一致性修改。原控制集 `q:[0,infinity)->[0,1]`、正初值、感染阈值及线性成本不变；不采用参考稿的固定触阈启动、沿阈值运行至传播临界值才退出或双控制二次成本。

当前 `REVISION_PLAN.md`、`START_HERE_CODEX.md` 和符号表覆盖条款同步更新为 v5。旧 v4 原文单独保存为 `REVISION_PLAN_v4.md`。当前路线为 **A1 返修审阅 → B → C1–C4 → D → F → G**；回流端点、释放规则、回流优化、安全证书与相应失配实验退出本稿验收。已保存的原无回流算例 E1–E5 继续保留，与退出的阶段 E1–E5 区分。

## 参考写法与来源

- `E:/work/draft-submission-ready/paper/sections/02_model.tex`：借鉴仓室与流量先行、完整五式、移出聚合及量纲、再进入控制问题的叙述顺序。该文件仅只读参考，没有修改。
- 本地 `ref/Tang_Zhou_2024_JMB.pdf`：读取第4–6页，目视第4–5页。第4页 §2.1 与式(2.1)提供接触追踪结构及住院/康复仓室定义；第6页 §3 明确指出前两式闭合并转入二维分析。没有照搬其控制时段设定，也没有将第5页康复者不再感染的理由用于论证隔离易感者不回流。

参考文件指纹和正文范围核对见 `content_preservation.json`。本次修改使用 `nature-writing` 与 `pdf` 的写作、来源和渲染检查流程。

## 实际命令及结果

从仓库根目录执行：

```powershell
python tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/audit_revision.py --capture
python tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/verify_model.py
python tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/build_revision.py --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/render_qa.py
python tracing_isolation_optimal_control_complete/validation/model_no_return_revision_20261020/audit_revision.py
```

`python` 为 `E:/anaconda/python.exe`。构建与渲染使用预装 `pypdf/Pillow` 的 bundled Python。独立目录名称沿用返修开始时的日期。

| 检查 | 实际结果 |
|---|---|
| 计数模型归一化、守恒与聚合 | 8/8 通过，见 `model_algebra_report.json` |
| 既有符号恒等式 | 28/28 为 True，见 `notation_checks.log` |
| 源稿、标签、引用及范围审计 | 35/35 通过，见 `audit_report.json` |
| 最终双版本编译 | 主文37页、TheoryOnly 29页；最终日志无错误、警告、未定义引用、缺字或溢出 |
| 实际目视页面 | 主文第1、3、4、5、7、33页；TheoryOnly 第1、4、5、7、26页，均正常 |
| 文件保护 | 535个数据、评估、代码、图形等保护文件字节不变；两块数值生成内容不变 |
| MATLAB、优化器、新增 OCP 求解 | 均为0次 |

两次构建均实际执行主文及 TheoryOnly 的 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，均成功。首次构建后补充 `N>0`、完整仓室非负性及“解析主问题固定接触率”的表述，再完整执行第二次构建；交付 PDF 对应 `attempt2/build_report.json` 的源文件哈希。两次日志分开保存，没有覆盖历史验证目录。

本轮没有运行新的优化或数值矩阵。第3节至主要结论之前的原有理论、数值及讨论正文与返修基线逐字相同，具体核对见 `content_preservation.json`。只检查上述渲染页面，没有声称逐页检查全部37/29页。

## 提交、差异与作者审阅

提交标题为 `paper: 重写无回流五仓室模型与二维约化（A1 返修）`，提交号为本报告所在提交。完整文件列表见 `changed_files.txt`。仅提交正文、双PDF、项目说明、v5计划及本轮证据，不推送。

与上次 A1 的38/29页相比，本次为37/29页；页数变化来自删去回流建模与等价命题后的段落整理。与旧 v4 的回流要求有意不同，依据是作者本次明确修改研究范围；旧 v4 和已有记录保留，未伪装为已完成的回流研究。

未触发实际停止条件。按 v5 A1 的作者审阅节点，提交后暂停，请作者审阅第2节（主文第4–5页）的模型与行文。后续 B 尚未开始。
