# 情景一 $q_c(t)$ 拐点分析：计算、配图与修改记录

本目录承载主论文情景一阈值控制隔离律 $q_c(t)$ 拐点分析的计算代码与三张配图，并记录对论文的改动。

- **2026-07-21 第一轮**：补齐拐点位置/两端消失/曲率幅度三块，统一记号 $\qinf$。
- **2026-07-21 第二轮（定稿）**：按 `../ai_markdown/拐点/PLAN_inflection_FINAL.md` 纠错升级——引入相对位置 $\lambda$、重写「参数方向」、加参数分工表、修正 §4.4 误导措辞、三张图改期刊风。

---

## 1. 文件

| 文件 | 说明 |
|---|---|
| `inflection_analysis.py` | 核心计算（`solve/trajectory/curvature_factor/scan`）。含 $S_0>S_c$ 守卫与 $\lambda$ 字段 |
| `verify_anchors.py` | 数值锚点 + **方向表**复现校验（写进论文的每个数与每个方向都要过这里） |
| `fig_landscape4.py` | 图 1：4 行 × 2 列图谱 → `../figures/scenario1_inflection_landscape.pdf` |
| `fig_scan_t.py` | 图 2：横轴真实时间的低/中/高扫描 → `../figures/scenario1_inflection_scan_t.pdf` |
| `fig_diagnose.py` | 图 4：三面板诊断 → `../figures/scenario1_inflection_diagnose.pdf` |
| `inflection_scan_beta.csv` | 早期 $\beta$ 扫描输出（探索性记录） |

**图风格**：蓝色顺序色、serif（Times New Roman）+ `mathtext=stix`、英文轴标签、无子图标题、`frameon=False` 图例、去顶/右边框、输出 PDF。图注写死参数值，不用「基准」字样。

**运行**（Python 环境 `thesis`，中文输出需 UTF-8）：
```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 conda run --no-capture-output -n thesis python verify_anchors.py
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 conda run --no-capture-output -n thesis python fig_landscape4.py
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

**方向表（实算，定稿论文表 1 的依据）**：

| 参数 | $\lambda$ 方向 | $\lambda$ 端点 | $\Delta t$ 方向 | $\Delta t$ 端点 |
|---|---|---|---|---|
| $\beta$ | $+$ | 0.002 → 0.998 | $+$ | 4.15 → 6.45 |
| $q_0$ | $\pm$ | 0.445 → 0.859 | $-$ | 6.11 → 0.88 |
| $c_0$ | $+$ | 0.012 → 0.546 | $\pm$ | 7.18 → 4.40 |
| $\theta=\eta/N$ | $-$ | 0.470 → 0.458 | $-$ | 22.37 → 5.90 |

其余：$\Delta t(c_0)=7.40/5.90/4.60/3.22$（$c_0=6/10/15/25$）；$\eta/N$ 由 0.05 降到 0.005 时 $\Delta t$ 5.9→60.7 天、弦偏差 4.44%→4.17%；低 $\beta=0.10$ 背景下 $\lambda$ 随 $q_0$ 先增后减（0.229→0.246→0.117）。

> **PLAN_FINAL §1c 原表有 4 处符号错**，已按实算改正：$\qinf$ 行 $\beta$ 应为 $-$（$\partial\qinf/\partial\beta<0$）；$t_2$ 端行应为 $-,-$；$t_1$ 端行 $q_0$ 应为 $-$；$\Delta t$ 行 $q_0$ 应为 $-$、$c_0$ 应为 $\pm$。

---

## 3. 论文改动（`../paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex`）

**第一轮**：导言区 `\newcommand{\qinf}{q_{\mathrm{inf}}}`；定理加 `\label{thm:s1:inflection}`；`t_{inf}`→`t_{\mathrm{inf}}`；§4.2 末命名 $\qinf$ 并给存在等价式 `eq:s1:inflection-exist`；新增 §4.3、§4.4；§6 加诊断图；§8.2 $q^\star\to\qinf$、认领 $\beta_{\max}=0.261448$。

**第二轮（定稿）**：
- §4.3 加「相对位置」小段与 $\lambda$ 定义 `eq:s1:lambda`（$\lambda=0.458$）。
- §4.3「参数方向」**整段重写**：按前/后段对数因子分解逐条判方向。$\eta,c_0$ 引命题 `prop:s1:sensitivity`（$S^*_\eta<0$、$S^*_{c_0}>0$）为**可证单调**；$\beta$ 只写「数值上单调」（$S^*_\beta$ 未证）；$q_0$ 两通道反向、**一般不单调**。修掉原文三处问题：$q_0$ 被错说成经 $\qinf$ 通道、整段误标「数值观察」、未点明 $q_0$ 非单调。
- §4.3 加参数分工表 `tab:s1:inflection-roles`（符号见上）。
- §4.3 换图：图 1 改 4 行版并重写图注；图 2 由 $\beta$ 扫描 $q_c/q_c'$ 换成横轴真实时间的低/中/高扫描（`scenario1_inflection_scan_t.pdf`），图注写明**水平跨度是 $\Delta t$、左右位移来自 $t_1$ 不同**。
- §4.4 补 $q_c''$ 一致上界 `eq:s1:qcpp-bound`；把误导的「精确抵消…不改变形状」改为「时间尺度因子只决定横轴单位…沿天数轴拉宽，而非变直」；弦偏差定义**降为脚注**；**删除** c₀ 非单调表及其依托句。
- §6 图 4 改期刊风（内容不变）。

**编译**：`xelatex → biber → xelatex → xelatex`（有活引文），用 PowerShell 跑。已验证 0 error、0 undefined、0 overfull。见记忆 `draft-paper-compile`。

---

## 4. 遗留项

1. **`figures/neff_inflection_beta.pdf` 图内图例仍是 $q^\star$**（由 `../xian_control_comparison/effective_population_sensitivity/` 生成，论文用手动拷贝的副本）。正文与图注已注明 $q^\star\equiv\qinf$。要统一图内标签需改该模块脚本并同步其自带 note——独立小任务。
2. **$S^*_\beta$、$S^*_{q_0}$ 的符号未证**：命题 `prop:s1:sensitivity` 只覆盖 $\eta,c_0$。$\beta,q_0$ 两条方向目前以数值为准，若要写成命题需对 $S^*$ 的 Lambert 隐函数求偏导。
3. §4 小节编号：新增两小节后，Ṡ与$t_2$、清零时间、总累计分别为 §4.5/4.6/4.7（正文全用 `\ref`）。
