# G1 文字及保护文件保全审计

- 基准：`689a627`。
- 结果：通过。
- 旧/新归一化段落数：208 / 207。
- 保留带标签公式：124；仅删除 eq:projection-feedback, eq:regularized-cost, eq:time-HJB, eq:time-boundary-set, eq:time-switch。
- 两个自动生成块逐字不变：True。
- 保护文件原始 SHA-256：2474 个；变化 0，新增 0。
- 移入附录的证明逐字不变：True；唯一性证明排除获准新增文字后不变：True。
- 优化器调用 / 新增 OCP 求解 / MATLAB 调用：0 / 0 / 0。

只折叠段落空白并剥离标题/节标签/注释/proof 包装；正文保全双向匹配且核对字符多重集；公式另作保留全部源空白的逐字核对（统一行尾LF）。

## 白名单逐项原文与新文

### theory-branch-1：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly
\begin{center}\small 常接触率理论校样：由同一份 \texttt{main.tex} 编译；省略时变讨论和数值图形章节。\end{center}
\fi
```

新文：

```latex
（删除，新文为空）
```

### theory-branch-2：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
五个代表初值在所报告网格上的直接配点结果支持解析预测的阶段顺序、切换位置和成本。
\fi
```

新文：

```latex

五个代表初值在所报告网格上的直接配点结果支持解析预测的阶段顺序、切换位置和成本。

```

### theory-branch-3：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
数值部分使用五类代表初值的已保存直接配点结果，对照不同区域下的阶段次序、切换位置和成本。
\fi
```

新文：

```latex

数值部分使用五类代表初值的已保存直接配点结果，对照不同区域下的阶段次序、切换位置和成本。

