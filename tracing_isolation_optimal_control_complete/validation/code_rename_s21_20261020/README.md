# 第二批 S2：S2.1 清点与确认门槛

日期：2026-10-20。分支：`codex/numerical-reproducibility-revision`。

本轮完成 **S2.1**，尚未执行 S2.2–S2.9。执行入口第二批明确规定：“先打标签 `pre-code-rename` 并提交改名清单（S2.1），等作者确认清单后再做 S2.2–S2.9。”因此本轮提交后暂停等待清单确认，没有提前改名或重跑。

## 1. 提交与文件清单

- S1 完成提交：`051099fba63cd6d326f2344d2bf4322c1f651282`。用户提供的 `420bcc7` 为计划提交，其后已完成 S1，不重复执行。
- 本地标签：`pre-code-rename`，指向上述 S1 提交。
- S2.1 提交：本报告所在提交；提交信息为“docs: 清点代码符号迁移并核对编译（S2.1，待作者确认）”。不推送。
- 新增 `ai/claude_revision_plan/code_rename_inventory.md`：文件、基准行号、旧名、新名、含义、适配边界及后续验收注意事项。
- 第 6–11 步和容差重评的 18 个历史入口：各加一行旧符号运行边界注释，不改逻辑；文件及前后 SHA-256 见 `audit_report.json`。
- 本目录新增清点/编译脚本、保护快照、报告和实际命令输出。完整提交路径列表见 `commit_files.json`。

现有论文源文件、正式 PDF、MATLAB 生产/测试代码、共享输入、解析检查点、原始数据、已有评估、历史基线和历史报告均未改写。历史入口的新增头注释不属于求解或评估指纹依赖。

## 2. 实际执行的命令与结果

以下命令均从仓库根目录执行。完整编译参数和工作目录保存在 `build_report.json`。

```powershell
git tag pre-code-rename 051099fba63cd6d326f2344d2bf4322c1f651282
git rev-parse pre-code-rename
python -I tracing_isolation_optimal_control_complete/validation/code_rename_s21_20261020/build_s21.py
python -I tracing_isolation_optimal_control_complete/validation/code_rename_s21_20261020/audit_s21.py --annotate-history
python -X utf8 -I tracing_isolation_optimal_control_complete/validation/code_rename_s21_20261020/audit_s21.py
git -c core.safecrlf=false diff --check
git -c core.safecrlf=false diff --cached --check -- . ':(glob,exclude)**/*.log'
```

| 核对 | 实际结果 |
|---|---|
| 标签目标 | `051099fba63cd6d326f2344d2bf4322c1f651282` |
| 主文最终构建 | XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，4/4 退出 0，37 页 |
| TheoryOnly 最终构建 | 同一四阶段构建，4/4 退出 0，29 页 |
| 两稿最终日志 | 无错误、未定义引用、缺字或 Overfull / Underfull |
| 两稿 PDF 文本 | `pdftotext -layout` 提取文字分别与现有 PDF 完全相同；4/4 提取命令退出 0 |
| 现有正式 PDF | 未替换，SHA-256 不变 |
| Git 内容与保护快照 | 322 个受保护路径内容与标签一致，当前 SHA-256 与本步快照一致 |
| 受保护数据范围 | 254 个已跟踪数据文件，含 35 raw MAT、35 solver JSON、70 assessment MAT |
| 旧配置配对 | 三组摘要去重后 `C01`–`C35` 完整覆盖，35 个 run_id 无冲突 |
| 历史入口 | 18/18 只有一行注释差异；Python AST 不变；未运行历史入口 |
| 源码、文档差异空白检查 | 工作区检查退出 0；暂存检查排除原始捕获的 `.log` 后退出 0 |

本轮没有运行 MATLAB、OpenOCL、IPOPT、`run_revision_validation`、S2.3 检查点测试或三项导出器回归。新增单元测试 **0 项**；优化器调用 **0 次**、科学求解 **0 次**、调度缓存命中 **0 次**。这些调用数来自本轮实际执行范围，未冒充 MATLAB 调度器计数。S2.1 不要求重跑改名后测试。

二次运行 `audit_s21.py` 校验已有 `protected_before.json`，不重建快照。Git 存储与工作区的文本换行差异只在与标签的内容比较时处理；原始 MAT、PDF 等二进制逐字节比较，工作区二次快照全部按原始 SHA-256 比较。该 322 项检查覆盖数据、MATLAB、论文和输入/检查点，不是全仓库哈希审计；旧验证证据与图目录未修改另由实际 Git 差异范围确认。

## 3. 与计划验收参照的差异

- 计划注记“14 个文件”与当前清点不符：实际为 19 个 MATLAB 文件，含 12 个生产/配置文件和 7 个测试文件。清单补入字段别名、结构键、参数断言、局部几何量和测试，没有改变数学或科学实验范围。
- 现有 35 条旧记录、70 个旧评估保留原处，`run_index.json` 仍为 35 条。本轮没有新增原始记录或评估。
- 计划中的 35 次新求解、成本/数组/事件逐条对比、原判据双通过 28/35 与修订判据双通过 30/35，均留待作者确认后的 S2.2–S2.9。本轮不把历史计数或预期参照写成新结果。
- 现有生成器 `--check` 采用绝对误差阈值，后续还须独立核对计划要求的新旧检查点相对差不超过 `1e-12`；输入键改名引起的来源哈希变化须如实登记。
- 当前理论内容未变，计划只强制主文编译；本轮同时实际编译 TheoryOnly，但不声称重新逐页目视检查两份 PDF。

## 4. 停止条件、操作问题与作者决定

没有触发科学停止条件：尚未进入预检、求解、对比或计数验收，没有放宽任何通过标准。

编译辅助脚本初版只接受日志中的“页数后跟逗号”，而本机 XeLaTeX 输出为 `(37 pages).`；四个主文编译命令已成功，随后页数解析断言失败，未发生 TeX 编译失败。初次四条日志和 `build_attempt1_report.json` 保留。修正解析后，用独立 `final/` 输出目录完整重编双稿，最终通过；合计实际执行 12 条 TeX/BibTeX 命令，均退出 0。

清点辅助脚本在开发中修正过括号语法、MATLAB 脚本/函数头识别及 Git LF/工作区 CRLF 的比较方式。最终检查通过；修正仅涉及本轮辅助脚本，没有运行科学代码或修改保护对象。

完整暂存区空白检查另报告了 9 行 TeX 原始控制台输出的行末空格，均来自同一包加载消息。日志保留原样；源码和文档的暂存区检查排除 `.log` 后通过。这些空格不是 TeX 编译错误或溢出。

**需要作者确认：** 审阅 `ai/claude_revision_plan/code_rename_inventory.md`，确认实际 19 个 MATLAB 文件及 Python/JSON 映射、旧参数计算副本适配、稳定 `configuration_id` 配对和检查点来源元数据处理。依据执行入口的明确门槛，确认前不继续 S2.2–S2.9。

原有未跟踪临时文件、归档和 LaTeX 中间文件保留原处，未纳入本提交。本轮构建中间文件及提取文本位于 `tmp/code_rename_s21_20261020/`，正式证据保存在本目录。
