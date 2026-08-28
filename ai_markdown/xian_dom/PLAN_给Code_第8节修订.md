# 论文 §8 修订 —— 给 Code 的完整执行计划

本文件是本次任务的唯一指令来源。按 **P0 → P9** 顺序执行。

---

## A. 目标与环境

**目标文件**：`paper_elegantpaper_relayout/flatten_curve_analysis_cn.tex`（1871 行）

**三个必须注意的技术细节**：

1. **该文件是 CRLF 换行**（1870 行全部 `\r\n`），UTF-8 编码。做精确字符串替换时，
   `old_str` 若跨行，必须匹配 `\r\n` 而非 `\n`，否则替换会失败。
2. **行号会随改动下移。** 本文件给出的行号是修改前的位置，仅供定位；
   **每处改动一律以 `old_str` 原文比对为准，不要认死行号。**
3. 编译在论文目录下进行，改动图/表/引用/标签/公式编号后需编译两遍：
   ```powershell
   cd paper_elegantpaper_relayout
   xelatex -interaction=nonstopmode flatten_curve_analysis_cn.tex
   xelatex -interaction=nonstopmode flatten_curve_analysis_cn.tex
   ```

**写作口径**：遵守根目录 `AGENTS.md` —— 研究笔记风格、条件性比较、
不写"已证明阈值控制更优"、统一使用「情景一阈值控制／TDINN控制／常规控制」。
涉及 `xian_control_comparison/` 时另遵守该子目录的 `AGENTS.md`。

---

## B. 交付文件清单与去向

| 文件 | 放到哪里 / 做什么 |
|---|---|
| `PLAN_给Code_第8节修订.md` | 本文件，指令 |
| `panel_captions_draft.tex` | 图注素材，内容抄进 P5-b；文件本身不入库 |
| `figures/fig_dom_combined.pdf` | → `paper_elegantpaper_relayout/figures/` |
| `figures/fig_panel_A.pdf` | → `paper_elegantpaper_relayout/figures/` |
| `figures/fig_panel_B.pdf` | → `paper_elegantpaper_relayout/figures/` |
| `figures/*.png`（3 个） | 仅供人眼预览，**不需要入库** |
| `code/dom_pretty.py` | 覆盖仓库同名文件 |
| `code/panels.py` | 覆盖仓库同名文件 |
| `code/compute_B.py` | 覆盖仓库同名文件 |
| `code/plot_B.py` | 覆盖仓库同名文件 |
| `code/resolve_clr.py` | 新增（clr 弧求解器，本次重算用） |
| `arc_clr_45.27.csv` | 新增，替代旧 `arc_data.csv` 的 clr 部分 |

**重跑绘图脚本的环境**（若需要重出图）：`pkg/` 平铺放四个求解器模块
（`threshold_landscape_analysis` / `xian_control_comparison` /
`effective_population_sensitivity` / `plot_eta_80_100_150_inflection`），
`真实数据/Xianguankong.xlsx` 放在 `pkg` 的**父目录**。numpy 2.x 需在脚本顶部加
`if not hasattr(np,"trapz"): np.trapz = np.trapezoid`。有真 scipy 时不需要 `_shim`。

---

## C. 改动总览

| 编号 | 内容 | 类型 |
|---|---|---|
| P0 | 给 $t_{\rm end}$ 定理补 `\label`（**必须最先做**） | .tex |
| P1 | §8.4 新增清零占优推论 `cor:clr` + 有效池下界 | .tex |
| P2 | 改写 TDINN 基准段（口径声明） | .tex |
| P3 | §8.6 局限与口径重写 | .tex |
| P4 | §8.5 西安实例数值更新（含 3 处订正） | .tex |
| P5 | §8.7 正文重写 + 换成三张新图 | .tex |
| P6 | §9 讨论与局限起草 | .tex |
| P7 | 记号统一 `q^\star \to q_{\rm inf}` | .py |
| P8 | 仓库清理：两个过期文件 | 文件 |
| P9 | 重写 `README_接续上下文.md` | .md |

---

## 0. 本次修订的核心变化（先读，决定了后面所有措辞）

**TDINN 基准的口径被明确为"固定的现实参照尺子"。**

TDINN 控制是**已经发生**的事：它在西安全市人口口径下拟合到真实日报数据，
产出 $I_{\rm peak}^{\rm T}=151.90$、$J^{\rm T}=49.35$、$I_{t\rm cum}^{\rm T}=2096.76$、
$t_{\rm end}^{\rm T}=45.27$ d。这四个数就是现实结局，是一把尺子，唯一且不随 $N_{\rm eff}$ 变。

情景一阈值控制与常规控制都**没有发生**，是反事实，必须在各自的 $N_{\rm eff}$ 上求解。

一句话规则：**发生过的事用一个固定的数，没发生过的事随 $N$ 变。**

> 原稿 §8 开头"逐 $N$ 只重拟合 $I_0$ 时其绝对轨迹近似不变"这句话**在数值上不成立**
> （见 P2 的漂移表），必须改写。改写方向不是修补这个近似，而是换成上面的口径声明——
> 我们本来就不需要那个近似。

---

## P0. 前置：补 `\label`（必须最先做，后续要引用）

**位置**：第 664 行，`\subsection{情景一实现动态清零所需时间$t_{end}$}` 下面的定理。