```

### theory-branch-4：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
% 数值章节已内联；下方两个标记块由数值导出程序定点更新。
\providecommand{\NumFigureRoot}{../figures/numerical_scenarios}
\providecommand{\NumTheoryRef}[2]{#2~\ref{#1}}
% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES
% MATLAB 解析公式评价；不含优化器结果。
\providecommand{\NumJRefEOne}{0.416186}
\providecommand{\NumJRefETwo}{1.529511}
\providecommand{\NumJRefEThree}{0.433981}
\providecommand{\NumJRefEFour}{1.268835}
\providecommand{\NumJRefEFive}{0.536233}
\providecommand{\NumSBRef}{0.54769512}
\providecommand{\NumSwitchSEOneRef}{0.51017169}
\providecommand{\NumSwitchIEOneRef}{0.13423054}
\providecommand{\NumMaxReleaseRef}{7.44746905}
\providecommand{\NumExitETwoTheory}{5.86950254}
\providecommand{\NumExitEFourTheory}{1.08077528}
% END AUTO-GENERATED NUMERICAL REFERENCE VALUES

% BEGIN AUTO-GENERATED NUMERICAL RESULTS
% 从 data/numerical_scenarios 的真实结果生成；条件开关由 main.tex 定义。
\NumResultsVerifiedtrue
\NumRobustnessCompletetrue
\renewcommand{\NumRobustnessStatement}{数值接受及容量控制比较容差于保存求解后调整，取值与原严格记录见复现附录。五例常值 $q=0.7$ 和固定种子随机初猜的阶段一致，成本最大绝对差为 $\num{6.1e-13}$。在当前接受容差下，最细两级成本与事件区间比较通过 E1、E2、E3、E4、E5。$n=2000$ 的 E2、E4 存在长中间控制块与阶段识别异常。该比较不提供收敛阶。$n=2000$ 的 E1、E3、E5 成本比较仍未通过。E3 的粗网格负成本差小于容量超出所致的解析最优值下降，与容量超出相容。固定步长时域复核五例通过。阈值复核通过。有限样本与浮点诊断不替代解析证明。}
\renewcommand{\NumReproducibilityDetails}{默认协议已记录 35/35 个不同配置，其中 30 个同时通过数值接受与理论比较。协议是否完成与比较是否一致分别记录。本次在保存求解后调整状态及容量接受容差为 $\num{1e-05}$、容量段控制与 $q_B$ 区间均值的绝对误差容差为 $\num{0.003}$，并重新评估全部保存结果；成本相对误差容差 $\num{0.0001}$ 与事件区间判据保持不变。原严格判据及其未通过记录另行保留。按保存求解前预定的原判据（状态容差 $\num{1e-06}$、容量容差 $\num{1e-06}$、容量段控制容差 $\num{0.002}$），数值接受与理论比较分别通过 29/35 与 29/35，同时通过 28/35；修订判据只重新划定浮点接受尺度，不提供新的收敛证据。五例常值 $q=0.7$ 和固定种子随机初猜的阶段一致，成本最大绝对差为 $\num{6.1e-13}$。在所列接受容差下，固定时域网格复核的最细两级成本与事件区间比较通过 E1、E2、E3、E4、E5。E2、E4 的 $n=2000$ 长中间控制块与阶段识别异常仍保留在配套记录中。该结果只支持所测最细两级的一致性，不给出收敛阶。$n=2000$ 的 E1、E3、E5 成本比较仍未通过。E3 的 $n=2000$ 负成本差为 $\num{-6.76e-05}$，重积分容量超出 $\varepsilon_K=\num{7.83e-06}$；把容量放宽为 $K+\varepsilon_K$ 后，解析最优值下降 $\num{1.08e-04}$，大于该负差。因此该负差与容量超出相容，评估记录中的 unresolved-discrepancy 分类按原样保留。固定步长时域复核五例通过。阈值复核通过。全部记录见配套文件；有限样本与浮点诊断不替代解析证明。}
\providecommand{\NumHorizon}{300}
\providecommand{\NumIntervals}{4000}
\providecommand{\NumDegree}{2}
\providecommand{\NumMeshDetails}{按预先指定设置，E2 使用 $n=8000$，E4 使用 $n=8000$；其余算例保留基准网格。图表均采用各例最终保存的结果。}
\providecommand{\NumJOclEOne}{0.416205}
\providecommand{\NumJOclETwo}{1.529523}
\providecommand{\NumJOclEThree}{0.433999}
\providecommand{\NumJOclEFour}{1.268831}
\providecommand{\NumJOclEFive}{0.536256}
\providecommand{\NumExitETwoStart}{5.85000000}
\providecommand{\NumExitETwoEnd}{5.88750000}
\providecommand{\NumExitEFourStart}{1.05000000}
\providecommand{\NumExitEFourEnd}{1.08750000}
\providecommand{\NumNeutralETwoCostDifference}{5.78648240435e-13}
\providecommand{\NumEFourSignedCostDifference}{-3.68275844664e-06}
\providecommand{\NumEFourCapacityExcess}{7.70286958773e-07}
\providecommand{\NumFindingWaiting}{实际控制输出中，E1 和 E2 分别识别出 $0\to 1\to 0$ 与 $0\to q_B\to 1\to 0$。E1 的完全跟踪开始区间为 $[6.975,7.05]$。对应端点的感染比例仍低于容量上限。E2 的容量退出区间为 $[5.85,5.8875]$。}
\providecommand{\NumFindingTrackingBoundary}{E3、E4、E5 的实际阶段依次为 $1\to 0$、$q_B\to 1\to 0$ 和 $1\to 0$。E3、E5 均从初始时刻采用完全跟踪。E4 的容量退出区间为 $[1.05,1.0875]$。E2、E4 的理论容量退出时刻均落在上述单网格过渡区间内；首个纯完全跟踪单元的起点仍不等同于连续切换点。}
\providecommand{\NumCheckStatement}{对原始分段常数控制逐区间重积分后，五例最大容量超出量为 $\num{8e-07}$，与配点状态的最大差异为 $\num{8.6e-08}$；末尾 $20$ 个时间单位内最大控制幅值为 $\num{0}$。各例终端状态均通过零控制安全延拓核查。这些浮点检查用于排查截断及离散问题，不是连续可行性的严格证明。}
\providecommand{\NumOverallFinding}{五例成本相对解析参考的最大差异约为 $0.00459\%$。计算结果支持这五个初值下的阶段顺序及切换位置预测；切换位置的偏差应结合控制区间宽度和过渡单元解释。E4 的离散成本比解析参考低 $\num{3.68e-06}$，重积分轨道有 $\varepsilon_K=\num{7.7e-07}$ 的容量超出；把容量放宽为 $K+\varepsilon_K$ 后，解析最优值下降 $\num{1.16e-05}$，大于该负差。因此该控制的成本仍不低于放宽容量后的解析最优值，负差与容量超出相容，不构成低于解析最优值的连续时间可行控制。}
\providecommand{\NumErrorTableRows}{E1 & \num{1.91e-05} & \num{4.59e-03} & \num{2.97e-07} & \num{4.05e-06} & 是 \\ E2 & \num{1.22e-05} & \num{7.98e-04} & \num{7.99e-07} & \num{1.28e-05} & 是 \\ E3 & \num{1.75e-05} & \num{4.03e-03} & \num{4.80e-08} & \num{6.60e-07} & 是 \\ E4 & \num{-3.68e-06} & \num{-2.90e-04} & \num{7.70e-07} & \num{1.16e-05} & 是 \\ E5 & \num{2.32e-05} & \num{4.32e-03} & \num{5.57e-08} & \num{7.76e-07} & 是 \\}
\providecommand{\NumResidualSummary}{五例成本相对解析参考差的绝对值最大为 $\num{0.00459}\%$。重积分最大容量超出为 $\num{7.99e-07}$，与配点状态的最大偏差为 $\num{8.57e-08}$。末段最大控制幅值为 $\num{0}$，各例终端状态均通过零控制安全检查。按求解前预定的原判据，数值接受与理论比较同时通过 28/35；按求解后修订的判据，同时通过 30/35；修订只调整浮点接受尺度，不提供新的收敛证据。未通过的网格记录（E2、E4 在 $n=2000$ 的阶段识别异常；E1、E3、E5 在 $n=2000$ 的成本比较未通过）见补充材料。}
% END AUTO-GENERATED NUMERICAL RESULTS
\providecommand{\NumMeshDetails}{}

% Missing actual figures remain blank. Never substitute predicted OCP plots.
\newcommand{\NumFigureOrBlank}[2]{%
  \IfFileExists{\NumFigureRoot/#1}{%
    \includegraphics[width=0.97\linewidth]{\NumFigureRoot/#1}%
  }{%
    \fbox{\parbox[c][#2][c]{0.93\linewidth}{\mbox{}}}%
  }%
}
\newcommand{\NumFindingParagraph}[1]{\par\smallskip #1\par\smallskip}

\section{数值方法与实验设置}
\label{sec:numerical-method}

本节围绕不同初值区域，比较解析最优策略与直接配点输出，
重点考察等待阶段、容量弧和完全跟踪阶段的出现顺序及其连接位置。
算例组织借鉴 \citet[第6节]{AvramFreddiGoreac2022} 的区域展示方式，
但该文含目标约束的有限时域问题不作为本文截断处理的等价性依据。
全局最优性与几乎处处唯一性分别由
\NumTheoryRef{thm:verification}{验证定理}和
\NumTheoryRef{thm:unique-q}{唯一性定理}给出；
数值实验用于检验这些解析结论的计算一致性。

五个主算例采用相同参数
\begin{equation}
 \beta=0.5,\qquad c=2,\qquad\gamma=0.3,\qquad K=0.15,
 \label{eq:numerical-common-parameters}
\end{equation}
仅改变初始状态。
$s,i$ 为相对于初始总量的比例，允许 $s_0+i_0<1$；
此时 $h=0.3$、$\ell=p=0.15$。
这些参数用于展示理论结构，不作为特定疫情的参数标定。

直接配点处理如下固定时域问题：
\begin{equation}
\begin{aligned}
 \min_q\quad &J_T(q)=\int_0^T \beta cq(t)\,\mathrm dt,\\
 \text{满足}\quad
 &\dot s=-c[\beta+(1-\beta)q]si,\qquad
 \dot i=[\beta c(1-q)s-\gamma]i,\\
 &0\le q\le1,\quad 0\le s\le1,\quad0\le i\le K,\\
 &(s(0),i(0))=(s_0,i_0).
\end{aligned}
\label{eq:numerical-ocp}
\end{equation}
该问题不增加终端状态约束、终端成本或二次控制正则化，
也不固定阶段数、切换时刻或容量控制。
解析策略可用于初始化，但不进入数值优化的目标或额外约束。

计算方法为 MATLAB/OpenOCL 直接配点\citep{Koenemann2019OpenOCL}，
通过 CasADi\citep{Andersson2019CasADi} 构造离散问题，
由 IPOPT 求解非线性规划\citep{WachterBiegler2006}。
基准设置为 $T=\NumHorizon$、$n=\NumIntervals$、$d=\NumDegree$；
控制在每个网格区间内为常数。
\NumMeshDetails
控制成本在完整求解时域上按实际区间长度计算：
\begin{equation}
 J_{\mathrm{OCL}}=\beta c\sum_{k=1}^{n}q_k\Delta t_k.
 \label{eq:numerical-cost-sum}
\end{equation}
绘图窗口不作为成本积分范围，求解输出不通过平滑或裁剪替换。

对于每个待报告结果，用原始分段常数控制重新积分状态方程，
检查区间内部的容量峰值、与配点状态的偏差以及终端零控制延拓。

固定 $T=300$ 的直接配点加终端检查是一种终端处理，
不等同于原无穷时域问题。
终端检查采用式\eqref{eq:uncontrolled-future-peak}中的无控制未来峰值
$P_0(s(T),i(T))$，终端状态取自重积分轨道，
并核查末段控制是否为零。
若该轨道在 $[0,T]$ 上满足 $i\le K$，且 $P_0(s(T),i(T))\le K$，
则在 $T$ 之后令 $q=0$，由引理\ref{lem:safe-invariant}的安全集正向不变性，
所得控制对原无穷时域问题可行，其完整成本为 $J_{\mathrm{OCL}}$，
从而 $J_{\mathrm{OCL}}\ge V(x_0)$。
若重积分轨道有最大容量超出 $\varepsilon_K>0$，
且终端满足 $P_0(s(T),i(T))\le K+\varepsilon_K$，
则同一延拓只保证对容量 $K+\varepsilon_K$ 可行，
相应结论为 $J_{\mathrm{OCL}}\ge V_{K+\varepsilon_K}(x_0)$；
这里 $V_{K'}$ 表示容量为 $K'$ 时的值函数。
这给出表\ref{tab:numerical-errors}中容量放宽对照的依据。
上述可行性推论以连续轨道满足相应条件为前提，
重积分及终端检查本身仍是浮点诊断。
本文没有证明离散有限时域最优值随网格加密收敛到 $V$，
也不以这些诊断代替该收敛性结论。

阶段依据数值控制及容量接近程度识别，切换位置按过渡网格区间报告。
已有复核改变初始猜测、网格、终止时刻及阶段识别阈值，
完整配置、判据与诊断结果见补充材料附录\ref{app:numerical-reproducibility}。

\section{不同初值区域下的数值验证}
\label{sec:numerical-results}

\subsection{代表初值与相平面分区}

表\ref{tab:numerical-scenarios}的五个初值覆盖表\ref{tab:optimal-stages}中的两种等待区、
立即完全跟踪区及容量线上 $s_B$ 两侧的状态，
用于检验\NumTheoryRef{thm:verification}{验证定理}给出的阶段结构与成本。

由安全边界和切换条件的数值评价得
\begin{equation}
 s_B\approx\NumSBRef,
 \label{eq:numerical-sB}
\end{equation}
其中 $(s_B,K)$ 为切换曲线与容量线的交点。
图\ref{fig:optimal-partition}给出成本分区的理论几何，图\ref{fig:numerical-regions}将 E1--E5 的直接配点轨道与该几何叠加比较。

\begin{table}[H]
\centering
\small
\setlength{\tabcolsep}{4.2pt}
\caption{代表初值、理论控制结构与控制成本。$J_{\mathrm{ref}}$ 为解析公式的数值评价，
$J_{\mathrm{OCL}}$ 为直接配点返回控制在完整求解时域内的成本。}
\label{tab:numerical-scenarios}
\begin{tabular}{@{}clclrr@{}}
\toprule
算例 & $(s_0,i_0)$ & 区域 & 理论结构 & $J_{\mathrm{ref}}$ & $J_{\mathrm{OCL}}$\\
\midrule
E1 & $(0.75,0.01)$ & $\mathcal W_\Gamma$ & $0\to1\to0$ & \NumJRefEOne & \NumJOclEOne\\
E2 & $(0.99,0.01)$ & $\mathcal W_K$ & $0\to q_B\to1\to0$ & \NumJRefETwo & \NumJOclETwo\\
E3 & $(0.50,0.14)$ & $\mathcal T$ & $1\to0$ & \NumJRefEThree & \NumJOclEThree\\
E4 & $(0.70,0.15)$ & $\mathcal B$ & $q_B\to1\to0$ & \NumJRefEFour & \NumJOclEFour\\
E5 & $(0.50,0.15)$ & $\mathcal T\cap\{i=K\}$ & $1\to0$ & \NumJRefEFive & \NumJOclEFive\\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[H]
\centering
\small
\setlength{\tabcolsep}{3pt}
\caption{主结果的带符号成本差与约束误差。
$J_{\mathrm{ref}}=V_K(x_0)$ 为解析参考值，相对差为
$(J_{\mathrm{OCL}}-J_{\mathrm{ref}})/J_{\mathrm{ref}}$。
按第\ref{sec:numerical-method}节的终端延拓逻辑，
末列检查成本差是否不小于 $-(V_K-V_{K+\varepsilon_K})$；
该浮点比较不构成严格连续可行性的证明。}
\label{tab:numerical-errors}
\begin{tabular}{@{}crrrrr@{}}
\toprule
算例 & $J_{\mathrm{OCL}}-J_{\mathrm{ref}}$ & \shortstack{相对差\\（\%）} & $\varepsilon_K$ & $V_K-V_{K+\varepsilon_K}$ & \shortstack{是否满足\\$J_{\mathrm{OCL}}\ge V_{K+\varepsilon_K}$}\\
\midrule
\NumErrorTableRows
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN1_regions.pdf}{4.2cm}
\caption{理论分区与直接配点轨道的相平面对照。
图中叠加 E1--E5 的初始点和 OpenOCL 轨道，并标出安全边界、切换曲线 $\Gamma_K$、
容量线 $i=K$ 及两种等待区的公共边界。理论曲线与数值轨道采用不同线型或标记；
灰色点划线为 $s=h$，灰色虚线为 $s+i=1$。}
\label{fig:numerical-regions}
\end{figure}


\subsection{两种等待区域的对照}

E1 与 E2 保持 $i_0=0.01$ 相同，分别位于 $\mathcal W_\Gamma$ 和 $\mathcal W_K$。
按表\ref{tab:optimal-stages}及\NumTheoryRef{def:candidate}{反馈构造}，
两者的差别是等待后是否出现正长度容量弧。
图\ref{fig:numerical-waiting}检验这一差别，以及完全跟踪的开始位置：
E1 的解析参考为 $(\NumSwitchSEOneRef,\NumSwitchIEOneRef)$，E2 的参考为 $(s_B,K)$。

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN2_waiting.pdf}{5.0cm}
\caption{两种等待区域下的控制与感染比例：左列为 E1，右列为 E2；
上排为 $q(t)$，下排为 $i(t)$。
每幅图比较解析参考与 OpenOCL 结果，数值控制按分段常数形式显示，
感染图中的水平线表示容量 $K$。}
\label{fig:numerical-waiting}
\end{figure}

\NumFindingParagraph{\NumFindingWaiting}

不存在容量平台与全时域内不接触容量并非同一命题。
解析策略在安全边界解除后，感染比例可以沿无控制轨道再次上升至 $K$，
但不超过它；此时 $q=0$，不应将这种后续接触误判为容量控制弧。

\subsection{立即完全跟踪与容量边界初值}

E3 检验内部初值 $(0.50,0.14)$ 的立即完全跟踪；
E4、E5 保持 $i_0=K$ 相同，检验 $0.70>s_B$ 与 $0.50<s_B$ 时初始阶段的差别。
表\ref{tab:optimal-stages}及\NumTheoryRef{def:candidate}{反馈构造}分别给出
$1\to0$、$q_B\to1\to0$、$1\to0$ 的参考结构，
图\ref{fig:numerical-boundary-tracking}与保存控制逐一比较。

另一个比较是 E2 与 E4 在容量退出时的状态。
两例到达该事件的时间不同，但理论上均经过同一状态 $(s_B,K)$；
从该点起的后续解析轨道相同。
因此可以在相平面中比较其数值退出位置，而不要求不同算例的时间序列重合。

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN3_boundary_tracking.pdf}{5.0cm}
\caption{立即完全跟踪与容量边界初值的对照。
从左到右为 E3、E4、E5，上排为 $q(t)$，下排为 $i(t)$。
解析参考与 OpenOCL 结果的比较重点为初始控制阶段、容量平台是否出现，以及解除位置。}
\label{fig:numerical-boundary-tracking}
\end{figure}

\NumFindingParagraph{\NumFindingTrackingBoundary}

\subsection{成本、约束误差与剩余残差}

表\ref{tab:numerical-errors}同时报告成本差、重积分容量超出及放宽容量后的值函数下降。
五例均满足表中的放宽容量成本比较；其中 E4 的负成本差小于容量放宽导致的值函数下降。
存在容量超出的离散结果不能称为优于解析最优策略的严格可行控制。
配点与重积分状态的偏差用于诊断动力学离散，
不等同于数值状态与解析最优轨道之间的误差；切换位置仍应结合过渡网格宽度解释。

\NumFindingParagraph{\NumResidualSummary}
\FloatBarrier

\section{\texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论}}
\label{sec:time-varying}
现在令 $c(t)>0$ 为给定的可测、局部本质有界函数。
由于恢复率 $\gamma$ 不随时间缩放，令 $\vartheta(t)=\int_0^t c(v)\dd v$ 后，
在该时间变换的值域内仍按几乎处处意义有
\[
\frac{\dd i}{\dd\vartheta}=\beta(1-q)si-\frac{\gamma}{c(t(\vartheta))}i.
\]
因此一般不能化为本稿的常系数问题。
本节仅陈述在另行建立值函数和验证条件后适用的公式与充分条件；
不声称已经解决任意时变 $c$ 的存在性、全局验证或唯一性。

\subsection{非自治 HJB 方程}
对具体定义的时变问题，在值函数 $V(t,s,i)$ 具备所需正则性、动态规划可作微分化的点，
内部 HJB 的条件性微分形式为
\begin{equation}
\begin{aligned}
0=V_t+\min_{q\in \mathcal Q(t,s,i)}\Big\{&-c(t)[\beta+(1-\beta)q]siV_s\\
&+[\beta c(t)(1-q)s-\gamma]iV_i+\beta c(t)q\Big\}.
\end{aligned}
\label{eq:time-HJB}
\end{equation}
当 $c$ 仅可测时，上式至多按时间几乎处处理解：在相应的 Lebesgue 点和所需值函数导数存在处使用，
不要求它在每个指定时刻都是经典等式。
若进一步用于验证，仍须针对每条被比较的轨道建立复合函数的链式法则和沿轨道的几乎处处不等式；
仅有状态--时间空间中几乎处处的等式，不自动保证它沿任意轨道成立。
内部取 $\mathcal Q=[0,1]$；容量边界在上述几乎处处时间意义下的内指或切向速度条件对应
\begin{equation}
\mathcal Q(t,s,K)=\left[\max\left\{0,1-\frac{\gamma}{\beta c(t)s}\right\},1\right].
\label{eq:time-boundary-set}
\end{equation}
切换系数为
\begin{equation}
\Sigma(t,s,i)=\beta c(t)-c(t)si[(1-\beta)V_s+\beta V_i].
\label{eq:time-switch}
\end{equation}
式 \eqref{eq:time-boundary-set}--\eqref{eq:time-switch} 不把时间零测集上的 $c,q$ 代表值作为额外的点态轨道约束。
若在时间 $t$ 定义无控制安全集，它必须使用从 $t$ 开始的\emph{完整未来接触率路径}，
不能仅把常系数安全集中的 $c$ 换成当前 $c(t)$。

\begin{proposition}[条件性的时变唯一性充分条件]
\label{prop:time-conditional}
对某个已经明确定义的时变问题，假设最优解存在，且已经证明对任意最优轨道的验证等式。
进一步假设：在所有可能被最优轨道经过的状态--时间点，验证等式使控制几乎处处等于同一单值反馈 $Q(t,x)$；
该反馈从给定初值生成的可行 Carath\'eodory 解唯一。
则最优控制几乎处处唯一。
\end{proposition}
\begin{proof}
任意最优控制均须沿自己的轨道满足 $q(t)=Q(t,x(t))$ 几乎处处。
所有最优状态轨道因此满足同一闭环方程与初值，由闭环唯一性得轨道一致，进而控制几乎处处一致。
\end{proof}
内部 $\Sigma\ne0$、容量上受限极小元单值，是控制选择单值的充分途径，
但仅在一条候选轨道上检查这些性质不足以排除所有其他最优轨道。
常接触率平台的唯一性反而说明点态单值不是最优控制唯一的必要条件。

\subsection{有限时域严格凸正则化}
另取固定 $T<\infty$ 及明确的终端数据，可研究不同于原无穷时域问题的正则化目标
\begin{equation}
J_\varepsilon(q)=\int_0^T\left[\beta c(t)q(t)+\frac\varepsilon2q(t)^2\right]\dd t,
\qquad\varepsilon>0.
\label{eq:regularized-cost}
\end{equation}
\begin{proposition}[唯一的点态正则化极小元]
\label{prop:regularized-pointwise}
若相应的有限时域值函数 $V_\varepsilon^T$ 在所考虑的点可微，
则固定满足上述时间约定的 $(t,s,i)$ 及其值梯度时，Hamiltonian 的内部极小元唯一，形式为
\begin{equation}
q_\varepsilon^*(t,s,i)=\proj_{[0,1]}
\left(\frac{c(t)si[(1-\beta)\partial_sV_\varepsilon^T+\beta\partial_iV_\varepsilon^T]-\beta c(t)}\varepsilon\right).
\label{eq:projection-feedback}
\end{equation}
容量边界上将投影区间换为 \eqref{eq:time-boundary-set}。
\end{proposition}
\begin{proof}
关于 $q$ 的二阶导数为 $\varepsilon>0$，无约束一阶条件给出括号中的值，
加入区间约束后取投影。
该计算只证明点态严格凸性；只有另行完成验证、达到性和可行闭环唯一性，才能进一步推出整个控制问题的唯一最优解。
\end{proof}
若需控制变化惩罚，可在离散目标中加入相邻控制差的平方，或在连续问题中把 $q$ 作为状态。
这些都是不同的控制问题，不能不经证明就视为原线性成本问题的等价改写。

\section{同时控制接触率与跟踪比例时的限制}
若把 $c$ 也作为控制并允许 $c=0$，而仍仅使用 \eqref{eq:linear-cost}，
则 $c=0,q=0$ 给出零成本可行方案，问题退化。
联合控制需另行定义接触减少和跟踪成本，例如
\begin{equation}
\int_0^T[\alpha_c(c_0-c)^2+\alpha_q q^2+\alpha_{cq}cq]\dd t,
\label{eq:joint-cost}
\end{equation}
并明确控制约束。
该示例中的权重须另行保证非负性或所需凸性；即使运行成本严格凸，
动力学中的 $cq$ 项以及非线性状态约束也不会自动给出整个问题的严格凸性。
本稿不为此扩展声称全局唯一性。

\section{模型假设与理论边界}
\label{sec:limitations}
本稿的 $q=1$ 代表理想化的完美追踪：所有被接触者均被及时追踪并隔离。
提前离开容量由命题\ref{prop:main-structure}给出，第\ref{sec:switching-mechanism}节的边际成本分解说明其来源。
这只是既定动力学与成本下的数学结论，不自动适用于含其他健康损失或资源约束的实际决策。
非隔离感染者阈值 $K$、自然感染增长阈值 $h$、以及出现在不变量中的 $p$ 是不同的量；切换点由特征线上的 $\Theta$ 匹配确定。

\begin{remark}[本稿未完成、且未用于主定理的扩展证明]
\label{rem:unproved-extensions}
任意时变 $c(t)$ 的全域值函数构造、无穷时域终端处理和无条件唯一性未在本稿证明。
离散网格加密和 $\varepsilon\downarrow0$ 的收敛、时变高峰后的真实安全延拓也未证明。
跟踪能力受限（$q\le\bar q<1$）时的最优控制未在本稿研究。
完全跟踪后残余感染生成、隔离者回流、联合控制以及参数不确定的情形仍需另行建立可行域和验证函数。
特别地，跟踪能力上限为 $\bar q<1$ 时，容量边界还必须满足 $\bar q\ge1-h/s$；
不能只把本稿的 $1$ 替换成 $\bar q$ 后沿用最优结构定理。
\end{remark}
\fi
```

