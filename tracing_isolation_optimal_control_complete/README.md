# 跟踪隔离模型中双传播系数的最优控制与唯一性

## 项目简介

本项目研究一个由同一跟踪隔离策略驱动、但在易感者耗竭方程和感染者生成方程中产生两个不同传播系数的二维模型。使用人口比例 `s=S/N`、`i=I/N` 表示状态，模型为

~~~text
s' = -c(t) [p + (1-p) q(t)] s i
i' =  p c(t) [1 - q(t)] s i - gamma i
~~~

其中 `c(t)` 是接触率，`p` 是单次接触传播概率，`q(t)∈[0,1]` 是跟踪隔离比例，`gamma` 是恢复/移除率。感染比例受到医疗容量约束 `i(t)≤K`，线性控制成本为

~~~text
J(q) = integral p c(t) q(t) dt.
~~~

项目的核心问题是：在两个系数由同一个 `q(t)` 反向耦合时，什么时候需要控制，容量边界上如何控制，以及最优控制是否在几乎处处意义下唯一。

## 主要结论

### 常接触率 `c(t)=c`

当 `c` 为常数时，模型具有可解析的相平面几何。自然传播不变量为

~~~text
Phi(s,i) = i + s - h log(s),     h = gamma/(p c).
~~~

若自然传播峰值不超过 `K`，则最优控制是 `q*=0`，成本为零。若自然峰值超过容量，最优策略通常具有以下结构：

~~~text
q = 0  ->  q = q_B(s)  ->  q = 1  ->  q = 0
自然传播    容量边界控制       完全跟踪隔离   解除控制
~~~

容量边界上的唯一切向控制为 `q_B(s)=1-h/s`；内部线性成本使控制几乎处处只能取端点 `0` 或 `1`，中间值只在状态约束强制时出现。通过切换函数和一维端点成本，可以检验切换曲线与候选轨道的横截性，并在相应条件下得到几乎处处唯一性。

### 时变接触率

当 `c(t)` 给定且随时间变化时，固定相平面不变量和闭式切换曲线一般不再存在。项目给出时变 Hamilton–Jacobi 判据、容量边界可行集和直接配置数值算法。对线性成本，不能仅由系数的代数形式无条件推出唯一性；加入小的严格凸正则项后，可得到唯一的投影反馈控制。

## 基准结果

默认参数为 `p=0.5`、`c=2`、`gamma=0.3`、`K=0.15`、`s0=0.99`、`i0=0.01`。随包提供的 `data/numerical_summary.csv` 给出完整数值摘要，主要结果为：

| 量 | 数值 |
|---|---:|
| 自然传播峰值 | `0.3418232594582696` |
| 首次到达容量的易感比例 | `0.7775221610386437` |
| 切换到完全跟踪的 `s` | `0.5476951354603352` |
| 解除隔离点 | `(0.4516637906662894, 0.12108289006592277)` |
| 最小控制成本 | `1.529511160151471` |
| 纯容量填充成本 | `1.5783855039561376` |
| 相对节省 | 约 `3.0965%` |

## 项目框架

~~~text
tracing_isolation_optimal_control_complete/
├── latex/
│   ├── main.tex                 # 完整中文理论报告
│   ├── references.bib           # BibTeX 文献库
│   └── main.bbl                 # 编译生成的参考文献表
├── python/
│   ├── common_tracing.py        # 解析公式、轨道拼接和优化核心
│   ├── generate_data.py         # CSV 数据总生成器
│   └── Figure_*.py              # 10 个独立绘图脚本
├── matlab/
│   └── Figure_*.m               # 10 个对应 MATLAB 脚本
├── data/                        # 常接触率和时变接触率 CSV
├── figures/                     # 10 幅图及总览图
├── validation/                  # 数值、PDF、字体、日志和静态检查
├── tracing_isolation_optimal_control.pdf
├── requirements.txt
├── build.sh / build.bat
└── MANIFEST.txt
~~~

其中，`python/common_tracing.py` 是计算核心：它实现自然轨道、最大安全轨道、容量边界成本、完全跟踪弧、候选策略比较、切换曲线、最优轨迹模拟以及时变正则化优化。 `Figure_1`–`Figure_8` 主要展示常接触率解析结果，`Figure_9`–`Figure_10` 展示时变接触率下的正则化控制和状态约束。

## Python 复现

建议使用 Python 3.10 或更高版本：

~~~bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
~~~

重新生成常接触率数据：

~~~bash
python python/generate_data.py
~~~

同时重新计算时变接触率下的三组正则化解：

~~~bash
python python/generate_data.py --recompute-tv
~~~

独立生成图形，例如：

~~~bash
python python/Figure_1_phase_geometry.py
python python/Figure_4_uniqueness_cost.py
python python/Figure_10_time_varying_states.py
~~~

脚本按自身文件位置定位项目根目录，可从任意当前工作目录运行，输出会覆盖 `figures/` 中对应的 JPG 文件。

## MATLAB 与 LaTeX

建议 MATLAB R2020b 或更高版本。脚本可在 MATLAB 中逐个运行，例如：

~~~matlab
run('matlab/Figure_1_phase_geometry.m')
run('matlab/Figure_10_time_varying_states.m')
~~~

建议使用 XeLaTeX 编译报告：

~~~bash
cd latex
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
~~~

也可以在项目根目录运行 `bash build.sh`；Windows 用户可使用 `build.bat`。验证记录说明 Python 数据和图形已复现，MATLAB 文件完成了静态检查；当前环境没有执行 MATLAB 运行时。

## 适用边界

唯一性结论依赖报告中列出的横截性、端点唯一性和无正长度奇异弧等条件。对一般时变 `c(t)`，代数上的双系数结构本身不保证唯一性；正则化结果是一个稳定、可复现的近似控制框架，而不是对所有线性成本问题的无条件唯一性宣称。

