# S2.1 代码改名清单（作者已确认；保留改名前清点基准）

日期：2026-10-20。分支：`codex/numerical-reproducibility-revision`。

本清单的基准是完成 S1 的提交 `051099fba63cd6d326f2344d2bf4322c1f651282`，本地标签 `pre-code-rename` 指向该提交。作者给出的 `420bcc7` 是计划提交，其后已有 S1 的四个提交；不回退或重复 S1。

**作者已确认本清单，S2.2–S2.9 已完成，三项导出器回归通过。** 以下内容保留 S2.1 改名前的清点依据与行号，不作为当前执行状态。实际 35 次新求解、35/35 严格对比、两套判据计数与逐步提交见 `validation/numerical_scenarios/rerun_20261020/README.md`。所有行号均为上述标签上的源文件行号；路径相对本项目目录 `tracing_isolation_optimal_control_complete/`。

## 1. 统一映射与实施边界

| 旧名 | 新名 | 数学含义 |
|---|---|---|
| 参数 `par.p` 及其别名、参数键 `"p"` / `'p'` | `par.beta`、`"beta"` / `'beta'` | 单次接触传播概率 $\beta$ |
| `geom.r` 及几何别名 | `geom.p` | $p=h-\ell=(1-\beta)h$ |
| `geom.e` 及几何别名 | `geom.s_e` | 安全边界与 $g$ 的交点横坐标 $s_e$ |
| `geom.s_K` 及几何别名 | `geom.s_A` | 安全集边界在横轴的交点 $s_A$ |

- 只改标识符、相应字段和说明，不改运算、运算顺序、参数值、求解设置、初值或判据。
- 旧概率 `p` 先按语义迁移为 `beta`，旧几何量 `r` 再迁移为 `p`；不得连续全局替换，造成新旧 `p` 混淆。
- `N`、`solver_settings.N`、`capacity_excess`、证明外已明确含义的局部变量不在本次代码改名范围。
- 已有 raw MAT、solver JSON、assessment MAT、历史摘要、基线和报告均保留原处；`run_index.json` 后续只追加，不删除旧条目。
- 实际清点为 **19 个**含待改名位置的 MATLAB 文件（12 个生产/配置文件、7 个测试文件），而非计划注记的 14 个。另有本清单第 3 节的 3 个 Python/JSON 文件，以及第 4 节的旧格式读取适配位置。

## 2. MATLAB：字段、局部量和断言

以下路径均位于 `matlab/numerical_scenarios/`。

| 文件 | 行号 | 旧名 → 新名 | 含义或用途 |
|---|---|---|---|
| `analytic_reference.m` | 10, 12, 34 | `geom.r` → `geom.p` | 几何常数 $p$ |
| 同上 | 11, 12, 48, 55, 61 | `par.p` → `par.beta` | 传播概率及解析成本中的参数 |
| 同上 | 19, 21 | `geom.s_K` → `geom.s_A` | 安全集横轴交点 |
| `assess_numerical_case.m` | 9, 10, 17, 40, 50 | `par.p` → `par.beta` | 动力学、成本和独立重积分 |
| 同上 | 15 | 注释中的 `pc` → `beta c` | 感染峰值位置公式中的传播概率，公式不变 |
| `build_theory_geometry.m` | 3, 4 | `par.p` → `par.beta` | 阈值与参数可行性 |
| 同上 | 12 | 结构键 `'r','s_K','e'` → `'p','s_A','s_e'` | 生成最终几何字段 |
| 同上 | 3, 7, 12, 17, 30, 36 | 局部 `r` → `p` | 几何常数；保留原表达式 `h-ell` |
| 同上 | 10–12 | 局部 `sk` → `s_A` | 安全集横轴交点 |
| 同上 | 11, 12, 17, 18, 20, 30–33, 37 | 局部 `e` → `s_e` | 交点及嵌套函数闭包使用的端点 |
| `classify_initial_state.m` | 22 | `geom.e` → `geom.s_e` | 初始区域分类 |
| `compare_numerical_events.m` | 193 | `par.p` → `par.beta` | 容量段解析控制 |
| `make_numerical_figures.m` | 12, 20 | `g.e` → `g.s_e` | 几何别名及相图采样 |
| 同上 | 27 | `g.s_K` → `g.s_A` | 相图安全边界采样 |
| `numerical_cases_config.m` | 16, 17 | `cfg.parameters.p` → `cfg.parameters.beta` | 共享参数断言 |
| 同上 | 21 | 错误说明 `0<p<1` → `0<beta<1` | 与参数名一致；约束不变 |
| `prepare_openocl_case.m` | 62, 63, 66 | `par.p` → `par.beta` | OCP 动力学及运行成本 |
| `revision_initial_guess.m` | 33, 34 | `par.p` → `par.beta` | 初猜状态的前向积分 |
| `revision_validation_config.m` | 7 | `struct('p',...)` → `struct('beta',...)` | 固定协议的参数结构断言 |
| `solve_openocl_case.m` | 42 | `par.p` → `par.beta` | 单元控制成本 |
| `tail_diagnostic.m` | 18, 19 | `par.p` → `par.beta`；局部 `p` → `beta` | 尾段动力学，不改乘法顺序 |
| `verify_numerical_assessment.m` | 107, 118 | `p.p` → `p.beta` | 参数结构别名中的概率字段 |
| `verify_numerical_cache.m` | 13 | 参数结构键 `'p'` → `'beta'` | 测试请求参数 |
| `verify_numerical_events.m` | 6 | 参数结构键 `'p'` → `'beta'` | 事件测试参数 |
| 同上 | 142, 149, 174 | `par.p` → `par.beta` | 测试辅助动力学及容量控制 |
| `verify_numerical_reference.m` | 16 | 参数字段列表 `'p'` → `'beta'` | 与新解析检查点对齐 |
| 同上 | 21 | 几何字段列表 `'r','s_K','e'` → `'p','s_A','s_e'` | 与新检查点结构对齐 |
| 同上 | 25, 95, 96 | `g.r` → `g.p` | 几何别名 |
| 同上 | 61, 112 | `p.p` → `p.beta` | 参数结构别名 |
| 同上 | 92, 98 | `g.e` → `g.s_e` | 端点测试 |
| `verify_revision_scheduler.m` | 255, 256 | `par.p` → `par.beta` | 调度 mock 的动力学；不改变调用次数逻辑 |
| `verify_revision_validation_unit.m` | 30 | `g.e` → `g.s_e` | 几何单元核对 |
| 同上 | 65, 67 | `other.p` → `other.beta` | 非默认参数测试 |
| 同上 | 66, 67 | `gp.r` → `gp.p` | 非默认参数的几何别名 |
| 同上 | 76, 77, 107, 108, 110 | `p.p` → `p.beta` | 测试辅助动力学、成本和控制 |
| `verify_solver_diagnostics.m` | 34 | 参数结构键 `'p'` → `'beta'` | solver 元数据测试请求 |