新文：

```latex

% 数值章节已内联；下方两个标记块由数值导出程序定点更新。
\providecommand{\NumFigureRoot}{../figures/numerical_scenarios}
\providecommand{\NumTheoryRef}[2]{#2~\ref{#1}}
% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES
% MATLAB 解析公式评价；不含优化器结果。
\providecommand{\NumJRefEOne}{0.416186}
\providecommand{\NumJRefETwo}{1.529511}
\providecommand{\NumJRefEThree}{0.433981}
\providecommand{\NumJRefEFour}{1.268835}
\providecommand{\NumJRefEFive}{0.536233}
\providecommand{\NumSBRef}{0.54769512}
\providecommand{\NumSwitchSEOneRef}{0.51017169}
\providecommand{\NumSwitchIEOneRef}{0.13423054}
\providecommand{\NumMaxReleaseRef}{7.44746905}
\providecommand{\NumExitETwoTheory}{5.86950254}
\providecommand{\NumExitEFourTheory}{1.08077528}
% END AUTO-GENERATED NUMERICAL REFERENCE VALUES

% BEGIN AUTO-GENERATED NUMERICAL RESULTS
% 从 data/numerical_scenarios 的真实结果生成；条件开关由 main.tex 定义。
\NumResultsVerifiedtrue
\NumRobustnessCompletetrue
\renewcommand{\NumRobustnessStatement}{数值接受及容量控制比较容差于保存求解后调整，取值与原严格记录见复现附录。五例常值 $q=0.7$ 和固定种子随机初猜的阶段一致，成本最大绝对差为 $\num{6.1e-13}$。在当前接受容差下，最细两级成本与事件区间比较通过 E1、E2、E3、E4、E5。$n=2000$ 的 E2、E4 存在长中间控制块与阶段识别异常。该比较不提供收敛阶。$n=2000$ 的 E1、E3、E5 成本比较仍未通过。E3 的粗网格负成本差小于容量超出所致的解析最优值下降，与容量超出相容。固定步长时域复核五例通过。阈值复核通过。有限样本与浮点诊断不替代解析证明。}
\renewcommand{\NumReproducibilityDetails}{默认协议已记录 35/35 个不同配置，其中 30 个同时通过数值接受与理论比较。协议是否完成与比较是否一致分别记录。本次在保存求解后调整状态及容量接受容差为 $\num{1e-05}$、容量段控制与 $q_B$ 区间均值的绝对误差容差为 $\num{0.003}$，并重新评估全部保存结果；成本相对误差容差 $\num{0.0001}$ 与事件区间判据保持不变。原严格判据及其未通过记录另行保留。按保存求解前预定的原判据（状态容差 $\num{1e-06}$、容量容差 $\num{1e-06}$、容量段控制容差 $\num{0.002}$），数值接受与理论比较分别通过 29/35 与 29/35，同时通过 28/35；修订判据只重新划定浮点接受尺度，不提供新的收敛证据。五例常值 $q=0.7$ 和固定种子随机初猜的阶段一致，成本最大绝对差为 $\num{6.1e-13}$。在所列接受容差下，固定时域网格复核的最细两级成本与事件区间比较通过 E1、E2、E3、E4、E5。E2、E4 的 $n=2000$ 长中间控制块与阶段识别异常仍保留在配套记录中。该结果只支持所测最细两级的一致性，不给出收敛阶。$n=2000$ 的 E1、E3、E5 成本比较仍未通过。E3 的 $n=2000$ 负成本差为 $\num{-6.76e-05}$，重积分容量超出 $\varepsilon_K=\num{7.83e-06}$；把容量放宽为 $K+\varepsilon_K$ 后，解析最优值下降 $\num{1.08e-04}$，大于该负差。因此该负差与容量超出相容，评估记录中的 unresolved-discrepancy 分类按原样保留。固定步长时域复核五例通过。阈值复核通过。全部记录见配套文件；有限样本与浮点诊断不替代解析证明。}
\providecommand{\NumHorizon}{300}
\providecommand{\NumIntervals}{4000}
\providecommand{\NumDegree}{2}
\providecommand{\NumMeshDetails}{按预先指定设置，E2 使用 $n=8000$，E4 使用 $n=8000$；其余算例保留基准网格。图表均采用各例最终保存的结果。}
\providecommand{\NumJOclEOne}{0.416205}
\providecommand{\NumJOclETwo}{1.529523}
\providecommand{\NumJOclEThree}{0.433999}
\providecommand{\NumJOclEFour}{1.268831}
\providecommand{\NumJOclEFive}{0.536256}
\providecommand{\NumExitETwoStart}{5.85000000}
\providecommand{\NumExitETwoEnd}{5.88750000}
\providecommand{\NumExitEFourStart}{1.05000000}
\providecommand{\NumExitEFourEnd}{1.08750000}
\providecommand{\NumNeutralETwoCostDifference}{5.78648240435e-13}
\providecommand{\NumEFourSignedCostDifference}{-3.68275844664e-06}
\providecommand{\NumEFourCapacityExcess}{7.70286958773e-07}
\providecommand{\NumFindingWaiting}{实际控制输出中，E1 和 E2 分别识别出 $0\to 1\to 0$ 与 $0\to q_B\to 1\to 0$。E1 的完全跟踪开始区间为 $[6.975,7.05]$。对应端点的感染比例仍低于容量上限。E2 的容量退出区间为 $[5.85,5.8875]$。}
\providecommand{\NumFindingTrackingBoundary}{E3、E4、E5 的实际阶段依次为 $1\to 0$、$q_B\to 1\to 0$ 和 $1\to 0$。E3、E5 均从初始时刻采用完全跟踪。E4 的容量退出区间为 $[1.05,1.0875]$。E2、E4 的理论容量退出时刻均落在上述单网格过渡区间内；首个纯完全跟踪单元的起点仍不等同于连续切换点。}
\providecommand{\NumCheckStatement}{对原始分段常数控制逐区间重积分后，五例最大容量超出量为 $\num{8e-07}$，与配点状态的最大差异为 $\num{8.6e-08}$；末尾 $20$ 个时间单位内最大控制幅值为 $\num{0}$。各例终端状态均通过零控制安全延拓核查。这些浮点检查用于排查截断及离散问题，不是连续可行性的严格证明。}
\providecommand{\NumOverallFinding}{五例成本相对解析参考的最大差异约为 $0.00459\%$。计算结果支持这五个初值下的阶段顺序及切换位置预测；切换位置的偏差应结合控制区间宽度和过渡单元解释。E4 的离散成本比解析参考低 $\num{3.68e-06}$，重积分轨道有 $\varepsilon_K=\num{7.7e-07}$ 的容量超出；把容量放宽为 $K+\varepsilon_K$ 后，解析最优值下降 $\num{1.16e-05}$，大于该负差。因此该控制的成本仍不低于放宽容量后的解析最优值，负差与容量超出相容，不构成低于解析最优值的连续时间可行控制。}
\providecommand{\NumErrorTableRows}{E1 & \num{1.91e-05} & \num{4.59e-03} & \num{2.97e-07} & \num{4.05e-06} & 是 \\ E2 & \num{1.22e-05} & \num{7.98e-04} & \num{7.99e-07} & \num{1.28e-05} & 是 \\ E3 & \num{1.75e-05} & \num{4.03e-03} & \num{4.80e-08} & \num{6.60e-07} & 是 \\ E4 & \num{-3.68e-06} & \num{-2.90e-04} & \num{7.70e-07} & \num{1.16e-05} & 是 \\ E5 & \num{2.32e-05} & \num{4.32e-03} & \num{5.57e-08} & \num{7.76e-07} & 是 \\}
\providecommand{\NumResidualSummary}{五例成本相对解析参考差的绝对值最大为 $\num{0.00459}\%$。重积分最大容量超出为 $\num{7.99e-07}$，与配点状态的最大偏差为 $\num{8.57e-08}$。末段最大控制幅值为 $\num{0}$，各例终端状态均通过零控制安全检查。按求解前预定的原判据，数值接受与理论比较同时通过 28/35；按求解后修订的判据，同时通过 30/35；修订只调整浮点接受尺度，不提供新的收敛证据。未通过的网格记录（E2、E4 在 $n=2000$ 的阶段识别异常；E1、E3、E5 在 $n=2000$ 的成本比较未通过）见补充材料。}
% END AUTO-GENERATED NUMERICAL RESULTS
\providecommand{\NumMeshDetails}{}

% Missing actual figures remain blank. Never substitute predicted OCP plots.
\newcommand{\NumFigureOrBlank}[2]{%
  \IfFileExists{\NumFigureRoot/#1}{%
    \includegraphics[width=0.97\linewidth]{\NumFigureRoot/#1}%
  }{%
    \fbox{\parbox[c][#2][c]{0.93\linewidth}{\mbox{}}}%
  }%
}
\newcommand{\NumFindingParagraph}[1]{\par\smallskip #1\par\smallskip}

\section{数值方法与实验设置}
\label{sec:numerical-method}

本节围绕不同初值区域，比较解析最优策略与直接配点输出，
重点考察等待阶段、容量弧和完全跟踪阶段的出现顺序及其连接位置。
算例组织借鉴 \citet[第6节]{AvramFreddiGoreac2022} 的区域展示方式，
但该文含目标约束的有限时域问题不作为本文截断处理的等价性依据。
全局最优性与几乎处处唯一性分别由
\NumTheoryRef{thm:verification}{验证定理}和
\NumTheoryRef{thm:unique-q}{唯一性定理}给出；
数值实验用于检验这些解析结论的计算一致性。

五个主算例采用相同参数
\begin{equation}
 \beta=0.5,\qquad c=2,\qquad\gamma=0.3,\qquad K=0.15,
 \label{eq:numerical-common-parameters}
\end{equation}
仅改变初始状态。
$s,i$ 为相对于初始总量的比例，允许 $s_0+i_0<1$；
此时 $h=0.3$、$\ell=p=0.15$。
这些参数用于展示理论结构，不作为特定疫情的参数标定。

直接配点处理如下固定时域问题：
\begin{equation}
\begin{aligned}
 \min_q\quad &J_T(q)=\int_0^T \beta cq(t)\,\mathrm dt,\\
 \text{满足}\quad
 &\dot s=-c[\beta+(1-\beta)q]si,\qquad
 \dot i=[\beta c(1-q)s-\gamma]i,\\
 &0\le q\le1,\quad 0\le s\le1,\quad0\le i\le K,\\
 &(s(0),i(0))=(s_0,i_0).
\end{aligned}
\label{eq:numerical-ocp}
\end{equation}
该问题不增加终端状态约束、终端成本或二次控制正则化，
也不固定阶段数、切换时刻或容量控制。
解析策略可用于初始化，但不进入数值优化的目标或额外约束。

计算方法为 MATLAB/OpenOCL 直接配点\citep{Koenemann2019OpenOCL}，
通过 CasADi\citep{Andersson2019CasADi} 构造离散问题，
由 IPOPT 求解非线性规划\citep{WachterBiegler2006}。
基准设置为 $T=\NumHorizon$、$n=\NumIntervals$、$d=\NumDegree$；
控制在每个网格区间内为常数。
\NumMeshDetails
控制成本在完整求解时域上按实际区间长度计算：
\begin{equation}
 J_{\mathrm{OCL}}=\beta c\sum_{k=1}^{n}q_k\Delta t_k.
 \label{eq:numerical-cost-sum}
\end{equation}
绘图窗口不作为成本积分范围，求解输出不通过平滑或裁剪替换。

对于每个待报告结果，用原始分段常数控制重新积分状态方程，
检查区间内部的容量峰值、与配点状态的偏差以及终端零控制延拓。

固定 $T=300$ 的直接配点加终端检查是一种终端处理，
不等同于原无穷时域问题。
终端检查采用式\eqref{eq:uncontrolled-future-peak}中的无控制未来峰值
$P_0(s(T),i(T))$，终端状态取自重积分轨道，
并核查末段控制是否为零。
若该轨道在 $[0,T]$ 上满足 $i\le K$，且 $P_0(s(T),i(T))\le K$，
则在 $T$ 之后令 $q=0$，由引理\ref{lem:safe-invariant}的安全集正向不变性，
所得控制对原无穷时域问题可行，其完整成本为 $J_{\mathrm{OCL}}$，
从而 $J_{\mathrm{OCL}}\ge V(x_0)$。
若重积分轨道有最大容量超出 $\varepsilon_K>0$，
且终端满足 $P_0(s(T),i(T))\le K+\varepsilon_K$，
则同一延拓只保证对容量 $K+\varepsilon_K$ 可行，
相应结论为 $J_{\mathrm{OCL}}\ge V_{K+\varepsilon_K}(x_0)$；
这里 $V_{K'}$ 表示容量为 $K'$ 时的值函数。
这给出表\ref{tab:numerical-errors}中容量放宽对照的依据。
上述可行性推论以连续轨道满足相应条件为前提，
重积分及终端检查本身仍是浮点诊断。
本文没有证明离散有限时域最优值随网格加密收敛到 $V$，
也不以这些诊断代替该收敛性结论。

阶段依据数值控制及容量接近程度识别，切换位置按过渡网格区间报告。
已有复核改变初始猜测、网格、终止时刻及阶段识别阈值，
完整配置、判据与诊断结果见补充材料附录\ref{app:numerical-reproducibility}。

\section{不同初值区域下的数值验证}
\label{sec:numerical-results}

\subsection{代表初值与相平面分区}

表\ref{tab:numerical-scenarios}的五个初值覆盖表\ref{tab:optimal-stages}中的两种等待区、
立即完全跟踪区及容量线上 $s_B$ 两侧的状态，
用于检验\NumTheoryRef{thm:verification}{验证定理}给出的阶段结构与成本。

由安全边界和切换条件的数值评价得
\begin{equation}
 s_B\approx\NumSBRef,
 \label{eq:numerical-sB}
\end{equation}
其中 $(s_B,K)$ 为切换曲线与容量线的交点。
图\ref{fig:optimal-partition}给出成本分区的理论几何，图\ref{fig:numerical-regions}将 E1--E5 的直接配点轨道与该几何叠加比较。

\begin{table}[H]
\centering
\small
\setlength{\tabcolsep}{4.2pt}
\caption{代表初值、理论控制结构与控制成本。$J_{\mathrm{ref}}$ 为解析公式的数值评价，
$J_{\mathrm{OCL}}$ 为直接配点返回控制在完整求解时域内的成本。}
\label{tab:numerical-scenarios}
\begin{tabular}{@{}clclrr@{}}
\toprule
算例 & $(s_0,i_0)$ & 区域 & 理论结构 & $J_{\mathrm{ref}}$ & $J_{\mathrm{OCL}}$\\
\midrule
E1 & $(0.75,0.01)$ & $\mathcal W_\Gamma$ & $0\to1\to0$ & \NumJRefEOne & \NumJOclEOne\\
E2 & $(0.99,0.01)$ & $\mathcal W_K$ & $0\to q_B\to1\to0$ & \NumJRefETwo & \NumJOclETwo\\
E3 & $(0.50,0.14)$ & $\mathcal T$ & $1\to0$ & \NumJRefEThree & \NumJOclEThree\\
E4 & $(0.70,0.15)$ & $\mathcal B$ & $q_B\to1\to0$ & \NumJRefEFour & \NumJOclEFour\\
E5 & $(0.50,0.15)$ & $\mathcal T\cap\{i=K\}$ & $1\to0$ & \NumJRefEFive & \NumJOclEFive\\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[H]
\centering
\small
\setlength{\tabcolsep}{3pt}
\caption{主结果的带符号成本差与约束误差。
$J_{\mathrm{ref}}=V_K(x_0)$ 为解析参考值，相对差为
$(J_{\mathrm{OCL}}-J_{\mathrm{ref}})/J_{\mathrm{ref}}$。
按第\ref{sec:numerical-method}节的终端延拓逻辑，
末列检查成本差是否不小于 $-(V_K-V_{K+\varepsilon_K})$；
该浮点比较不构成严格连续可行性的证明。}
\label{tab:numerical-errors}
\begin{tabular}{@{}crrrrr@{}}
\toprule
算例 & $J_{\mathrm{OCL}}-J_{\mathrm{ref}}$ & \shortstack{相对差\\（\%）} & $\varepsilon_K$ & $V_K-V_{K+\varepsilon_K}$ & \shortstack{是否满足\\$J_{\mathrm{OCL}}\ge V_{K+\varepsilon_K}$}\\
\midrule
\NumErrorTableRows
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN1_regions.pdf}{4.2cm}
\caption{理论分区与直接配点轨道的相平面对照。
图中叠加 E1--E5 的初始点和 OpenOCL 轨道，并标出安全边界、切换曲线 $\Gamma_K$、
容量线 $i=K$ 及两种等待区的公共边界。理论曲线与数值轨道采用不同线型或标记；
灰色点划线为 $s=h$，灰色虚线为 $s+i=1$。}
\label{fig:numerical-regions}
\end{figure}


\subsection{两种等待区域的对照}

E1 与 E2 保持 $i_0=0.01$ 相同，分别位于 $\mathcal W_\Gamma$ 和 $\mathcal W_K$。
按表\ref{tab:optimal-stages}及\NumTheoryRef{def:candidate}{反馈构造}，
两者的差别是等待后是否出现正长度容量弧。
图\ref{fig:numerical-waiting}检验这一差别，以及完全跟踪的开始位置：
E1 的解析参考为 $(\NumSwitchSEOneRef,\NumSwitchIEOneRef)$，E2 的参考为 $(s_B,K)$。

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN2_waiting.pdf}{5.0cm}
\caption{两种等待区域下的控制与感染比例：左列为 E1，右列为 E2；
上排为 $q(t)$，下排为 $i(t)$。
每幅图比较解析参考与 OpenOCL 结果，数值控制按分段常数形式显示，
感染图中的水平线表示容量 $K$。}
\label{fig:numerical-waiting}
\end{figure}

\NumFindingParagraph{\NumFindingWaiting}

不存在容量平台与全时域内不接触容量并非同一命题。
解析策略在安全边界解除后，感染比例可以沿无控制轨道再次上升至 $K$，
但不超过它；此时 $q=0$，不应将这种后续接触误判为容量控制弧。

\subsection{立即完全跟踪与容量边界初值}

E3 检验内部初值 $(0.50,0.14)$ 的立即完全跟踪；
E4、E5 保持 $i_0=K$ 相同，检验 $0.70>s_B$ 与 $0.50<s_B$ 时初始阶段的差别。
表\ref{tab:optimal-stages}及\NumTheoryRef{def:candidate}{反馈构造}分别给出
$1\to0$、$q_B\to1\to0$、$1\to0$ 的参考结构，
图\ref{fig:numerical-boundary-tracking}与保存控制逐一比较。

另一个比较是 E2 与 E4 在容量退出时的状态。
两例到达该事件的时间不同，但理论上均经过同一状态 $(s_B,K)$；
从该点起的后续解析轨道相同。
因此可以在相平面中比较其数值退出位置，而不要求不同算例的时间序列重合。

\begin{figure}[H]
\centering
\NumFigureOrBlank{FigN3_boundary_tracking.pdf}{5.0cm}
\caption{立即完全跟踪与容量边界初值的对照。
从左到右为 E3、E4、E5，上排为 $q(t)$，下排为 $i(t)$。
解析参考与 OpenOCL 结果的比较重点为初始控制阶段、容量平台是否出现，以及解除位置。}
\label{fig:numerical-boundary-tracking}
\end{figure}

\NumFindingParagraph{\NumFindingTrackingBoundary}

\subsection{成本、约束误差与剩余残差}

表\ref{tab:numerical-errors}同时报告成本差、重积分容量超出及放宽容量后的值函数下降。
五例均满足表中的放宽容量成本比较；其中 E4 的负成本差小于容量放宽导致的值函数下降。
存在容量超出的离散结果不能称为优于解析最优策略的严格可行控制。
配点与重积分状态的偏差用于诊断动力学离散，
不等同于数值状态与解析最优轨道之间的误差；切换位置仍应结合过渡网格宽度解释。

\NumFindingParagraph{\NumResidualSummary}
\FloatBarrier

\section{\texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论}}
\label{sec:time-varying}
现在令 $c(t)>0$ 为给定的可测、局部本质有界函数。
由于恢复率 $\gamma$ 不随时间缩放，令 $\vartheta(t)=\int_0^t c(v)\dd v$ 后，
在该时间变换的值域内仍按几乎处处意义有
\[
\frac{\dd i}{\dd\vartheta}=\beta(1-q)si-\frac{\gamma}{c(t(\vartheta))}i.
\]
因此一般不能化为本稿的常系数问题。
本节仅陈述在另行建立值函数和验证条件后适用的公式与充分条件；
不声称已经解决任意时变 $c$ 的存在性、全局验证或唯一性。

\subsection{非自治 HJB 方程}
对具体定义的时变问题，在值函数 $V(t,s,i)$ 具备所需正则性、动态规划可作微分化的点，
内部 HJB 的条件性微分形式为
\begin{equation}
\begin{aligned}
0=V_t+\min_{q\in \mathcal Q(t,s,i)}\Big\{&-c(t)[\beta+(1-\beta)q]siV_s\\
&+[\beta c(t)(1-q)s-\gamma]iV_i+\beta c(t)q\Big\}.
\end{aligned}
\label{eq:time-HJB}
\end{equation}
当 $c$ 仅可测时，上式至多按时间几乎处处理解：在相应的 Lebesgue 点和所需值函数导数存在处使用，
不要求它在每个指定时刻都是经典等式。
若进一步用于验证，仍须针对每条被比较的轨道建立复合函数的链式法则和沿轨道的几乎处处不等式；
仅有状态--时间空间中几乎处处的等式，不自动保证它沿任意轨道成立。
内部取 $\mathcal Q=[0,1]$；容量边界在上述几乎处处时间意义下的内指或切向速度条件对应
\begin{equation}
\mathcal Q(t,s,K)=\left[\max\left\{0,1-\frac{\gamma}{\beta c(t)s}\right\},1\right].
\label{eq:time-boundary-set}
\end{equation}
切换系数为
\begin{equation}
\Sigma(t,s,i)=\beta c(t)-c(t)si[(1-\beta)V_s+\beta V_i].
\label{eq:time-switch}
\end{equation}
式 \eqref{eq:time-boundary-set}--\eqref{eq:time-switch} 不把时间零测集上的 $c,q$ 代表值作为额外的点态轨道约束。
若在时间 $t$ 定义无控制安全集，它必须使用从 $t$ 开始的\emph{完整未来接触率路径}，
不能仅把常系数安全集中的 $c$ 换成当前 $c(t)$。

\begin{proposition}[条件性的时变唯一性充分条件]
\label{prop:time-conditional}
对某个已经明确定义的时变问题，假设最优解存在，且已经证明对任意最优轨道的验证等式。
进一步假设：在所有可能被最优轨道经过的状态--时间点，验证等式使控制几乎处处等于同一单值反馈 $Q(t,x)$；
该反馈从给定初值生成的可行 Carath\'eodory 解唯一。
则最优控制几乎处处唯一。
\end{proposition}
\begin{proof}
任意最优控制均须沿自己的轨道满足 $q(t)=Q(t,x(t))$ 几乎处处。
所有最优状态轨道因此满足同一闭环方程与初值，由闭环唯一性得轨道一致，进而控制几乎处处一致。
\end{proof}
内部 $\Sigma\ne0$、容量上受限极小元单值，是控制选择单值的充分途径，
但仅在一条候选轨道上检查这些性质不足以排除所有其他最优轨道。
常接触率平台的唯一性反而说明点态单值不是最优控制唯一的必要条件。

\subsection{有限时域严格凸正则化}
另取固定 $T<\infty$ 及明确的终端数据，可研究不同于原无穷时域问题的正则化目标
\begin{equation}
J_\varepsilon(q)=\int_0^T\left[\beta c(t)q(t)+\frac\varepsilon2q(t)^2\right]\dd t,
\qquad\varepsilon>0.
\label{eq:regularized-cost}
\end{equation}
\begin{proposition}[唯一的点态正则化极小元]
\label{prop:regularized-pointwise}
若相应的有限时域值函数 $V_\varepsilon^T$ 在所考虑的点可微，
则固定满足上述时间约定的 $(t,s,i)$ 及其值梯度时，Hamiltonian 的内部极小元唯一，形式为
\begin{equation}
q_\varepsilon^*(t,s,i)=\proj_{[0,1]}
\left(\frac{c(t)si[(1-\beta)\partial_sV_\varepsilon^T+\beta\partial_iV_\varepsilon^T]-\beta c(t)}\varepsilon\right).
\label{eq:projection-feedback}
\end{equation}
容量边界上将投影区间换为 \eqref{eq:time-boundary-set}。
\end{proposition}
\begin{proof}
关于 $q$ 的二阶导数为 $\varepsilon>0$，无约束一阶条件给出括号中的值，
加入区间约束后取投影。
该计算只证明点态严格凸性；只有另行完成验证、达到性和可行闭环唯一性，才能进一步推出整个控制问题的唯一最优解。
\end{proof}
若需控制变化惩罚，可在离散目标中加入相邻控制差的平方，或在连续问题中把 $q$ 作为状态。
这些都是不同的控制问题，不能不经证明就视为原线性成本问题的等价改写。

\section{同时控制接触率与跟踪比例时的限制}
若把 $c$ 也作为控制并允许 $c=0$，而仍仅使用 \eqref{eq:linear-cost}，
则 $c=0,q=0$ 给出零成本可行方案，问题退化。
联合控制需另行定义接触减少和跟踪成本，例如
\begin{equation}
\int_0^T[\alpha_c(c_0-c)^2+\alpha_q q^2+\alpha_{cq}cq]\dd t,
\label{eq:joint-cost}
\end{equation}
并明确控制约束。
该示例中的权重须另行保证非负性或所需凸性；即使运行成本严格凸，
动力学中的 $cq$ 项以及非线性状态约束也不会自动给出整个问题的严格凸性。
本稿不为此扩展声称全局唯一性。

\section{模型假设与理论边界}
\label{sec:limitations}
本稿的 $q=1$ 代表理想化的完美追踪：所有被接触者均被及时追踪并隔离。
提前离开容量由命题\ref{prop:main-structure}给出，第\ref{sec:switching-mechanism}节的边际成本分解说明其来源。
这只是既定动力学与成本下的数学结论，不自动适用于含其他健康损失或资源约束的实际决策。
非隔离感染者阈值 $K$、自然感染增长阈值 $h$、以及出现在不变量中的 $p$ 是不同的量；切换点由特征线上的 $\Theta$ 匹配确定。

\begin{remark}[本稿未完成、且未用于主定理的扩展证明]
\label{rem:unproved-extensions}
任意时变 $c(t)$ 的全域值函数构造、无穷时域终端处理和无条件唯一性未在本稿证明。
离散网格加密和 $\varepsilon\downarrow0$ 的收敛、时变高峰后的真实安全延拓也未证明。
跟踪能力受限（$q\le\bar q<1$）时的最优控制未在本稿研究。
完全跟踪后残余感染生成、隔离者回流、联合控制以及参数不确定的情形仍需另行建立可行域和验证函数。
特别地，跟踪能力上限为 $\bar q<1$ 时，容量边界还必须满足 $\bar q\ge1-h/s$；
不能只把本稿的 $1$ 替换成 $\bar q$ 后沿用最优结构定理。
\end{remark}

```

