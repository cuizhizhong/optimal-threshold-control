# 给 Codex：常接触率 HJB 证明的精选增补任务

## 目标文件与核对基线

仓库：`cuizhizhong/optimal-threshold-control`  
分支：`codex/integrate-theory-revision`  
目标：`tracing_isolation_optimal_control_complete/latex/main.tex`  
本次已读取的主稿 Git blob：`929a3a523c059adcd74efc4e47c774e0c38a1c11`。

先检查工作区和目标文件版本，再按下述标签和文字锚点合并。
如果目标文件已经变化，应核对每一段的实际上下文，不得直接回滚到此基线。
本任务是现有证明的局部展开与结果汇总，不是重写模型或引入另一套求解路线。
片段不是可直接单独编译的完整论文，也不能整包 `\input` 到主稿末尾。

## 保留范围

以下内容保持原有数学含义、参数范围及证明顺序：模型、运行成本、所有 Lebesgue 可测可行控制构成的控制类、
安全集、完全跟踪可达域、切换曲线、分区与候选函数公式。

本轮尤其保留 `thm:verification` 的原证明、`cor:verification-equality`、
`lem:no-early-boundary-exit`、`thm:unique-q` 的容量下段零测集、平台延续、严格横穿与安全延拓论证。
对唯一性证明仅在指定位置插入“区间上的积分方程”段落，不整体替换。
时变接触率、正则化、数值代码、既有图表数值不在此次修改范围内。
除明确授权的局部说明和最优结构汇总外，不扩大任何结论。

不要添加控制右连续性、分段连续性、全域 C^1、端点一致时间界、折现，
也不要新增“唯一黏性解”或“全部 PMP 极值分类”作为本稿主定理的前提。
保留既有宏 `\dd`、`\e`、`\Acal`、`\Dcal` 等，不为合并片段更换全文记号。
不将标量 D 全局改名，不新增文献键。

## 数学来源与陈述范围

各正则性、零集和轨道段落是对主稿现有公式的显式推导，应以相邻证明及标签为依据；
不要将这些本模型计算伪称为从教材逐字引述的命题，也不要宣传为新方法。

模型对照使用已有 `MicloSpiroWeibull2022` 期刊版：
第 3 页式(1)给出同一传播率进入两条状态方程，第 3 页式(2)给出 `[beta-b]_+` 成本；
附录 A.1 给出候选函数上下界的验证思路。
原稿已有的 `Liberzon2012` §5.1.4 引用保留，不声称该教材已证明本稿的特定状态约束拼接结论。

## 必须避免的误加内容

1. 不得写 `Gamma_K union B` 在整个 `Omega` 中相对闭；
   切换曲线缺少的下端点 `(e,a(e))` 位于 `Omega` 的安全边界。
   本增补只使用等待区和完全跟踪区的相对开放性，不需要该错误闭性断言。
2. `D` 在 `E` 上的零集写成 `Gamma_K`，不是未经截断的整条 `Gamma_infty`。
3. 不要求孤立切换时刻的经典导数存在，或控制代表值必须同时匹配左右阶段。
4. 保留容量 Hamiltonian 的退化，不把平台极小元改成单点。
5. 新增最优结构推论只在最优性、唯一性之后陈述，不能被用来证明它们。
6. 不写 MSW 完全抑制时“整个系统被冻结”；只有易感坐标不变，感染坐标仍下降。
7. 不写基准直接策略参数区间“大部分不可达”，不新增未经本次复算的数值。

## 合并顺序

下面按逻辑任务编号列出操作。每个片段只执行一次。
已存在等价内容时合并而非叠加；不要把说明文字或本任务书原文写入论文正文。


## 1. 内部界面的梯度延拓与 C^1 拼接

**操作位置：** 在 prop:regularity 的证明中，替换从 \emph{内部值与梯度匹配。} 开始、到 \emph{安全边界连续性。} 之前的全部内容；保留后者及其后各段。

展开已有梯度匹配和局部坐标计算；不要求整个分区闭包或安全边界上全域 C^1。

对应片段：`snippets/01_internal_C1_patching.tex`。