```
old_str:
\begin{theorem}
    对于系统\eqref{eq:s1:dynamics},实现动态清零目标所需时间由下式给出

new_str:
\begin{theorem}\label{thm:s1:tend}
    对于系统\eqref{eq:s1:dynamics},实现动态清零目标所需时间由下式给出
```

理由：P1 新增的清零占优推论要引用它。该定理当前无 `\label`，无法引用。

---

## P1. §8.4 新增清零时间占优推论

**位置**：第 1781 行 `\end{corollaryn}`（`cor:cum` 结尾）之后、
第 1783 行 `\subsection{西安参数下的实例}` 之前，插入两块内容。

### P1-a 先给 `cor:cum` 补一个有效池下界的注记

现有 `cor:cum`（1768–1781 行）定义 $N^\ast_{\rm cum}$，但没说 $N$ 小到一定程度时该约束会
平凡成立。**在 `\end{corollaryn}` 前插入**：

```latex
注意 $h<1$，故当 $N<I_{t\rm cum}^{\rm T}$ 时 $N h<N<I_{t\rm cum}^{\rm T}$ 自动成立：
此时"累计不劣"只是有效池装不下这么多人所致的算术必然，与控制优劣无关。
因此下文一律附加\emph{有效池下界}
\begin{equation}
  N\ \ge\ I_{t\rm cum}^{\rm T},
  \label{eq:dom:Nfloor}
\end{equation}
即有效混合池至少要容纳真实疫情的总累计感染；低于该界的比较不具信息量（见第~\ref{sec:dom:limits}~节）。
```

> 注：`\label{sec:dom:limits}` 需在 P3 给 §8.6 补上。

### P1-b 新增 `cor:clr`

```latex
\begin{corollaryn}[纳入清零时间的收缩]\label{cor:clr}
情景一到动态清零的时刻 $t_{\rm end}$ 由定理~\ref{thm:s1:tend} 给出。与累计不同，
$t_{\rm end}$ 不是 $\theta$ 的函数：平台段贴边维持使 $S$ 的消耗速率正比于 $\eta$，
而退出段经 $S_{\rm end}$（式~\eqref{eq:s1:Send}，清零判据 $I=1$ 即 $i=1/N$）带绝对尺度，
故 $t_{\rm end}=t_{\rm end}(\theta,N)$，在固定 $\theta$ 下随 $N$ 递增。若再要求
\emph{(v)} $t_{\rm end}^{\rm thr}\le t_{\rm end}^{\rm T}$，
则在占优带内该约束给出一条 $(N,\eta)$ 平面上的曲线边界
\begin{equation}
  t_{\rm end}\big(\eta/N,\,N\big)=t_{\rm end}^{\rm T},
  \label{eq:dom:clrarc}
\end{equation}
其占优侧为小 $N$ 一侧；记其与给定 $\eta$ 的交点为 $N_{\rm clr}(\eta)$。由式~\eqref{eq:dom:Nfloor}，
有信息量的区间为 $N\in[\,I_{t\rm cum}^{\rm T},\,N_{\rm clr}(\eta)\,]$。数值上该区间远小于
$\mathcal{W}_{\rm pcd}$，也小于累计约束给出的区间（第~\ref{sec:dom:xian}~节）。
\end{corollaryn}

\begin{remark}[强度量与广延量的二分]\label{rem:dom:dichotomy}
命题~\ref{prop:dom:region} 的三个指标（峰值、成本 $J$、控制时长 $\Delta t$）由
引理~\ref{lem:dom:scaling} 只经 $\theta=\eta/N$ 进入，故在 $(N,\eta)$ 双对数平面上其边界
是\emph{直线}（水平线或斜率 $1$ 的射线），占优与否与池规模无关。累计 $I_{t\rm cum}$ 与
清零时刻 $t_{\rm end}$ 则带绝对尺度，边界是\emph{弧线}，占优只在小池成立。这一二分是
第~\ref{sec:dom:figure}~节两个面板的组织原则：面板 (a) 画直线族，面板 (b) 画弧线族。
\end{remark}
```

> **口径说明（给 Code 的背景，不写进论文）**：把清零写成推论，前提正是第 0 节确立的
> "TDINN 是固定尺子"。若改用"同一 $N$ 上两策略对打"的口径，该推论不成立——
> 同规模池上 TDINN 清零更快。这一点已在 P3 局限 (c) 中如实交代。

---

## P2. 改写 TDINN 基准段（§8 开头）

**位置**：第 1632–1636 行，`\paragraph{TDINN 基准（绝对常数）.}` 整段。

