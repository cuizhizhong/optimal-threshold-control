# AGENTS.md - 单阈值控制响应图谱实验说明

## 用途

本目录保存西安 SIQR 模型下 `情景一阈值控制` 的单阈值响应图谱实验。当前阶段只做理论量、数值轨迹、成本指标和可行性状态的整理，不写论文最终结论，也不把阶段性结果解释为某一策略已经优于另一策略。

处理本目录内容时，应同时遵守项目根目录 `AGENTS.md` 和 `xian_control_comparison/AGENTS.md`。若涉及本目录已经生成的图谱、表格和报告，以本文件的实验口径为准。

## 控制律与基本口径

`情景一阈值控制` 保持为理论推导得到的时间开环控制：

```tex
q_c(t)=1-\frac{\gamma N}{\beta c_0 S_{\rm th}(t)}.
```

其中 `S_th(t)` 是由阈值启动点和平台期解析轨迹得到的时间函数。不要把该控制律改写成依赖数值积分实时 `S(t)` 的状态反馈。

本目录统一比较三类策略：

- `TDINN控制`：来自 He--Tang--Xiao (2023) 的固定文献控制函数；
- `情景一阈值控制`：固定 `c(t)=c0`，通过时间开环 `q_c(t)` 维持 `I(t)=eta`；
- `常规控制`：反事实基准，满足 `c(t)=c0` 且 `q(t)=q0`。

在变 `c0` 图中，`TDINN控制` 只作为固定文献参照；`情景一阈值控制` 和 `常规控制` 均使用当前文件名中的 `c0` 重新计算。不要再写成 TDINN 控制和常规控制同时固定。

## 核心文件

- `threshold_landscape_analysis.py`：生成本目录全部扫描、代表面板、热图、成本表和简短 notes。
- `notes.md`：记录状态字段、控制时长字段和变 `c0` 图的基本口径。
- `elegantnote_report/xian_threshold_landscape_note.tex`：当前阶段的 ElegantNote 研究笔记源码。
- `elegantnote_report/xian_threshold_landscape_note.pdf`：由上述源码编译得到的 PDF 报告。

运行入口为：

```powershell
python -B xian_control_comparison\threshold_landscape_analysis\threshold_landscape_analysis.py
```

该命令会刷新本目录下的图、CSV 和 LaTeX 表格。除非用户明确要求，不要随意重跑并覆盖已有输出。

## 输出目录与实验内容

### `eta_landscape/`

该目录保存基准 `c0=12.8872` 下的单阈值扫描。扫描区间为：

```tex
\eta\in[100,30000],
```

使用对数取点，并强制包含代表阈值：

```tex
100,\ 520,\ 1300,\ 3200,\ 6500,\ 15000,\ 26326.
```

主要文件：

- `eta_landscape_summary.csv`：每个 `eta` 的理论量、数值指标、成本和状态；
- `eta_landscape_sensitivity.png/pdf`：阈值敏感性图；
- `eta_landscape_summary_table.tex`：代表阈值 LaTeX 表。

CSV 中控制时长字段统一为 `control_duration`；图表和 LaTeX 表头中记为 `\Delta t=t_2-t_1`。

CSV 中清零终止时刻字段为 `clear_time`，但图表和 LaTeX 表头中记为 `t_{\rm end}`，不要使用旧的清零时间记号。该时间由主论文中的相平面公式计算：先由 `I(t_{\rm end})=1` 求 `S_{\rm end}`，再从 `S_c` 积分到 `S_{\rm end}`。隔离率强度指标使用 `q_{\max}`；当前平台段中 `q_c(t)` 随时间下降，因此最大值在启动端点取得，但图表中不要把最大值指标直接写成控制函数取值。

### `representative_eta_panels/`

该目录保存基准 `c0=12.8872` 下代表阈值的图 2 风格面板。代表阈值为：

```tex
100,\ 520,\ 1300,\ 3200,\ 6500,\ 15000,\ 26326.
```

每个阈值均生成：

- `panels_eta*.png/pdf`：图 2 风格面板；
- `timeseries_eta*.csv`：三类策略的时间序列。

面板包含 `I(t)`、`I_new(t)`、`I_{q_new}(t)`、`c(t)` 和 `q(t)`。主图仍显示三类策略。对于 `eta>1300` 的 inset 放大图，只显示 `TDINN控制` 的蓝色曲线和真实日报点，不显示红色阈值控制曲线，也不显示 `eta` 水平线，以免高阈值平台压平 TDINN 曲线；`eta<=1300` 的 inset 保持原比较逻辑。

### `cost_weight_analysis/`

该目录保存固定权重下的二次加权总成本分析。主成本记为

