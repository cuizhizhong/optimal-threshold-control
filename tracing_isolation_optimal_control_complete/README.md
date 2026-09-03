# 跟踪隔离模型中双传播系数的最优控制与唯一性

本文件包研究

\[
\dot S=-\beta_1(t)SI,\qquad
\dot I=\beta_2(t)SI-\gamma I
\]

在

\[
\beta_1(t)=\frac{c(t)[p+(1-p)q(t)]}{N},\qquad
\beta_2(t)=\frac{pc(t)(1-q(t))}{N}
\]

下的医疗容量约束最优跟踪隔离问题。`c(t)` 为给定接触数函数，`q(t)∈[0,1]` 为跟踪隔离比例，`p` 为单次接触传播概率。完整理论、唯一性条件、常接触率解析几何和时变接触率正则化数值实验见根目录 PDF。

## 1. 文件结构

- `tracing_isolation_optimal_control.pdf`：已编译的最终中文报告，26 页。
- `latex/main.tex`：完整 LaTeX 主文件。
- `latex/references.bib`：BibTeX 文献库。
- `latex/main.bbl`：本次编译生成的参考文献表，便于无 BibTeX 环境直接复编。
- `python/Figure_1_*.py` 至 `python/Figure_10_*.py`：十个可分别启动的 Python 绘图程序。
- `python/common_tracing.py`：常接触率解析计算、轨道拼接和时变直接配置的公共模块。
- `python/generate_data.py`：数据总生成器。
- `matlab/Figure_1_*.m` 至 `matlab/Figure_10_*.m`：十个可分别启动的 MATLAB 程序。
- `figures/Figure_1_*.jpg` 至 `figures/Figure_10_*.jpg`：十幅 300 dpi JPG。
- `figures/contact_sheet.jpg`：十幅图的总览。
- `data/*.csv`：基准轨道、切换曲线、成本、敏感性、结构分区和时变优化数据。
- `validation/VALIDATION_CHECKLIST.md`：最终校验清单。
- `validation/`：PDF 预检、字体、渲染、数值残差、Python 运行和 MATLAB 静态检查记录。

## 2. Python 复现

建议 Python 3.10 或更高版本。

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

重新生成常接触率全部 CSV：

```bash
python python/generate_data.py
```

同时重新运行时变接触率下三组正则化直接配置：

```bash
python python/generate_data.py --recompute-tv
```

每幅图可独立启动，例如：

```bash
python python/Figure_1_phase_geometry.py
python python/Figure_4_uniqueness_cost.py
python python/Figure_10_time_varying_states.py
```

十个脚本均按自身文件位置解析根目录，因此可从任意工作目录启动。图 1--8 调用包内 `common_tracing.py`；图 9--10 读取包内时变优化 CSV。所有输出覆盖写入 `figures/`。

## 3. MATLAB 复现

建议 MATLAB R2020b 或更高版本；脚本使用局部函数、`readtable`、`yyaxis`、`xline` 和 300 dpi `print`。不需要专用工具箱。

在 MATLAB 命令窗口中可逐个运行：

```matlab
run('matlab/Figure_1_phase_geometry.m')
run('matlab/Figure_2_state_time_series.m')
% ...
run('matlab/Figure_10_time_varying_states.m')
```

图 1--5 的 MATLAB 程序各自包含所需解析函数；图 6--10 读取 `data/` 中已提供的 CSV。每个程序均把 JPG 写入 `figures/`。

本生成环境没有 MATLAB 或 Octave 可执行文件，因此十个 MATLAB 文件完成了逐文件的词法、括号、控制块、相对路径和输出文件名静态校验，但没有在 MATLAB 运行时执行。详见 `validation/matlab_static_check.txt`。

## 4. LaTeX 编译

需要 XeLaTeX、`ctex`、`natbib` 和常用数学/图形宏包。

```bash
cd latex
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main          # 若系统没有 bibtex，可用 bibtex8 main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

也可在包根目录执行：

```bash
bash build.sh
```

若希望同时重算时变接触率优化：

```bash
bash build.sh --recompute-tv
```

编译结果会复制到根目录 `tracing_isolation_optimal_control.pdf`。

## 5. 基准数值结果

参数为

\[
p=0.5,\quad c=2,\quad \gamma=0.3,\quad K=0.15,
\quad s_0=0.99,\quad i_0=0.01.
\]

主要结果：

- 自然传播峰值：`0.3418232594582696`；
- 首次到达容量的易感比例：`0.7775221610386437`；
- 容量边界转入完全跟踪的唯一切换值：`0.5476951354603352`；
- 解除隔离点：`(0.4516637906662894, 0.12108289006592277)`；
- 最小控制成本：`1.529511160151471`；
- 纯 filling-the-box 成本：`1.5783855039561376`；
- 成本节省：约 `3.0964769812%`。

解析成本与程序中闭式分段计算一致到机器精度；稠密时间网格积分误差约 `1.1e-5`。时变接触率正则化结果满足最大感染比例 `0.15000000000000005`，无隔离峰值约 `0.4599709187`。

## 6. 结论使用边界

常接触率下的几乎处处唯一性依赖报告中明确列出的横截性、端点唯一性和无正长度奇异弧条件；这些条件均可由给出的解析导数和一维根计算检验。对一般给定时变 `c(t)`，系数的代数形式本身不足以无条件推出唯一性；报告给出切换函数判据，并通过严格凸正则化得到唯一投影反馈和可复现的数值方案。