```latex
\emph{内部值与梯度匹配。}
各开分区中的端点和触点映射光滑。
在 $\Gamma_K\cap\{i<K\}$ 上，等待终点趋于当前点，$U$ 两侧均趋于 $W$；
由 \eqref{eq:waiting-gradient}，等待侧梯度的极限为
\[
\left(\frac{p(s-h)}{si(s-r)},\ \frac{p}{i(s-r)}\right),
\]
恰等于切换条件下的 $\nabla W$。
在 $\Phi=\Phi_B,s>s_B,i<K$ 的界面上，两个等待分支的终点均趋于 $(s_B,K)$；
由 $C_B(s_B,s_B)=0$，两侧函数值相同，而共同的梯度极限为
\[
\left(\frac{p(s-h)}{sK(s_B-r)},\ \frac{p}{K(s_B-r)}\right).
\]
上述极限随界面点连续变化。
在每个固定内部界面点的充分小邻域内，所用端点感染值及导数公式的分母保持为正，
故这些公式确实给出各侧梯度到该界面的连续延拓。

下面说明局部拼接的可微性。
两类内部界面分别是 $i=I_\Gamma(s)$ 和
$i=\Phi_B-s+h\ln s$ 的光滑图像，且在不安全内部不相交。
固定其中一个点 $x_*=(s_*,k(s_*))$，其中 $k$ 表示对应图像函数。
缩小邻域后，坐标变换
\[
\Xi(y_1,y_2)=(s_*+y_1,k(s_*+y_1)+y_2)
\]
将以原点为中心的小矩形 $Q$ 映到该点的不安全内部邻域，
并把 $y_2=0$ 映到界面。
该变换及其逆均为 $C^1$。
令 $v=U\circ\Xi$，则 $v$ 连续，在 $Q\cap\{y_2>0\}$ 和
$Q\cap\{y_2<0\}$ 内分别为 $C^1$。
由已证的梯度匹配以及
$\nabla v(y)=(\mathrm D\Xi(y))^{\mathsf T}\nabla U(\Xi(y))$，
两侧梯度可连续拼接为 $Q$ 上的向量值函数 $P$。
当 $y_2\ne0$ 时，从 $\varepsilon y$ 到 $y$ 沿同侧线段积分，
再令 $\varepsilon\downarrow0$，得到
\[
v(y)-v(0)=\int_0^1 P(ty)\cdot y\dd t.
\]
当 $y_2=0$ 时，由连续性从任一侧取极限，等式仍成立。
因此
\[
v(y)-v(0)-P(0)\cdot y
=\int_0^1 [P(ty)-P(0)]\cdot y\dd t
=o(\lVert y\rVert).
\]
这证明 $v$ 在原点可微且导数为 $P(0)$。
在每个界面点重复此论证，并利用 $P$ 的连续性，得到局部 $C^1$ 拼接。
变回原坐标，$U$ 在不安全内部为 $C^1$。
切换曲线的下端点位于安全边界，上端点位于容量边界，
均不属于此处的不安全内部论域。
```


## 2. 相对局部 Lipschitz 的显式估计

**操作位置：** 在 prop:regularity 的同一证明中，替换从 \emph{一致梯度界。} 开始、到该证明的 \end{proof} 之前的全部内容；保留 \end{proof}。

保留安全边界连续性及容量迹的前置计算，补出坐标线段、有限分段和具体估计。

对应片段：`snippets/02_relative_local_lipschitz.tex`。