```tex
J
=
\int
\left[
w_c\left(\frac{(c_0-c(t))_+}{c_0}\right)^2
+
w_q\left(\frac{(q(t)-q_0)_+}{1-q_0}\right)^2
\right]dt,
\qquad
w_c=1,\quad w_q=2.
```

主要文件：

- `cost_summary_wq2.csv`：包含 `strategy`, `eta`, `c0`, `w_c`, `w_q`, `J`, `J_c`, `J_q` 等字段；
- `cost_summary_wq2.png/pdf`：固定 `w_q=2` 下总成本 `J` 随阈值变化的图。

其中 `J_c` 和 `J_q` 是单独归一化分项成本，只用于观察控制投入来源，不相加为综合成本。旧的 `cost_weight_summary.csv` 和 `cost_weight_sensitivity.*` 若仍留在目录中，只作为早期权重敏感性探索输出，不作为当前主分析口径。

### `eta_c0_heatmap/`

该目录保存 `eta` 与 `c0` 的二维敏感性图谱。主扫描范围为：

```tex
c_0\in[6,13],\qquad \eta\in[100,30000].
```

主要文件：

- `eta_c0_heatmap_summary.csv`：二维扫描长表；
- `heatmap_control_duration.png/pdf`；
- `heatmap_clear_time.png/pdf`；
- `heatmap_cum_total_infections.png/pdf`；
- `heatmap_J.png/pdf`；
- `heatmap_status.png/pdf`。

连续指标还额外生成参考样式的 `_contour` 版本：

- `heatmap_control_duration_contour.png/pdf`；
- `heatmap_clear_time_contour.png/pdf`；
- `heatmap_cum_total_infections_contour.png/pdf`；
- `heatmap_J_contour.png/pdf`。

这些图保留彩色热图底图，并叠加红色虚线等高线和曲线标签。等高线绘制时横向坐标使用 `log10(eta)`，但横轴刻度仍标回真实 `eta`；这只是绘图坐标变换，不改变 CSV 中的真实阈值和指标值。`status` 是分类状态变量，当前又全部为 `ok`，因此不生成 `heatmap_status_contour.*`。

当前 `eta_c0_heatmap_summary.csv` 中 1680 个组合均为 `status=ok`。尽管如此，`status` 字段仍保留为可行性诊断字段，后续扩大参数范围时可能出现 `q_below_q0`、`q_out_of_bounds`、`threshold_not_reached` 或 `not_cleared`。

当前二维扫描中，固定 `eta` 改变 `c0` 的数值影响应分指标理解。对固定 `eta`，当 `c0` 从 6 增至 13 时，`control_duration` 一般缩短约 `17%-18%`。低阈值下这个绝对变化仍很大，例如 `eta=100` 时，`control_duration` 从约 `27474.82` 降至 `22429.22`，`t_{\rm end}` 从约 `29287.83` 降至 `23648.88`；但由于平台期仍是万天量级，从热图尺度看，`eta` 对控制持续时间的主导作用更强。高阈值下平台期较短，`c0` 对清零终止时刻的相对影响更明显；例如 `eta=26326` 时，`t_{\rm end}` 从约 `379.97` 降至 `256.95`，约下降 `32.38%`。

固定 `eta` 下，增大 `c0` 通常会增加累计感染和隔离强度。当前网格中，`eta=100` 时 `cum_total_infections` 从约 `1,730,432` 增至 `2,110,734`；`eta=26326` 时从约 `2,129,123` 增至 `2,378,174`。相应地，`q_{\max}` 和 `q_mean_control` 也随 `c0` 升高而增大；以 `eta=100` 为例，`q_{\max}` 约从 `0.671` 增至 `0.848`，`q_mean_control` 约从 `0.503` 增至 `0.618`。总成本 `J` 通常也升高，因为在较大接触率下维持同一阈值平台需要更强隔离率。

按当前固定权重 `w_c=1,w_q=2` 读取代表组合，`eta=100,c0=6` 时 `J≈5116.71`，`eta=100,c0=13` 时 `J≈10911.90`；`eta=26326,c0=6` 时 `J≈18.35`，`eta=26326,c0=13` 时 `J≈40.71`。这些数值只用于记录当前二维网格下的成本变化，不写成最终策略优劣结论。

需要注意，当前网格下低 `c0` 附近的 `control_duration` 存在轻微非单调性。例如 `eta=100` 时，最长平台期约出现在 `c0=6.5`，不是严格出现在 `c0=6`。这一点目前只作为数值观察记录，不写成解析单调性结论。

### `representative_c0_panels/`

