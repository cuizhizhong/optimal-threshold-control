# 情景一 $q_c(t)$ 拐点分析：计算、配图与修改记录

本目录承载主论文情景一阈值控制隔离律 $q_c(t)$ 拐点分析的计算代码与四张配图，并记录对论文的改动。

- **2026-07-21 第一轮**：补齐拐点位置/两端消失/曲率幅度三块，统一记号 $\qinf$。
- **2026-07-21 第二轮（定稿）**：按 `../ai_markdown/拐点/PLAN_inflection_FINAL.md` 纠错升级——引入相对位置 $\lambda$、重写「参数方向」、加参数分工表、修正 §4.4 误导措辞、三张图改期刊风。
- **2026-08-02 第三轮**：把四参数方向由数值扫描提升为解析偏导；新增启动点引理、相对位置命题和控制时长推论；加入 $q_0$ 驻点检测、解析差分校验及 $\lambda$ 四面板图。
- **2026-08-05 第四轮**：§4.3 加「操作性动机」段（$\lambda$ = 释放节奏的前重/后重偏向，弯曲幅度受 §4.4 上界 `eq:s1:qcpp-bound` 封顶、方向引 `prop:s1:lambda-sensitivity`，明确非严重度指标）。B/C 清理：$\qinf$ 定义去重、定理假设改「设…则…」、两方向表加统一引导句、定理证明标点统一、$\lambda$ 图注删不存在的空心三角、弦偏差数字去重。图调整：landscape 的 $q_0$ 扫到 0.42（露可行截断）、scan\_t 低/中/高取值重定、$\lambda$ 图删 t-exit 标注与底部状态带、各面板扫到 0、$q_0$ 面板只画 $\beta=0.155$ 不可行区。删图：移除 §9.2 的 `fig:neff_inflection`（$\qinf$–$\beta$ + 残差面板，学术论文不必展示差分精度），验证结论并入正文——连带解决原遗留项 1。

---

## 1. 文件

| 文件 | 说明 |
|---|---|
| `inflection_analysis.py` | 核心计算（`solve/trajectory/curvature_factor/scan`）及 `startup_sensitivities()`、`lambda_sensitivities()`、`find_q0_stationary_points()` |
| `verify_anchors.py` | 数值锚点、解析偏导中心差分、驻点两侧符号与既有曲率回归校验 |
| `fig_lambda_sensitivity.py` | $\lambda$ 四参数响应图 → `../figures/scenario1_inflection_lambda_sensitivity.pdf` |
| `fig_landscape4.py` | 4 行 × 2 列存在性与时长图谱 → `../figures/scenario1_inflection_landscape.pdf` |
| `fig_scan_t.py` | 横轴真实时间的低/中/高扫描 → `../figures/scenario1_inflection_scan_t.pdf` |
| `fig_diagnose.py` | 三面板曲率诊断 → `../figures/scenario1_inflection_diagnose.pdf` |
| `inflection_scan_beta.csv` | 早期 $\beta$ 扫描输出（探索性记录） |

**图风格**：蓝色顺序色、serif（Times New Roman）+ `mathtext=stix`、英文轴标签、无子图标题、`frameon=False` 图例、去顶/右边框、输出 PDF。图注写死参数值，不用「基准」字样。

**运行**（从项目根目录执行，Python 环境 `thesis`）：
```powershell
conda run --no-capture-output -n thesis python -B scenario1_inflection\verify_anchors.py
conda run --no-capture-output -n thesis python -B scenario1_inflection\fig_lambda_sensitivity.py
conda run --no-capture-output -n thesis python -B scenario1_inflection\fig_landscape4.py
```

---

## 2. 数值锚点（`verify_anchors.py` 全部通过）

$N=763,\ S_0=762,\ I_0=1,\ \gamma=0.3504,\ \beta=0.155,\ c_0=10,\ q_0=0.01526,\ \eta=0.05N$：
```
S*=708.347  S_c=175.160  q_max=0.7565  q_inf=0.40828
Δt=5.9026  前段=2.7013  后段=3.2012（和=Δt）  lam=0.4577
q_c'' 因子分解误差 <1e-12；|g|≤0.09623 于 x=1.268,4.732；弦偏差 4.44%
```
西安（$\beta=0.1498,\gamma=0.2953,c_0=12.8872,q_0=0.3230,N=13163000,\eta=0.002N,I_0=0.001007$）：
$\qinf=0.4119$、$q_{\max}=0.8454$、弦偏差 $9.59\%$。

**解析方向与差分校验**：

\[
S^*_\eta<0,\qquad S^*_{c_0}>0,\qquad
S^*_\beta>0,\qquad S^*_{q_0}<0,
\]
\[
\lambda_\eta<0,\qquad \lambda_{c_0}>0,\qquad
\lambda_\beta>0,
\]
而 $\lambda_{q_0}$ 的解析式含一正一负两个竞争项，一般不能统一定号。
控制时长满足 $\Delta t_\eta<0$、$\Delta t_\beta>0$、
$\Delta t_{q_0}<0$、$\Delta t_\theta<0$；$\Delta t_{c_0}$ 由正文的
$\Theta$ 判据确定。`verify_anchors.py` 使用自适应中心差分逐项核对上述解析偏导，
并在 `status=="ok"`、`has_inflection==False` 的点确认 $S^*$ 偏导仍可计算。

