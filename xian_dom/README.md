# xian_dom — §8 有效人口占优分析：绘图与求解脚本

产出主论文 `paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex` §8.7 的三张占优图及
Panel A 的三个附录案例：

- 图 20 `fig_dom_combined.pdf`：$(N_{\rm eff},\eta)$ 平面占优区域，(a) 直线族（强度量）/ (b) 弧线族（广延量）；
- 图 21 `fig_panel_A.pdf`：$\eta$ 杠杆（固定 $N_{\rm eff}=2\times10^4$，展示三条边界取值）；
- 图 22 `fig_panel_B.pdf`：$N$ 杠杆（固定 $\eta=100$，展示五个 $N_{\rm eff}$）。
- Panel A 另按 $N_{\rm eff}=10^4,\,2\times10^4,\,40377,\,91727$ 生成四个带后缀文件；
  N2e4 文件另以 `fig_panel_A.pdf` 作正文兼容别名，其余三张进入附录。

## 口径（重要）

TDINN 是**固定的现实参照**：已发生的现实结局，用固定的四个数
（$I_{\rm peak}^{\rm T}=151.90$、$J^{\rm T}=49.35$、$I_{t\rm cum}^{\rm T}=2096.76$、$t_{\rm end}^{\rm T}=45.27$ d），
不随 $N_{\rm eff}$ 重算。情景一阈值控制与常规控制是反事实，逐 $N_{\rm eff}$ 重解（各自重拟合 $I_0$）。
强度量（峰值、$J$、$\Delta t$）边界是直线；广延量（累计、清零时刻）带绝对尺度、边界是弧线。

## 文件

| 文件 | 作用 |
|---|---|
| `dom_pretty.py` | 图 20 合成图（自包含，只需 numpy/matplotlib） |
| `panels.py` | 四个 $N_{\rm eff}$ 的 Panel A（直接 `python panels.py`）；`python panels.py diag` 输出四案例数值诊断；含求解器封装 `solve_threshold`/`solve_tdinn` 与共享量 `N_OF`/`_envelope`（供 `compute_B` 导入） |
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
python panels.py         # 正文 Panel A + 三张附录案例（四个带 N 后缀文件）
python compute_B.py      # 图 22 的重算 → panelB.pkl（约 25 s）
python plot_B.py         # 图 22 Panel B（读缓存，秒出）
```

用 conda 环境时在每行前加 `conda run -n thesis`。顺序上 `compute_B.py` 要在 `plot_B.py` 之前；
`dom_pretty.py`、`panels.py` 各自独立。也可一键运行本目录的 **`run_all.ps1`**（PowerShell：设好环境后自动跑完四步并把图复制到 `../figures/`）。

`resolve_clr.py` 是一次性求解器（把清零弧重算到 $t_{\rm end}^{\rm T}=45.27$ d，输出 `clr_4527.json`），平时不用跑；其结果即 `arc_clr_45.27.csv`、也已写入 `dom_pretty.py` 的弧线数组。

## 图去向与尺寸约束

- 四脚本把图写到 `xian_dom/dominance_panels/`；定稿时把正文图与 Panel A 附录图复制到 `../figures/`
  （主论文 graphicspath 经 `../figures/` 解析）。`run_all.ps1` 已包含全部生成与复制步骤。
- 各图按 tight bbox 宽度 = **451.28 bp**（= 主论文 `\textwidth`，A4 减左右各 1 in）渲染，
  使 `\includegraphics[width=\textwidth]` 缩放为 1.0×。改 `figsize` 后**必须用 `pdfinfo` 复量**
  （因 `bbox_inches="tight"`，成图尺寸 ≠ `figsize`）。当前值：`dom_pretty` `(6.288, 2.925)`、
  `panels`/`plot_B` `(6.151, 5.459)`、`plot_B_decomp` `(6.151, 4.0)`。

## 图 23：图 22 的轨迹分解（`plot_B_decomp.py`）

正文图 23 `fig:panel_N_decomp`，紧接图 22 收在 §8.6。目的是把图 22 里被压成灰色包络的常规控制
与五条重合的阈值平台按 $N_{\rm eff}$ 拆开。`GridSpec(2,4)`：(a)--(d) 四格各对应一个
$N_{\rm eff}$，画该 $N$ 的阈值控制（实线）、同 $N$ 的常规控制（虚线）与固定 TDINN（黑实线）；
(e) 跨两列只画四条常规控制，(f) 跨两列只画四条阈值控制 + 唯一一条 TDINN。

- **只取四个角色** `clear / cum / dur45 / cost`，丢掉图 22 的 `dur150`（$N$=87944）。
- **口径守恒**：阈值轨迹与 $t_{\rm inf}$、TDINN 全部直接读 `panelB.pkl`，不重算；只有常规控制
  缓存里没有这四个 $N$（缓存只存 8 条几何间隔的包络成员），故用 `panels.prep(N)[2]` 现解——
  该调用与 `compute_B.py` 求包络成员时逐字相同。脚本末尾打印四行校验表
  （$t_1/t_{\rm inf}/t_2/\Delta t/t_{\rm clear}$ 与常规峰值、峰时、清零），供对账。
- **绝不 `import plot_B`**：它是脚本式模块，import 会立刻重绘并覆盖 `fig_panel_B.pdf`。
  `threshold_q_parts` 与 `COL/ETA/IPEAK_T/Q0/ALPHA/ROLE_LW` 因此是复制过去的。
- **横轴逐格自适应**（定版决策）：`xmax = 1.05 ×` 该格实际画到的最晚清零时刻，六格不共用。
  好处是 (a)/(b) 的三条线分得开；**代价是第一排看不出平台时长随 $N$ 从 6.3 d 涨到 102.8 d**，
  该数字由正文文字给出，图内只有共用横轴的 (f) 能直读。曾比较过的另两种横轴口径
  （六格共用、仅 (e) 放大）保留在脚本末尾的注释里。
- **图内不加图题、不加图例**，只有 (a)--(f) 角标；面板与线型的识别信息全部由图注承担，
  绘制约定沿用图 22 的图注（§8 现行约定：图注只留识别信息，分析进正文）。
- 图 20--22 的四个共享角色仍定义为随 $\eta$ 加深的顺序蓝：
  dur150 `#6BADD7`、cost `#206FB6`、dur45 `#073068`、interior `#084a91`；
  为简化定稿图，图 20--22 当前只展示 dur150、cost、dur45，interior 数值角色与颜色定义保留，
  但不绘制轨迹、图例、inset 柱或占优图采样点。
  清零边界使用暖灰棕 `#9a6b5a`（曲线与采样标记 `alpha=0.85`），累计边界使用蓝青
  `#238b8e`。图 20 的清零内区与累计外环分别使用浅暖灰棕 `#E7DDD8` 和浅蓝青
  `#D7EBE9`；其他约束线与参照线颜色不变。