```latex
\emph{一致梯度界与相对局部 Lipschitz 性。}
等待区内 $j\ge i$、$\eta-r>h-r=\ell$，从而
\[
0<U_i\le\frac{1}{hi},\qquad 0\le U_s\le U_i.
\]
完全跟踪区内 $0<\Theta(\bar x)<\Theta(x)<1/i$，故
\[
0\le W_s\le\frac{p}{si},\qquad 0\le W_i\le\frac{1}{hi}.
\]
内部切换界面取相同的梯度极限。
安全集内部 $U$ 为常数零；沿任何完全位于安全集内的线段，$U$ 的增量亦为零。

固定 $x_*\in\Omega$，取包含 $x_*$ 的一个充分小的闭矩形
\[
R=[s_-,s_+]\times[i_-,i_+],\qquad s_->0,\quad i_->0,
\]
使 $x_*$ 属于 $R\cap\Omega$ 的相对内部。
在该集合各光滑分支上，两偏导数的绝对值均不超过
\[
M_R:=\max\left\{\frac{1}{hi_-},\frac{p}{s_-i_-}\right\}.
\]
不位于 $i=K$ 的水平或竖直线段只可能穿过以下内部界面：
安全边界 $i=a(s)$ 的有关部分、非平凡切换图像 $i=I_\Gamma(s)$，
以及等待分支界面 $i=\Phi_B-s+h\ln s$ 的有关部分。
安全边界在 $s>h$ 严格递减，切换图像严格递增，
最后一条图像在所用的 $s>s_B>h$ 范围内严格递减。
故每条水平或竖直线段与各图像至多相交一次。
在有限个交点之间分段应用一维微积分基本定理，
再利用已经证明的界面连续性取端点极限，
可知水平线段上 $U$ 的增量绝对值不超过 $M_R$ 乘以其长度，
竖直线段上也有相同估计。

若水平线段位于 $i=K$，则使用容量迹 $b(s)=U(s,K)$。
在 $s\le h$ 上 $b=0$；在 $h<s<s_B$ 上 $b'=W_s(s,K)$；
在 $s>s_B$ 上由 \eqref{eq:boundary-value} 和 \eqref{eq:boundary-cost}
得到 $b'=p(s-h)/[Ks(s-r)]$。
这些导数满足上述局部界；在 $h,s_B$ 处分段并使用容量迹连续性，
得到同一水平线段估计。

任取 $x=(s_1,i_1),y=(s_2,i_2)\in R\cap\Omega$，
中间点 $z=(s_2,i_1)$ 以及连接 $x$ 到 $z$、$z$ 到 $y$ 的两条坐标线段
均属于 $R\cap\Omega$。
因此
\[
|U(x)-U(y)|
\le M_R\bigl(|s_1-s_2|+|i_1-i_2|\bigr)
\le\sqrt{2}\,M_R\lVert x-y\rVert.
\]
这证明 $U$ 在 $\Omega$ 上相对局部 Lipschitz。
将该估计限制到 $\Dcal\subset\Omega$ 即得物理域上的结论；
这里的辅助坐标线段无需满足 $s+i\le1$。
```


## 3. 隐函数定理的局部定义域

**操作位置：** 在 prop:Gamma-geometry 的证明开头，替换从“取特征线标号”开始到“根方程为 ... =0。”的三句话；保留随后“由引理\ref{lem:unimodal}”及 F_s、F_psi 的原计算。

只补反函数、对数定义域及非平凡根邻域，不改变原来的求导与端点论证。

对应片段：`snippets/03_implicit_function_domain.tex`。

```latex
取特征线标号 $\psi=G(z)=a(z)-\ell\ln z$。
由于 $G'(z)=(r-z)/z<0$，$G$ 将 $(h,e)$ 光滑地一一映到
$(G(e),G(h))$，其逆映射记为 $z=z(\psi)$。
在开集
\[
\{(s,\psi):s>h,\ G(e)<\psi<G(h),\ \psi+\ell\ln s>0\}
\]
上定义光滑函数
\[
L(s,\psi)=\ln\frac{s-h}{s-r}-\ln(\psi+\ell\ln s),\qquad
F(s,\psi)=L(s,\psi)-L(z(\psi),\psi).
\]
其中 $\psi+\ell\ln z(\psi)=a(z(\psi))>0$，故第二项有定义。
每个非平凡根都满足 $s=\sigma(z)>z>h$ 和
$\psi+\ell\ln s=j(z)>0$，因而位于该开集内；
隐函数定理只在这些根的局部邻域使用，不在 $z=e$ 的合并端点使用。
根方程为 $F(s,\psi)=0$。
```


## 4. 切换零集与法向量关系

**操作位置：** 在 lem:tracking-region 的证明中，替换从“为确定 $D$ 的符号”开始、到“向未来即向较小 $s$ 移动时 ... 到 $x$ 为止均有 $D<0$。”为止的整段；保留前面的可达性证明和后面的“设 $x$ 的安全端点为 $z$”。

显式排除平凡根，限定零集为 Gamma_K，并在容量端点用内侧极限说明法向量关系。

对应片段：`snippets/04_tracking_zero_set_and_normals.tex`。

