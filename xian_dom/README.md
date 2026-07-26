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
| `panels.py` | Panel A（`panels.py A`）；含求解器封装 `solve_threshold`/`solve_tdinn` |
| `compute_B.py` | Panel B 重算，产出 `panelB.pkl`（约 25 s） |
| `plot_B.py` | 从 `panelB.pkl` 快速绘 Panel B |
| `resolve_clr.py` | 清零弧（$t_{\rm end}^{\rm T}=45.27$ d 口径）逐点求根 |
| `arc_clr_45.27.csv` | 清零弧 28 点数据 |

## 运行环境

- conda env `thesis`（numpy / scipy / matplotlib）。
- `PYTHONPATH` 需含三个求解器目录：`xian_control_comparison/`、
  `.../threshold_landscape_analysis/`、`.../effective_population_sensitivity/`。
- 真实数据 `真实数据/Xianguankong.xlsx` 在仓库根，`xian_control_comparison.py` 按相对路径自动解析，无需额外配置。
- numpy 2.x：`panels.py` / `compute_B.py` 顶部已内置 `np.trapz = np.trapezoid` shim。

用 PowerShell 跑（Git Bash 会破坏 `;` 分隔的 `PYTHONPATH`）：

```powershell
Set-Location xian_dom
$R = "..\xian_control_comparison"
$env:PYTHONPATH = "$R;$R\threshold_landscape_analysis;$R\effective_population_sensitivity"
conda run --no-capture-output -n thesis python dom_pretty.py
conda run --no-capture-output -n thesis python panels.py A
conda run --no-capture-output -n thesis python compute_B.py
conda run --no-capture-output -n thesis python plot_B.py
```

**注意 `panels.py` 必须带参数 `A`。** 无参运行会连带执行一个遗留的 `panel_B()`，覆盖 `plot_B.py` 产出的真 Panel B。

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
