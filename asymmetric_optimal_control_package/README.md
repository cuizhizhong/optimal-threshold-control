# 不同易感耗竭与感染生成系数下的最优控制

## 项目简介

本项目研究带医疗容量约束的二维系统

~~~text
S' = - beta_1(t) S I
I' =   beta_2(t) S I - gamma I
~~~

重点不是简单地把一个传播率改名为两个传播率，而是区分以下三种建模层次：

1. `beta_1` 与 `beta_2` 由同一个控制驱动，但数值不同；
2. 两个系数完全独立控制；
3. 独立控制下加入边界和严格凸成本的正则化模型。

项目说明了：控制变量的耦合方式、自然水平、是否允许加速传播以及成本定义，会直接决定最优控制是否存在、是否唯一，以及是否能得到解析公式。

## 核心可解模型

设 `B` 是 `beta_1` 的自然水平，`q>0` 是固定比例，使用同一个政策强度 `u(t)` 定义

~~~text
beta_1(t) = u(t),
beta_2(t) = q u(t),
0 <= u(t) <= B.
~~~

令 `x=qS`，系统精确变为

~~~text
x' = -u x I
I' =  u x I - gamma I.
~~~

因此 `x+I` 的变化只由恢复/移除项决定，问题可以在 `(x,I)` 平面中按守恒结构分析，再通过 `S=x/q` 还原。

主成本为

~~~text
J(u) = integral max(B-u(t), 0) dt,
~~~

并要求 `I(t)≤K`。自然传播下的阈值为 `x_h=gamma/B`，相应的易感阈值为 `S_h=gamma/(qB)`。

## 主要理论结论

### 比例但不同的两个系数

自然传播峰值不超过容量时，无需控制，`u*=B` 且成本为零。当容量约束真正绑定时，最优策略为

~~~text
u = B  ->  u = gamma/x  ->  u = B
自然传播    容量边界控制     解除控制
~~~

容量边界上保持 `I=K` 的唯一切向控制是 `u=gamma/x`。在抑制-only 约束 `0≤u≤B` 下，通过校准不变量与成本缺口恒等式，可以证明该策略在几乎处处意义下全局唯一。若允许 `u>B` 却不惩罚加速，则解除容量约束后会出现零成本延拓的非唯一性。

### 完全独立控制的退化

如果 `beta_1` 和 `beta_2` 完全独立，而成本仍只惩罚低于自然水平的部分，那么提高 `beta_1` 可以无成本地快速耗竭 `S`，同时保持 `beta_2` 不变。这样可以在感染达到容量前把系统推过阈值，产生无穷多个零成本可行控制。 `Figure_7_independent_control_nonuniqueness` 给出了这一反例的数值轨迹。

因此，真正的独立控制模型至少需要控制上界、双向成本或严格凸正则项，并结合状态约束 Pontryagin 条件和二阶充分条件检查局部唯一性。

## 基准结果

默认参数为 `B=1.0`、`q=0.8`、`gamma=0.3`、`S0=0.99`、`I0=0.01`、`K=0.15`。 `data/numerical_summary.csv` 提供完整汇总，主要结果为：

| 量 | 数值 |
|---|---:|
| 感染方程自然系数 `beta2_bar` | `0.8` |
| 易感阈值 `S_h` | `0.375000` |
| 自然传播感染峰值 | `0.2107663249` |
| 首次到达容量的 `S_entry` | `0.6667873240` |
| 首次到达容量时间 `tau1` | `6.6594644456` |
| 解除控制时间 `tau2` | `11.8467946506` |
| 最小抑制成本 `J_star` | `1.3503627745` |
| 最终易感比例 `S_infinity_opt` | `0.1131410860` |

## 项目框架

~~~text
asymmetric_optimal_control_package/
├── latex/
│   ├── main.tex                 # 完整中文理论报告
│   └── references.bib           # BibTeX 文献库
├── python/
│   ├── Figure_1_*.py ... Figure_7_*.py  # 7 个独立绘图程序
│   ├── generate_numerical_summary.py    # 生成基准 CSV
│   └── requirements.txt
├── matlab/
│   └── Figure_1_*.m ... Figure_7_*.m    # MATLAB 复现程序
├── data/numerical_summary.csv           # 报告使用的数值结果
├── figures/                             # 7 幅 300 dpi 图形
├── asymmetric_two_rate_optimal_control.pdf
├── CHECKSUMS.sha256
└── MANIFEST.txt
~~~

图形按证据链组织：`Figure_1` 为相平面几何，`Figure_2` 为状态轨迹，`Figure_3` 为两个最优传播系数，`Figure_4` 为容量比较静态，`Figure_5` 为平台策略唯一性，`Figure_6` 为附加感染成本的稳健阈值，`Figure_7` 为独立控制导致的非唯一性反例。

## Python 复现

建议使用 Python 3.10 或更高版本：

~~~bash
python -m pip install -r python/requirements.txt
python python/generate_numerical_summary.py
python python/Figure_1_phase_plane.py
python python/Figure_7_independent_control_nonuniqueness.py
~~~

所有绘图脚本按项目根目录定位输出路径，生成的 JPG 会写入 `figures/`。

## MATLAB 与 LaTeX

在 MATLAB 中将当前目录设为 `matlab/`，然后运行函数，例如：

~~~matlab
Figure_1_phase_plane
Figure_6_infection_cost_threshold
Figure_7_independent_control_nonuniqueness
~~~

报告使用 XeLaTeX 编译：

~~~bash
cd latex
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
~~~

## 关于感染成本阈值

报告对附加感染成本的阈值进行了独立核查，没有机械采用附件中的显示式。根据 HJB 条件，临界值应由安全集上相关比值的上确界取倒数得到。 `Figure_6`、Python 和 MATLAB 程序使用同一经推导、量纲和单调性检查后的分段公式。

## 建模边界

完整的闭式唯一性结论对应固定比例结构 `beta_2=q beta_1`。如果两个系数确实独立，则原有线性正部成本不足以排除零成本加速，不能直接移植单控制模型的唯一性定理。此时应明确控制范围和成本，并以状态约束最优控制条件验证结论。