```latex
为确定 $D$ 的符号，先说明其零集。
任取 $x=(s,i)\in\mathcal E$，记其安全端点的易感坐标为 $z=\bar s(x)$。
由命题\ref{prop:reachable}，$h<z<s$ 且 $i=I_z(s)$，所以
\[
D(x)=0
\iff \Theta(s,I_z(s))=\Theta(z,a(z)).
\]
平凡根 $s=z$ 位于安全边界，不属于这里的不安全状态。
由引理\ref{lem:unimodal}，上述等式成立当且仅当
$h<z<e$ 且 $s=\sigma(z)$。
结合已经证明的切换点可达性以及 $i\le K$，得到
\[
\{x\in\mathcal E:D(x)=0\}=\Gamma_K.
\]

在非平凡切换点 $y=(\sigma(z),j(z))$，
沿所属的反向完全跟踪特征线有
\[
\left.\frac{\mathrm d}{\mathrm d s}D(s,I_z(s))\right|_{s=\sigma(z)}
=-\left.\frac{\mathrm d}{\mathrm d s}\Theta(s,I_z(s))\right|_{s=\sigma(z)}>0,
\]
其中严格符号来自非平凡根位于单峰函数的严格下降段。
由于 $q=1$ 时 $\dot s=-csi<0$，故 $L_{f_1}D(y)<0$，特别地
$\nabla D(y)\ne0$。
端点映射的光滑性给出 $D$ 在各有关点附近的光滑性；
在容量切换点，$a(z)>0$ 及 $G'(z)\ne0$ 还给出环境开邻域上的光滑延拓，
这里只将其用于求导。

另一方面，$\chi(s,i)=i-I_\Gamma(s)$ 满足
$\nabla\chi=(-I_\Gamma'(s),1)\ne0$。
沿 $\Gamma_K$ 上的恒等式 $D(s,I_\Gamma(s))=0$ 求导，
得到 $\nabla D\cdot(1,I_\Gamma')=0$；
在容量端点通过 $s\uparrow s_B$ 取极限，关系同样成立。
因此存在标量 $\lambda(y)$，使
\[
\nabla D(y)=\lambda(y)\nabla\chi(y),\qquad
\lambda(y)=\frac{L_{f_1}D(y)}{L_{f_1}\chi(y)}<0.
\]
再由引理\ref{lem:strict-crossing}知 $L_{f_0}D(y)<0$。
沿自然轨道的时间方向有 $\dot s<0$，所以在触点 $s=\eta$ 处，
$D$ 沿该轨道关于 $s$ 的导数严格为正。
向未来即向较小 $s$ 移动时，$D$ 因而先变为负值。
从 $y_\Gamma$ 到 $x$ 的自然轨道段已知保持在 $\mathcal E$ 内，
而该轨道没有第二个非平凡切换交点。
由零集刻画和连续性，到 $x$ 为止始终有 $D<0$。
```


## 5. 等待区与完全跟踪区的相对开放性

**操作位置：** 插入到 lem:chi-regions 的证明结束之后、lem:tracking-region 之前。

只建立分段轨道分析实际需要的相对开放性；不添加 Gamma_K union B 在 Omega 中相对闭的错误断言。

对应片段：`snippets/05_relative_open_regions.tex`。

```latex
\begin{remark}[控制分区的相对开放性]
\label{rem:relative-open-control-regions}
记 $\mathcal W:=\mathcal W_\Gamma\cup\mathcal W_K$。
由引理\ref{lem:chi-regions}及分区定义，
\[
\mathcal W
=\{x=(s,i)\in\Omega\setminus\widehat{\Acal}:
  i<K,\ s>e,\ \chi(s,i)<0\}.
\]
事实上，当 $\Phi\le\Phi_B$ 时使用该引理；当 $\Phi>\Phi_B$ 且 $i<K$ 时，
$s\ge\eta_K(\Phi)>s_B$，故 $I_\Gamma(s)>K>i$。
反向包含由按 $\Phi\le\Phi_B$ 或 $\Phi>\Phi_B$ 分类得到。
由于安全集在 $\Omega$ 中相对闭，上式表明 $\mathcal W$ 在 $\Omega$ 中相对开。

在 $\mathcal T$ 中实际上有 $\Phi<\Phi_B$。
若 $\Phi=\Phi_B$，则 $i\le K$ 以及 $s>h$ 给出
\[
s-h\ln s\ge s_B-h\ln s_B,
\]
从而 $s\ge s_B=\eta_\Gamma(\Phi_B)$，与 $\mathcal T$ 的定义矛盾。
因此 $\mathcal T$ 也可由
\[
s>h,\qquad \Phi_A<\Phi<\Phi_B,\qquad
s<\eta_\Gamma(\Phi)
\]
这些连续严格不等式在 $\Omega$ 中刻画，故亦相对开。
将上述集合限制到 $\Dcal$ 后，相对开放性仍成立。
\end{remark}
```