```
old_str:
\paragraph{TDINN 基准（绝对常数）.}
TDINN 控制使用固定时间函数 $c_{\rm TDINN}(t),q_{\rm TDINN}(t)$，拟合到固定绝对日报数据；
逐 $N$ 只重拟合 $I_0$ 时其绝对轨迹近似不变。故其社区峰值 $I_{\rm peak}^{\rm T}$、二次加权成本
$J^{\rm T}$（$w_c=1,w_q=2$）与总累计感染 $I_{t\rm cum}^{\rm T}$ 在本节中作为不依赖 $N$ 的常数处理
（该近似需数值复核，见局限）。

new_str:
\paragraph{TDINN 基准（现实参照）.}
TDINN 控制是\emph{已经发生}的控制：其时间函数 $c_{\rm TDINN}(t),q_{\rm TDINN}(t)$ 与初值
$I_0$ 在西安全市人口口径下拟合到同一份真实日报数据，给出社区峰值
$I_{\rm peak}^{\rm T}=151.90$、二次加权成本 $J^{\rm T}=49.35$（$w_c=1,w_q=2$）、
总累计感染 $I_{t\rm cum}^{\rm T}=2096.76$ 与清零时刻 $t_{\rm end}^{\rm T}=45.27$ d。
本节把这四个数作为\emph{固定的现实参照}，不随 $N_{\rm eff}$ 重算：它们刻画的是这场疫情
实际的结局，唯一且不依赖于我们如何重新划定有效混合池。相对地，情景一阈值控制与
常规控制都是\emph{未发生}的反事实，必须在各自的 $N_{\rm eff}$ 上求解（逐 $N$ 重拟合 $I_0$，
见第~\ref{sec:scaling}~节）。
故本节的占优是"反事实策略在规模 $N_{\rm eff}$ 的控制单元上，能否达到不劣于现实结局的指标"，
而非"同一池上两种策略对打"；二者的区别与由此产生的口径限制见第~\ref{sec:dom:limits}~节。
```

---

## P3. §8.6 局限与口径：重写

**位置**：第 1818–1830 行整个 `\subsection{局限与口径}`。

改动要点：
- 加 `\label{sec:dom:limits}`（P1、P2 都要引用）
- **删掉**原 (2) 的"漂移约 9\%"说法 —— 该数字只在 $N=5\times10^4$ 成立，图覆盖的
  $N\sim10^3$–$10^4$ 区间漂移达 50–114\%，原文会误导
- 新增三条：跨尺度反事实口径、小 $N$ 拟合退化、有效池下界与域墙
- 原 (4) 说 $N^\ast_{\rm cum}$ "属外推，需另行数值核算" —— 本次已核算，改为报告结果

```latex
\subsection{局限与口径}
\label{sec:dom:limits}
(1) 占优结论依赖所选指标集：情景一在总累计上仅当 $N\lesssim N^\ast_{\rm cum}$、在清零时刻上仅当
$N\lesssim N_{\rm clr}$ 才不劣；两者一律取到清零口径，与 $I_{t\rm cum}^{\rm T},t_{\rm end}^{\rm T}$
的积分／终止终点一致。

(2) \textbf{比较是跨尺度的反事实，不是同池对打。} TDINN 基准锁定在全市口径下的现实结局
（第~\ref{sec:dominance}~节开头），而阈值控制在规模 $N_{\rm eff}$ 的池上求解。若改问"同一
$N_{\rm eff}$ 上两策略孰优"，需把 TDINN 控制函数施加到该池并重解：数值上其绝对轨迹
\emph{并不}保持不变，例如逐 $N$ 重拟合 $I_0$ 后
\[
\begin{array}{lcccc}
N_{\rm eff} & I_{\rm peak}^{\rm T} & J^{\rm T} & I_{t\rm cum}^{\rm T} & t_{\rm end}^{\rm T}\\[2pt]
1.2\times10^{3} & 103.2 & 9.5 & 375 & 25.4\\
5.8\times10^{3} & 190.4 & 29.9 & 1196 & 36.8\\
1.0\times10^{4} & 201.8 & 36.9 & 1597 & 39.9\\
8.8\times10^{4} & 160.0 & 48.1 & 2071 & 44.8\\
1.316\times10^{7} & 151.9 & 49.4 & 2097 & 45.3
\end{array}
\]
在 $N\sim10^3$–$10^4$ 区间偏离全市值达 $50\%$–$114\%$。因此本节的占优\emph{不能}被读成
"同规模池上阈值控制优于 TDINN"；在同池口径下，清零时刻一项的结论实际相反
（该池上的 TDINN 清零更快）。两种口径回答的是不同问题，本节采用前者，
因为 TDINN 的现实结局是唯一确定的、可作为参照的量。

(3) \textbf{有效人口重解释在小 $N$ 端已无法保持对数据的拟合。} 逐 $N$ 只有 $I_0$ 一个自由参数，
其拟合残差随 $N$ 减小而显著退化（$\mathrm{rmse}$：全市 $9.43$、$N=10^4$ 时 $30.9$、
$N=5.8\times10^3$ 时 $39.4$、$N\approx2.1\times10^3$ 时 $44.3$，即全市的 $3.3$–$4.7$ 倍），
且所需 $I_0$ 由 $10^{-3}$ 升到 $10^{-1}$ 量级。故 $N\lesssim10^4$ 的反事实轨迹应理解为结构性推演，
而非标定过的预测；而两条弧线给出的占优区恰好落在该区间，结论的可信度相应打折。
若后续对每个 $N_{\rm eff}$ 重新拟合全部控制参数（而非只拟合 $I_0$），该退化可望消除。

(4) \textbf{有效池下界与触发域墙。} 由式~\eqref{eq:dom:Nfloor}，$N<I_{t\rm cum}^{\rm T}=2096.76$ 时
广延量比较平凡成立，不具信息量；故清零边界的有信息区间为 $N\in[2.10\times10^{3},\,N_{\rm clr}]$。
另有一重更弱的限制：逐 $N$ 拟合的 $I_0$ 随 $N$ 减小而增大，在 $N\approx1.12\times10^{3}$ 处越过 $1$，
此时"首例触发控制"的前提失效。当前参数下前者先绑定，域墙不起作用。

(5) 命题在归一化初值固定口径下严格；逐 $N$ 重拟合绝对 $I_0$ 时 $i_0=I_0/N$ 随 $N$ 变，
$t_1$ 轻微漂移，"$\Delta t,J$ 只依赖 $\theta$"降为数值近似（见第~\ref{sec:scaling}~节）。
量级上，$\theta=0.002$ 处 $J$ 由全市的 $40.71$ 变为 $N=5\times10^{4}$ 的 $40.25$（约 $1.3\%$）；
$\theta_{\rm cost}$ 本身也带同量级的 $N$ 依赖（在 $N=2\times10^{4}$ 上反查得 $J=49.12$ 而非 $49.35$）。

(6) 小 $N$ 的物理实现分两类（自然有界单元 vs 封控造池），后者靠空间分区/封控实现，该分区本身
即一种接触控制、成本未计入 $J$；第~\ref{sec:dom:xian}~节的"指标依赖性与物理口径"注记已分层讨论。

(7) $\Delta t$ 有界但可长达数十至逾百天，"可接受"由政策变量 $T_{\max}$ 编码；
图~\ref{fig:dom} (a) 的阴影楔形对应 $T_{\max}\to\infty$（成本封顶）口径，
有限 $T_{\max}$ 的边界见同图两条时长线。
```

