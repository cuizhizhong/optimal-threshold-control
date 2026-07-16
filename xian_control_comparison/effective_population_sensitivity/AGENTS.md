# AGENTS.md - 有效人口规模敏感性实验

## 用途

本目录用于保存“有效混合人口规模” \(N_{\rm eff}\) 对情景一阈值控制影响的探索性数值实验。该实验不替代西安主基准 \(N=13,163,000\)，也不修改 `xian_control_comparison.py`、`low_eta_analysis/` 或 `threshold_landscape_analysis/` 中的既有结果。

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