## 6. 从几乎处处的控制选择到分段状态方程

**操作位置：** 在 thm:unique-q 的证明中，插入到 E_K^- 零测集论证之后的“因此，在轨道属于整个 ... q=1 几乎处处。”之后、\emph{容量弧上的延续。} 之前。仅插入，不替换整篇唯一性证明。

把原来直接引用 ODE 唯一性的步骤写成积分方程；保留现有容量、横穿和安全延拓论证。

对应片段：`snippets/06_interval_flow_argument.tex`。

```latex
由注\ref{rem:relative-open-control-regions}及轨道连续性，
$\{t\in[0,\tau_q):x_q(t)\in\mathcal W\}$ 与
$\{t\in[0,\tau_q):x_q(t)\in\mathcal T\}$
均为 $[0,\tau_q)$ 中的相对开集，因而各自是至多可数个相对开区间的并。
在任一等待区间内，对该区间中的 $t_1<t_2$ 有
\[
x_q(t_2)-x_q(t_1)=\int_{t_1}^{t_2}f_0(x_q(v))\dd v;
\]
在任一完全跟踪区间内，相同等式将 $f_0$ 换为 $f_1$。
这由状态轨道的绝对连续性及上述几乎处处的控制选择得到。
在有限区间端点，通过连续性取极限，积分关系仍成立。
因此，给定每段的起始状态后，由 $f_0,f_1$ 的局部 Lipschitz 性，
该段轨道分别等于对应的唯一自然流或完全跟踪流，直至首次离开相应分区。
这里并未预先假设最优控制只有有限个切换；
各阶段的实际顺序由下面的边界延续与横穿论证确定。
```


## 7. 验证引理中的时间集合覆盖

**操作位置：** 在 lem:trajectory-verification 的证明末尾，将“以上集合覆盖所有时刻。”替换为本片段；保留其后的物理斜边说明。

只显式写出已由安全集定义保证的覆盖，不增加新的验证假设。

对应片段：`snippets/07_time_set_coverage.tex`。

```latex
由于 $\{t:i(t)=K,\ s(t)\le h\}\subset E_A$，且不安全状态必有 $s>h$，
上述三类时间集合确实覆盖全部时刻：
\[
[0,T]
=\{t\in[0,T]:x_q(t)\notin\Acal,\ i(t)<K\}
\cup\{t\in[0,T]:i(t)=K,\ s(t)>h\}
\cup E_A.
\]
```


## 8. 平台 Hamiltonian 与允许控制集的区分

**操作位置：** 插入到 prop:all-HJB 的证明结束之后、lem:trajectory-verification 之前。

不修改控制区间、不把原表格改成无约束控制问题，只澄清量词和优化域。

对应片段：`snippets/08_platform_hamiltonian_clarification.tex`。

```latex
式\eqref{eq:capacity-tie}表明，平台上的 Hamiltonian 表达式
$H_U(s,K,q)$ 对每个 $q\in[0,1]$ 均为零。
表\eqref{eq:HJB-table}的平台行只列出边界允许方向对应的区间
$Q_K(s)=[q_B(s),1]$；在该区间内，整个区间都是点态极小集。
这并不把 $q<q_B(s)$ 变为边界允许方向，也不单独确定最优轨道的延续。
容量时间集合上的控制选择和平台延续由后面的沿轨道及唯一性论证处理。
```


## 9. 候选反馈轨道的积分表述

**操作位置：** 在 prop:candidate-attainment 的证明末尾，插入到“候选构造不需要先使用任何最优性结论。”之前。

