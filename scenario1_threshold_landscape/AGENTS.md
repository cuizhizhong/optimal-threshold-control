# AGENTS.md

## 目录用途

本目录是 `N=763` 情景一阈值控制的独立数值实验模块，用于生成“阈值响应图谱”。本实验只研究情景一：

- 固定接触率 `c(t)=c0`；
- 在平台期使用理论推导得到的时间开环隔离控制 `q_c(t)`；
- 考察二维参数平面 `(\eta/N,c_0)` 对启动时间、平台时长、清零时间、隔离强度、控制成本和累计感染的影响。

不要把本目录中的探索性图、表、CSV 直接同步到主论文目录；是否替换主论文图表需要用户明确要求。

## 当前实验版本

当前参数设置见 `common/scenario1_params.m`，截至本文件创建时为：

```matlab
N = 763;
S0 = 762;
I0 = 1;
beta = 0.155;
gamma = 0.3504;
q0 = 0.01526;
c0_base = 10;

eta_frac_list = 0.002:0.0002:0.050;
c0_list = 2.3:0.1:14;
selected_eta_frac = [0.002, 0.005, 0.010, 0.020];
selected_c0 = [6, 10, 14];
baseline_eta_frac = [0.020, 0.002];

main_c0_values = [4, 5, 8, 10, 12];
main_eta_frac_values = [0.002, 0.006, 0.010, 0.020];
main_c0_sweep_eta_frac = 0.050;
main_eta_sweep_c0 = 10;
main_eta_sweep_c0_values = [5, 8, 10, 12];
c0_response_eta_frac = main_eta_frac_values;
```

探索性 `selected_*` 与主论文候选图的 `main_*` 配置必须分开维护。`baseline_eta_frac` 暂时保持
`[0.020,0.002]`，因为 `plot_baseline_validation.m` 的两个稳定输出文件名仍按这两个阈值定义。

当前完整网格为 `241 x 118 = 28438` 个参数点。最近一次检查结果（2026-07-28）：

- `current_run/output_csv/landscape_summary.csv`：28438 行；
- `valid`：26780/28438；
- `current_run/output_csv/diagnostics.csv`：1658 条预期的阈值不可达记录；
- `current_run/output_csv/representative_cases.csv`：9 个代表组合；
- `current_run/output_csv/peak_validation.csv`：5 组峰值验收；
- `current_run/figures/`：17 张 PDF；
- `current_run/tables/`：4 个 LaTeX 表格。

## 目录结构与入口

当前目录结构采用“源码、共享函数、当前结果、历史归档”分离：

```text
scenario1_threshold_landscape/
├── AGENTS.md
├── README.md
├── run_all.m
├── common/
├── scripts/
├── current_run/
│   ├── output_csv/
│   ├── figures/
│   ├── tables/
│   └── logs/
└── archive_runs/
```

推荐入口：

```powershell
matlab -batch "run('E:\work\draft\scenario1_threshold_landscape\run_all.m')"
```

`run_all.m` 会先调用 `common/reset_output_dirs.m` 清空 `current_run/` 的 `output_csv/`、`figures/`、`tables/`、`logs/`（避免上一轮过期文件残留），再运行 `scripts/generate_landscape_data.m` 和各绘图/表格脚本，生成本轮完整结果。`common/scenario1_params.m` 现在只负责返回参数和固定输出路径，不再做运行状态记录或自动归档；`mode` 参数保留只为向后兼容，会被忽略。如需保留某一轮结果，请在重跑前手动复制 `current_run/`。`archive_runs/` 中的历史结果保留，但不再由脚本自动写入。

注意：`reset_output_dirs` 只应由 `run_all.m` 在整轮开始时调用；单独重跑某个 `scripts/plot_*.m` 时不要清空目录，否则会误删其他输出。

## 脚本职责

