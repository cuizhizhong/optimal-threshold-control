# 固定阈值比例下的 c0 数值实验

## 实验口径

- 固定参数：`N_eff=20000`、`beta=0.1498`、`gamma=0.2953`、`q0=0.323`。
- 固定阈值比例：`theta=eta/N=0.002`，所以共同平台为 `eta=40.00` 人。
- 在 `N_eff=20000` 下按现稿的四序列最小二乘口径只拟合一次初值，得到
  `I0=0.00100662823352`；所有 c0 情景共同使用该初值，不随 c0 重新拟合。
- 作为复现检查，同一程序在全市人口下得到 `I0=0.00100659186644`、
  目标函数 `1036.761462098`，附件记录值分别为
  `0.00100662823352`、`1036.76140515`。
- 不画 TDINN，也不画公共无控制轨迹；图中只比较阈值控制自身。

## 三个结构位置

- 阈值首次可达边界：`c0_trigger=3.33372463`。低于该值时无需启动阈值控制。
- 内部拐点出现边界：`c0_inf=3.54308966`。在触发边界与此边界之间，
  q_c(t) 可构造但全程凸，不存在内部拐点。
- 控制时长极大点：`c0_duration_max=6.60699438`，
  `Delta_t_max=103.18101642` 天。

隔离率拐点高度在所有存在内部拐点的情景中均为
`q_inf=0.411903081628`，与 c0 无关。

## 五个代表情景

| c0 | t1 (d) | Delta t (d) | t2 (d) | q_max | t_inf / lambda | clear time (d) | total cumulative |
|---:|---:|---:|---:|---:|:---:|---:|---:|
| 3.4337 | 209.99 | 30.22 | 240.21 | 0.3834 | 无（全程凸） | 366.52 | 1831.71 |
| 3.5931 | 157.38 | 47.53 | 204.91 | 0.4227 | 162.52 / 0.108 | 328.49 | 2020.73 |
| 6.607 | 28.33 | 103.18 | 131.51 | 0.6971 | 108.46 / 0.777 | 223.82 | 3333.91 |
| 9 | 17.18 | 98.00 | 115.19 | 0.7782 | 98.26 / 0.827 | 194.92 | 3536.62 |
| 12.887 | 10.48 | 85.07 | 95.55 | 0.8454 | 83.73 / 0.861 | 162.95 | 3608.57 |

## 直接读图结论

1. c0 增大时，阈值平台高度始终等于 eta，变化的是到达平台的速度、平台长度和所需隔离强度。
2. t1 严格提前，q_max 严格增大；c0=3.43、3.59
   分居拐点出现边界两侧，展示触发边界到控制时长极大点之间的近临界过渡。
3. Delta t 在整个可行域上不是单调量：从触发边界的 0 上升，在 c0≈6.61 达到约 103.18 天，
   随后随 c0 增大而下降；基准情景展示这一回落阶段。
4. c0=3.43 虽能触发阈值控制，但 q_max<q_inf，因此 q_c(t) 全程凸、无内部拐点。
   c0=3.59、6.61、9.00、12.89 均超过约 3.5431，存在唯一内部拐点。
5. 内部拐点存在时，q_inf 不变，但 lambda 随 c0 增大而增大：
   拐点在归一化平台时间中向 t2 端移动；绝对 t_inf 则因整条轨迹提前而提前。
6. I(t) 平台上的实心圆只是 q_c(t) 拐点时刻的投影，不是 I(t) 自身的拐点。
7. 总累计感染按各情景自身的清零时刻 I(t)=1 截止，定义为
   I_tcum=I_cum+Iq_cum；累计仓室从 0 开始，不重复计入共同的初始感染 I0。

## 数值校验

- 五个开环平台的最大绝对平台误差（换算为人数）为 `0.000e+00`。
- 对存在拐点的三条曲线，用均匀时间网格二阶差分独立定位：
  最大时刻误差 `3.973e-03` 天，最大高度误差 `3.011e-05`。

## 文件

- `c0_sensitivity_main.png/.pdf`：I(t) 与 q(t) 的两面板主图。
- `c0_sensitivity_main_linear.png/.pdf`：仅将主图 I(t) 纵轴改为线性坐标的对照版。
- `c0_sensitivity_main_linear_cumulative.png/.pdf`：线性主图；用清零时总累计感染柱状图替代相对时间 inset。

## 到论文图的映射（复制到 ../figures/ 时务必按此对应）

主图有三个变体，**正文图 23 用的是 `main_linear_cumulative`**（线性纵轴 + 总累计感染柱图 inset），
不是 `main`（对数纵轴 + 相对时间 inset）。三者版式相近，容易复制错。

| 本目录输出 | ../figures/ 目标名 | 正文 |
|---|---|---|
| `c0_sensitivity_main_linear_cumulative.pdf` | `c0_sensitivity_panel.pdf` | 图 23（`fig:c0-panel`） |
| `c0_sensitivity_phase.pdf` | `c0_sensitivity_phase.pdf` | 图 24（`fig:c0-phase`） |
| `c0_sensitivity_scan.pdf` | `c0_sensitivity_scan.pdf` | 附录（`fig:c0-scan`） |
| `c0_beta_existence.pdf` | `c0_beta_existence.pdf` | 附录（`fig:c0-beta-existence`） |

`c0_sensitivity_main.pdf` 与 `c0_sensitivity_main_linear.pdf` 仅作对照，不进论文。
- `c0_sensitivity_scan.png/.pdf`：c0 连续扫描的八指标图，上排 t1、Δt、tail、t_end
  （三者相加即 t_end），下排 q_max、λ、J、I_tcum。
- `c0_sensitivity_phase.png/.pdf`：(θ,c0) 结构相图（三条结构边界叠 Δt 等值线）。
- `c0_beta_existence.png/.pdf`：(c0,β) 平面内部拐点存在域（β 为病原情景变量，θ、q0 固定）。
- `c0_representative_summary.csv`：五个代表情景的指标表。
- `c0_representative_timeseries.csv`：五条轨迹的逐时点数据。
- `c0_continuous_scan.csv`：连续 c0 扫描数据。
- `experiment_parameters.json`：参数、边界与一次性初值标定结果。
- `run_c0_sensitivity.py`：可复现实验脚本。
- `inputs/xian_observed_data_processed.csv`：脚本的一次性初值标定输入。