---

## P4. §8.5 西安实例：数值更新

**位置**：第 1783–1801 行。加 `\label{sec:dom:xian}`（P3 引用）。

### P4-a 阈值数值块（1787–1797 行）

```
old_str:
\[
  \theta_{\rm cost}\approx1.66\times10^{-3},\qquad
  \theta_{\rm dur}(90\text{d})\approx1.89\times10^{-3},
\]
\[
  N^\ast(60\text{d})\approx5.4\times10^{4},\quad
  N^\ast(90\text{d})\approx8.0\times10^{4},\quad
  N^\ast_\infty\approx9.2\times10^{4},\quad
  N^\ast_{\rm cum}\approx1.17\times10^{4}.
\]

new_str:
\[
  \theta_{\rm int}\approx5.612\times10^{-3},\quad
  \theta_{\rm dur}(45\text{d})\approx3.762\times10^{-3},\quad
  \theta_{\rm dur}(90\text{d})\approx1.891\times10^{-3},
\]
\[
  \theta_{\rm cost}\approx1.656\times10^{-3},\quad
  \theta_{\rm dur}(150\text{d})\approx1.137\times10^{-3},
\]
其中 $\theta_{\rm int}$ 对应 $\Delta t=30$ d，作为占优带内部的参照。相应的临界有效人口
（$N^\ast=I_{\rm peak}^{\rm T}/\max(\theta_{\rm cost},\theta_{\rm dur})$）为
\[
  N^\ast(45\text{d})\approx4.04\times10^{4},\quad
  N^\ast(60\text{d})\approx5.4\times10^{4},\quad
  N^\ast(90\text{d})\approx8.03\times10^{4},\quad
  N^\ast_\infty\approx9.17\times10^{4}.
\]
由 $\theta_{\rm dur}(T)\,T\approx0.170$ 近似为常数，$\theta_{\rm dur}=\theta_{\rm cost}$ 发生在
$T_{\max}\approx103$ d：$T_{\max}$ 大于该值时成本约束绑定（$N^\ast=N^\ast_\infty$），
小于该值时时长约束绑定。
```

### P4-b 两条弧线的数值（接在 P4-a 之后新增）

```latex
两条广延量边界（推论~\ref{cor:cum}、\ref{cor:clr}）由求解器逐点求根得到，均为微弯弧线而非竖直线：
\begin{itemize}
  \item \textbf{累计边界} $N\,h(\theta,N)=I_{t\rm cum}^{\rm T}$：自 $(N,\eta)=(9471,\,151.90)$ 延伸到
  $(12177,\,10)$，$\eta=100$ 处 $N_{\rm cum}\approx1.011\times10^{4}$。沿弧 $h$ 由 $0.172$ 变到 $0.221$，
  故 $h\approx\text{const}$ 的竖直近似 $N\lesssim N^\ast_{\rm cum}\approx1.17\times10^{4}$ 只是其粗化。
  该弧在 $(N,\eta)\approx(11764,\,19.48)$ 穿出成本线；穿出后等值线继续存在，但 $\mathcal{W}_{\rm cum}$
  的实际边界在该处已改由成本线给出。
  \item \textbf{清零边界} $t_{\rm end}=t_{\rm end}^{\rm T}$：在有效池下界~\eqref{eq:dom:Nfloor} 之上，
  自 $(2096.76,\,27.89)$ 延伸到 $(5914.3,\,151.90)$，$\eta=100$ 处 $N_{\rm clr}\approx4.60\times10^{3}$。
  即清零约束把占优区进一步压到 $N\lesssim5.9\times10^{3}$，比累计约束更紧。
\end{itemize}
```

### P4-c 定位点数值订正（1799–1801 行）

原文 "$J=40.77$" 是全市 $\theta=0.002$ 的值，在 $(5\times10^4,100)$ 处实算为 $40.25$。