用积分方程说明反馈轨道，不把切换时刻的代表值设为额外控制约束。

对应片段：`snippets/09_candidate_integral_equation.tex`。

```latex
记上述拼接控制及其轨道为 $q^*,x^*$。
在各阶段的开时间区间上，分区定义给出
$q^*(t)=Q^*(x^*(t))$；可能例外的孤立切换时刻只有有限个。
故对每个有限 $t$，状态积分方程可写为
\[
x^*(t)=x_0+\int_0^t f_{Q^*(x^*(v))}(x^*(v))\dd v.
\]
因此该拼接确为所给反馈的一条 Carath\'eodory 轨道，
无需规定孤立切换时刻处状态导数的点态值。
```


## 10. 与 MSW 的动力学及成本差别

**操作位置：** 插入到第 1 节“结果的适用范围”注记结束之后、\section{解的适定性、正性与基本耗散} 之前。保留原有文献引述和模型方程。

模型对照来自 MSW 期刊版式(1)、式(2)；本模型结论通过已有标签引用，不声称一种新验证方法或已完成全面原创性检索。

对应片段：`snippets/10_model_comparison.tex`。

```latex
\paragraph{与传播率控制模型的区别。}
为便于比较，将 \citet[式(1)]{MicloSpiroWeibull2022}
中的状态和恢复率分别改记为 $s,i,\gamma$，传播控制仍记为 $b$。
该系统为 $\dot s=-bsi$、$\dot i=(bs-\gamma)i$，
故完全抑制 $b=0$ 时，易感比例保持不变而感染比例按恢复率下降。
相比之下，在本文常接触率情形，$q=1$ 时
\[
\dot s=-csi<0,\qquad \dot i=-\gamma i<0.
\]
因此，完全跟踪不仅使感染生成项为零，还使未隔离易感者继续移出。
相应轨道具有式\eqref{eq:Psi}的不变量，
其最优切换位置由式\eqref{eq:switch-condition}的特征线匹配确定。
本文证明的非平凡切换曲线满足式\eqref{eq:Gamma-slope}，
并在出现正长度容量阶段时于 $s_B>h$ 离开容量线、进入完全跟踪阶段；
最优结构及其初值判据集中见推论\ref{cor:optimal-synthesis}。
这些是本模型相对于上述标准传播率控制模型的结构差异。

两问题的控制集和成本亦不同。
\citet[式(2)]{MicloSpiroWeibull2022}允许传播率超过其自然水平 $\beta$，
且运行成本 $[\beta-b]_+$ 在 $b\ge\beta$ 时为零；
本文则在 $q\in[0,1]$ 上使用 $pcq$，其唯一零点为 $q=0$。
因此，不应直接移用文献中关于最优控制集合或后期唯一性的结论。
本文分别验证全局最优性，并分析验证等号条件下的可行轨道唯一性。
```


## 11. 最优策略的分区汇总

**操作位置：** 插入到 thm:unique-q 的证明结束之后、“一维切换成本与全局结论的关系”子节之前；不能把这个最优结构推论前移为全局验证的前提。

仅汇总已经证明的候选、达到性、最优性及唯一性；不借这个推论反证其前置定理。

对应片段：`snippets/11_optimal_synthesis.tex`。

