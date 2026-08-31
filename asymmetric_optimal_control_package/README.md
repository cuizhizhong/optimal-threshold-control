# 不同易感耗竭与感染生成系数下的最优控制：复现包

本复现包对应二维系统

\[
\dot S=-\beta_1(t)SI,\qquad
\dot I=\beta_2(t)SI-\gamma I,
\]

重点给出带容量约束 `I(t) <= K` 时的解析最优策略、全局唯一性证明、感染成本稳健性、完全独立控制下的非唯一性反例，以及数值复现程序。

## 目录

- `asymmetric_two_rate_optimal_control.pdf`：最终中文技术报告。
- `latex/main.tex`：可编辑 LaTeX 主文件。
- `latex/references.bib`：参考文献数据库。
- `figures/Figure_1_*.jpg` 至 `Figure_7_*.jpg`：300 dpi 图形。
- `python/Figure_1_*.py` 至 `Figure_7_*.py`：每幅图独立运行的 Python 程序。
- `matlab/Figure_1_*.m` 至 `Figure_7_*.m`：每幅图独立运行的 MATLAB 程序。
- `python/generate_numerical_summary.py`：生成基准数值汇总。
- `data/numerical_summary.csv`：报告中使用的数值结果。

## LaTeX 编译

推荐 XeLaTeX：

```bash
cd latex
xelatex main.tex
bibtex main          # 若本机 bibtex 不可用，可改用 bibtex8 main
xelatex main.tex
xelatex main.tex
```

依赖常见 TeX Live 宏包：`ctex`、`amsmath`、`graphicx`、`natbib`、`hyperref`、`booktabs`、`listings` 等。

## Python 复现

Python 3.10 或更高版本，安装依赖：

```bash
python -m pip install -r python/requirements.txt
```

每幅图可独立运行，例如：

```bash
python python/Figure_1_phase_plane.py
python python/Figure_6_infection_cost_threshold.py
```

脚本会直接覆盖 `figures/` 中对应的 JPG 文件。生成汇总数据：

```bash
python python/generate_numerical_summary.py
```

## MATLAB 复现

将 MATLAB 当前目录设为 `matlab/`，逐个运行同名函数，例如：

```matlab
Figure_1_phase_plane
Figure_6_infection_cost_threshold
```

程序会将 300 dpi JPG 输出到相邻的 `figures/` 目录。代码使用 `ode45`、`fzero` 和基础绘图函数，不依赖额外工具箱。

## 基准参数

```text
B = 1.0
q = 0.8
beta2_bar = q B = 0.8
gamma = 0.3
S0 = 0.99
I0 = 0.01
K = 0.15
```

关键结果：

```text
S_h       = 0.375000
I_peak    = 0.2107663249
S_entry   = 0.6667873240
tau1      = 6.6594644456
tau2      = 11.8467946506
J_star    = 1.3503627745
S_inf     = 0.1131410860
```

## 关于附件式 (25) 的核查

报告没有机械照抄附件中感染成本阈值的显示式。附件附录的 HJB 条件是

\[
a\,I\ell/(\gamma-B\ell)\le 1,
\]

所以临界值应为该比值在安全集上上确界的**倒数**。复现包中的理论、Figure 6、Python 和 MATLAB 程序均使用这一经 HJB 推导、量纲和单调性共同核验后的公式：

\[
a_0(K)=
\begin{cases}
(\gamma-B\lambda)/(K\lambda), & K\le K_0,\\
B\rho/[(1-\rho)K_0], & K>K_0.
\end{cases}
\]

## 建模边界

- 完整闭式唯一性结论对应固定比例结构 `beta2(t) = q beta1(t)`，即两个系数不同但由同一政策强度驱动。
- 若 `beta1` 与 `beta2` 完全独立，且只惩罚低于自然水平的部分，允许无成本上调 `beta1` 会产生无穷多个零成本可行控制；此时不存在与单控制模型相同的唯一性结论。
- 真正非比例的独立控制问题应加入控制上界和双向严格凸成本，并用状态约束 Pontryagin 系统与二阶充分条件检验局部唯一性。
