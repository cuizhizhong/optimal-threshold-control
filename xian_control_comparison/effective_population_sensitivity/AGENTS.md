# AGENTS.md - 有效人口规模敏感性实验

## 用途

本目录用于保存“有效混合人口规模” \(N_{\rm eff}\) 对情景一阈值控制影响的探索性数值实验。该实验不替代西安主基准 \(N=13,163,000\)，也不修改 `xian_control_comparison.py`、`archive_unused/low_eta_analysis/` 或 `threshold_landscape_analysis/` 中的既有结果。

本实验的核心问题是：若把 SIQR 模型中的人口规模从全市人口解释为有效混合人口 \(N_{\rm eff}\)，则固定绝对阈值和同比例阈值下的启动时间、平台控制时长和清零时间如何变化。

## 模型口径

感染项仍写为

```tex
\frac{\beta c(t)(1-q(t))S(t)I(t)}{N_{\rm eff}}.
```

对每个 \(N_{\rm eff}\)，固定 He--Tang--Xiao 参数和 TDINN 控制函数：

```tex
\beta,\quad \gamma,\quad \delta_q,\quad c_{\rm TDINN}(t),\quad q_{\rm TDINN}(t).
```

只重新拟合初始种子 \(I_0\)，并令

```tex
S_0=N_{\rm eff}-I_0,\qquad R(0)=0.
```

该设定是条件性敏感性分析，不表示已经重新估计了完整传播参数，也不能直接推出真实传播网络规模。

## 主要文件

源文件：

- `effective_population_sensitivity.py`

主要输出：

- `effective_population_summary.csv`：每个 \((N_{\rm eff},\eta)\) 情景的阈值控制指标；
- `effective_population_fit_summary.csv`：每个 \(N_{\rm eff}\) 下重新拟合得到的 \(I_0\) 和拟合误差；
- `effective_population_summary_table.tex`：LaTeX 表格；
- `effective_population_sensitivity_note.tex`：中文 LaTeX 实验笔记；
- `effective_population_sensitivity_note.pdf`：已编译的实验笔记；
- `figures/effective_population_time_metrics.*`：\(t_1,\Delta t,T_{\rm clear}\) 随 \(N_{\rm eff}\) 的变化；
- `figures/effective_population_cost_metrics.*`：累计感染和控制成本指标；
- `figures/effective_population_eta_fraction.*`：不同阈值口径下的 \(\eta/N_{\rm eff}\)。

代表性面板图：

- `representative_panels/panels_Neff50000_eta100.*`
- `representative_panels/timeseries_Neff50000_eta100.csv`

局部拐点分析：

- `plot_eta_80_100_150_inflection.py`：固定 `N_eff=50,000`，比较 `eta=80,100,150`；
- `plot_Neff_40000_50000_60000_inflection.py`：固定 `eta=100`，比较 `N_eff=40,000,50,000,60,000`；
- `representative_panels/*inflection*.{pdf,png,csv}`：对应轨迹图、绘图时间序列和拐点汇总。

无量纲标度验证：

- `dimensionless_scaling_analysis.py`：区分固定无量纲初值的精确结构实验与逐个 `N_eff` 重拟合 `I0` 的数据实验；
- `dimensionless_scaling_exact_summary.csv`：组一，固定 `(s0,i0,rho)` 只变 `N_eff` 的指标；
- `dimensionless_scaling_rho_sweep.csv`：组二，固定 `(s0,i0)` 变 `rho`，并在 `N_eff=50,000` 和 `13,163,000` 上交叉验证；
- `dimensionless_scaling_refit_summary.csv`：逐个 `N_eff` 重拟合绝对 `I0` 时的同比例阈值指标；
- `dimensionless_scaling_invariance_checks.csv`：标度不变量的数值容差检查；
- `figures/dimensionless_scaling_collapse.*`：`i(t)` 和 `q(t)` 折叠图；
- `figures/clearance_tail_decomposition.*`：绝对清零判据与固定分数判据的尾段比较；
- `figures/dimensionless_rho_dependence.*`：组二的 `Delta t`--`rho` 和 `h(rho)`--`rho` 曲线。

拐点不变量与存在边界：

- `inflection_inverse_summary.csv`：固定 `beta` 时，变 `eta` 和变 `N_eff` 两组的二阶差分拐点定位及 `beta` 反演结果；
- `inflection_invariance_analysis.py`：`beta` 扫描与 `q0` 存在边界扫描（结构性实验，不重新拟合数据）；
- `inflection_beta_sweep.csv`：拐点高度随 `beta` 的理论值、数值值和残差；
- `inflection_boundary_scan.csv`：`q0` 逼近并越过 `(1-beta)(1-q0)=1/2` 时的拐点存在性；
- `figures/inflection_height_beta_invariance.*`：`q_c(2*Sbar)` 对 `beta` 的理论曲线与数值散点；
- `figures/inflection_boundary_scan.*`：平台解除点滑到固定拐点上的过程。