## 3. Python、共享 JSON 和检查点

以下路径均位于 `validation/numerical_scenarios/`。

| 文件 | 行号 | 旧名 → 新名 | 含义或用途 |
|---|---|---|---|
| `scenario_inputs.json` | 3 | 参数键 `"p"` → `"beta"` | 共享传播概率，数值 0.5 不变 |
| `generate_analytic_checkpoints.py` | 42, 46, 47, 56, 123 | `self.p` → `self.beta` | 传播概率 |
| 同上 | 43 | 输入键 `"p"` → `"beta"` | 参数读取 |
| 同上 | 53 | 提示 `0 < p < 1` → `0 < beta < 1` | 与新参数名一致 |
| 同上 | 58, 80, 86 | `self.r` → `self.p` | 几何常数 $p$ |
| 同上 | 63, 64, 113, 116 | `self.s_K` → `self.s_A` | 安全集横轴交点 |
| 同上 | 64, 65, 68, 90, 92, 96 | `self.e` → `self.s_e` | 几何端点 |
| 同上 | 93 | 提示 `h < z < e` → `h < z < s_e` | 端点命名 |
| 同上 | 155, 157 | `geo.r` → `geo.p` | 几何常数 |
| 同上 | 156, 157, 184 | `geo.p` → `geo.beta` | 传播概率 |
| 同上 | 160 | `geo.e` → `geo.s_e` | 几何端点 |
| 同上 | 207 | 输出 geometry 键 `"r","s_K","e"` → `"p","s_A","s_e"` | 检查点字段 |
| `test_analytic_checkpoints.py` | 30 | 错误匹配 `0 < p < 1` → `0 < beta < 1` | 与生成器错误原文一致 |
| 同上 | 35, 43 | 参数键 `"p"` → `"beta"` | 参数边界回归 |

`analytic_checkpoints.json` 已在 S2.3 用改名后的生成器重新生成并核对；S2.1 清点当时未生成、未改写。后续验收须区分：

- 数学数值逆映射后逐项比较，相对差不超过 $10^{-12}$；现有 `--check` 的 `CHECK_TOL=5e-12` 是绝对误差阈值，不能单独代替这项要求。
- `input_sha256` 因共享输入键变化而改变，属于应如实更新的来源元数据；不能把它当作数学数值变化，也不能继续填旧哈希。
- 当前 Python 测试含 9 个 `test_*`。本轮未运行 S2.3 测试，不能填为已通过。

## 4. 旧格式适配与来源保护

以下是 **S2.1 清点时列出的 S2.2 适配位置，现已完成**。先校验旧 raw、solver sidecar、兼容副本和指纹，再为计算创建规范化参数副本：旧概率字段 `p` 显式映射为 `beta`。不得就地改写 `run.parameters`、`run.solve_fingerprint_payload` 或磁盘记录。