- `scripts/generate_landscape_data.m`：只生成 CSV 和诊断，不画图。
- `scripts/validate_main_outputs.m`：在绘图前强制检查 28438 行网格、有效指标、诊断码、五组 `Delta_t` 峰值与拐点恒等式。
- `scripts/plot_baseline_validation.m`：生成两个基准验证图和 `baseline_validation_table.tex`；当前基准图同时画常规控制虚线、阈值控制曲线、`t1/t2` 竖线和 `eta/S_c/q0` 参考线。
- `scripts/plot_main_q_trajectories.m`：生成主论文图 5/6 候选图；画平台期开环 `q_c(t)`、公共 `q0/q_inf` 参考线、切入/解除标记和内部拐点。
- `scripts/plot_sensitivity_curves.m`：生成四档 `c0` 下的对数阈值响应图和四档阈值下的 `c0` 响应图；`c0` 图的 `Delta_t` 面板使用线性纵轴并标出离散峰值，`eta` 图的 `q_max` 面板固定为 `0.45--0.85`。
- `scripts/plot_heatmaps.m`：生成六张单指标热图与 `t1/Delta_t/t_end/I_t_cum` 的 2×2 主论文候选图；解析可行边界以下留白。
- `scripts/plot_duration_regions.m`：按 `Delta_t` 划分控制时长区域。
- `scripts/plot_representative_trajectories.m`：生成代表阈值和代表 `c0` 下的轨迹图。
- `scripts/plot_cumulative_decomposition.m`：生成累计感染分解图。
- `scripts/write_representative_tables.m`：生成代表组合表。
- `scripts/write_main_summary_tables.m`：生成主论文候选的 `c0`、`eta` 汇总 CSV 和 LaTeX 表。

共享计算逻辑在 `common/`：

- `compute_metrics.m`：理论指标和诊断的核心函数；
- `compute_trajectory.m`：三阶段轨迹重构；
- `q_control_tau.m`：平台期时间开环控制；
- `critical_c0_for_eta.m`：解析求取给定 `eta` 的可行下界 `c0_min`；
- `scenario1_inflection_point.m`：判断内部拐点并返回 `q_inf/t_inf`；
- `scenario1_main_plot_style.m`：主论文图 5--9 的 Times/蓝色梯度/红色强调点样式，以及按论文最终宽度定义的物理尺寸；
- `save_figure_safe.m`：矢量 PDF 保存、指定最终 MediaBox 尺寸与 PNG fallback；
- `scenario1_params.m`：参数与固定输出路径（不再做归档/状态记录）。

各绘图脚本共用的小工具也放在 `common/`，避免逐脚本复制：

- `set_graphics_defaults.m`：设置 LaTeX 解释器等图形默认值；
- `open_log.m`：在 `logs/` 下打开单脚本日志；
- `log_line.m`：带时间戳、同时写控制台和日志的输出；
- `append_row.m`：按下标把标量 struct 追加进 struct 数组。

主论文候选图共用 `scenario1_main_plot_style.m`；其他探索性图仍可保留各脚本内的局部 `style_axes`。
主论文图的最终字号固定为：刻度 `8.5 pt`，坐标标签与标题 `10 pt`，图例 `7.5 pt`，
面板编号 `11 pt`，普通注释 `8.5 pt`，热图等值线标签 `8 pt`。图 5/6、图 7/8、
图 9 的目标 PDF 宽度分别为 `324.9 bp`、`397.1 bp`、`451.3 bp`；导出后应确认
LaTeX 插入缩放比例处于 `0.98--1.02`。

## 当前图形输出与格式

当前 `current_run/figures/` 应包含：

```text
baseline_validation_eta0002.pdf
baseline_validation_eta0020.pdf
c0_sensitivity_selected_eta.pdf
cumulative_decomposition_c0_10.pdf
eta_sensitivity_selected_c0.pdf
heatmap_t1.pdf
heatmap_delta_t.pdf
heatmap_t_end.pdf
heatmap_q_max.pdf
heatmap_J.pdf
heatmap_I_t_cum.pdf
region_by_duration.pdf
scenario1_heatmaps_c0_eta.pdf
scenario1_u_time_c0.pdf
scenario1_u_time_eta.pdf
trajectories_c0_selected_eta0010.pdf
trajectories_eta_selected_c0_10.pdf
```

热图格式已经被用户后续修改过，不要随意改回早期版本。当前 `scripts/plot_heatmaps.m` 的关键样式为：