该目录保存代表 `eta` 和代表 `c0` 的图 2 风格面板。参数组合为：

```tex
\eta\in\{100,1300,26326\},\qquad
c_0\in\{6,9,12.8872\}.
```

每个组合均生成：

- `panels_eta*_c0_*.png/pdf`；
- `timeseries_eta*_c0_*.csv`。

其中 `TDINN控制` 固定为文献参照；`情景一阈值控制` 和 `常规控制` 均随当前 `c0` 重新计算。此前图片顶部的小字说明已经去掉。

额外生成的 `panels_eta100_c0_6p0_linear.png/pdf` 是只针对 `eta=100, c0=6` 的线性纵轴试看图。它不覆盖默认对数纵轴图，用于观察对数轴下不可见的 `I(t)<1` 早期阶段；同时也会使常规控制大峰值压缩平台附近细节。

### `high_c0_stress_test_panels/`

该目录保存高接触率压力测试，不属于主分析的 `c0 in [6,13]` 图谱。参数为：

```tex
c_0\in\{14,18,20\},\qquad
\eta\in\{100,1300,26326\}.
```

主要文件：

- `high_c0_stress_test_summary.csv`；
- `stress_panels_eta*_c0_*.png/pdf`；
- `stress_timeseries_eta*_c0_*.csv`。

这些图沿用变 `c0` 口径：`TDINN控制` 固定为文献参照，`情景一阈值控制` 和 `常规控制` 均使用当前 `c0`。

## 已观察到的主要数值现象

在基准 `c0=12.8872` 下，当前扫描数值显示：降低 `eta` 会使控制启动时间 `t1` 提前，但会明显拉长平台控制时长 `control_duration` 和清零终止时刻 `t_{\rm end}`。

代表结果包括：

- `eta=100`：`t1≈11.38`，`control_duration≈22523.29`，`t_{\rm end}≈23748.32`；
- `eta=520`：`t1≈13.01`，`control_duration≈4331.01`，`t_{\rm end}≈5027.38`；
- `eta=1300`：`t1≈13.91`，`control_duration≈1732.12`，`t_{\rm end}≈2233.26`；
- `eta=26326`：`t1≈16.90`，`control_duration≈85.07`，`t_{\rm end}≈258.11`。

因此，低阈值并不只是“更早控制”。在该模型和参数下，它同时对应长期平台维持。这个现象应作为低阈值长期控制或常态化管控的数学情形保留，后续需要结合控制持续时间、累计感染和成本函数再解释。

高 `c0` 压力测试中，`c0=14,18,20` 均已生成 `eta={100,1300,26326}` 的代表结果。当前这些结果用于观察高接触水平下单独调节 `q(t)` 的响应边界，不应直接写成新的主基准。

## 状态字段

本目录 CSV 中的 `status` 字段用于区分理论控制律的可行性：

- `ok`：理论隔离率在可行范围内，数值轨迹使用原始 `q_c(t)`；
- `q_below_q0`：理论所需隔离率低于常规隔离率，但仍在 `[0,1]` 内；
- `q_out_of_bounds`：理论隔离率超出 `[0,1]`，ODE 轨迹使用截断后的隔离率；
- `threshold_not_reached`：常规控制轨道未达到给定阈值；
- `not_cleared`：在设定时间上限内未达到 `I(t)<=1`。

`q_out_of_bounds` 不是让扫描停止的错误，而是可行性诊断。理论量仍可保存，但截断后的 ODE 轨迹不再严格等同于原始理论开环控制。正常图谱解释应优先使用 `status=ok` 的结果。

## 后续协作规则

- 不要用本目录探索性输出覆盖 `xian_control_comparison/` 主基准输出。
- 不要修改 `archive_unused/low_eta_analysis/` 历史结果，除非用户明确要求。
- 继续保持 `TDINN控制`、`情景一阈值控制`、`常规控制` 三个名称，不引入其他旧称或临时称呼。
- 变 `c0` 分析中，`TDINN控制` 不随 `c0` 重新拟合，只作为固定参照；`情景一阈值控制` 和 `常规控制` 使用当前 `c0`。
- 对 `eta>1300` 的图 2 风格面板，inset 的规则是只展示 TDINN 蓝线和真实数据点，不展示红色阈值控制线和 `eta` 水平线；主图仍保留三类策略和阈值线。
- 当前阶段不主动推进双阈值或反馈控制。若后续进入双阈值控制，应另建模块或清晰后缀，不要混入本目录的单阈值图谱。
- 写作时先描述指标和参数依赖，再给条件性解释；不要把低阈值长期平台直接写成“不合理”，也不要把总成本 `J` 的阶段性结果写成最终优劣排序。
