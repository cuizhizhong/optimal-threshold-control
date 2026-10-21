# G1 全文结构重排与结构性删除验证

基准：`689a6277dc478099971280909a65ffa728feb8ea`。作者决定见 [G_DECISIONS.md](../../ai/claude_revision_plan/G_DECISIONS.md)。本目录只记录 G1，不授权执行 G2–G5。

## 实际结果

- 主文 46 → 45 页。正文重排为 10 节，附录按指定顺序排列，补充材料 S 本批仍内联。
- 保全审计通过：124 个保留公式标签对应的公式逐字相同，仅删除指定 5 式；两个自动生成块逐字不变。
- 白名单之外无旧段落缺失或新段落；段落归一化后字符多重集一致。原 208 段与新 207 段的计数差来自结构删除后相邻段落拼接，双向整段查找均通过。
- 2474 个 data/、figures/、生成宏、MATLAB 源码和既有 validation/ 文件的工作区原始字节不变。历史数据、导出器、图形和已有验证记录未改。
- 完全跟踪分区引理的完整 proof 环境逐字移入附录 C；唯一性证明只剔除获准新增路线与分步前缀后，原有证明内部逐字相同。
- 工作区与 Git 暂存区导出的独立副本各运行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，再额外运行一次 XeLaTeX，共 10 条命令退出 0。最终 .log/.blg/stdout 零诊断，无未定义引用、溢出、缺图或缺字。
- 独立副本初始仅含从 Git 导出的 latex/ 和 figures/；移除副本内旧编译产物后从零构建。fls 未读入工作区其他路径或 validation/ 内容。两份 45 页 PDF 的逐页提取文本和完整目录一致；正式 PDF 与工作区最终构建 SHA-256 相同。
- 指定的 11 页已以 150 dpi 实际渲染并逐张目视：目录 1–3 页，第 4/5/6/7/9 节起始 8/13/20/25/35 页，唯一性证明 24–25 页，新增附录证明 37–38 页。未见重叠、溢出、缺字或截断。详见两份 visual_qa JSON。
- 优化器 / 新增 OCP / MATLAB 调用：**0 / 0 / 0**。未运行导出器、数据重评或图形重导出。未推送；完成一次独立提交后停止等作者审阅。

## 新目录与页码

| 章节 | 标题 | 起始页 |
|---|---|---:|
| 1 | 引言 | 4 |
| 2 | 模型与控制问题 | 5 |
| 3 | 主结果与最优分区 | 6 |
| 4 | 预备结果 | 8 |
| 5 | 候选策略的构造 | 13 |
| 6 | 全局最优性与唯一性 | 20 |
| 7 | 机制与量级 | 25 |
| 8 | 数值结果 | 31 |
| 9 | 讨论 | 35 |
| 10 | 结论 | 36 |
| A | 完全跟踪成本导数的逐步计算 | 36 |
| B | 容量边界成本积分的逐步计算 | 37 |
| C | 完全跟踪分区可达性与不再返回等待区的证明 | 37 |
| D | 梯度拼接与相对正则性的详细证明 | 38 |
| E | 小容量渐近的完整推导 | 40 |
| F | 感染阈值与医疗需求 | 41 |
| G | 补充材料 S：数值复现、复核与诊断记录 | 42 |

完整层级：

- 引言（第 4 页）
- 模型与控制问题（第 5 页）
  - 基本模型（第 5 页）
  - 二维约化与控制问题（第 6 页）
- 主结果与最优分区（第 6 页）
  - 安全集与可行性（第 7 页）
  - 全域反馈与阶段结构（第 7 页）
- 预备结果（第 8 页）
  - 解的适定性、正性与基本耗散（第 9 页）
  - 常接触率问题、自然轨道与安全目标集（第 9 页）
    - 自然传播不变量与峰值（第 9 页）
    - 安全集与目标边界（第 10 页）
  - 两类控制弧与显式成本（第 10 页）
    - 一般控制下的不变量导数（第 10 页）
    - 完全跟踪弧（第 10 页）
    - 容量弧（第 11 页）
  - 有限成本可行性与首次到达问题（第 11 页）
  - HJB 方程与验证所需的边界条件（第 12 页）
- 候选策略的构造（第 13 页）
  - 完全跟踪成本的有限可达域及导数（第 13 页）
  - 切换曲线的存在、单调性及严格横穿（第 14 页）
  - 全域候选反馈与候选成本（第 17 页）
  - 两种等待分支的统一导数（第 19 页）
  - 内部界面与局部 Lipschitz 性（第 20 页）
- 全局最优性与唯一性（第 20 页）
  - 容量 Hamiltonian 与沿任意轨道的链式法则（第 21 页）
  - 全局最优性验证（第 22 页）
  - 常接触率下控制与轨道的唯一性（第 23 页）
- 机制与量级（第 25 页）
  - 一维切换成本与全局结论的关系（第 25 页）
  - 不变量坐标与切换机制（第 26 页）
  - 比较基准、小容量渐近与参数量级（第 27 页）
    - 纯容量填充与比较指标（第 27 页）
    - 固定传播概率下的小容量命题（第 28 页）
    - 参数来源与解析扫描（第 29 页）
- 数值结果（第 31 页）
  - 数值方法与实验设置（第 31 页）
  - 不同初值区域下的数值验证（第 32 页）
    - 代表初值与相平面分区（第 32 页）
    - 两种等待区域的对照（第 33 页）
    - 立即完全跟踪与容量边界初值（第 34 页）
    - 成本、约束误差与剩余残差（第 35 页）