```latex
\begin{corollary}[最优策略的分区表述]
\label{cor:optimal-synthesis}
在定理\ref{thm:verification}和定理\ref{thm:unique-q}的条件下，
固定 $x_0\in\Dcal$。
下述辅助分区均与物理域 $\Dcal$ 取交。
最优控制按几乎处处相等识别，其阶段顺序由初值唯一确定如下。
\begin{enumerate}[label=\textup{(\roman*)}]
\item 若 $x_0\in\Acal$，则永久取 $q=0$。
\item 若 $x_0\in\mathcal T\cup\Gamma_K$，则立即取 $q=1$，
直至首次进入 $\Acal$，随后永久取 $q=0$。
\item 若 $x_0\in\mathcal W_\Gamma$，则先取 $q=0$，
直至到达 $y_\Gamma(\Phi(x_0))$；随后取 $q=1$ 至首次进入 $\Acal$，
再永久取 $q=0$。
\item 若 $x_0\in\mathcal W_K\cup\mathcal B$，则先取 $q=0$ 至容量触点
$(\eta_K(\Phi(x_0)),K)$；初值位于 $\mathcal B$ 时该等待阶段长度为零。
此后沿 $q=q_B(s)$ 的容量弧运行至 $(s_B,K)$，
再取 $q=1$ 至首次进入 $\Acal$，最后永久取 $q=0$。
\end{enumerate}
特别地，不安全初值的最优控制具有式\eqref{eq:direct-structure}
或式\eqref{eq:capacity-structure}的结构。
正长度容量阶段恰对应于 $x_0\in\mathcal W_K\cup\mathcal B$；
对不安全初值，$\Phi(x_0)=\Phi_B$ 时不产生正长度容量阶段。
上述结构不规定孤立切换时刻的控制代表值。
\end{corollary}

\begin{proof}
定义\ref{def:candidate}给出各分区的候选控制及事件顺序，
命题\ref{prop:candidate-attainment}证明其可行性和有限时间达到性。
定理\ref{thm:verification}证明这些控制实现值函数，
定理\ref{thm:unique-q}排除同一初值下其他不同的最优控制轨道。
在 $\mathcal W_K\cup\mathcal B$ 中，$\Phi(x_0)>\Phi_B$，
故容量阶段从严格大于 $s_B$ 的易感坐标开始，持续时间严格为正。
对不安全初值，若 $\Phi(x_0)=\Phi_B$，则
$x_0\in\mathcal W_\Gamma\cup\{(s_B,K)\}$。
初值为 $(s_B,K)$ 时立即完全跟踪；其余情形先自然到达该点，再立即完全跟踪。
因此不会出现正长度容量阶段。
\end{proof}
```


## 12. 少量局部文字调整


这些修改均按语义和标签定位。已经有等价表述时不重复添加。

## 1. 单峰性引理中的唯一返回

在 `lem:unimodal` 中，将“它恰好一次返回正的初始值，返回点严格在峰点右侧。”替换为：

```latex
由于峰值严格大于初始值，而峰后严格递减段趋于零，
且 $\Theta(z,a(z))>0$，介值定理与严格单调性给出唯一的返回点，
且该点严格位于峰点右侧。
```

## 2. 可达性命题中的重复等号情形

在 `prop:reachable` 的证明中，保留“若 $h\le s_\infty<s_K$”这一分支，
删除随后“在等号 $s_\infty=h$ 的情形，前一种论证同样适用。”一句。
等号已经被前一分支包含，不需要另作含混指代。

## 3. 等待分支公共界面的归属

在 `def:regions` 的末尾、“它不是整条竖线 $s=s_B$。”之后补：

```latex
该界面上的两种候选成本公式及其梯度具有相同的极限，
详见命题\ref{prop:regularity}。
因此将界面归入 $\mathcal W_\Gamma$ 只是记号约定，
不改变候选成本及实际使用的控制 $q=0$。
```

这句话是向后引用已安排的正则性结论作解释，不得作为该正则性命题的证明前提。
不要在定义处对仅原先定义于 $\Phi>\Phi_B$ 的函数直接代入边界值而不说明取极限。

## 4. 候选结构注记与新最优结构推论的关系

保留原注记及 `eq:direct-structure`、`eq:capacity-structure` 两个标签。
将注记标题“允许零长度阶段的结构表述”改为“候选策略的阶段结构”，
并在注记开头增加：

```latex
本注记录定义\ref{def:candidate}中的候选阶段结构，
其最优性由定理\ref{thm:verification}确立；
各初值分区对应的最优结构汇总见推论\ref{cor:optimal-synthesis}。
```

不要在这个验证之前的注记中引用最优结构推论来证明候选达到性。

## 5. 一维推论明确为全局极小

在 `cor:one-dimensional-min` 中：

- 标题改为“候选策略族中的唯一全局极小”；
- “存在唯一极小点”改为“存在唯一全局极小点”；
- 保留当前达到性和利用全时间控制唯一性的证明。

无需补充“没有其他局部极小点”之类未经本推论独立证明的结论，
也无需声称整个扩展值成本函数严格凸。

## 6. 基准直接策略成本的含义

在 `tab:baseline-results` 之后，将“在该初值下，直接策略族的最低成本恰在容量触点取得。”替换为：