适配仅处理 `parameters` 结构中的概率字段；若 `p`、`beta` 同时存在且数值不一致，或二者都不存在，应报错。其他字段和值不得被静默丢弃。先按原结构比较 raw / fingerprint payload，再按规范化副本比较当前参数。

| 文件（`matlab/numerical_scenarios/`） | 行号 | 拟处理内容 | 保护条件 |
|---|---|---|---|
| `numerical_assessment_view.m` | 3–6 | 旧 `run.parameters.p` → 计算副本的 `beta` | 几何、参考与评估共用副本；raw 保留 |
| `refresh_numerical_assessments.m` | 9–12 | 读入旧记录后进入统一适配入口 | 新评估追加，原评估不覆盖 |
| `make_numerical_figures.m` | 78–83 | 历史参数重建几何、参考解时适配 | 先完成选中记录的来源检查 |
| `export_numerical_latex.m` | 618–619 | 容量放松比较中的参数副本适配 | 只修改计算副本 |
| `load_selected_numerical_runs.m` | 15–28 | 保持原始字段及文件哈希校验；在校验后的计算路径适配 | 不在原始校验前改字段 |
| `numerical_run_consistency.m` | 15–24, 39 | raw 与 fingerprint payload 仍按原结构比较；与当前参数比较时规范化副本 | 不将来源一致性检查降为仅数值比较 |
| `numerical_main_verification.m` | 11 | 新旧参数结构的语义比较 | 原始数据与指纹不动 |
| `numerical_additional_verification.m` | 21 | 同上 | 同上 |
| `revision_group_summary.m` | 223 | 同上 | 同上 |
| `revision_threshold_saved.m` | 24 | 同上 | 同上 |
| `compare_neutral_initialization.m` | 21 | 同上 | 同上 |

若新增适配辅助函数，应在 `numerical_code_hash.m:5–25` 中将其登记到实际调用它的 solve / assessment / figure / export 依赖；不得漏记。`assess_saved_numerical_run.m:11–12` 仍须以原始 run 哈希构造评估指纹。计划要求的 `compare_rerun_results.m` 不进入任何指纹清单。

`revision_validation_config.m:58–60` 对完整参数结构计算配置哈希，键名变化会改变 `configuration_fingerprint`。因此 S2.5 必须按稳定的 `configuration_id` 配对，不能按新旧指纹配对。

已只读核对标签下的 `initialization_summary.json`（10 行）、`grid_summary.json`（15 行）和 `horizon_summary.json`（15 行）：去重后完整覆盖 `C01`–`C35`，每个配置对应一个旧 run_id。映射已保存在 `validation/code_rename_s21_20261020/audit_report.json`。`main_summary.json` 为 5 主例的重评摘要，没有 `configuration_id`，不可单独用于全矩阵配对。

## 5. 不改的同名项与历史边界

- `make_numerical_figures.m:41` 的 `'p'` 是五角星绘图标记，不改为 `'beta'`。
- 参数结构变量本身的名字 `p` 可以保留，例如只把 `p.p` 改为 `p.beta`。`numerical_run_consistency.m:8` 的 `p` 是 provenance，不是传播概率。
- 导出器中的 `e` 常表示事件结构，`r` 常表示 run，不属于几何端点或常数。
- `geom.ell`、`geom.h`、`geom.Phi_A`、`geom.s_B` 等已一致的字段保留。论文内容与理论不在 S2.1 修改范围。
- 第 6–11 步和容差重评的 18 个历史入口，本轮仅补一行“只针对标签 `pre-code-rename` 运行；历史基线与输出不得刷新。”，未改运行逻辑。完整文件清单与头注释前后哈希见 `audit_report.json`。
- 这些历史脚本不在当前 `numerical_code_hash.m` 四类依赖中，补头注释不改变求解/评估指纹。旧 checkout manifest 中的脚本哈希仍指旧快照，不刷新旧 manifest 或报告。
- `summarize_stage89.py` 会把自身哈希写入输出来源；本轮不执行它。`grid_explanation_20261009/`、旧 exporter/config 快照等证据目录中的脚本均不改。
- `pre-code-rename` 规定旧符号口径的运行边界，不保证更早冻结的正文/快照断言全部通过。不得为使历史 verifier 通过而改写旧基线。

## 6. S2.1 提交后的确认记录

作者已确认实际 19 个 MATLAB 文件、旧格式计算副本适配、`configuration_id` 配对和检查点元数据处理。S2.4 已实际新求解 35 次、缓存 0 次；S2.5 严格比较 35/35 通过，成本与数组差均为 0；S2.6 原判据双通过 28/35、修订判据双通过 30/35。S2.7 的三项导出器回归共 16 项检查已通过，S2.8 文档及 S2.9 汇总已完成；最终提交以本批总报告所在 Git 历史为准。

S2.1 当时优化器调用 0 次、科学求解 0 次；未将计划的 35 次重跑或历史通过数记为当时结果。批次命令、编译结果、文件保护与验收差异见 `validation/code_rename_s21_20261020/README.md`。