### theory-branch-5：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
\ifNumResultsVerified
五个代表初值的直接配点结果再现了两种等待方式、内部立即完全跟踪，
以及容量线上切换阈值两侧的不同初始阶段。
该比较支持所选算例的结构一致性，不构成全域最优性或唯一性的额外证明。
\fi
\fi
```

新文：

```latex

\ifNumResultsVerified
五个代表初值的直接配点结果再现了两种等待方式、内部立即完全跟踪，
以及容量线上切换阈值两侧的不同初始阶段。
该比较支持所选算例的结构一致性，不构成全域最优性或唯一性的额外证明。
\fi

```

### theory-branch-6：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
时变接触率仅保留条件性的验证与唯一性讨论。
严格凸正则化给出的是固定状态和梯度下的唯一点态极小元，不能单凭此推出整个非线性控制问题全局唯一。
本稿未完成的扩展证明已在注\ref{rem:unproved-extensions}中列明，不作为常接触率主定理的结论。
\fi
```

新文：

```latex

时变接触率仅保留条件性的验证与唯一性讨论。
严格凸正则化给出的是固定状态和梯度下的唯一点态极小元，不能单凭此推出整个非线性控制问题全局唯一。
本稿未完成的扩展证明已在注\ref{rem:unproved-extensions}中列明，不作为常接触率主定理的结论。

```