```
old_str:
命题~\ref{prop:dom:region} 的占优带内：峰值 $100<151.90$、$J=40.77<49.35$、$\Delta t=85.07$ 天；但其
到清零累计 $Nh\approx9.0\times10^{3}>\bar I_{t\rm cum}^{\rm T}$，不满足 (iv)，与推论~\ref{cor:cum} 一致。

new_str:
命题~\ref{prop:dom:region} 的占优带内（取 $T_{\max}=150$ d）：峰值 $100<151.90$、
$J=40.25<49.35$、$\Delta t=85.07$ 天；但其到清零累计 $Nh\approx9.03\times10^{3}>\bar I_{t\rm cum}^{\rm T}$
且清零 $t_{\rm end}\approx176$ d $>45.27$ d，(iv)(v) 均不满足，与推论~\ref{cor:cum}、\ref{cor:clr} 一致。
（第~\ref{sec:xian}~节报的 $J\approx40.77$ 是全市口径同 $\theta$ 的值；二者约 $1.3\%$ 的差异
来自逐 $N$ 重拟合 $I_0$，见第~\ref{sec:dom:limits}~节 (5)。）
```

---

## P5. §8.7 占优区域图的构造：重写 + 换图

**位置**：第 1832–1858 行（含 `\subsection{占优区域图的构造}` 与 `figure` 环境）。

### P5-a 正文（1835–1849 行）

保留原有四条直线的公式块（1837–1842 行）不动，其后的段落改写：

```
old_str:
占优楔形
$\mathcal{W}_{\rm pcd}=\{(N,\eta):\max(\theta_{\rm cost},\theta_{\rm dur})N<\eta<\min(I_{\rm peak}^{\rm T},i_{\max}^{no} N)\}$，
下界取成本/时长中较陡者，上界取峰值线/触发线中较低者，顶点为下界射线与 $\eta=I_{\rm peak}^{\rm T}$
之交 $(N^\ast,I_{\rm peak}^{\rm T})$。纳入累计的子区域
$\mathcal{W}_{\rm cum}=\mathcal{W}_{\rm pcd}\cap\{N\,h(\eta/N)\le I_{t\rm cum}^{\rm T}\}$
（$h$ 近似常数时约为竖直边界 $N\lesssim N^\ast_{\rm cum}$），以斜线阴影叠加。标出顶点 $(N^\ast,I_{\rm peak}^{\rm T})$、
成本封顶竖线 $N^\ast_\infty$，并叠加定位点 $(5\times10^4,100)$（落在 $\mathcal{W}_{\rm pcd}$ 内、$\mathcal{W}_{\rm cum}$ 外）。

new_str:
占优楔形
$\mathcal{W}_{\rm pcd}=\{(N,\eta):\max(\theta_{\rm cost},\theta_{\rm dur})N<\eta<\min(I_{\rm peak}^{\rm T},i_{\max}^{no} N)\}$，
下界取成本/时长中较陡者，上界取峰值线/触发线中较低者，顶点为下界射线与 $\eta=I_{\rm peak}^{\rm T}$
之交 $(N^\ast,I_{\rm peak}^{\rm T})$。

按注记~\ref{rem:dom:dichotomy} 的二分，图~\ref{fig:dom} 分两个面板：面板 (a) 画\emph{直线族}，
即上述四条强度量边界；面板 (b) 在同一坐标下画\emph{弧线族}，即推论~\ref{cor:cum} 的累计边界与
推论~\ref{cor:clr} 的清零边界，二者围出的区域满足
$\mathcal{W}_{\rm cum}=\mathcal{W}_{\rm pcd}\cap\{N h\le I_{t\rm cum}^{\rm T}\}$、
$\mathcal{W}_{\rm clr}=\mathcal{W}_{\rm pcd}\cap\{t_{\rm end}\le t_{\rm end}^{\rm T}\}$，
且 $\mathcal{W}_{\rm clr}\subset\mathcal{W}_{\rm cum}\subset\mathcal{W}_{\rm pcd}$。
两个面板上以同色标记点与图~\ref{fig:panel_eta_lever}、\ref{fig:panel_N_lever} 的采样角色联动：
圆点为 $\eta$ 杠杆（固定 $N_{\rm eff}=2\times10^{4}$）的四个取样，方点为 $N$ 杠杆（固定 $\eta=100$）
的六个取样。

面板 (a) 的阴影楔形以成本线为下界，对应 $T_{\max}\to\infty$ 的封顶口径（顶点 $N^\ast_\infty$）；
两条时长线（$45$ d、$150$ d）画在其中，用以显示有限 $T_{\max}$ 下边界将如何抬高或压低，
以及轨迹族在跨越成本线时的位置。面板 (b) 的骨架线改用中性灰以突出两条弧线；
累计弧穿出楔形后的一段、清零弧位于有效池下界 $N<I_{t\rm cum}^{\rm T}$ 的一段，均以虚线示意
"等值线继续存在但已不构成有效边界"。
```

### P5-b 图环境（1851–1858 行）：三张新图

