# xian_dom — §8 有效人口占优分析：绘图与求解脚本

产出主论文 `paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex` §8.7 的三张占优图：

- 图 20 `fig_dom_combined.pdf`：$(N_{\rm eff},\eta)$ 平面占优区域，(a) 直线族（强度量）/ (b) 弧线族（广延量）；
- 图 21 `fig_panel_A.pdf`：$\eta$ 杠杆（固定 $N_{\rm eff}=2\times10^4$，沿四条边界取 $\eta$）；
- 图 22 `fig_panel_B.pdf`：$N$ 杠杆（固定 $\eta=100$，六个 $N_{\rm eff}$）。

## 口径（重要）

TDINN 是**固定的现实参照**：已发生的现实结局，用固定的四个数
（$I_{\rm peak}^{\rm T}=151.90$、$J^{\rm T}=49.35$、$I_{t\rm cum}^{\rm T}=2096.76$、$t_{\rm end}^{\rm T}=45.27$ d），
不随 $N_{\rm eff}$ 重算。情景一阈值控制与常规控制是反事实，逐 $N_{\rm eff}$ 重解（各自重拟合 $I_0$）。
强度量（峰值、$J$、$\Delta t$）边界是直线；广延量（累计、清零时刻）带绝对尺度、边界是弧线。

## 文件

| 文件 | 作用 |
|---|---|
| `dom_pretty.py` | 图 20 合成图（自包含，只需 numpy/matplotlib） |
| `panels.py` | Panel A（直接 `python panels.py`）；含求解器封装 `solve_threshold`/`solve_tdinn` 与共享量 `N_OF`/`_envelope`（供 `compute_B` 导入） |
| `compute_B.py` | Panel B 重算，产出 `panelB.pkl`（约 25 s） |
| `plot_B.py` | 从 `panelB.pkl` 快速绘 Panel B |
| `resolve_clr.py` | 清零弧（$t_{\rm end}^{\rm T}=45.27$ d 口径）逐点求根 |
| `arc_clr_45.27.csv` | 清零弧 28 点数据 |

## 运行环境与运行方法

- conda env `thesis`（numpy / scipy / matplotlib / openpyxl）。
- 三个求解器模块目录（`xian_control_comparison/` 及其下 `threshold_landscape_analysis/`、
  `effective_population_sensitivity/`）由每个脚本头部自动加入 `sys.path`，**无需手动设 `PYTHONPATH`**。
- 真实数据 `真实数据/Xianguankong.xlsx` 在仓库根，`xian_control_comparison.py` 按相对路径自动解析，无需配置。
- numpy 2.x：`panels.py` / `compute_B.py` 顶部已内置 `np.trapz = np.trapezoid` shim。

因为不再依赖环境变量，**任何终端（PowerShell / Git Bash / cmd）或 VS Code 的“运行”按钮都能直接跑**
（VS Code 里把解释器选成 `thesis` 环境即可）。依次运行四个脚本重出三张图：

```bash
python dom_pretty.py     # 图 20（自包含，只需 numpy/matplotlib）
python panels.py         # 图 21 Panel A（不再需要 A 参数）
python compute_B.py      # 图 22 的重算 → panelB.pkl（约 25 s）
python plot_B.py         # 图 22 Panel B（读缓存，秒出）
```

用 conda 环境时在每行前加 `conda run -n thesis`。顺序上 `compute_B.py` 要在 `plot_B.py` 之前；
`dom_pretty.py`、`panels.py` 各自独立。也可一键运行本目录的 **`run_all.ps1`**（PowerShell：设好环境后自动跑完四步并把图复制到 `../figures/`）。

`resolve_clr.py` 是一次性求解器（把清零弧重算到 $t_{\rm end}^{\rm T}=45.27$ d，输出 `clr_4527.json`），平时不用跑；其结果即 `arc_clr_45.27.csv`、也已写入 `dom_pretty.py` 的弧线数组。

## 图去向与尺寸约束

- 三脚本把图写到 `xian_dom/dominance_panels/`；定稿时把三个 `.pdf` 复制到 `../figures/`
  （主论文 graphicspath 经 `../figures/` 解析）。
- 三图按 tight bbox 宽度 = **451.28 bp**（= 主论文 `\textwidth`，A4 减左右各 1 in）渲染，
  使 `\includegraphics[width=\textwidth]` 缩放为 1.0×。改 `figsize` 后**必须用 `pdfinfo` 复量**
  （因 `bbox_inches="tight"`，成图尺寸 ≠ `figsize`）。当前值：`dom_pretty` `(6.288, 2.925)`、
  `panels`/`plot_B` `(6.164, 5.459)`。
- Panel A 的 $\eta$ 直标垂直余量仅约 $0.027$ decade；调大字号或让 $\eta$ 变五位数会重叠。

## 数值锚点（对账用）

$N_{\rm clr}(100)=4601.9$、$N_{\rm cum}(100)=10105$、$N^\ast(45\text{d})=40377$、$N^\ast_\infty=91727$、
cum 弧穿成本线 $(11764,19.48)$、clr 弧端点 $(2096.76,27.89)$ 与 $(5914.3,151.90)$、
常规控制带 $N$ 区间 $[4602,87951]$。重跑后若与此不符，先查环境差异，勿擅改论文正文数值。