## 实验设置

扫描的有效人口规模为：

```tex
N_{\rm eff}\in
\{5\times10^4,10^5,3\times10^5,10^6,3\times10^6,13,163,000\}.
```

阈值口径为：

```tex
\eta=100,\qquad \eta=520,\qquad \eta=0.002N_{\rm eff}.
```

其中：

- `eta100` 和 `eta520` 是固定绝对阈值，用于观察 \(N_{\rm eff}\) 降低时 \(\eta/N_{\rm eff}\) 增大的影响；
- `eta_fraction_0p002` 是同比例阈值口径，用于观察 \(\eta/N_{\rm eff}=0.002\) 固定时的变化。

## 已得到的主要数值现象

当前输出中全部 18 个实验点均为 `status=ok`。

重新拟合的 \(I_0\) 在不同 \(N_{\rm eff}\) 下变化不大，例如：

```text
N_eff=50,000:     I0≈0.001309
N_eff=13,163,000: I0≈0.001007
```

这与早期 \(S(t)/N_{\rm eff}\approx1\) 时新增感染近似不显含 \(N_{\rm eff}\) 的结构一致。

在固定绝对阈值 \(\eta=100\) 下，降低 \(N_{\rm eff}\) 会显著缩短平台控制时长：

```text
N_eff=13,163,000, eta=100:
Delta t≈22523.29, T_clear≈23748.32

N_eff=50,000, eta=100:
Delta t≈85.07, T_clear≈176.20
```

在同比例阈值 \(\eta=0.002N_{\rm eff}\) 下，平台控制时长保持在约 85 天量级：

```text
N_eff=50,000, eta=100=0.002N_eff:
Delta t≈85.07

N_eff=13,163,000, eta=26326=0.002N_eff:
Delta t≈85.07
```

这个结果说明，在当前参数和拟合口径下，低阈值长期平台主要与 \(\eta/N_{\rm eff}\) 很小有关，而不是仅由阈值控制公式本身造成。

平台期隔离率曲线的凹凸拐点满足：

```tex
S_{\rm th}(\bar t)=2\bar S,
\qquad
\bar t=t_1+\frac{N_{\rm eff}}{c_0\eta}
\log\frac{S^*-\bar S}{\bar S}.
```

当前两组局部扫描均满足 `Sc < 2*Sbar < S_star`，因此控制期内存在唯一拐点。
固定 `N_eff=50,000` 时，`eta=80,100,150` 对应 `t_bar≈102.59,84.38,60.21` 天；
固定 `eta=100` 时，`N_eff=40,000,50,000,60,000` 对应
`t_bar≈69.57,84.38,99.17` 天。拐点处 `q_c(t_bar)≈0.4119`，在固定 `beta` 下不依赖
`N_eff` 和 `eta`。`t_bar` 只表示 `q_c(t)` 的曲率变化，不是控制启动或解除时刻。

拐点图中应保留水平参考线：

```tex
q^*=1-\frac{1}{2(1-\beta)}\approx0.4119.
```

当前实现还使用均匀采样的 `q_c(t)` 做二阶差分，通过负到正变号独立定位拐点，并用

```tex
\widehat\beta=1-\frac{1}{2(1-q^*)}
```

反演 `beta`。这只是给定解析控制律下的一致性检查；不要直接解释为含噪真实控制数据上的参数估计。

## 拐点的存在条件

存在条件 `Sc < 2*Sbar < S_star` 的左端可以等价改写为

```tex
S_c<2\bar S
\iff
(1-\beta)(1-q_0)>\tfrac12
\iff
q_0<q^*=1-\frac{1}{2(1-\beta)}.
```

也就是说，拐点存在等价于常规隔离率低于拐点高度本身。西安参数下
`q0=0.323 < q*≈0.4119`；等价地，给定 `q0` 时要求 `beta < 0.2614`。
右端不等式 `2*Sbar < S_star` 在当前参数下不起约束作用
（`2*Sbar/N_eff≈0.260`，`S_star/N_eff≈0.989`）。

`beta` 扫描（固定 `N_eff=50,000`、`eta=100`、`c0`、`q0`）中，`beta` 从 `0.06`
到 `0.24`，数值拐点高度与 `1-1/(2(1-beta))` 的最大绝对误差约 `2.1e-08`，
`beta` 反演逐行还原输入值。

`q0` 边界扫描（固定 `beta=0.1498`）中，`Sbar` 和 `k=c0*eta/N_eff` 都不含 `q0`，
因此 `q_c(tau)` 曲线几乎不动；改变 `q0` 改变的是平台何时解除，截断点高度恰好是
`q0`。`q0` 从 `0.3230` 增到 `0.4118` 时 `t2-t_bar` 从约 `11.82` 天降到 `0.014`
天；`q0=0.4200` 时 `(1-beta)(1-q0)=0.4931<1/2`，控制期内不再存在拐点。