在 $q_0\in[0,0.39]$、2001 点扫描下检测到的变号驻点根为：

| $\beta$ | 检测根 $q_0^\dagger$ | 根左侧 $\lambda_{q_0}$ | 根右侧 $\lambda_{q_0}$ |
|---:|---:|---:|---:|
| 0.10 | 0.0736525 | 正 | 负 |
| 0.12 | 0.1969606 | 正 | 负 |
| 0.155 | 0.3890712 | 正 | 负 |

残差阈值为 $10^{-7}$ 时未检测到不变号的近零候选点。变号区间以 `brentq`
精化，未变号的残差绝对值局部极小点以 `minimize_scalar` 检查；该搜索不构成
驻点存在性、唯一性或完备性的证明。既有网格方向分类仅保留为数值回归检查，
不再作为解析方向的依据。

其余回归锚点：$\Delta t(c_0)=7.40/5.90/4.60/3.22$（$c_0=6/10/15/25$）；
$\eta/N$ 由 0.05 降到 0.005 时 $\Delta t$ 5.9→60.7 天、弦偏差 4.44%→4.17%。

---

## 3. 论文改动（`../paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex`）

**第一轮**：导言区 `\newcommand{\qinf}{q_{\mathrm{inf}}}`；定理加 `\label{thm:s1:inflection}`；`t_{inf}`→`t_{\mathrm{inf}}`；§4.2 末命名 $\qinf$ 并给存在等价式 `eq:s1:inflection-exist`；新增 §4.3、§4.4；§6 加诊断图；§8.2 $q^\star\to\qinf$、认领 $\beta_{\max}=0.261448$。

**第二轮（定稿）**：
- §4.3 加「相对位置」小段与 $\lambda$ 定义 `eq:s1:lambda`（$\lambda=0.458$）。
- §4.3「参数方向」按前/后段对数因子分解逐条整理，并区分可证方向与当时的数值观察；第三轮已用四参数解析偏导整体替代该口径。
- §4.3 加参数分工表 `tab:s1:inflection-roles`（符号见上）。
- §4.3 换图：图 1 改 4 行版并重写图注；图 2 由 $\beta$ 扫描 $q_c/q_c'$ 换成横轴真实时间的低/中/高扫描（`scenario1_inflection_scan_t.pdf`），图注写明**水平跨度是 $\Delta t$、左右位移来自 $t_1$ 不同**。
- §4.4 补 $q_c''$ 一致上界 `eq:s1:qcpp-bound`；把误导的「精确抵消…不改变形状」改为「时间尺度因子只决定横轴单位…沿天数轴拉宽，而非变直」；弦偏差定义**降为脚注**；**删除** c₀ 非单调表及其依托句。
- §6 图 4 改期刊风（内容不变）。

**第三轮**：
- §4.3 按“启动点敏感性引理 → 相对位置敏感性命题 → 控制时长敏感性推论”重构；正文不引入长期代数缩写，$F$、$A,B$ 只在各自证明内临时使用。
- 给出 $S^*$ 对 $\eta,c_0,\beta,q_0$ 的严格偏导公式与符号；给出 $\lambda_\eta<0$、$\lambda_{c_0}>0$、$\lambda_\beta>0$ 的严格证明，以及 $\lambda_{q_0}$ 的竞争表达式和驻点充要方程。
- 将 $\Delta t$ 的四参数结论集中到 `cor:s1:duration-sensitivity`，原 `prop:s1:sensitivity` 收窄为启动时间与最大隔离率，不再重复证明 $S^*$ 或 $\Delta t$。
- 新增 `tab:s1:lambda-sensitivity` 与 `scenario1_inflection_lambda_sensitivity.pdf`；表格中的“移动”明确限定为归一化位置，真实时间图只解释绝对时刻。
- 数值部分只报告指定区间内检测到的变号根，并单列不变号近零候选点；正文与本 README 均不宣称根搜索完备。

**编译**：`xelatex → biber → xelatex → xelatex`（有活引文），用 PowerShell 跑。第三轮已完成四步编译与修改页渲染检查：主稿为 53 页，无编译错误、未定义引用、未解析文献或 `Overfull` 警告。

---

## 4. 遗留项

1. §4 小节编号：新增两小节后，Ṡ与$t_2$、清零时间、总累计分别为 §4.5/4.6/4.7（正文全用 `\ref`）。
2. `figures/neff_inflection_beta.pdf` 已成孤儿文件（第四轮删图后不再被论文引用）；由 `../xian_control_comparison/effective_population_sensitivity/` 生成，留着无害，如需清理可删。
3. A 类可选改进（未做）：把 §4.3 的引理/命题/推论**证明移附录**以给正文减重（结构取舍，待定）。