```latex
这里 $J_{\rm direct}=\min_{\sigma\in[s_1,s_0]}\mathcal J_D(\sigma)$。
对不属于式\eqref{eq:reachable}有限可达域的切换状态，
按照定义\ref{def:W}将该指定策略的成本置为 $+\infty$。
在本基准初值下，最小值取于区间端点 $\sigma=s_1$，
即自然轨道首次到达容量后立即转入完全跟踪。
```

保持已有表格数值，不新增可达阈值、不可达区间比例等数值。
尤其不要写“直接切换区间大部分为 $+\infty$”。
本次不修改或重跑 Python 数值实现；正文的扩展值约定不等于声称代码中的罚值已经修复。

## 7. 辅助域与实际比较的关系

在“几何截断不是额外参数假设”注记中，将“某些参数或初值不经过容量平台，不影响后续全域验证。”替换为：

```latex
候选函数和辅助曲线在 $\Omega$ 上构造，
而最优控制问题的比较始终针对 $\Dcal\subset\Omega$ 内的可行轨道。
状态方程的正性与耗散保证实际轨道保持在物理域中，
故可将辅助条带上的函数及相应局部计算限制到实际轨道使用。
辅助曲线的部分点不在物理域内，并不使这些点成为可行状态。
某些初值不经过容量平台时，相应阶段直接省略。
```

不要将正式仅针对 $\Dcal$ 陈述的轨道验证引理擅自改称为
“已经对 $\Omega$ 上所有控制轨道证明”。

## 8. 方法说明（只在现有段落缺少这一层意思时追加一句）

在 `sec:HJB` 已有“直接沿轨道验证”说明之后，可加入：

```latex
边界 HJB 和仿射 Hamiltonian 的点态分析用于说明控制方向和候选结构；
全局充分性以随后对每条可行轨道建立的积分不等式为依据。
本文不需要先对全部 PMP 极值作分类，也不以黏性解唯一性为前提，
但仍须验证候选函数的局部正则性、沿轨道链式法则及终端处理。
```

不要删去已经完成的边界和横穿分析；不要写成“无须分析任何奇异或边界行为”。



## 完成后的检查与交付

### 结构和引用

保留所有原有标签。预计新增正文标签仅有：

- `rem:relative-open-control-regions`
- `cor:optimal-synthesis`

若基线仍与本任务一致，标签总数应由 171 变为 173；
若用户已作其他改动，按真实基线报告，不强制凑数。
检查重复标签、未定义引用、缺失文献键、环境与括号配对。
局部内部 C^1 拼接不得依赖随后才证明的 Lipschitz 性；
局部 Lipschitz 证明不得用该命题自己尚未得出的容量迹 Lipschitz 性。
本片段通过已有容量迹公式的有界导数独立处理该线段。

### 数学依赖

确认 `thm:verification`、`cor:verification-equality` 和
`lem:no-early-boundary-exit` 不反向依赖 `thm:unique-q` 或 `cor:optimal-synthesis`。
相对开放性说明置于 `lem:chi-regions` 之后；
唯一性证明中的时间区间段落置于控制选择、特别是 `E_K^-` 零测集处理之后。
保留原来的切换端点处理，不把 `I_Gamma` 用在 `s<=e` 区域。

### 编译和呈现

沿用项目已有构建入口，分别编译全文与现有 `theory_only.tex`。
优先使用项目已经使用的 XeLaTeX/latexmk 配置；记录实际执行命令、退出码和最终日志。
检查新增长式和编号后的分页；编译成功与数学证明有效性分开报告。
若环境缺少编译工具，报告未编译，不得伪造成功记录。
若仓库维护根目录同步 PDF，仅在实际编译成功后更新并核对来源。
没有必要重跑未改动的数值实验；不得把旧实验写成本轮新运行。

### 建议交付摘要

输出最终 diff，逐项列出完成的插入/替换、实际标签增量、
未定义引用检查结果、实际编译情况和未执行事项。
不要把静态检查、编译或数值抽查称为形式化数学证明认证。

## 本增补包的状态

本包已完成片段层面的文字和数学核对；另附静态结构检查记录。
它尚未写入远程仓库，也未与整篇论文合并编译。
所有构建和完整引用检查应由 Codex 在实际仓库中执行。