**删除**原 `figure` 环境（引用的 `figures/dominance_region.png` 已废弃），
替换为下列三张。图注文字见附件 `panel_captions_draft.tex`，此处给 dom 图的完整图注。

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{figures/fig_dom_combined.pdf}
  \caption{$(N_{\rm eff},\eta)$ 平面上情景一阈值控制相对 TDINN 现实结局的占优区域，双对数坐标。
  \textbf{(a) 直线族（强度量）}：峰值线 $\eta=I_{\rm peak}^{\rm T}=151.90$（红）、成本线
  $\eta=\theta_{\rm cost}N$（蓝）、两条时长线 $\eta=\theta_{\rm dur}(T_{\max})N$（$45$ d 虚线、
  $150$ d 点划线）与触发线 $\eta=i_{\max}^{no}N$（点线，$i_{\max}^{no}=0.1047$）。
  阴影为占优楔形 $\mathcal{W}_{\rm pcd}$，以成本线为下界，对应 $T_{\max}\to\infty$ 口径，
  顶点 $N^\ast_\infty\approx9.17\times10^{4}$；由 $\theta_{\rm dur}(T)T\approx0.170$，
  $T_{\max}\lesssim103$ d 时改由时长线绑定，例如 $N^\ast(45\text{d})\approx4.04\times10^{4}$。
  \textbf{(b) 弧线族（广延量）}：累计边界（蓝，$N h=I_{t\rm cum}^{\rm T}$，自 $(9471,151.90)$ 到
  $(12177,10)$）与清零边界（红，$t_{\rm end}=t_{\rm end}^{\rm T}$，自 $(2097,27.89)$ 到
  $(5914.3,151.90)$）；红色内区与蓝色外环互斥填充，故红区即两约束同时满足的区域。
  累计弧在 $(11764,19.48)$ 穿出楔形，其后一段以淡虚线示意等值线延续但不再构成
  $\mathcal{W}_{\rm cum}$ 的边界；清零弧在有效池下界 $N<I_{t\rm cum}^{\rm T}=2096.76$ 的一段
  同样以虚线示意（该区间内广延量比较平凡成立，见第~\ref{sec:dom:limits}~节 (4)）。
  骨架线（峰值·成本·时长·触发）以中性灰重绘以突出弧线。两面板的圆点与方点分别对应
  图~\ref{fig:panel_eta_lever} 与图~\ref{fig:panel_N_lever} 的采样角色，同色联动。
  $\eta=100$ 处 $N_{\rm cum}\approx1.011\times10^{4}$、$N_{\rm clr}\approx4.60\times10^{3}$。}
  \label{fig:dom}
\end{figure}
```

其后接入 Panel A、Panel B 两个 `figure` 环境，**图注见附件
`panel_captions_draft.tex`**（已按本次口径写好，含各自的参数、TDINN 单曲线说明、
常规控制带的构造与 $\qinf$ 记号）。标签分别为
`\label{fig:panel_eta_lever}`、`\label{fig:panel_N_lever}`。

### P5-c 全文交叉引用替换

原 `\label{fig:dominance}` 改名为 `fig:dom`。**全文搜索 `\ref{fig:dominance}` 并替换**
（若无其他引用则只需改定义处）。

---

## P6. §9 讨论与局限：起草

**位置**：第 1861–1862 行，替换占位文字。

```latex
\section{讨论与局限}

本文在 SIQR 框架下给出了情景一阈值控制的闭式结构：启动点 $S^\ast$ 的 Lambert $W$ 表达、
平台期开环控制律 $q_c(t)$、控制时长 $\Delta t$、清零时刻 $t_{\rm end}$ 与总累计感染的三段公式，
并在西安数据上与 TDINN 控制、常规控制作了条件性比较。以下按"结论成立条件—参数依赖—
边界情形—可改进方向"整理。

\paragraph{权衡结构。}
比较结果是\emph{指标相对}的，不存在单一意义上的优劣。在全市口径下，阈值控制把社区感染者
峰值精确压到 $\eta$ 且完全不降低接触率（$J_c=0$），二次加权成本反低于 TDINN
（$40.71$ 对 $49.35$）；但因平台期贴边维持、易感者消耗缓慢，控制时长与清零时刻显著拉长，
总累计感染也远高。这一权衡的来源在式~\eqref{eq:dom:Jtheta} 与 $\Delta t\approx\text{const}/(c_0\theta)$
中是显式的：降低 $\eta$ 同时降低峰值与提高时间代价，二者由同一个 $\theta$ 控制，无法解耦。

\paragraph{尺度结构与两条杠杆。}
引理~\ref{lem:dom:scaling} 表明峰值分数、$\Delta t$、$J$、$q_{\max}$ 只经 $\theta=\eta/N$ 进入，
故扩大占优范围只有两条等价杠杆：提高医疗容量阈值 $\eta$，或降低有效混合人口 $N_{\rm eff}$。
数值上二者的作用完全折叠到同一条曲线上（第~\ref{sec:scaling}~节）。但注记~\ref{rem:dom:dichotomy}
的二分说明这一不变性只覆盖强度量：累计与清零时刻带绝对尺度，其边界是弧线，占优只在小池成立。
"贴边维持 $\Rightarrow$ 总感染正比于池规模"是该策略的本性，不能靠调 $N$ 消除。

\paragraph{开环控制的脆弱性。}
$q_c(t)$ 按理论 $S_{\rm th}(t)$ 构造，是时间开环函数而非状态反馈。其代价是对模型误差与
参数偏移没有自校正能力：若真实 $S(t)$ 偏离理论轨迹，$I(t)$ 将偏离阈值 $\eta$ 而控制律不会察觉。
本文未评估该敏感性，也未引入观测噪声或参数不确定性。设计带反馈修正的变体、
并比较其在模型失配下的稳健性，是直接的下一步。

