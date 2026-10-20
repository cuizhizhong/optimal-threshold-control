# 第四批 B：引言与贡献初稿

基线：`3be55d664b494429a86fc26ee270f14637ff3c75`。当前分支为 `codex/numerical-reproducibility-revision`。本报告所在提交的标题为 `paper: 重写引言与贡献（B）`，提交号以该提交为准；不推送。

## 修改与来源

摘要先陈述无回流五仓室问题及其闭合二维子系统，再依次陈述全域反馈与切换几何、全部可测可行控制的验证及提前退出容量、退化平台上的几乎处处唯一性。保留既有五例直接配点结果的有界表述，没有增加效应量级或回流结论。

引言按“控制问题—最接近的研究—跟踪动力学差异—本文结果”连续叙述。明确承认 MSW 与 FGLX 的候选成本验证、Angulo 的 final push、Morris 的维持后抑制结构，以及 AFG 的分区方法。三项贡献分别引用现有命题 9.2、推论 9.3、引理 9.4、定理 12.1、推论 12.2、引理 13.1、定理 13.2 和推论 13.3；编号由 LaTeX 引用生成。全域限定为正初值的物理域，提前退出限定于具有正长度容量阶段的轨道，唯一性按几乎处处相等理解。

`references.bib` 新增 Freddi–Goreac、Freddi–Goreac–Li–Xu、Kretzschmar 和 Morris 四项；已有 AFG 保留为独立项。FG 正式信息为 JCA 31(2), 525–562 (2024)，FGLX 为 AMO 86, article 23 (2022)，作者全名为 Juan Li 和 Boxiang Xu。五篇最近理论文献的位置、版本、来源指纹和适用条件见 [原文核对记录](sources/literature_audit.md) 与 [来源清单](sources/source_manifest.json)。

新增两篇背景文献的正式来源为 [Kretzschmar 2020](https://www.thelancet.com/article/S2468266720301572/pdf) 与 [Morris 2021](https://www.nature.com/articles/s42005-021-00570-y)。仅将前者用于说明检测、追踪延迟会影响效果，将后者用于承认不同目标下的维持后抑制先例；没有移植其参数或数值结果。网页搜索内容可读取，Morris 直接打开受到出版方登录跳转限制，不声称下载或审阅其完整补充材料。

## 实际命令及结果

以下从本项目目录执行；脚本内部逐条实际命令、绝对路径及退出码另见 `attempt1/build_report.json` 和 `render_manifest.json`。

```powershell
python validation/intro_contributions_20261021/audit_revision.py --capture
python validation/intro_contributions_20261021/audit_revision.py
python ai/claude_revision_plan/checks/verify_new_notation.py
node 'C:/Users/cui/.codex/plugins/cache/openai-primary-runtime/pdf/26.1015.12040/skills/pdf/container_tools/mark_artifact_operation_started.mjs' --operation-kind edit --expected-output-count 2 --output-format pdf
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/intro_contributions_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/intro_contributions_20261021/render_qa.py
git diff --check
git diff --cached --check -- '*.tex' '*.bib' '*.py' '*.md' '*.json'
```

原文文本通过 `pdftotext -layout <ref/PDF> <新目录文本>` 读取；关键来源页由 `pdftoppm` 渲染，输出及来源哈希见 `sources/`。相关提取文件仅为本轮阅读资料，不代替原始 PDF。

| 检查 | 结果 |
|---|---|
| B 范围、标签、引用与保护文件审计 | 18/18 通过，见 `audit_report.json` |
| 既有符号恒等式 | 28/28 为 True，见 `notation_checks.log` |
| 主文实际构建 | XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，4/4 退出 0，38 页 |
| TheoryOnly 实际构建 | 同一四阶段流程，4/4 退出 0，29 页 |
| 两份最终日志 | 无错误、警告、未定义引用、缺字或溢出 |
| 实际页面检查 | 主文 1、2、3、4、5、37、38 页；TheoryOnly 1、2、3、4、5、28、29 页 |
| 文件保护 | 507 个已有 data、matlab、figures 文件字节不变；模型节起至文末逐字不变，原有书目项不变 |
| 优化器调用 / 新增 OCP 求解 / MATLAB 调用 | 0 / 0 / 0 |

页面检查包括摘要、目录、引言、模型衔接及全部参考文献页，未声称目视全部 38/29 页。TheoryOnly 页面由独立审核任务检查，主文和三页关键原文由主任务检查。源文件哈希与双 PDF 指纹见构建报告，页面 PNG 指纹见渲染清单。

一次临时 PDF 文本预览在控制台输出含变音字符的作者名时触发 `UnicodeEncodeError: 'gbk' codec can't encode character`。这是标准输出编码问题，不是 PDF、编译或科学检查失败；正式渲染脚本将标准输出设为 UTF-8，后续渲染与文本写入全部成功，见 `operational_notes.json`。旧验证目录和原始数值记录没有改写或删除。

提交使用 `staging_paths.json` 的 43 条明确路径逐项传给 `git add -- <paths>`，没有使用 `git add .`。首次暂存在受限环境因 `.git/index.lock` 写权限失败；同一清单在获准执行的环境中重试成功。提交信息使用 UTF-8 文本文件传给 `git commit --file=<message-file>`，保留本仓库的 `Co-Authored-By: Codex <noreply@openai.com>`。工作开始前已有的未跟踪文件不纳入本提交。

## 与计划参照的差异及审阅节点

与本轮基线主文 37 页、TheoryOnly 28 页相比，最终为 38/29 页，来自引言和参考文献扩充。没有将计划中的历史数值称为新结果，没有调用旧版 E2 或 S2 优化，也没有启动 D 的效应量级计算。

本次仅完成 B，未修改两层分区、相图、主结果顺序、受限能力可行域或机制证明。C1–C4 尚未执行，C5 及回流研究继续不在范围内。完整改动路径见 `changed_files.txt`。

未触发公式失败或编译失败等停止条件；执行到计划明确要求的作者审阅节点。`START_HERE_CODEX.md` 第四批原文要求“重写引言与贡献，提交 B 后先等作者审阅；再整理两层分区、主结果前置、$\bar q$ 可行域命题、机制说明”。因此本提交后暂停，需作者审阅摘要和引言（主文第 1、3–4 页），确认后再执行 C1–C4。待审阅的核心是三项贡献的数学定位及相关工作比较的详略；没有尚待决定的模型或数值改动。