- 使用 `contourf(..., 200, 'LineColor','none')`；
- 使用 `parula(256)`；
- 除 `Delta_t` 固定为 `[0,215]` 外，其余色标由全体有效值按 1--2--5 规则向外取整后固定；
- 叠加红色虚线等高线并尽量显示黑色标签；
- 用 `critical_c0_for_eta` 的解析边界裁切白色不可行区，而不是用离散 `valid` 阶梯线代替；
- 额外输出 `scenario1_heatmaps_c0_eta.pdf` 四面板合成图；
- 使用 `Times New Roman`；
- 图窗尺寸为 `[120, 100, 788, 734]`；
- `exportgraphics(..., 'ContentType','image', 'Resolution',600)`，即 PDF 内采用高分辨率图像方式导出，避免复杂等高线矢量 PDF 过慢或过大。

`scripts/` 下还存在若干用户手动保存或调整过的 `.fig`、`.jpg` 图稿，例如 `Delta_heatmap.jpg`、`I_cum.jpg`、`J.jpg`、`q.jpg`、`sensitive_eta.jpg`、`senstive_c.jpg`、`清零.jpg` 等。不要删除、覆盖或当作自动生成中间文件处理，除非用户明确要求整理这些手动图稿。

## 数值指标与诊断口径

每个参数点保存的主要指标包括：

- 启动与平台：`S_star`、`S_c`、`S_bar`、`t1`、`t2`、`Delta_t`；
- 隔离强度：`q_max`、`q_mean`；
- 清零时间：`t_end`；
- 成本：`J_q`、二次型成本 `J`；
- 累计感染：`I_pre`、`I_wall`、`I_post`、`I_t_cum`；
- 诊断量：`Imax_pre`、`q_t2_error`。

（`platform_error` 只在 `compute_trajectory.m` 重构轨迹时计算，用于基准验证图/表，不再作为图谱汇总列；早先恒为 0 的 `cum_decomp_error` 已删除。）

可行性检查在 `compute_metrics.m` 内逐点强制：不满足时该点标记为 invalid 并写入一条 `diagnostics.csv` 记录，不再在 `generate_landscape_data.m` 里对整表重复检查一遍。逐点检查至少包括：

- `I0 < eta < Imax_pre`；
- `S0 > S_star > S_c > S_bar`；
- `Delta_t > 0`；
- `t_end > t2`；
- `q_max <= 1`；
- `q_c(t2) ≈ q0`。

本实验不把 `q_max=0.8` 或 `q_max=0.9` 当作可行性边界；这些值只作为热图读数或执行压力参考。理论不可行边界仍以 `q_max > 1` 等诊断为准。

## 维护规则

- 默认只使用 MATLAB，不引入 Python 重写本实验流程。
- 修改参数网格、输出数量、图形格式后，同步更新本文件和 `README.md`。
- 不要把 `scripts/plot_heatmaps.m` 的高分辨率 image PDF 导出改回复杂矢量导出，除非用户明确要求。
- 不要把 `q_c(t)` 改成依赖数值积分实时 `S(t)` 的反馈控制；情景一控制律应保持为理论时间开环控制。
- 不要删除 `archive_runs/` 中的历史结果，除非用户明确要求清理归档。
- 单独重画图时优先运行对应 `scripts/plot_*.m`，不要重新生成数据，除非参数或指标公式确实改变。
- 若运行 MATLAB 后出现退出阶段 Java 报错或超时，但日志与输出文件已经完整，先检查 `current_run/logs/` 和输出数量，不要直接判定数值实验失败。

## 当前写作口径

本实验用于说明在当前 `N=763` 小规模算例中，阈值比例和接触率共同决定控制启动时间、平台维持时间、清零时间、隔离强度、成本和累计感染。低阈值对应较长平台控制，高阈值对应较短平台和更晚启动；`c0` 增大通常使启动提前并提高隔离强度需求。相关结论只在当前参数范围和情景一固定 `c(t)=c0` 的理论控制律下成立，不应写成对所有防控策略的最终优劣判断。