\paragraph{有效人口的解释限度。}
$N_{\rm eff}$ 应理解为"控制单元规模"，而非可自由调节以偏袒某策略的旋钮。其物理实现分两类：
天然有界单元（校园、厂区、邮轮）与封控造出的小池，后者的空间分区本身即一种接触控制，
成本未计入 $J$，占优结论相应打折。此外第~\ref{sec:dom:limits}~节 (3) 指出，
逐 $N$ 只重拟合 $I_0$ 时，$N\lesssim10^4$ 的拟合质量已显著退化，
而两条弧线给出的占优区恰落在该区间——这是当前结论最薄弱的一环。

\paragraph{与 TDINN 比较的口径。}
本文的占优是"反事实策略在规模 $N_{\rm eff}$ 的单元上能否达到不劣于现实结局的指标"，
TDINN 的现实结局作为固定参照。这与"同一池上两种策略对打"是不同的问题，后者在清零时刻
一项上会给出相反结论（第~\ref{sec:dom:limits}~节 (2)）。要做同池比较，需对每个 $N_{\rm eff}$
重新拟合 TDINN 的全部控制参数而非只拟合 $I_0$；这有待其原始训练代码。

\paragraph{未来工作。}
（i）对每个 $N_{\rm eff}$ 全参数重拟合 TDINN，给出同池口径下的比较；
（ii）在情景二、情景三（同时调节 $c$ 与 $q$）下重做同一套尺度分析，检验二分结构是否保持；
（iii）多城多病验证：海南模块已有平行结构，可检验 $\theta$ 阈值与 $\qinf$ 等结构不变量的可移植性；
（iv）引入观测噪声与参数不确定性，评估开环控制律的稳健边界。
```

---

## P7. 遗留代码改动（图外，可选但建议一并做）

### P7-a 记号统一 `q^\star \to q_{\mathrm{inf}}`

论文宏为 `\newcommand{\qinf}{q_{\mathrm{inf}}}`（第 32 行），但两处生成图/表的脚本仍用 `q^\star`：

| 文件 | 行 | 现状 |
|---|---|---|
| `plot_eta_80_100_150_inflection.py` | 256 | `label=rf"$q^\star={q_star:.4f}$"` |
| `effective_population_sensitivity.py` | 818, 879 | 生成的 LaTeX 文本中的 `q^\star` |

改成 `q_{\mathrm{inf}}` 后需重跑对应脚本出图。改完可**删除** `fig:neff_inflection` 图注里
那句补丁："（图内图例记为 $q^\star$，即本文 $\qinf=q_c(2\bar S)$）"（第 1712 行）。

### P7-b 已完成的绘图脚本改动（供记录，图已重出）

- `panels.py`：TDINN 一律取全市口径 `solve_tdinn(N_FULL)`，`N_FULL=13163000`；
  Panel A 去掉图上 $N=2\times10^4$ 灰标注，改为在平台下降转角处直标各自 $\eta$；
  (b) 子图图例移除；`$q_\infty$` $\to$ `$q_{\mathrm{inf}}$`。
- `compute_B.py`：TDINN 飘逸带改单曲线；常规控制带 `Nrib` 区间改为由六个角色的 $N$ 自动取范围
  $[4602,\,87951]$；清零成员按判据补 $I=1$ 使包络在全区间良定义。
- `plot_B.py`：绘制条件改为 `rhi>1.0`（去掉魔数 `rlo>=2`）；图例带各自 $N$；
  `TDINN (city-fit)` $\to$ `TDINN`；(b) 子图图例移除；输出路径改为相对 `__file__`。
- `dom_pretty.py`：清零弧插入端点 $(2096.76,\,28.348)$，其下一段改虚线（填充保持完整）。

---

## P8. 仓库清理：两个文件已过期，留着会自相矛盾

### P8-a `arc_data.csv`

其中 clr 弧的 27 个点仍是旧口径（$t_{\rm end}^{\rm T}=45.0$ d）。cum 弧的 16 点未变、仍有效。

处理：用交付的 `arc_clr_45.27.csv` 替换 clr 部分，或直接删除 `arc_data.csv`
并改为并列保存两个文件（cum 一个、clr 一个）。**不要保留旧 clr 数据**，
否则与论文正文和图中的 $N_{\rm clr}=4601.9$、端点 $(2096.76,\,27.89)$、$(5914.3,\,151.90)$ 冲突。

### P8-b `dom_final.py`

分面独立版（产出 `fig_dom_a/b`），内嵌的是旧弧线数据、旧图例 `clear $\leq$ 45 d`、
旧的红弧下端（未截到有效池下界）。它跑出来的图与定稿的 `fig_dom_combined` 对不上。

处理：论文只使用合成图，**建议直接删除** `dom_final.py` 与 `fig_dom_a/b.*`。
若要保留，须同步 `dom_pretty.py` 中的 `clr_N` / `clr_eta` / `N_FLOOR` / `ETA_FLOOR`
与图例文字。

### P8-c `arc_solve.py` 里的沙盒死路径

这三个文件原先在一个 Linux 沙盒里开发，顶部写死了 `/sessions/exciting-tender-brahmagupta/...`
的 `sys.path` 与输出路径。在 Windows 机上这些路径不存在。

- `plot_B.py`、`panels.py`、`compute_B.py`：**交付版本已清除**，无需再动。
- **`arc_solve.py`：仍有 2 行未清**（仓库里的版本），需删除：
  ```python
  sys.path.insert(0, "/sessions/exciting-tender-brahmagupta/mnt/outputs/run/_shim")
  sys.path.insert(0, "/sessions/exciting-tender-brahmagupta/mnt/outputs/run/pkg")
  ```
  改为依赖 `PYTHONPATH`（同交付版 `panels.py` 的做法）。另外 `arc_solve.py` 里的
  `CLR_TARGET = 45.0` 也应改为 `45.27` 以与本次口径一致；该文件目前只剩 cum 弧
  重算的用途（clr 弧已由新增的 `resolve_clr.py` 接管），若不再使用可直接删除。

---

## P9. 重写 `README_接续上下文.md`

该文件写于本轮讨论之前，有**五处已不成立**，留着会误导下一轮接续：

| 原文说法 | 现状 |
|---|---|
| TDINN 基准"逐 $N$ 只重拟合 $I_0$ 时绝对轨迹近似不变" | 不成立；已改为"固定现实参照"口径（见本文件第 0 节） |
| clr 弧目标 $45.0$ d，"建议重算到 45.27" | 已重算完成，现为 $45.27$ d |
| clr 弧终于 I0=1 域墙 $N\approx1118$ | 改为终于有效池下界 $N=I_{t\rm cum}^{\rm T}=2096.76$；域墙不再绑定 |
| Panel B 有 "TDINN 飘逸带" | 已改为单条全市曲线；只有常规控制保留带子 |
| 拐点记号 $q_\infty$ | 改为 $q_{\rm inf}$，与论文宏 `\qinf` 一致 |

另需补入本轮新增的事实：

- 常规控制带的构造：$N$ 区间由六个角色自动取范围 $[4602,\,87951]$；
  8 条成员各自按自身 $N$ 重拟合 $I_0$，故**轨迹相互交叉**，两条代表虚线并非处处即包络；
  清零成员按判据补 $I=1$ 使包络在全区间良定义，绘制条件为 `rhi>1.0`。
  峰值处带宽约 $55$ 倍（$167$ vs $9203$）。
- 关键数值：$N_{\rm clr}(100)=4601.9$、$N_{\rm cum}(100)=10105$、
  $N^\ast_{45}=40377$、$N^\ast_\infty=91727$、
  cum 弧穿成本线于 $(11764,\,19.48)$、$\theta_{\rm dur}(T)\,T\approx0.170$（故 $T_{\max}\approx103$ d 为绑定切换点）。
- TDINN 基准随 $N$ 的漂移表与逐 $N$ 拟合 rmse 退化表（见 P3 局限 (2)(3)）。
- Panel A 的 $\eta$ 直标在平台下降转角处；两个 panel 的 (b) 子图图例已移除；
  Panel B 的 $N$ 值放在 (a) 子图图例中（直标会重叠，实测曲线间距 $11$–$18$ d < 标签宽 $23$ d）。

---

## 执行顺序与校验

1. **顺序**：P0（补 label）→ P2（TDINN 段）→ P1（新增推论）→ P3（局限）→ P4（实例）
   → P5（图）→ P6（§9）→ P7（记号）→ P8（清理）→ P9（README）。
   P0 必须最先：P1 的推论要引用 `thm:s1:tend`，否则编译出 `??`。
2. 每步后 `xelatex` 编译**两遍**，检查：
   - 新标签 `thm:s1:tend`、`cor:clr`、`rem:dom:dichotomy`、`sec:dom:limits`、
     `sec:dom:xian`、`eq:dom:Nfloor`、`eq:dom:clrarc`、`fig:dom`、
     `fig:panel_eta_lever`、`fig:panel_N_lever` 均无 `??`
   - 旧标签 `fig:dominance` 的引用已全部改名
   - 三个新 `\includegraphics` 路径存在：`figures/fig_dom_combined.pdf`、
     `figures/fig_panel_A.pdf`、`figures/fig_panel_B.pdf`
3. 删除废弃文件引用：`figures/dominance_region.png` 不再被引用，可从 `figures/` 移除。
4. 最终自检：全文搜索 `45 d`（旧 clr 口径）、`4537`、`5827`、`28.35`、`q^\star`、
   `dominance_region`，确认无残留。

## 待确认（动手前定）

1. **清零约束写成正式推论 `cor:clr`（本计划采用）还是只在实例/图注里描述？**
   本计划采用前者。理由：在"TDINN 为固定现实参照"的口径下，清零与累计完全平行，
   而累计已有 `cor:cum`。若担心该结论在同池口径下反号，P3 局限 (2) 已如实交代。
2. ~~$t_{\rm end}^{\rm T}$ 口径~~ **已定：采用精确值 $t_{\rm end}^{\rm T}=45.27$ d。**
   clr 弧已按该目标全部重解（28 点，见 `arc_clr_45.27.csv`），图例改为 `clear $\leq$ 45.3 d`。
   受影响数值：有效池下界端点 $\eta^\ast$ $28.35\to27.89$（$-1.6\%$）、
   顶端 $N$ $5827.5\to5914.3$（$+1.5\%$）、$N_{\rm clr}(100)$ $4537.1\to4601.9$（$+1.4\%$）。
   Panel B 的 clear 角色 $N$ 同步改为 $4601.9$（校验 $t_{\rm end}=45.270$ d），
   常规控制带的 $N$ 下界随之变为 $4602$。三张图已按新口径重出。
