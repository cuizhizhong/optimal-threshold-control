# tradeoff_frontier

把情景一阈值控制看成**单参数族**，在"实际社区感染峰值—控制代价"平面上画前沿曲线，
并把 TDINN 控制和常规控制各作为一个点叠上去。目的是避免"用单个 `eta=0.002N` 去比 TDINN"
带来的挑参数质疑，改为展示整条前沿及其被支配关系。

## 关键设计

- **横轴统一用实际峰值 `max I`（对数）**，使三条策略可比：阈值控制 `max I = eta`；
  TDINN、常规的峰值不是 `eta`，只有用实际峰值才能落进同一坐标。
- **纵轴（对数）**：控制时长 `Δt`、清零时间 `T_clear`、二次加权成本 `J`。
- `eta` 的两种身份：横轴上的 `eta` 是政策目标峰值（自由旋钮）；医疗容量约束
  `eta_cap = 0.002N = 26326` 只是图上一条竖虚线，不是曲线的选取点。
- 累计感染暂不纳入本图。

## 输出

运行脚本生成：

- `tradeoff_frontier_main.pdf/png`：1×3 主图（`Δt` / `T_clear` / `J` vs `max I`）。
- `tradeoff_cost_caliber.pdf/png`：1×2 成本口径对照（积分 `J` vs 日均 `J/Δt`）。
- `tradeoff_frontier_points.csv`：装配好的绘图数据（含 `daily_J = J/Δt`）。

## 数据来源（只读，不重算）

- `../cost_weight_analysis/cost_summary_wq2.csv`：阈值控制 `eta` 扫描（56 点，`w_q=2`）。
- `../../xian_control_comparison_summary.csv`：TDINN / 常规控制参照点（含 `control_duration`）。

## 当前数值现象（诊断输出，仅在当前西安参数下成立）

- 在 TDINN 峰值附近（`max I ≈ 100–152`），阈值控制的 `Δt`、`J` 约为 TDINN 的 **498×、221×**。
- 阈值族日均成本率 `J/Δt` 在整个 `eta` 扫描上几乎不变（约 `0.47–0.48`），而积分 `J` 跨约 310×；
  说明低 `eta` 的高 `J` 主要来自超长 `Δt`，不是每天隔离强度高。TDINN 日均率约 `1.09`，反而更高。

这些是条件性数值现象，不作为"某策略更好"的最终结论。

## 运行

```powershell
conda run -n thesis python tradeoff_frontier.py
```