### theory-branch-7：删除 TheoryOnly 专属分支及条件壳，保留主文分支

原文：

```latex
\ifdefined\TheoryOnly\else
\section{补充材料 S：数值复现、复核与诊断记录}
\label{app:numerical-reproducibility}

本附录将在定稿时拆为独立的补充材料文件，本阶段仍保留在主文版本中。
数值代码位于 \path{matlab/numerical_scenarios/}。

独立解析检查点及其生成程序位于
\path{validation/numerical_scenarios/}；
检查点只评价正文中的解析构造，不调用数值优化器。
具体环境准备及检查点生成命令见该目录和数值目录的说明文件。
从仓库根目录启动 MATLAB 后运行：
\begin{lstlisting}
addpath(fullfile(pwd, ...
 'tracing_isolation_optimal_control_complete', ...
 'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
make_numerical_figures();
export_numerical_latex();
\end{lstlisting}

\texttt{all} 运行预先规定的主算例和附加复核。
各次求解分别保存初值、参数、网格、初始化、求解状态和原始控制数组，
并记录求解时的源码指纹与环境信息。
重做后处理不改写原求解的来源信息。
作图和正文数据导出只读取已保存且来源明确的结果，
不在缺少结果时以解析参考代替数值优化输出。

\NumFindingParagraph{\NumCheckStatement}
\NumFindingParagraph{\NumRobustnessStatement}
\NumFindingParagraph{\NumOverallFinding}
\NumFindingParagraph{\NumReproducibilityDetails}

正文中的数值摘要与所选结果文件保持一一对应。
完整记录分别位于：
\begin{itemize}
\item 初猜、网格、时域及阶段识别阈值复核：\\
\path{data/numerical_scenarios/revision_checks/}。
\item 事件候选、检测区间及主结果诊断：\\
\path{data/numerical_scenarios/numerical_checks.json}。
\item 容差重评与原严格记录：\\
\path{validation/numerical_scenarios/tolerance_revision_20261010/}。
\item S2 的重跑、原判据重评及逐条对照报告：\\
\path{validation/numerical_scenarios/rerun_20261020/}；\\
其中判据计数来源为 \path{S2.6/assessment_revision_report.json}。
\end{itemize}
\clearpage
\fi
```

