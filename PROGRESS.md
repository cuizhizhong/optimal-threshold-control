# 论文整合进度记录（PROGRESS）

> 工作日志。主稿：`paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex`。
> 目标：把分散的理论与数值实验整合为一篇「情景一阈值控制」论文。

## 状态（截至 2026-07-21）

**Step 1–5 全部完成。** 主稿编译完全干净（`xelatex → biber → xelatex → xelatex` 全 exit 0；
0 undefined refs / 0 undefined citations / 0 errors / 0 overfull·underfull \hbox；30 页；9 章；3 条文献）。
**改动尚未提交**（按要求先不提交；工作树另含本会话开始前已有的未提交改动）。

## 结果定位（头条论点）

不是"情景一阈值控制一定优于 TDINN"，而是 **有条件占优**：在指标集 {峰值, 二次成本 J, 控制时长 Δt} 上，
情景一相对 TDINN **不劣，当且仅当 θ=η/N 足够大**。两条政策杠杆使 θ 变大——**提高 η（医疗容量）**
或 **降低有效人口 N（分区/封控单元）**。诚实边界：一旦纳入总累计感染，占优区域急剧收缩
（累计 ∝ N·h(θ)，调参无法消除）。

## 已完成的修改

### Step 1 — 骨架重构
主稿重排为 9 章：`1 引言 / 2 模型与医疗容量约束 / 3 常规阶段首次积分与触发条件 /
4 情景一：精确压平曲线的闭式解 / 5 成本与参数敏感性 / 6 数值验证(N=763) /
7 西安真实疫情应用 / 8 尺度不变性与有效人口占优 / 9 讨论与局限`。
加了摘要/引言/讨论/参考文献的占位；删除情景二、情景三空标题与两处"预留章节"；原 §3 拆为 §4/§5/§6。

### Step 2 — 文件夹整理
- 新建 `refs/`：`He_Tang2023PCB.{pdf,txt,raw.txt}`、`Timing…surge.pdf`、两个 SIQR pptx。
- 新建 `archive_unused/`：`fit_method_comparison/`、`tdinn_q_only_comparison/`、`low_eta_analysis/`（`git mv`）。
- 删 `看.md` 与 9 个散乱 `xelatex*.fls`。
- `.gitignore` 增 LaTeX 构建产物与 `__pycache__/`；`git rm --cached` 取消跟踪 51 个构建产物 + 27 个 `.pyc`（文件仍在磁盘）。
- 更新 3 个 `AGENTS.md` 指向 `low_eta_analysis/` 的指针为 `archive_unused/…`，并在 `xian_control_comparison/AGENTS.md` 顶部加"目录变更"说明。

### Step 3 — §7 西安真实疫情应用
从 `xian_control_comparison.tex` 搬入 6 小节（真实数据与 TDINN 控制函数 / 模型与初值拟合 /
情景一阈值控制的西安实例 / 比较指标与三策略数值结果 / 阈值 η 敏感性 / (c0,η) 二维图谱），
与西安 η 敏感性去重。biblatex 接线：新建 `references.bib`、加 `\addbibresource`+`\printbibliography`、
补章节 `\label`。建立 TDINN 基准（峰值 151.90、J 49.35、总累计 2096.76）。

### Step 4 — §8 尺度不变性与有效人口占优（头条）
章首前景化"有条件占优 + 两杠杆"；新增 §8.2「有效人口标度与结构不变量的数值验证」（`\label{sec:scaling}`，
含 θ 折叠、降 N 杠杆、β/q0 拐点不变量）；局限段提升为 `\subsection{局限与口径}`；
修复 3 个悬空 label（`sec:scaling`、`thm:s1:Itcum`、`eq:s1:Send`）。

### Step 5 — 一致性通读
表格 `I_{t_{cum}}`→`I_{t_{\rm cum}}`（正体）；§7 模型名统一为"包含追踪的 SIR"；
§8.2 补 t1 口径澄清（固定无量纲初值 t1≈11.13，逐 N 重拟合 t1→16.90，Δt 两口径都≈85.07）；
无违禁术语，策略名一致，跨章数值核对通过。

## 新建/复制的文件
- `paper_elegantpaper_relayout/references.bib`（新建）
- `figures/`（12 个新 `.pdf`）：`xian_observed_daily_cases`、`xian_control_comparison_panels`、
  `xian_control_cumulative`、`xian_effective_reproduction_number`、`xian_eta_sensitivity`、
  `xian_heatmap_{control_duration,clear_time,cum_total,J}`、`neff_{scaling_collapse,time_metrics,inflection_beta}`
- `table/`（4 个）：`xian_{initial_fit,i0_sensitivity,control_comparison_results,eta_sensitivity}_table.tex`
- 目录：`refs/`、`archive_unused/`

## 当前顶层结构
```
paper_elegantpaper_relayout/   主稿（唯一正文落点）
figures/  table/               主稿用图/表
xian_control_comparison/       合并来源（仅剩 effective_population_sensitivity/、threshold_landscape_analysis/）
scenario1_threshold_landscape/ N=763 验证图来源
真实数据/                       6 城原始数据（Guangzhou/Hainan/Liaoning/Xian/Xinjiang/Yangzhou）
refs/                          参考资料
archive_unused/                归档失效实验
code/  tmp/
```

## 尚待（Step 6）
- 撰写 **摘要、引言 + 文献综述、讨论/局限、补全参考文献**（`refs/` 已备 He_Tang 与 Timing…surge 两篇关键文献）。
- 小记号统一：§8 的 `I_{t\rm cum}^{\rm T}` 与正文 `I_{t_{\rm cum}}` 对齐。
- 多城多病验证（`真实数据/` 已有 6 城）作为讨论中的未来工作，本轮不实现。
- 提交（可一次，或按 骨架/整理/合并 分几次）。