- 讨论（第 35 页）
  - 同时控制接触率与跟踪比例时的限制（第 35 页）
  - 模型假设与理论边界（第 36 页）
- 结论（第 36 页）
- 完全跟踪成本导数的逐步计算（第 36 页）
- 容量边界成本积分的逐步计算（第 37 页）
- 完全跟踪分区可达性与不再返回等待区的证明（第 37 页）
- 梯度拼接与相对正则性的详细证明（第 38 页）
- 小容量渐近的完整推导（第 40 页）
- 感染阈值与医疗需求（第 41 页）
- 补充材料 S：数值复现、复核与诊断记录（第 42 页）

## 证据与可复核命令

- [文字、公式和白名单原文/新文审计](preservation_audit.md)；机器结果为 [preservation_audit.json](preservation_audit.json)。全部白名单逐条列出，结构标题新旧清单另列。
- [前向引用依赖说明](forward_dependency_review.md)；完整清单逐项附在本 README 下方。
- [工作区构建记录](workspace_attempt1/build_report.json)、[自包含构建记录](isolated_attempt1/build_report.json)，保存每条实际 argv/cwd/退出码及最终日志。
- [150 dpi 渲染记录](render_manifest.json)、[目视记录一](visual_qa_primary.json)、[目视记录二](visual_qa_secondary.json)。
- [最终验收汇总](acceptance_report.json)。初始默认 Anaconda 缺少 pypdf 的失败保留在 initial_runtime_failure.json；未开始编译，随后使用 bundled Python。保护文件首次枚举遭遇 Windows 长路径限制的记录保留在 audit_attempt1_capture_failure.json，修正枚举后核对通过。
- [明确提交路径](changed_files.txt)与[实际暂存范围核对](commit_preflight.json)。首次暂存因已经暂存删除的路径再次作为 pathspec 传入而失败，记录见 staging_initial_failure.json 和 commit_preflight_initial_failure.json；修正后实际索引与完整预期清单逐项相同。
- 重复汇总时对已相同的 main.bbl 回写遇到 Windows `OSError: [Errno 22] Invalid argument`，记录见 finalize_repeat_failure.json。核对现有 bbl 与最终构建逐字相同后，汇总改为跳过相同成品，正式 PDF 校验通过。原始编译记录保留工具产生的行尾空格，源码与文档的 `git diff --check` 排除原始 `.log` 与 `.aux` 文件后通过。