新文：

```latex

\section{补充材料 S：数值复现、复核与诊断记录}
\label{app:numerical-reproducibility}

本附录将在定稿时拆为独立的补充材料文件，本阶段仍保留在主文版本中。
数值代码位于 \path{matlab/numerical_scenarios/}。

独立解析检查点及其生成程序位于
\path{validation/numerical_scenarios/}；
检查点只评价正文中的解析构造，不调用数值优化器。
具体环境准备及检查点生成命令见该目录和数值目录的说明文件。
从仓库根目录启动 MATLAB 后运行：
\begin{lstlisting}
addpath(fullfile(pwd, ...
 'tracing_isolation_optimal_control_complete', ...
 'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
make_numerical_figures();
export_numerical_latex();
\end{lstlisting}

\texttt{all} 运行预先规定的主算例和附加复核。
各次求解分别保存初值、参数、网格、初始化、求解状态和原始控制数组，
并记录求解时的源码指纹与环境信息。
重做后处理不改写原求解的来源信息。
作图和正文数据导出只读取已保存且来源明确的结果，
不在缺少结果时以解析参考代替数值优化输出。

\NumFindingParagraph{\NumCheckStatement}
\NumFindingParagraph{\NumRobustnessStatement}
\NumFindingParagraph{\NumOverallFinding}
\NumFindingParagraph{\NumReproducibilityDetails}

正文中的数值摘要与所选结果文件保持一一对应。
完整记录分别位于：
\begin{itemize}
\item 初猜、网格、时域及阶段识别阈值复核：\\
\path{data/numerical_scenarios/revision_checks/}。
\item 事件候选、检测区间及主结果诊断：\\
\path{data/numerical_scenarios/numerical_checks.json}。
\item 容差重评与原严格记录：\\
\path{validation/numerical_scenarios/tolerance_revision_20261010/}。
\item S2 的重跑、原判据重评及逐条对照报告：\\
\path{validation/numerical_scenarios/rerun_20261020/}；\\
其中判据计数来源为 \path{S2.6/assessment_revision_report.json}。
\end{itemize}
\clearpage

```