改变 `beta` 或 `q0` 会破坏 He--Tang--Xiao 参数与 TDINN 控制函数的标定，
因此这两组扫描是结构性实验，只验证控制律的恒等式和存在边界，不是参数估计，
也不重新拟合日报数据。

## 无量纲标度的条件

令 `s=S/N_eff`、`i=I/N_eff`、`rho=eta/N_eff`。传播参数和控制函数固定时，
`N_eff` 不显含于 `(s,i)` 方程，但严格轨迹折叠还要求无量纲初值 `(s0,i0)` 固定。

必须区分：

- 精确结构实验：固定 `(s0,i0,rho)`，此时 `t1`、`Delta t`、`t2`、`q_c(t)`、`J` 和固定分数终止时间是数值不变量；
- 数据重拟合实验：每个 `N_eff` 重新拟合绝对 `I0`，所以 `i0=I0/N_eff` 改变，`t1` 不会严格不变；
- 动态清零 `I<=1` 等价于 `i<=1/N_eff`，因此 `T_clear` 额外依赖 `N_eff`；
- `I_tcum=N_eff*h(rho)` 只在固定无量纲终点或共同时间下严格成立。使用 `I<=1` 终止时，累计感染分数也有终止地板造成的小量修正。

当前固定 `(s0,i0,rho=0.002)` 的结构实验中，六个 `N_eff` 的
`t1≈11.128429`、`Delta t≈85.071082`、固定 `i<=1e-7` 的清零时间
`≈248.584434` 天。公共区间内 `i(t)` 最大折叠误差约 `2.1e-10`，
`q(t)` 最大折叠误差约 `2.2e-16`。绝对判据 `I<=1` 的清零时间仍随
`N_eff` 从约 `176.20` 天增至 `252.34` 天。

依赖分离需要两组扫描合起来才成立：

- 组一（固定 `rho` 变 `N_eff`）说明指标不随 `N_eff` 变；
- 组二（固定 `(s0,i0)` 变 `rho`，见 `dimensionless_scaling_rho_sweep.csv`）说明指标确实随 `rho` 变，
  且同一 `rho` 下 `N_eff=50,000` 与 `13,163,000`（相差约 263 倍）给出同一组无量纲指标，
  最大差异约 `1.1e-13`。

组二中 `rho` 从 `5e-4` 增到 `8e-3` 时 `Delta t` 从约 `341.75` 天降到 `20.89` 天，
而对数因子 `c0*rho*Delta t=log[(s*-sbar)/(sc-sbar)]` 只从 `2.2021` 变到 `2.1538`，
因此 `Delta t≈const/(c0*rho)` 是好的近似。同一 `rho` 下绝对判据的
`T_clear` 仍随 `N_eff` 改变，与组一结论一致。

## 写作口径

描述本实验时应使用条件性表述，例如：

- “在固定 \(\beta,\gamma,\delta_q,c(t),q(t)\) 并重新拟合 \(I_0\) 的条件下，数值结果显示……”
- “当 \(\eta/N_{\rm eff}\) 保持不变时，\(\Delta t\) 基本保持同量级。”
- “当 \(\eta\) 固定而 \(N_{\rm eff}\) 降低时，\(\eta/N_{\rm eff}\) 增大，平台控制时长缩短。”

不要写成：

- “真实人口规模应取 \(N_{\rm eff}=50,000\)”；
- “证明全市人口口径错误”；
- “有效人口修正后情景一阈值控制一定更合理”。

更准确的表述是：\(N_{\rm eff}\) 是一个有效混合人口尺度假设，需要接触网络、空间活动或分区病例数据进一步支持。

## 常用命令

从项目根目录运行：

```powershell
python -B xian_control_comparison\effective_population_sensitivity\effective_population_sensitivity.py
```

该命令会依次重建基础扫描、无量纲标度实验（含组二 `rho` 扫描）、两组局部拐点分析、
`beta` 与 `q0` 不变量扫描，以及 LaTeX 笔记源文件。

编译 LaTeX 笔记：

```powershell
cd xian_control_comparison\effective_population_sensitivity
xelatex -interaction=nonstopmode effective_population_sensitivity_note.tex
xelatex -interaction=nonstopmode effective_population_sensitivity_note.tex
```

## 编辑规则

- 不要覆盖西安主基准结果；
- 不要把本目录结果写成最终政策结论；
- 若新增 \(N_{\rm eff}\) 点，应重新拟合 \(I_0\)，并记录 `I0_fit`、`fit_objective` 和 `fit_raw_rmse`；
- 若修改图、表或 LaTeX 笔记，需重新运行脚本并编译笔记两遍。