Python 使用 `load_workspace_dependencies` 返回的 `C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。工作区初次构建和自包含初次构建均已通过，无额外隐藏预编译。构建脚本拒绝覆盖既有 attempt；重复运行须增加 `--attempt`。

```powershell
& $py -X utf8 validation/structure_g1_20261021/audit_preservation.py
& $py -X utf8 validation/structure_g1_20261021/check_forward_refs.py
& $py -X utf8 validation/structure_g1_20261021/build_g1.py --mode workspace --attempt 2
# 自包含构建前，须先用明确路径列表暂存所要验证的 LaTeX 源码和删除项。
& $py -X utf8 validation/structure_g1_20261021/build_g1.py --mode isolated --attempt 2
```

上述命令相对于项目目录；`$py` 应绑定上述 bundled Python 绝对路径。完整实际首次命令见 build_report.json；不得将示例重跑命令当成本轮执行次数。

## 作者审阅重点

请通读新第 4–6 节导读及唯一性证明分步，检查正文长引理证明思路与附录 C 的衔接。讨论只移动，现有时变接触率未完成证明的说明原样保留；未进入 G2 改写。第 3 节概览中的前向引用及第 4 节证明路线中的预告是有意导读，概览以外的证明内前向引用为 0，详见下方逐项清单及依赖说明。

---

# 前向引用完整清单

源文件：`E:\work\optimal-threshold-control\tracing_isolation_optimal_control_complete\latex\main.tex`；SHA-256：`13668de1eeb989f2db12677cde35b3e1e48536d4f7a613ac0b3d195e3f2d9633`。

检查 `ref`、`eqref`、`autoref`、`cref` 等命令及已知引用包装宏 `NumTheoryRef`，目标限于定理、引理、命题、推论和带标签公式。未转义注释不参与扫描；定义位置采用对象的 `begin` 行，另列 `label` 行。同一公式内部的自引用不计为前向。已核对 `\providecommand{\NumTheoryRef}[2]{#2~\ref{#1}}`，只按这一已知展开纳入该包装宏；目标是定义、图表等其他类型时仍按范围排除。其他任意宏不推断，主文件之外的 `input` 不展开，当前审计范围为 `main.tex`。

计数：definitions=154；references=208；wrapped_references=3；forward=37；intentional_overview=11；other_forward=26；proof_forward_outside_overview=0。

## 第 3 节概览中的有意前向引用

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 13 | 251:12 | `\ref{thm:wellposed}` | 3 主结果与最优分区 | 正文 | 387 / 388 | 是（第 3 节概览） |
| 14 | 264:2 | `\eqref{eq:sum-decay}` | 3 主结果与最优分区 | 正文 | 391 / 397 | 是（第 3 节概览） |
| 15 | 296:3 | `\ref{lem:safe-invariant}` | 3 主结果与最优分区 > 3.1 安全集与可行性 | 正文 | 504 / 505 | 是（第 3 节概览） |
| 17 | 322:7 | `\ref{prop:candidate-attainment}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1111 / 1112 | 是（第 3 节概览） |
| 18 | 322:41 | `\ref{thm:verification}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1349 / 1350 | 是（第 3 节概览） |
| 19 | 322:66 | `\ref{thm:unique-q}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1530 / 1531 | 是（第 3 节概览） |
| 21 | 331:48 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 832 / 833 | 是（第 3 节概览） |
| 22 | 331:76 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 898 / 899 | 是（第 3 节概览） |
| 23 | 336:16 | `\ref{cor:optimal-synthesis}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 1640 / 1641 | 是（第 3 节概览） |
| 24 | 337:16 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 832 / 833 | 是（第 3 节概览） |
| 25 | 337:44 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 898 / 899 | 是（第 3 节概览） |

## 其他前向引用

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 1 | 137:3 | `\ref{thm:main-overview}` | 1 引言 | 正文 | 313 / 314 | 是 |
| 2 | 137:40 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 326 / 327 | 是 |
| 3 | 143:3 | `\ref{lem:finite-entry}` | 1 引言 | 正文 | 597 / 598 | 是 |
| 4 | 144:3 | `\ref{thm:verification}` | 1 引言 | 正文 | 1349 / 1350 | 是 |
| 5 | 145:3 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 326 / 327 | 是 |
| 6 | 153:3 | `\ref{cor:verification-equality}` | 1 引言 | 正文 | 1377 / 1378 | 是 |
| 7 | 153:44 | `\ref{lem:no-early-boundary-exit}` | 1 引言 | 正文 | 1453 / 1454 | 是 |
| 8 | 155:3 | `\ref{thm:unique-q}` | 1 引言 | 正文 | 1530 / 1531 | 是 |
| 26 | 381:56 | `\ref{cor:one-dimensional-min}` | 4 预备结果 | 正文 | 1710 / 1711 | 是 |
| 27 | 382:12 | `\ref{cor:verification-equality}` | 4 预备结果 | 正文 | 1377 / 1378 | 是 |
| 28 | 382:68 | `\ref{lem:no-early-boundary-exit}` | 4 预备结果 | 正文 | 1453 / 1454 | 是 |
| 29 | 382:118 | `\ref{thm:unique-q}` | 4 预备结果 | 正文 | 1530 / 1531 | 是 |
| 30 | 382:165 | `\ref{thm:unique-q}` | 4 预备结果 | 正文 | 1530 / 1531 | 是 |
| 31 | 383:13 | `\ref{prop:reachable}` | 4 预备结果 | 正文 | 703 / 704 | 是 |
| 32 | 383:36 | `\ref{lem:tracking-region}` | 4 预备结果 | 正文 | 1070 / 1071 | 是 |
| 33 | 383:76 | `\ref{prop:Gamma-geometry}` | 4 预备结果 | 正文 | 832 / 833 | 是 |
| 34 | 383:104 | `\ref{cor:Gamma-labels}` | 4 预备结果 | 正文 | 898 / 899 | 是 |
| 35 | 383:135 | `\ref{lem:strict-crossing}` | 4 预备结果 | 正文 | 923 / 924 | 是 |
| 36 | 383:178 | `\ref{lem:chi-regions}` | 4 预备结果 | 正文 | 1002 / 1003 | 是 |
| 37 | 383:222 | `\eqref{eq:ac-level-set}` | 4 预备结果 | 正文 | 428 / 430 | 是 |
| 38 | 383:276 | `\ref{prop:regularity}` | 4 预备结果 | 正文 | 1219 / 1220 | 是 |
| 39 | 383:300 | `\ref{lem:finite-entry}` | 4 预备结果 | 正文 | 597 / 598 | 是 |
| 68 | 997:5 | `\ref{prop:regularity}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1219 / 1220 | 是 |
| 77 | 1142:8 | `\ref{thm:verification}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1349 / 1350 | 是 |
| 78 | 1143:18 | `\ref{cor:optimal-synthesis}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1640 / 1641 | 是 |
| 87 | 1243:17 | `\ref{lem:trajectory-verification}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 正文 | 1302 / 1303 | 是 |

## 概览以外证明中的前向引用

无。

## 全部引用（按源码顺序）

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 1 | 137:3 | `\ref{thm:main-overview}` | 1 引言 | 正文 | 313 / 314 | 是 |
| 2 | 137:40 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 326 / 327 | 是 |
| 3 | 143:3 | `\ref{lem:finite-entry}` | 1 引言 | 正文 | 597 / 598 | 是 |
| 4 | 144:3 | `\ref{thm:verification}` | 1 引言 | 正文 | 1349 / 1350 | 是 |
| 5 | 145:3 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 326 / 327 | 是 |
| 6 | 153:3 | `\ref{cor:verification-equality}` | 1 引言 | 正文 | 1377 / 1378 | 是 |
| 7 | 153:44 | `\ref{lem:no-early-boundary-exit}` | 1 引言 | 正文 | 1453 / 1454 | 是 |
| 8 | 155:3 | `\ref{thm:unique-q}` | 1 引言 | 正文 | 1530 / 1531 | 是 |
| 9 | 202:2 | `\eqref{eq:five-compartment-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 172 / 180 | 否 |
| 10 | 240:45 | `\eqref{eq:normalized-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 210 / 215 | 否 |
| 11 | 241:22 | `\eqref{eq:capacity}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 222 / 224 | 否 |
| 12 | 245:37 | `\eqref{eq:normalized-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 210 / 215 | 否 |
| 13 | 251:12 | `\ref{thm:wellposed}` | 3 主结果与最优分区 | 正文 | 387 / 388 | 是（第 3 节概览） |
| 14 | 264:2 | `\eqref{eq:sum-decay}` | 3 主结果与最优分区 | 正文 | 391 / 397 | 是（第 3 节概览） |
| 15 | 296:3 | `\ref{lem:safe-invariant}` | 3 主结果与最优分区 > 3.1 安全集与可行性 | 正文 | 504 / 505 | 是（第 3 节概览） |
| 16 | 315:3 | `\eqref{eq:constants}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 253 / 256 | 否 |
| 17 | 322:7 | `\ref{prop:candidate-attainment}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1111 / 1112 | 是（第 3 节概览） |
| 18 | 322:41 | `\ref{thm:verification}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1349 / 1350 | 是（第 3 节概览） |
| 19 | 322:66 | `\ref{thm:unique-q}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1530 / 1531 | 是（第 3 节概览） |
| 20 | 328:4 | `\ref{thm:main-overview}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 313 / 314 | 否 |
| 21 | 331:48 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 832 / 833 | 是（第 3 节概览） |
| 22 | 331:76 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 898 / 899 | 是（第 3 节概览） |
| 23 | 336:16 | `\ref{cor:optimal-synthesis}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 1640 / 1641 | 是（第 3 节概览） |
| 24 | 337:16 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 832 / 833 | 是（第 3 节概览） |
| 25 | 337:44 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 898 / 899 | 是（第 3 节概览） |
| 26 | 381:56 | `\ref{cor:one-dimensional-min}` | 4 预备结果 | 正文 | 1710 / 1711 | 是 |
| 27 | 382:12 | `\ref{cor:verification-equality}` | 4 预备结果 | 正文 | 1377 / 1378 | 是 |
| 28 | 382:68 | `\ref{lem:no-early-boundary-exit}` | 4 预备结果 | 正文 | 1453 / 1454 | 是 |
| 29 | 382:118 | `\ref{thm:unique-q}` | 4 预备结果 | 正文 | 1530 / 1531 | 是 |
| 30 | 382:165 | `\ref{thm:unique-q}` | 4 预备结果 | 正文 | 1530 / 1531 | 是 |
| 31 | 383:13 | `\ref{prop:reachable}` | 4 预备结果 | 正文 | 703 / 704 | 是 |
| 32 | 383:36 | `\ref{lem:tracking-region}` | 4 预备结果 | 正文 | 1070 / 1071 | 是 |
| 33 | 383:76 | `\ref{prop:Gamma-geometry}` | 4 预备结果 | 正文 | 832 / 833 | 是 |
| 34 | 383:104 | `\ref{cor:Gamma-labels}` | 4 预备结果 | 正文 | 898 / 899 | 是 |
| 35 | 383:135 | `\ref{lem:strict-crossing}` | 4 预备结果 | 正文 | 923 / 924 | 是 |
| 36 | 383:178 | `\ref{lem:chi-regions}` | 4 预备结果 | 正文 | 1002 / 1003 | 是 |
| 37 | 383:222 | `\eqref{eq:ac-level-set}` | 4 预备结果 | 正文 | 428 / 430 | 是 |
| 38 | 383:276 | `\ref{prop:regularity}` | 4 预备结果 | 正文 | 1219 / 1220 | 是 |
| 39 | 383:300 | `\ref{lem:finite-entry}` | 4 预备结果 | 正文 | 597 / 598 | 是 |
| 40 | 390:3 | `\eqref{eq:normalized-model}` | 4 预备结果 > 4.1 解的适定性、正性与基本耗散 | 正文 | 210 / 215 | 否 |
| 41 | 421:9 | `\eqref{eq:i-integrable}` | 4 预备结果 > 4.1 解的适定性、正性与基本耗散 | 证明 3，thm:wellposed | 400 / 402 | 否 |
| 42 | 444:6 | `\eqref{eq:constants}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 | 正文 | 253 / 256 | 否 |
| 43 | 444:31 | `\eqref{eq:value-definition}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 | 正文 | 268 / 270 | 否 |
| 44 | 455:3 | `\eqref{eq:Phi}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 > 4.2.1 自然传播不变量与峰值 | 正文 | 304 / 306 | 否 |
| 45 | 466:20 | `\eqref{eq:uncontrolled-future-peak}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 > 4.2.1 自然传播不变量与峰值 | 正文 | 277 / 283 | 否 |
| 46 | 475:16 | `\eqref{eq:safe-set}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 > 4.2.2 安全集与目标边界 | 正文 | 291 / 293 | 否 |
| 47 | 476:3 | `\eqref{eq:uncontrolled-future-peak}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 > 4.2.2 安全集与目标边界 | 正文 | 277 / 283 | 否 |
| 48 | 485:3 | `\eqref{eq:natural-peak}` | 4 预备结果 > 4.2 常接触率问题、自然轨道与安全目标集 > 4.2.2 安全集与目标边界 | 证明 4，prop:safe-exact | 461 / 463 | 否 |
| 49 | 510:10 | `\eqref{eq:Phi-derivative}` | 4 预备结果 > 4.3 两类控制弧与显式成本 > 4.3.1 一般控制下的不变量导数 | 证明 5，lem:safe-invariant | 493 / 495 | 否 |
| 50 | 512:9 | `\eqref{eq:sum-decay}` | 4 预备结果 > 4.3 两类控制弧与显式成本 > 4.3.1 一般控制下的不变量导数 | 证明 5，lem:safe-invariant | 391 / 397 | 否 |
| 51 | 549:15 | `\eqref{eq:ac-level-set}` | 4 预备结果 > 4.3 两类控制弧与显式成本 > 4.3.3 容量弧 | 正文 | 428 / 430 | 否 |
| 52 | 589:11 | `\eqref{eq:boundary-duration}` | 4 预备结果 > 4.4 有限成本可行性与首次到达问题 | 证明 6，lem:finite-feasible | 563 / 565 | 否 |
| 53 | 589:41 | `\eqref{eq:boundary-cost}` | 4 预备结果 > 4.4 有限成本可行性与首次到达问题 | 证明 6，lem:finite-feasible | 567 / 572 | 否 |
| 54 | 612:59 | `\eqref{eq:i-integrable}` | 4 预备结果 > 4.4 有限成本可行性与首次到达问题 | 证明 7，lem:finite-entry | 400 / 402 | 否 |
| 55 | 629:19 | `\ref{lem:finite-entry}` | 4 预备结果 > 4.4 有限成本可行性与首次到达问题 | 证明 8，prop:exit-equivalence | 597 / 598 | 否 |
| 56 | 687:3 | `\eqref{eq:H-affine}` | 4 预备结果 > 4.5 HJB 方程与验证所需的边界条件 | 证明 9，lem:bangbang | 648 / 651 | 否 |
| 57 | 731:7 | `\eqref{eq:endpoint-system}` | 5 候选策略的构造 > 5.1 完全跟踪成本的有限可达域及导数 | 证明 10，prop:reachable | 712 / 716 | 否 |
| 58 | 744:24 | `\ref{lem:finite-feasible}` | 5 候选策略的构造 > 5.1 完全跟踪成本的有限可达域及导数 | 正文 | 578 / 579 | 否 |
| 59 | 782:3 | `\eqref{eq:Ws}` | 5 候选策略的构造 > 5.1 完全跟踪成本的有限可达域及导数 | 证明 11，prop:W-HJB | 753 / 755 | 否 |
| 60 | 782:18 | `\eqref{eq:Wi}` | 5 候选策略的构造 > 5.1 完全跟踪成本的有限可达域及导数 | 证明 11，prop:W-HJB | 753 / 757 | 否 |
| 61 | 802:3 | `\eqref{eq:q1-backward}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 正文 | 790 / 792 | 否 |
| 62 | 877:4 | `\ref{lem:unimodal}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 证明 13，prop:Gamma-geometry | 800 / 801 | 否 |
| 63 | 891:37 | `\ref{lem:unimodal}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 证明 13，prop:Gamma-geometry | 800 / 801 | 否 |
| 64 | 917:14 | `\eqref{eq:Gamma-slope}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 证明 14，cor:Gamma-labels | 847 / 852 | 否 |
| 65 | 935:5 | `\eqref{eq:Gamma-slope}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 证明 15，lem:strict-crossing | 847 / 852 | 否 |
| 66 | 942:2 | `\eqref{eq:ac-level-set}` | 5 候选策略的构造 > 5.2 切换曲线的存在、单调性及严格横穿 | 证明 15，lem:strict-crossing | 428 / 430 | 否 |
| 67 | 971:49 | `\eqref{eq:Gamma-hit-map}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 908 / 911 | 否 |
| 68 | 997:5 | `\ref{prop:regularity}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1219 / 1220 | 是 |
| 69 | 1017:3 | `\ref{cor:Gamma-labels}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 16，lem:chi-regions | 898 / 899 | 否 |
| 70 | 1026:38 | `\eqref{eq:chi-regions}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 16，lem:chi-regions | 1006 / 1010 | 否 |
| 71 | 1044:4 | `\ref{lem:chi-regions}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1002 / 1003 | 否 |
| 72 | 1115:6 | `\eqref{eq:candidate-feedback}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1084 / 1091 | 否 |
| 73 | 1124:8 | `\eqref{eq:boundary-duration}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 17，prop:candidate-attainment | 563 / 565 | 否 |
| 74 | 1125:10 | `\ref{lem:tracking-region}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 17，prop:candidate-attainment | 1070 / 1071 | 否 |
| 75 | 1126:3 | `\eqref{eq:sum-decay}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 17，prop:candidate-attainment | 391 / 397 | 否 |
| 76 | 1127:9 | `\eqref{eq:candidate-U}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 证明 17，prop:candidate-attainment | 1094 / 1102 | 否 |
| 77 | 1142:8 | `\ref{thm:verification}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1349 / 1350 | 是 |
| 78 | 1143:18 | `\ref{cor:optimal-synthesis}` | 5 候选策略的构造 > 5.3 全域候选反馈与候选成本 | 正文 | 1640 / 1641 | 是 |
| 79 | 1175:39 | `\eqref{eq:Ws}` | 5 候选策略的构造 > 5.4 两种等待分支的统一导数 | 证明 18，lem:waiting-gradient | 753 / 755 | 否 |
| 80 | 1175:54 | `\eqref{eq:Wi}` | 5 候选策略的构造 > 5.4 两种等待分支的统一导数 | 证明 18，lem:waiting-gradient | 753 / 757 | 否 |
| 81 | 1204:4 | `\eqref{eq:waiting-gradient}` | 5 候选策略的构造 > 5.4 两种等待分支的统一导数 | 证明 19，lem:waiting-HJB | 1168 / 1171 | 否 |
| 82 | 1210:20 | `\ref{lem:unimodal}` | 5 候选策略的构造 > 5.4 两种等待分支的统一导数 | 证明 19，lem:waiting-HJB | 800 / 801 | 否 |
| 83 | 1214:3 | `\eqref{eq:Lambda-natural}` | 5 候选策略的构造 > 5.4 两种等待分支的统一导数 | 证明 19，lem:waiting-HJB | 1206 / 1208 | 否 |
| 84 | 1232:11 | `\eqref{eq:waiting-gradient}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 证明 20，prop:regularity | 1168 / 1171 | 否 |
| 85 | 1232:40 | `\eqref{eq:Ws}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 证明 20，prop:regularity | 753 / 755 | 否 |
| 86 | 1232:55 | `\eqref{eq:Wi}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 证明 20，prop:regularity | 753 / 757 | 否 |
| 87 | 1243:17 | `\ref{lem:trajectory-verification}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 正文 | 1302 / 1303 | 是 |
| 88 | 1256:8 | `\eqref{eq:ac-level-set}` | 5 候选策略的构造 > 5.5 内部界面与局部 Lipschitz 性 | 正文 | 428 / 430 | 否 |
| 89 | 1288:7 | `\ref{lem:waiting-HJB}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 21，prop:all-HJB | 1193 / 1194 | 否 |
| 90 | 1288:37 | `\ref{lem:tracking-region}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 21，prop:all-HJB | 1070 / 1071 | 否 |
| 91 | 1288:65 | `\ref{prop:W-HJB}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 21，prop:all-HJB | 771 / 772 | 否 |
| 92 | 1290:8 | `\eqref{eq:capacity-gradient}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 21，prop:all-HJB | 1225 / 1227 | 否 |
| 93 | 1291:39 | `\eqref{eq:capacity-tie}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 21，prop:all-HJB | 1282 / 1284 | 否 |
| 94 | 1295:2 | `\eqref{eq:capacity-tie}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 正文 | 1282 / 1284 | 否 |
| 95 | 1297:2 | `\eqref{eq:HJB-table}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 正文 | 1270 / 1278 | 否 |
| 96 | 1313:4 | `\ref{prop:regularity}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 1219 / 1220 | 否 |
| 97 | 1316:10 | `\ref{prop:all-HJB}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 1267 / 1268 | 否 |
| 98 | 1322:37 | `\eqref{eq:ac-level-set}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 428 / 430 | 否 |
| 99 | 1324:32 | `\ref{prop:regularity}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 1219 / 1220 | 否 |
| 100 | 1328:13 | `\eqref{eq:boundary-cost}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 567 / 572 | 否 |
| 101 | 1333:3 | `\eqref{eq:ac-level-set}` | 6 全局最优性与唯一性 > 6.1 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，lem:trajectory-verification | 428 / 430 | 否 |
| 102 | 1351:3 | `\eqref{eq:constants}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 253 / 256 | 否 |
| 103 | 1352:6 | `\eqref{eq:candidate-U}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1094 / 1102 | 否 |
| 104 | 1352:48 | `\eqref{eq:value-definition}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 268 / 270 | 否 |
| 105 | 1358:13 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1111 / 1112 | 否 |
| 106 | 1359:22 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1111 / 1112 | 否 |
| 107 | 1359:54 | `\ref{prop:regularity}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1219 / 1220 | 否 |
| 108 | 1359:78 | `\ref{lem:finite-entry}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 597 / 598 | 否 |
| 109 | 1362:3 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 23，thm:verification | 1111 / 1112 | 否 |
| 110 | 1364:19 | `\ref{lem:finite-entry}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 23，thm:verification | 597 / 598 | 否 |
| 111 | 1365:4 | `\ref{lem:trajectory-verification}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 23，thm:verification | 1302 / 1303 | 否 |
| 112 | 1379:4 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1349 / 1350 | 否 |
| 113 | 1411:4 | `\ref{lem:finite-entry}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 597 / 598 | 否 |
| 114 | 1413:16 | `\ref{lem:trajectory-verification}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 1302 / 1303 | 否 |
| 115 | 1425:3 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 1349 / 1350 | 否 |
| 116 | 1426:4 | `\eqref{eq:verification-gap}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 1391 / 1397 | 否 |
| 117 | 1429:2 | `\eqref{eq:verification-gap}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 1391 / 1397 | 否 |
| 118 | 1433:13 | `\eqref{eq:verification-equality-conditions}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 证明 24，cor:verification-equality | 1400 / 1405 | 否 |
| 119 | 1443:15 | `\ref{lem:trajectory-verification}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1302 / 1303 | 否 |
| 120 | 1445:3 | `\ref{cor:verification-equality}` | 6 全局最优性与唯一性 > 6.2 全局最优性验证 | 正文 | 1377 / 1378 | 否 |
| 121 | 1455:4 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1349 / 1350 | 否 |
| 122 | 1496:3 | `\ref{cor:verification-equality}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 25，lem:no-early-boundary-exit | 1377 / 1378 | 否 |
| 123 | 1497:3 | `\ref{lem:waiting-HJB}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 25，lem:no-early-boundary-exit | 1193 / 1194 | 否 |
| 124 | 1508:2 | `\eqref{eq:ac-level-set}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 25，lem:no-early-boundary-exit | 428 / 430 | 否 |
| 125 | 1513:13 | `\eqref{eq:optimal-boundary-continuation}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 25，lem:no-early-boundary-exit | 1467 / 1471 | 否 |
| 126 | 1532:4 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1349 / 1350 | 否 |
| 127 | 1540:7 | `\ref{cor:verification-equality}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1377 / 1378 | 否 |
| 128 | 1540:46 | `\ref{lem:waiting-HJB}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1193 / 1194 | 否 |
| 129 | 1540:70 | `\ref{prop:all-HJB}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1267 / 1268 | 否 |
| 130 | 1541:6 | `\ref{lem:no-early-boundary-exit}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1453 / 1454 | 否 |
| 131 | 1541:52 | `\ref{lem:strict-crossing}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 923 / 924 | 否 |
| 132 | 1541:80 | `\ref{lem:chi-regions}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1002 / 1003 | 否 |
| 133 | 1542:7 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1111 / 1112 | 否 |
| 134 | 1542:41 | `\ref{lem:tracking-region}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1070 / 1071 | 否 |
| 135 | 1552:4 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1349 / 1350 | 否 |
| 136 | 1553:3 | `\ref{cor:verification-equality}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1377 / 1378 | 否 |
| 137 | 1561:3 | `\ref{lem:waiting-HJB}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1193 / 1194 | 否 |
| 138 | 1565:3 | `\ref{prop:all-HJB}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1267 / 1268 | 否 |
| 139 | 1573:3 | `\ref{lem:trajectory-verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1302 / 1303 | 否 |
| 140 | 1601:2 | `\eqref{eq:ac-level-set}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 428 / 430 | 否 |
| 141 | 1604:3 | `\ref{lem:no-early-boundary-exit}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1453 / 1454 | 否 |
| 142 | 1609:3 | `\ref{lem:strict-crossing}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 923 / 924 | 否 |
| 143 | 1612:2 | `\eqref{eq:strict-crossing-time}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 947 / 949 | 否 |
| 144 | 1614:5 | `\ref{lem:chi-regions}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1002 / 1003 | 否 |
| 145 | 1622:12 | `\ref{cor:Gamma-labels}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 898 / 899 | 否 |
| 146 | 1623:13 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1111 / 1112 | 否 |
| 147 | 1628:4 | `\ref{lem:tracking-region}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 26，thm:unique-q | 1070 / 1071 | 否 |
| 148 | 1642:4 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1349 / 1350 | 否 |
| 149 | 1642:29 | `\ref{thm:unique-q}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1530 / 1531 | 否 |
| 150 | 1658:18 | `\eqref{eq:direct-structure}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1146 / 1148 | 否 |
| 151 | 1659:3 | `\eqref{eq:capacity-structure}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 正文 | 1152 / 1154 | 否 |
| 152 | 1667:3 | `\ref{prop:candidate-attainment}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 27，cor:optimal-synthesis | 1111 / 1112 | 否 |
| 153 | 1668:3 | `\ref{thm:verification}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 27，cor:optimal-synthesis | 1349 / 1350 | 否 |
| 154 | 1669:3 | `\ref{thm:unique-q}` | 6 全局最优性与唯一性 > 6.3 常接触率下控制与轨道的唯一性 | 证明 27，cor:optimal-synthesis | 1530 / 1531 | 否 |
| 155 | 1708:26 | `\ref{thm:verification}` | 7 机制与量级 > 7.1 一维切换成本与全局结论的关系 | 正文 | 1349 / 1350 | 否 |
| 156 | 1722:3 | `\ref{thm:unique-q}` | 7 机制与量级 > 7.1 一维切换成本与全局结论的关系 | 证明 28，cor:one-dimensional-min | 1530 / 1531 | 否 |
| 157 | 1733:6 | `\eqref{eq:constants}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 253 / 256 | 否 |
| 158 | 1736:16 | `\eqref{eq:Phi-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 493 / 495 | 否 |
| 159 | 1746:2 | `\eqref{eq:cost-in-Phi}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1737 / 1739 | 否 |
| 160 | 1772:5 | `\ref{lem:unimodal}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 800 / 801 | 否 |
| 161 | 1772:25 | `\eqref{eq:theta-log-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 803 / 806 | 否 |
| 162 | 1774:3 | `\eqref{eq:theta-characteristic-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1767 / 1770 | 否 |
| 163 | 1774:52 | `\eqref{eq:JD-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1701 / 1703 | 否 |
| 164 | 1774:78 | `\eqref{eq:JB-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1701 / 1705 | 否 |
| 165 | 1793:65 | `\eqref{eq:H0-theta}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 774 / 777 | 否 |
| 166 | 1802:19 | `\ref{thm:verification}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1349 / 1350 | 否 |
| 167 | 1806:22 | `\eqref{eq:JB-derivative}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1701 / 1705 | 否 |
| 168 | 1810:3 | `\eqref{eq:JB-curvature-integral}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1775 / 1780 | 否 |
| 169 | 1812:6 | `\ref{cor:one-dimensional-min}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1710 / 1711 | 否 |
| 170 | 1812:52 | `\ref{thm:verification}` | 7 机制与量级 > 7.2 不变量坐标与切换机制 | 正文 | 1349 / 1350 | 否 |
| 171 | 1834:3 | `\eqref{eq:boundary-cost}` | 7 机制与量级 > 7.3 比较基准、小容量渐近与参数量级 > 7.3.1 纯容量填充与比较指标 | 正文 | 567 / 572 | 否 |
| 172 | 1834:28 | `\eqref{eq:q1-cost}` | 7 机制与量级 > 7.3 比较基准、小容量渐近与参数量级 > 7.3.1 纯容量填充与比较指标 | 正文 | 536 / 538 | 否 |
| 173 | 1882:2 | `\eqref{eq:small-K-switch}` | 7 机制与量级 > 7.3 比较基准、小容量渐近与参数量级 > 7.3.2 固定传播概率下的小容量命题 | 正文 | 1861 / 1863 | 否 |
| 174 | 1882:29 | `\eqref{eq:small-K-time}` | 7 机制与量级 > 7.3 比较基准、小容量渐近与参数量级 > 7.3.2 固定传播概率下的小容量命题 | 正文 | 1861 / 1867 | 否 |
| 175 | 1896:17 | `\eqref{eq:common-capacity-comparison}` | 7 机制与量级 > 7.3 比较基准、小容量渐近与参数量级 > 7.3.2 固定传播概率下的小容量命题 | 正文 | 1835 / 1841 | 否 |
| 176 | 2039:1 | `\NumTheoryRef{thm:verification}{验证定理}` | 8 数值结果 > 8.1 数值方法与实验设置 | 正文 | 1349 / 1350 | 否 |
| 177 | 2040:1 | `\NumTheoryRef{thm:unique-q}{唯一性定理}` | 8 数值结果 > 8.1 数值方法与实验设置 | 正文 | 1530 / 1531 | 否 |
| 178 | 2087:8 | `\eqref{eq:uncontrolled-future-peak}` | 8 数值结果 > 8.1 数值方法与实验设置 | 正文 | 277 / 283 | 否 |
| 179 | 2091:21 | `\ref{lem:safe-invariant}` | 8 数值结果 > 8.1 数值方法与实验设置 | 正文 | 504 / 505 | 否 |
| 180 | 2116:5 | `\NumTheoryRef{thm:verification}{验证定理}` | 8 数值结果 > 8.2 不同初值区域下的数值验证 > 8.2.1 代表初值与相平面分区 | 正文 | 1349 / 1350 | 否 |
| 181 | 2242:29 | `\eqref{eq:linear-cost}` | 9 讨论 > 9.1 同时控制接触率与跟踪比例时的限制 | 正文 | 228 / 230 | 否 |
| 182 | 2257:10 | `\ref{prop:main-structure}` | 9 讨论 > 9.2 模型假设与理论边界 | 正文 | 326 / 327 | 否 |
| 183 | 2278:32 | `\ref{thm:verification}` | 10 结论 | 正文 | 1349 / 1350 | 否 |
| 184 | 2281:3 | `\ref{thm:unique-q}` | 10 结论 | 正文 | 1530 / 1531 | 否 |
| 185 | 2311:6 | `\eqref{eq:endpoint-derivatives}` | A 完全跟踪成本导数的逐步计算 | 正文 | 747 / 750 | 否 |
| 186 | 2335:9 | `\eqref{eq:boundary-cost}` | B 容量边界成本积分的逐步计算 | 正文 | 567 / 572 | 否 |
| 187 | 2348:40 | `\ref{prop:reachable}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 703 / 704 | 否 |
| 188 | 2353:4 | `\ref{prop:reachable}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 703 / 704 | 否 |
| 189 | 2359:4 | `\ref{lem:unimodal}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 800 / 801 | 否 |
| 190 | 2389:5 | `\ref{lem:strict-crossing}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 923 / 924 | 否 |
| 191 | 2401:15 | `\ref{lem:chi-regions}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 1002 / 1003 | 否 |
| 192 | 2403:11 | `\eqref{eq:strict-crossing-time}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 947 / 949 | 否 |
| 193 | 2403:45 | `\ref{lem:chi-regions}` | C 完全跟踪分区可达性与不再返回等待区的证明 | 证明 29，lem:tracking-region | 1002 / 1003 | 否 |
| 194 | 2410:8 | `\ref{prop:regularity}` | D 梯度拼接与相对正则性的详细证明 | 正文 | 1219 / 1220 | 否 |
| 195 | 2415:3 | `\eqref{eq:waiting-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 1168 / 1171 | 否 |
| 196 | 2468:4 | `\ref{cor:Gamma-labels}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 898 / 899 | 否 |
| 197 | 2474:42 | `\eqref{eq:waiting-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 1168 / 1171 | 否 |
| 198 | 2474:73 | `\eqref{eq:capacity-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 1225 / 1227 | 否 |
| 199 | 2512:14 | `\eqref{eq:boundary-value}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 1105 / 1107 | 否 |
| 200 | 2512:42 | `\eqref{eq:boundary-cost}` | D 梯度拼接与相对正则性的详细证明 | 证明 30，prop:regularity | 567 / 572 | 否 |
| 201 | 2534:17 | `\ref{prop:small-capacity}` | E 小容量渐近的完整推导 | 证明 31，prop:small-capacity | 1855 / 1856 | 否 |
| 202 | 2567:18 | `\eqref{eq:small-K-switch}` | E 小容量渐近的完整推导 | 证明 31，prop:small-capacity | 1861 / 1863 | 否 |
| 203 | 2581:3 | `\eqref{eq:small-K-cost}` | E 小容量渐近的完整推导 | 证明 31，prop:small-capacity | 1861 / 1865 | 否 |
| 204 | 2600:5 | `\eqref{eq:small-K-time}` | E 小容量渐近的完整推导 | 证明 31，prop:small-capacity | 1861 / 1867 | 否 |
| 205 | 2610:53 | `\eqref{eq:small-K-relative}` | E 小容量渐近的完整推导 | 证明 31，prop:small-capacity | 1876 / 1880 | 否 |
| 206 | 2642:10 | `\eqref{eq:medical-total-incidence}` | F 感染阈值与医疗需求 | 正文 | 2630 / 2633 | 否 |
| 207 | 2662:7 | `\eqref{eq:medical-incidence-bound}` | F 感染阈值与医疗需求 | 正文 | 2638 / 2640 | 否 |
| 208 | 2683:3 | `\eqref{eq:medical-threshold}` | F 感染阈值与医疗需求 | 正文 | 2674 / 2678 | 否 |

## 解释限制

前向引用属于排版次序事实；是否构成循环依赖还需阅读对应证明。附录中的独立计算或详细证明在正文陈述之后出现，不能单凭其位置判为循环。`self_reference` 只表示证明中指向其所证明对象的引用，不能代替证明依赖判断。