- Panel A 不再在 $I(t)$ 平台转角处直接标 $\eta$；两面板均按
  dur150 $\to$ cost $\to$ dur45（$\eta$ 升序）绘制。
  图 21、22 的彩色策略轨迹统一使用实线，以颜色和空间位置区分角色；彩色策略使用 `lw=1.6`。图 20 仍保留边界图自身的
  实线/虚线/点划线约定。
  两个 Panel 的 $I(t)$ 与 $q_c(t)$ 均按 $t_{\rm clear}$ 从长到短叠绘，使后画的短清零
  轨迹在共同平台或 $q_0$ 重合段上优先可见；图例仍按原有语义顺序排列，不随 painter order 改变。
  Panel A 的 $I(t)$ 平台以同色实心圆标出 $q_c(t)$ 拐点时刻的投影 $(t_{\rm inf},\eta)$；
  该点不是 $I(t)$ 自身拐点。四案例的绝对 $t_{\rm inf}$ 随逐 $N$ 重拟合的 $t_1$ 平移，
  但平台内相对位置 $\lambda\approx0.861$ 与各边界的 $t_2-t_{\rm inf}$ 保持不变。
  图 21、22 的 $I_{\rm peak}^{\rm T}$ 参照统一为红色虚线
  `color="#a50518f4", lw=1.4, ls="--", alpha=0.8`；routine 轨迹统一为灰色虚线
  `color="#8a8a8a", lw=1.4, ls="--", alpha=0.9`。Panel B 的灰色包络填色与上下边界
  保持原样，只有包络内的代表性 routine 轨迹采用上述线型。
  Panel A 的面板 (b) 右上角用从零起算的内嵌柱图比较三条阈值曲线在动态清零时的
  总累计感染 $I_{t_{\rm cum}}$，并以 $I_{t_{\rm cum}}^{\rm T}=2096.76$ 虚线作为固定
  TDINN 现实参照。
  四案例的 $I(t)$ 上限与 inset 上限均按各自量级自适应，跨图比较应读取刻度和柱顶数值。
- 图 21、22 的每条 $q_c(t)$ 均以角色色展示完整三阶段轨迹：控制前和 $t_2$ 后直到
  自身动态清零的 $q_0$ 阶段为彩色实线，$t_1$ 处从 $q_0$ 到 $q_c(t_1^+)$ 的瞬时
  跳跃为同色竖直虚线，$t_1\leq t\leq t_2$ 的阈值控制段为彩色实线。绘制顺序按
  $t_{\rm clear}$ 从长到短，使后画的短清零轨迹覆盖重合段、其端点优先可见；每条曲线在
  $q_0$ 上的同色短竖线标出自身动态清零时刻。图 22
  直接从现有 `panelB.pkl` 恢复 $t_1,t_2,t_{\rm clear}$，无需重算缓存。
  Panel B 的面板 (b) 右上角同样内嵌到清零总累计感染柱图，五柱按
  `clear → cumulative → dur45 → cost → dur150`（即 $N_{\rm eff}$ 升序）排列，
  横轴以 $10^3$ 人为单位。柱值由总累计感染的三段解析式结合缓存中的
  $q_c(t_1^+)$、$t_2$ 和控制后 $I(t)$ 尾段恢复，不修改 `panelB.pkl`。

## 数值锚点（对账用）

以下数值均属全节单一口径 **固定绝对初值 $I_0=1.00663\times10^{-3}$ 人**（跨 $N_{\rm eff}$ 不重拟合，
$i_0=I_0/N$，见 `caliber.py` 的 `I0_ABS`）；换口径后清零弧会整体移动（旧固定 $i_0$ 口径下最大值仅 2439）。

$N_{\rm clr}(100)=3969.7$（$\approx3.97\times10^{3}$，`caliber` 直接求根；16 点弧线性插值为 3966）、
$N_{\rm cum}(100)=10105$（`dom_pretty` 弧线性插值；`caliber` 直接求根为 10102.3，正文图 22 用后者）、
$N^\ast(45\text{d})=40377$、$N^\ast_\infty=91727$、
cum 弧穿成本线 $(11762,19.48)$（显示用 PCHIP 弧与成本线的交点；对同一 16 点作线性插值则得 11764）、
clr 弧端点 $(865.86,10)$ 与 $(5165.70,151.90)$、
常规控制带 $N$ 区间 $[3970,87944]$。重跑后若与此不符，先查环境差异，勿擅改论文正文数值。
