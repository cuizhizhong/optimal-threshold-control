# AGENTS.md - TDINN-q-only 消融对照实验

## 用途

本目录用于保存 `TDINN-q-only` 消融对照实验。实验目标是分离完整 TDINN 控制中接触率控制 \(c(t)\) 和隔离率控制 \(q(t)\) 的作用。

`TDINN-q-only` 不是重新训练得到的新 TDINN 控制，而是反事实机制对照：

```tex
c(t)\equiv c_0,\qquad q(t)=q_{\rm TDINN}(t).
```

它用于回答：若取消 TDINN 中的接触率下降，只保留 TDINN 学到的隔离率轨迹，控制效果会发生什么变化。

## 比较策略

每个参数情景比较四条曲线：

```tex
\text{常规控制}:\quad c(t)=c_0,\quad q(t)=q_0.
```

```tex
\text{TDINN控制}:\quad c(t)=c_{\rm TDINN}(t),\quad q(t)=q_{\rm TDINN}(t).
```

```tex
\text{TDINN-q-only}:\quad c(t)=c_0,\quad q(t)=q_{\rm TDINN}(t).
```

```tex
\text{情景一阈值控制}:\quad c(t)=c_0,\quad q(t)=q_c(t).
```

其中情景一阈值控制仍保持理论时间开环控制：

```tex
q_c(t)=1-\frac{\gamma N}{\beta c_0 S_{\rm th}(t)}.
```

不要把 `TDINN-q-only` 写成“新的 TDINN 控制”或“重新学习的 TDINN 控制”。

## 主要文件

源文件：

- `tdinn_q_only_comparison.py`

汇总结果：

- `tdinn_q_only_summary.csv`

三组图 2 风格面板：

- `panels_city_eta002N.pdf`
- `panels_city_eta002N.png`
- `panels_city_eta100.pdf`
- `panels_city_eta100.png`
- `panels_Neff50000_eta100.pdf`
- `panels_Neff50000_eta100.png`

对应时间序列：

- `timeseries_city_eta002N.csv`
- `timeseries_city_eta100.csv`
- `timeseries_Neff50000_eta100.csv`

## 参数情景

当前实验包含三组参数：

```tex
(N,\eta)=(13,163,000,\ 0.002N),
```

```tex
(N,\eta)=(13,163,000,\ 100),
```

```tex
(N_{\rm eff},\eta)=(50,000,\ 100).
```

全市人口两组使用主西安口径拟合初值。\(N_{\rm eff}=50,000\) 组使用 `effective_population_sensitivity/` 中相同口径重新拟合 \(I_0\)。

所有非阈值策略均用 ODE 数值求解。情景一阈值控制使用已有分段实现：

1. 启动前用常规控制 ODE 积分到 \(I(t)=\eta\)；
2. 平台期用解析公式保持 \(I(t)=\eta\)；
3. 平台结束后回到常规控制，继续积分到 \(I(t)\le1\)。

## 汇总指标

`tdinn_q_only_summary.csv` 每个情景 4 行，共 12 行。字段包括：

- `scenario`
- `strategy`
- `N`
- `eta`
- `eta_fraction`
- `peak_I`
- `peak_time`
- `time_above_eta`
- `clear_time`
- `cum_total_infections`
- `J_c`
- `J_q`
- `J`
- `q_max`
- `control_start`
- `control_end`
- `control_duration`
- `status`

其中 `control_duration` 在论文表述中记为 \(\Delta t\)。

口径为：

- `情景一阈值控制`：\(\Delta t=t_2-t_1\)，即平台控制期；
- `TDINN控制` 和 `TDINN-q-only`：无明确启动/解除时刻，表中 \(\Delta t=T_{\rm clear}\)；
- `常规控制`：\(\Delta t=0\)。

本实验不在汇总表中输出 `q_mean`。`J` 为固定权重 \(w_c=1,w_q=2\) 下的二次加权总成本；`J_c` 和 `J_q` 为单独归一化分项成本。

## 已得到的主要结果

当前 12 个结果点均为 `status=ok`。

### 全市人口，\(\eta=0.002N=26326\)