### sec:time-varying：整节删除时变接触率条件性结论

原文：

```latex
\section{\texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论}}
\label{sec:time-varying}
现在令 $c(t)>0$ 为给定的可测、局部本质有界函数。
由于恢复率 $\gamma$ 不随时间缩放，令 $\vartheta(t)=\int_0^t c(v)\dd v$ 后，
在该时间变换的值域内仍按几乎处处意义有
\[
\frac{\dd i}{\dd\vartheta}=\beta(1-q)si-\frac{\gamma}{c(t(\vartheta))}i.
\]
因此一般不能化为本稿的常系数问题。
本节仅陈述在另行建立值函数和验证条件后适用的公式与充分条件；
不声称已经解决任意时变 $c$ 的存在性、全局验证或唯一性。

\subsection{非自治 HJB 方程}
对具体定义的时变问题，在值函数 $V(t,s,i)$ 具备所需正则性、动态规划可作微分化的点，
内部 HJB 的条件性微分形式为
\begin{equation}
\begin{aligned}
0=V_t+\min_{q\in \mathcal Q(t,s,i)}\Big\{&-c(t)[\beta+(1-\beta)q]siV_s\\
&+[\beta c(t)(1-q)s-\gamma]iV_i+\beta c(t)q\Big\}.
\end{aligned}
\label{eq:time-HJB}
\end{equation}
当 $c$ 仅可测时，上式至多按时间几乎处处理解：在相应的 Lebesgue 点和所需值函数导数存在处使用，
不要求它在每个指定时刻都是经典等式。
若进一步用于验证，仍须针对每条被比较的轨道建立复合函数的链式法则和沿轨道的几乎处处不等式；
仅有状态--时间空间中几乎处处的等式，不自动保证它沿任意轨道成立。
内部取 $\mathcal Q=[0,1]$；容量边界在上述几乎处处时间意义下的内指或切向速度条件对应
\begin{equation}
\mathcal Q(t,s,K)=\left[\max\left\{0,1-\frac{\gamma}{\beta c(t)s}\right\},1\right].
\label{eq:time-boundary-set}
\end{equation}
切换系数为
\begin{equation}
\Sigma(t,s,i)=\beta c(t)-c(t)si[(1-\beta)V_s+\beta V_i].
\label{eq:time-switch}
\end{equation}
式 \eqref{eq:time-boundary-set}--\eqref{eq:time-switch} 不把时间零测集上的 $c,q$ 代表值作为额外的点态轨道约束。
若在时间 $t$ 定义无控制安全集，它必须使用从 $t$ 开始的\emph{完整未来接触率路径}，
不能仅把常系数安全集中的 $c$ 换成当前 $c(t)$。

\begin{proposition}[条件性的时变唯一性充分条件]
\label{prop:time-conditional}
对某个已经明确定义的时变问题，假设最优解存在，且已经证明对任意最优轨道的验证等式。
进一步假设：在所有可能被最优轨道经过的状态--时间点，验证等式使控制几乎处处等于同一单值反馈 $Q(t,x)$；
该反馈从给定初值生成的可行 Carath\'eodory 解唯一。
则最优控制几乎处处唯一。
\end{proposition}
\begin{proof}
任意最优控制均须沿自己的轨道满足 $q(t)=Q(t,x(t))$ 几乎处处。
所有最优状态轨道因此满足同一闭环方程与初值，由闭环唯一性得轨道一致，进而控制几乎处处一致。
\end{proof}
内部 $\Sigma\ne0$、容量上受限极小元单值，是控制选择单值的充分途径，
但仅在一条候选轨道上检查这些性质不足以排除所有其他最优轨道。
常接触率平台的唯一性反而说明点态单值不是最优控制唯一的必要条件。

\subsection{有限时域严格凸正则化}
另取固定 $T<\infty$ 及明确的终端数据，可研究不同于原无穷时域问题的正则化目标
\begin{equation}
J_\varepsilon(q)=\int_0^T\left[\beta c(t)q(t)+\frac\varepsilon2q(t)^2\right]\dd t,
\qquad\varepsilon>0.
\label{eq:regularized-cost}
\end{equation}
\begin{proposition}[唯一的点态正则化极小元]
\label{prop:regularized-pointwise}
若相应的有限时域值函数 $V_\varepsilon^T$ 在所考虑的点可微，
则固定满足上述时间约定的 $(t,s,i)$ 及其值梯度时，Hamiltonian 的内部极小元唯一，形式为
\begin{equation}
q_\varepsilon^*(t,s,i)=\proj_{[0,1]}
\left(\frac{c(t)si[(1-\beta)\partial_sV_\varepsilon^T+\beta\partial_iV_\varepsilon^T]-\beta c(t)}\varepsilon\right).
\label{eq:projection-feedback}
\end{equation}
容量边界上将投影区间换为 \eqref{eq:time-boundary-set}。
\end{proposition}
\begin{proof}
关于 $q$ 的二阶导数为 $\varepsilon>0$，无约束一阶条件给出括号中的值，
加入区间约束后取投影。
该计算只证明点态严格凸性；只有另行完成验证、达到性和可行闭环唯一性，才能进一步推出整个控制问题的唯一最优解。
\end{proof}
若需控制变化惩罚，可在离散目标中加入相邻控制差的平方，或在连续问题中把 $q$ 作为状态。
这些都是不同的控制问题，不能不经证明就视为原线性成本问题的等价改写。


```

新文：

```latex
（删除，新文为空）
```

### proof-scope-scan：删除数值扫描句

原文：

```latex
任何一个数值扫描都不被用于证明这些全称命题。
```

新文：

```latex
（删除，新文为空）
```

### proof-scope-last-paragraph：删除附录 E 最后校验口径段

原文：

```latex
本稿区分解析证明、符号恒等式检查、有限样本数值检查及排版编译检查。
后面三类检查可发现错误，但均不等价于对所有可行控制的解析证明，也不是形式化证明系统的验证。
```

新文：

```latex
（删除，新文为空）
```

### conclusion-time：删除结论时变段

原文：

```latex
时变接触率仅保留条件性的验证与唯一性讨论。
严格凸正则化给出的是固定状态和梯度下的唯一点态极小元，不能单凭此推出整个非线性控制问题全局唯一。
本稿未完成的扩展证明已在注\ref{rem:unproved-extensions}中列明，不作为常接触率主定理的结论。
```

新文：

```latex
（删除，新文为空）
```

### G1-INTRO-PRELIMINARIES：附录 E 前两段改为新第 4 节证明路线

原文：

```latex
常接触率证明的依赖顺序为：
状态正性和耗散；安全集及有限成本比较策略；有限成本入安全集；
完全跟踪可达域和成本；切换曲线几何；全域候选及达到性；梯度与拼接正则性；
沿任意轨道的验证；全局最优性；最后另证唯一性。
推论\ref{cor:one-dimensional-min}在全局验证之后陈述，不用候选策略族内的极小性替代全控制类比较。
全局最优性确立后，推论\ref{cor:verification-equality}
由沿轨道验证不等式积分得到最优控制的等号条件。
引理\ref{lem:no-early-boundary-exit}据此证明容量弧上的延续性质，
再由定理\ref{thm:unique-q}完成控制与状态轨道的唯一性证明。
上述推论和引理均不依赖定理\ref{thm:unique-q}。

端点存在性由命题\ref{prop:reachable}及引理\ref{lem:tracking-region}处理；
曲线正则性和横截性由命题\ref{prop:Gamma-geometry}、推论\ref{cor:Gamma-labels}处理；
不滑行由引理\ref{lem:strict-crossing}处理，横穿方向与实际分区的衔接由引理\ref{lem:chi-regions}处理。
容量和安全时间集合上的导数关系统一使用式\eqref{eq:ac-level-set}的水平集性质。
局部 Lipschitz 性和终端处理分别由命题\ref{prop:regularity}及引理\ref{lem:finite-entry}证明。
```

新文：

```latex
本节先建立状态正性和耗散、安全集及两类控制弧，再证明有限成本轨道入安全集，并给出后文使用的 HJB 边界条件。
后续构造先处理完全跟踪可达域和成本、切换曲线几何、全域候选及达到性与梯度拼接，再沿任意轨道验证全局最优性；推论\ref{cor:one-dimensional-min}在全局验证之后陈述，不用候选策略族内的极小性替代全控制类比较。
全局最优性确立后，推论\ref{cor:verification-equality}由沿轨道验证不等式积分得到最优控制的等号条件，引理\ref{lem:no-early-boundary-exit}据此证明容量弧上的延续性质，再由定理\ref{thm:unique-q}完成控制与状态轨道的唯一性证明；上述推论和引理均不依赖定理\ref{thm:unique-q}。
具体地，端点存在性由命题\ref{prop:reachable}及引理\ref{lem:tracking-region}处理，曲线正则性和横截性由命题\ref{prop:Gamma-geometry}、推论\ref{cor:Gamma-labels}处理，不滑行由引理\ref{lem:strict-crossing}处理，横穿方向与实际分区的衔接由引理\ref{lem:chi-regions}处理；容量和安全时间集合上的导数关系统一使用式\eqref{eq:ac-level-set}的水平集性质，局部 Lipschitz 性和终端处理分别由命题\ref{prop:regularity}及引理\ref{lem:finite-entry}证明。
```

### G1-INTRO-CONSTRUCTION：新第 5 节导读

原文：

```latex
（新增，原文为空）
```

新文：

```latex
本节从完全跟踪成本的有限可达域出发，依次构造切换曲线、全域候选反馈和候选成本。
随后计算等待分支的梯度并处理拼接正则性，为第\ref{sec:optimality}节沿任意可行轨道的验证准备候选函数。
```

### G1-INTRO-VERIFICATION：新第 6 节导读

原文：

```latex
（新增，原文为空）
```

新文：

```latex
本节利用前节候选函数的梯度和正则性，先建立各分区的 Hamiltonian 关系及沿任意轨道的验证不等式。
再结合有限成本入安全集性质证明全局最优性，并用验证等号条件、容量弧延续和切换曲线横穿逐段确定最优轨道，完成唯一性证明。
```

### G1-TRACKING-PROOF-SKETCH：正文引理证明思路及附录指引

原文：

```latex
（新增，原文为空）
```

新文：

```latex
证明先由同一自然轨道上的不变量比较确定完全跟踪可达性，再以单峰性刻画 $\Delta_\Theta$ 的零集及其在切换点附近的符号。
结合严格横穿和分区关系，可知完全跟踪弧在到达安全集前不再返回等待区；正安全端点给出有限到达时间。
完整证明见附录 \ref{app:tracking-region-proof}。
```

### G1-UNIQUENESS-ROADMAP：唯一性证明路线

原文：

```latex
（新增，原文为空）
```

新文：

```latex
证明先用推论\ref{cor:verification-equality}的等号条件及引理\ref{lem:waiting-HJB}、命题\ref{prop:all-HJB}确定各分区内的控制。
随后由引理\ref{lem:no-early-boundary-exit}确定容量弧上的延续，再用引理\ref{lem:strict-crossing}和引理\ref{lem:chi-regions}处理切换曲线。
最后结合命题\ref{prop:candidate-attainment}、引理\ref{lem:tracking-region}及各段状态方程解的唯一性，依次确定全部阶段和安全延拓。
```

### constant-scope：对应新第 3–7 节并说明一般时变 c 的适定性

原文：

```latex
本节及第\ref{sec:constant-problem}--\ref{sec:constant-uniqueness}节固定

```

新文：

```latex
预备结果中的适定性定理\ref{thm:wellposed}对一般 $c(t)$ 成立。
第\ref{sec:main-results}--\ref{sec:mechanisms}节固定
```

### uniqueness-step-1：仅增加分步前缀

原文：

```latex
\emph{各分区内的控制选择。}
```

新文：

```latex
\emph{第 1 步：各分区内的控制选择。}
```

### uniqueness-step-2：仅增加分步前缀

原文：

```latex
\emph{容量弧上的延续。}
```

新文：

```latex
\emph{第 2 步：容量弧上的延续。}
```

### uniqueness-step-3：仅增加分步前缀

原文：

```latex
\emph{切换曲线上的行为。}
```

新文：

```latex
\emph{第 3 步：切换曲线上的行为。}
```

### uniqueness-step-4：仅增加分步前缀

原文：

```latex
\emph{各阶段轨道的唯一确定。}
```

新文：

```latex
\emph{第 4 步：各阶段轨道的唯一确定。}
```

## 结构 token 变动

标题和节标签在段落审计中剥离；下面完整列出新旧标题，供作者核对层级及标题。

### 原标题

- L89 `section`：引言
- L165 `section`：模型与控制问题
- L168 `subsection`：基本模型
- L204 `subsection`：二维约化与控制问题
- L252 `section`：主结果与最优分区
- L278 `subsection`：安全集与可行性
- L305 `subsection`：全域反馈与阶段结构
- L379 `section`：解的适定性、正性与基本耗散
- L436 `section`：常接触率问题、自然轨道与安全目标集
- L443 `subsection`：自然传播不变量与峰值
- L462 `subsection`：安全集与目标边界
- L483 `section`：两类控制弧与显式成本
- L485 `subsection`：一般控制下的不变量导数
- L509 `subsection`：完全跟踪弧
- L535 `subsection`：容量弧
- L570 `section`：有限成本可行性与首次到达问题
- L633 `section`：HJB 方程与验证所需的边界条件
- L685 `section`：完全跟踪成本的有限可达域及导数
- L774 `section`：切换曲线的存在、单调性及严格横穿
- L953 `section`：全域候选反馈与候选成本
- L1209 `section`：全域梯度、拼接正则性与验证不等式
- L1211 `subsection`：两种等待分支的统一导数
- L1267 `subsection`：内部界面与局部 Lipschitz 性
- L1308 `subsection`：容量 Hamiltonian 与沿任意轨道的链式法则
- L1389 `section`：全局最优性验证
- L1493 `section`：常接触率下控制与轨道的唯一性
- L1715 `subsection`：一维切换成本与全局结论的关系
- L1762 `section`：不变量坐标与切换机制
- L1847 `section`：比较基准、小容量渐近与参数量级
- L1850 `subsection`：纯容量填充与比较指标
- L1885 `subsection`：固定传播概率下的小容量命题
- L1937 `subsection`：参数来源与解析扫描
- L2057 `section`：数值方法与实验设置
- L2135 `section`：不同初值区域下的数值验证
- L2138 `subsection`：代表初值与相平面分区
- L2203 `subsection`：两种等待区域的对照
- L2227 `subsection`：立即完全跟踪与容量边界初值
- L2251 `subsection`：成本、约束误差与剩余残差
- L2262 `section`：\texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论}
- L2274 `subsection`：非自治 HJB 方程
- L2317 `subsection`：有限时域严格凸正则化
- L2343 `section`：同时控制接触率与跟踪比例时的限制
- L2356 `section`：模型假设与理论边界
- L2374 `section`：主要结论
- L2404 `section`：完全跟踪成本导数的逐步计算
- L2433 `section`：容量边界成本积分的逐步计算
- L2446 `section`：小容量渐近的完整推导
- L2530 `section`：梯度拼接与相对正则性的详细证明
- L2654 `section`：证明依赖与校验口径
- L2678 `section`：感染阈值与医疗需求
- L2749 `section`：补充材料 S：数值复现、复核与诊断记录

### 新标题

- L85 `section`：引言
- L161 `section`：模型与控制问题
- L164 `subsection`：基本模型
- L200 `subsection`：二维约化与控制问题
- L248 `section`：主结果与最优分区
- L275 `subsection`：安全集与可行性
- L302 `subsection`：全域反馈与阶段结构
- L376 `section`：预备结果
- L385 `subsection`：解的适定性、正性与基本耗散
- L442 `subsection`：常接触率问题、自然轨道与安全目标集
- L449 `subsubsection`：自然传播不变量与峰值
- L468 `subsubsection`：安全集与目标边界
- L489 `subsection`：两类控制弧与显式成本
- L491 `subsubsection`：一般控制下的不变量导数
- L515 `subsubsection`：完全跟踪弧
- L541 `subsubsection`：容量弧
- L576 `subsection`：有限成本可行性与首次到达问题
- L639 `subsection`：HJB 方程与验证所需的边界条件
- L691 `section`：候选策略的构造
- L698 `subsection`：完全跟踪成本的有限可达域及导数
- L787 `subsection`：切换曲线的存在、单调性及严格横穿
- L966 `subsection`：全域候选反馈与候选成本
- L1161 `subsection`：两种等待分支的统一导数
- L1218 `subsection`：内部界面与局部 Lipschitz 性
- L1259 `section`：全局最优性与唯一性
- L1266 `subsection`：容量 Hamiltonian 与沿任意轨道的链式法则
- L1347 `subsection`：全局最优性验证
- L1451 `subsection`：常接触率下控制与轨道的唯一性
- L1679 `section`：机制与量级
- L1684 `subsection`：一维切换成本与全局结论的关系
- L1731 `subsection`：不变量坐标与切换机制
- L1816 `subsection`：比较基准、小容量渐近与参数量级
- L1819 `subsubsection`：纯容量填充与比较指标
- L1854 `subsubsection`：固定传播概率下的小容量命题
- L1906 `subsubsection`：参数来源与解析扫描
- L1967 `section`：数值结果
- L2031 `subsection`：数值方法与实验设置
- L2109 `subsection`：不同初值区域下的数值验证
- L2112 `subsubsection`：代表初值与相平面分区
- L2177 `subsubsection`：两种等待区域的对照
- L2201 `subsubsection`：立即完全跟踪与容量边界初值
- L2225 `subsubsection`：成本、约束误差与剩余残差
- L2236 `section`：讨论
- L2241 `subsection`：同时控制接触率与跟踪比例时的限制
- L2254 `subsection`：模型假设与理论边界
- L2272 `section`：结论
- L2295 `section`：完全跟踪成本导数的逐步计算
- L2324 `section`：容量边界成本积分的逐步计算
- L2337 `section`：完全跟踪分区可达性与不再返回等待区的证明
- L2408 `section`：梯度拼接与相对正则性的详细证明
- L2532 `section`：小容量渐近的完整推导
- L2616 `section`：感染阈值与医疗需求
- L2687 `section`：补充材料 S：数值复现、复核与诊断记录

## 未解释旧段落

无。

## 未解释新段落

无。