```text
TDINN控制:
peak_I≈151.90, clear_time≈45.27

TDINN-q-only:
peak_I≈6719.08, clear_time≈67.40

情景一阈值控制:
peak_I=26326, clear_time≈258.11, Delta t≈85.07

常规控制:
peak_I≈1.38e6
```

这说明完整 TDINN 的低峰值效果不仅来自 \(q_{\rm TDINN}(t)\)，接触率下降 \(c_{\rm TDINN}(t)\) 起到重要作用。

### 全市人口，\(\eta=100\)

```text
TDINN-q-only:
peak_I≈6719.08 > 100

情景一阈值控制:
peak_I=100, Delta t≈22523.29, clear_time≈23748.32
```

这说明在 \(c(t)\equiv c_0\) 的单隔离率控制约束下，直接使用 \(q_{\rm TDINN}(t)\) 不能满足低阈值硬约束；情景一阈值控制能守住 \(\eta=100\)，但平台期和清零时间非常长。

### 有效人口，\(N_{\rm eff}=50,000,\eta=100\)

```text
TDINN控制:
peak_I≈166.25, clear_time≈44.33

TDINN-q-only:
peak_I≈1020.08, clear_time≈47.80

情景一阈值控制:
peak_I=100, Delta t≈85.07, clear_time≈176.20

常规控制:
peak_I≈5232.66
```

在该有效人口口径下，情景一阈值控制仍能守住 \(\eta=100\)，但清零时间长于 TDINN 类控制；`TDINN-q-only` 峰值显著高于完整 TDINN，说明完整 TDINN 中 \(c(t)\) 下降仍是重要因素。

## 解释口径

推荐写法：

> 为分离接触率控制与隔离率控制的作用，构造 TDINN 隔离率单控制反事实对照：保持 \(q_{\rm TDINN}(t)\) 不变，但令 \(c(t)\equiv c_0\)。该对照并非重新训练得到的 TDINN 控制，而是用于评估 TDINN 隔离率轨迹在单控制约束下的效果。

当前数值结果支持以下条件性观察：

- 完整 TDINN 的低峰值主要依赖双控制自由度，即同时降低 \(c(t)\) 和提高 \(q(t)\)；
- 当取消 \(c(t)\) 下降后，`TDINN-q-only` 的峰值明显高于完整 TDINN；
- 在低阈值 \(\eta=100\) 下，`TDINN-q-only` 不能保证 \(I(t)\le\eta\)；
- 情景一阈值控制能按给定 \(\eta\) 守住峰值，但代价是清零时间和控制持续时间增加。

不要写成：

- “情景一阈值控制优于 TDINN”；
- “TDINN-q-only 是新的 TDINN 控制”；
- “TDINN 失效”。

更稳妥的结论是：该消融实验说明完整 TDINN 和情景一阈值控制并不处在同一控制自由度下；若只允许调节隔离率，解析阈值控制更直接服务于医疗容量硬约束，而 TDINN 的隔离率轨迹单独使用时不一定满足该约束。

## 图像口径

三张图均为图 2 风格面板，包含：

- \(I(t)\)
- \(I_{\rm new}(t)\)
- \(I_{q_{\rm new}}(t)\)
- \(c(t)\)
- \(q(t)\)

图中四条曲线：

- `TDINN控制`：蓝色实线；
- `TDINN-q-only`：紫色点划线；
- `情景一阈值控制`：红色虚线；
- `常规控制`：黑色点线。

对 `city_eta100`，由于情景一阈值控制清零时间超过两万天，图像主轴只展示前 120 天，并在标题中标记 `display truncated`。完整清零时间和控制时长保存在 `tdinn_q_only_summary.csv` 和 `timeseries_city_eta100.csv` 中。

## 常用命令

从项目根目录运行：

```powershell
python -B xian_control_comparison\tdinn_q_only_comparison\tdinn_q_only_comparison.py
```

## 编辑规则

- 不覆盖主西安比较结果；
- 不修改 `threshold_landscape_analysis/` 或 `effective_population_sensitivity/` 的既有输出；
- 若新增指标，优先保持 `tdinn_q_only_summary.csv` 的现有字段稳定；
- 若修改图像，需要重新检查四条曲线、真实日报点、阈值线和阈值控制启动时间线是否仍在图中。
