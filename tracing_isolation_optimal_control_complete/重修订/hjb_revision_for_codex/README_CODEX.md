# Codex 修改任务书：常接触率 HJB 验证等号条件与唯一性证明

## 工作对象与范围

仓库：`cuizhizhong/optimal-threshold-control`  
分支：`codex/integrate-theory-revision`  
主要文件：`tracing_isolation_optimal_control_complete/latex/main.tex`  
本任务书核对的 main.tex Git blob：`5e43b4af7db0871726ad1a4e977f17f75ed87570`。

请先阅读当前工作区的相关内容，再按 LaTeX 标签定位修改；不要重置分支或覆盖本任务以外的改动。若工作区已包含相同结论，应核对并合并，避免重复插入。

本轮仅整理论证：显式记录验证等号条件，将原唯一性证明中的容量弧论证提取为独立引理，并相应调整唯一性证明及交叉引用。不修改模型、成本泛函、可测控制类、状态域、候选函数、切换曲线、主定理的参数范围或数值算法。

方法出处继续采用原稿中的 `Liberzon2012`（§5.1.4）和 `MicloSpiroWeibull2022`（期刊版附录 A.1—A.2）。新增的等号条件是本稿已有验证结果的直接推论，不作为新的控制方法提出，也不说下列具体公式逐字来自参考文献。不要将 Miclo 的早期预印本与期刊版的证明混用。

保留 `thm:verification` 及其原有证明。该定理必须先完成全局最优性证明；不要反过来引用下方依赖它的等号条件推论。不要新增控制右连续性、分段连续性、全域 C^1 或未经证明的无穷远条件，也不要通过正则化、PMP 或黏性解比较替换当前的证明路线。

## 修改一：在全局最优性证明之后插入验证等号条件

位置：`thm:verification` 对应的 `proof` 环境结束之后、`sec:constant-uniqueness` 节标题之前。

插入以下完整片段。`R_q` 通过复合函数的几乎处处时间导数定义，不在不具备经典导数的边界上直接代入未经证明的梯度公式。初值已经安全的情形包含在推论内。

```latex
下面记录验证证明中的等号条件，以用于下一节的唯一性分析。

\begin{corollary}[验证等号条件]
\label{cor:verification-equality}
在定理\ref{thm:verification}的条件下，固定 $x_0\in\Dcal$。
对任意满足 $J_{x_0}(q)<\infty$ 的可行控制 $q\in\Uad(x_0)$，记
\[
\tau_q:=\tau_{\Acal}(x_0,q).
\]
在 $(0,\tau_q)$ 上几乎处处定义
\begin{equation}
R_q(t):=\frac{\mathrm d}{\mathrm d t}U(x_q(t))+pcq(t).
\label{eq:trajectory-verification-residual}
\end{equation}
则 $\tau_q<\infty$，$R_q\in L^1(0,\tau_q)$，且 $R_q\ge0$ 几乎处处。
此外，
\begin{equation}
J_{x_0}(q)-V(x_0)
=
\int_0^{\tau_q}R_q(t)\dd t
+
\int_{\tau_q}^{\infty}pcq(t)\dd t.
\label{eq:verification-gap}
\end{equation}
因此，在上述有限成本可行控制类中，$q$ 最优当且仅当
\begin{equation}
\begin{cases}
R_q(t)=0 & \text{几乎处处于 }(0,\tau_q),\\
q(t)=0 & \text{几乎处处于 }(\tau_q,\infty).
\end{cases}
\label{eq:verification-equality-conditions}
\end{equation}
当 $x_0\in\Acal$ 时，取 $\tau_q=0$，并将第一个积分理解为零。
\end{corollary}

\begin{proof}
由引理\ref{lem:finite-entry}，$\tau_q<\infty$，且
$x_q(\tau_q)\in\Acal$，故 $U(x_q(\tau_q))=0$。
若 $\tau_q>0$，引理\ref{lem:trajectory-verification}保证
$U\circ x_q$ 在 $[0,\tau_q]$ 上绝对连续，且 $R_q\ge0$ 几乎处处。
绝对连续函数的导数可积，而 $q$ 有界，所以
$R_q\in L^1(0,\tau_q)$。
由微积分基本定理，
\begin{align*}
\int_0^{\tau_q}R_q(t)\dd t
&=U(x_q(\tau_q))-U(x_0)
  +\int_0^{\tau_q}pcq(t)\dd t\\
&=-U(x_0)+\int_0^{\tau_q}pcq(t)\dd t.
\end{align*}
将成本积分在 $\tau_q$ 处分开，并使用
定理\ref{thm:verification}中的 $U(x_0)=V(x_0)$，
即得 \eqref{eq:verification-gap}。
当 $\tau_q=0$ 时，$U(x_0)=V(x_0)=0$，该恒等式同样成立。

式\eqref{eq:verification-gap}右端两项均非负。
非负可积函数的积分为零，当且仅当该函数几乎处处为零；
又因 $pc>0$，第二项为零当且仅当 $q=0$ 几乎处处于
$(\tau_q,\infty)$。
结合最优性的定义，得到 \eqref{eq:verification-equality-conditions}。
\end{proof}

\begin{remark}[等号条件与唯一性]
\label{rem:verification-equality-uniqueness}
在 $U$ 可微的不安全内部，普通链式法则给出
\[
R_q(t)=H_U(x_q(t),q(t))
\]
几乎处处成立。
在状态约束边界上，仍使用引理\ref{lem:trajectory-verification}
所建立的沿轨道导数关系。
推论\ref{cor:verification-equality}刻画最优控制的等号条件，
但不单独蕴含最优控制唯一。
唯一性还需结合状态约束、切换曲线的横穿性质及状态方程解的唯一性。
\end{remark}
```

## 修改二：将容量弧上的延续性质提为独立引理

位置：`\section{常接触率下控制与轨道的唯一性}` 和 `\label{sec:constant-uniqueness}` 之后、`thm:unique-q` 之前。

该引理整理原证明中“禁止从 s>s_B 提前离边”的反证，并写明局部结论向整个容量阶段的延续。它只针对最优控制；不能改写成“所有可行控制均不能提前离开容量边界”。

```latex
\begin{lemma}[最优轨道在容量弧上的延续]
\label{lem:no-early-boundary-exit}
在定理\ref{thm:verification}的条件下，设 $q\in\Uad(x_0)$ 为最优控制，
其状态轨道为 $x_q=(s_q,i_q)$，首次进入安全集的时间为 $\tau_q$。
若某个 $t_0\in[0,\tau_q)$ 满足
\[
x_q(t_0)=(s_*,K),\qquad s_*>s_B,
\]
令
\[
t_B:=t_0+T_B(s_*,s_B)
=t_0+\frac1{cK}\ln\frac{s_*-r}{s_B-r}.
\]
则 $t_B<\tau_q$，并且
\begin{equation}
i_q(t)=K,\qquad
s_q(t)=r+(s_*-r)\e^{-cK(t-t_0)}
\quad(t_0\le t\le t_B).
\label{eq:optimal-boundary-continuation}
\end{equation}
在 $(t_0,t_B)$ 上，$q(t)=q_B(s_q(t))$ 几乎处处。
特别地，最优轨道不能在 $s>s_B$ 时离开容量边界。
\end{lemma}

\begin{proof}
先证明局部结论。
由 $\Phi(s_*,K)>\Phi_B$ 及连续性，
可取 $(s_*,K)$ 在 $\Dcal$ 中的一个相对邻域 $O$，
使其中 $s>s_B$、$\Phi>\Phi_B$，且
\[
O\cap\{i<K\}\subset\mathcal W_K.
\]
轨道连续性给出 $\delta>0$，使
$t_0+\delta<\min\{\tau_q,t_B\}$ 且
$x_q([t_0,t_0+\delta])\subset O$。

若开时间集合
\[
E:=\{t\in(t_0,t_0+\delta):i_q(t)<K\}
\]
非空，取其任一连通分支 $(a,b)$。
由连续性及 $i_q(t_0)=K$，有 $a\ge t_0$ 和 $i_q(a)=K$。
在 $(a,b)$ 上轨道属于 $\mathcal W_K$。
推论\ref{cor:verification-equality}与
引理\ref{lem:waiting-HJB}因此给出 $q=0$ 几乎处处于 $(a,b)$。
于是对每个 $t\in(a,b)$，
\[
i_q(t)-K
=\int_a^t pc\bigl(s_q(v)-h\bigr)i_q(v)\dd v>0,
\]
因为 $s_q(v)>s_B>h$ 且 $i_q(v)>0$。
这与 $i_q<K$ 矛盾，故 $E$ 为空。
因此 $i_q=K$ 在 $[t_0,t_0+\delta]$ 上成立。

在任何保持 $i_q=K$ 的时间区间上，
引理\ref{lem:ac-level-set}与状态方程给出
\[
q(t)=1-\frac{h}{s_q(t)},\qquad
\dot s_q(t)=-cK(s_q(t)-r)
\]
几乎处处成立，从而得到 \eqref{eq:optimal-boundary-continuation} 中的显式解。

为将局部结论延续至 $t_B$，令
\[
t_*:=\sup\{T\in[t_0,t_B]:
 i_q(t)=K\text{ 对所有 }t\in[t_0,T]\text{ 成立}\}.
\]
由局部结论，$t_*>t_0$；由连续性，$i_q=K$ 在 $[t_0,t_*]$ 上成立。
若 $t_*<t_B$，上述显式解给出 $s_q(t_*)>s_B$。
同时，该段轨道始终位于安全集外，故 $t_*<\tau_q$。
在 $t_*$ 处重新应用局部结论，可将 $i_q=K$ 的区间继续向右延长，
与 $t_*$ 的定义矛盾。
因此 $t_*=t_B$，所述状态公式与控制公式在整个容量阶段成立。
最后，$x_q(t_B)=(s_B,K)$，且
$\Phi(s_B,K)=\Phi_B>\Phi_A$，所以 $t_B<\tau_q$。
\end{proof}
```

## 修改三：替换唯一性定理及其证明

保留标签 `thm:unique-q`，用以下片段替换原定理环境及紧随其后的完整证明环境。删除原证明中已被提取到新引理的重复段落。后面的“一维切换成本与全局结论的关系”及 `cor:one-dimensional-min` 保留。

特别保留对 `i=K, h<s<s_B` 对应时间集合的处理。该处不能直接声称最优轨道沿容量线取 q=1；应先用已有沿轨道验证计算证明该时间集合为零测集，再得到整个完全跟踪区内 q=1 几乎处处。

```latex
\begin{theorem}[全时间轴上的几乎处处唯一性]
\label{thm:unique-q}
在定理\ref{thm:verification}的基本模型条件下，
从同一 $x_0\in\Dcal$ 出发的最优状态轨道唯一，
最优控制 $q^*$ 在 $[0,\infty)$ 上几乎处处唯一。
平台上不要求 Hamiltonian 的点态极小集为单点。
\end{theorem}

\begin{proof}
若 $x_0\in\Acal$，则 $V(x_0)=0$。
由于 $pc>0$，任意最优控制都满足 $q=0$ 几乎处处；
状态方程解的唯一性随即给出最优轨道唯一。
以下设 $x_0\notin\Acal$。

任取最优控制 $q$，记其状态轨道为 $x_q=(s_q,i_q)$，
首次进入安全集的时间为 $\tau_q$。
由定理\ref{thm:verification}，该控制成本有限。
推论\ref{cor:verification-equality}给出
\[
R_q=0\quad\text{几乎处处于 }(0,\tau_q),\qquad
q=0\quad\text{几乎处处于 }(\tau_q,\infty).
\]

\emph{各分区内的控制选择。}
在自然等待区的时间集合上，
引理\ref{lem:waiting-HJB}与普通链式法则给出
$R_q=q\Sigma_U$，其中 $\Sigma_U>0$，
故 $q=0$ 几乎处处。
在 $\mathcal T\cap\{i<K\}$ 的时间集合上，
命题\ref{prop:all-HJB}给出
$R_q=(1-q)H_{0,U}$，其中 $H_{0,U}>0$，
故 $q=1$ 几乎处处。

对于时间集合
\[
E_K^-:=\{t\in(0,\tau_q):i_q(t)=K,\ h<s_q(t)<s_B\},
\]
引理\ref{lem:trajectory-verification}的容量边界计算给出
\[
R_q(t)
=\bigl(1-q_B(s_q(t))\bigr)H_{0,W}(x_q(t))>0
\]
对 $E_K^-$ 中几乎所有时刻成立。
由于最优控制满足 $R_q=0$ 几乎处处，$E_K^-$ 必为零测集。
因此，在轨道属于整个 $\mathcal T$ 的时间集合上，
$q=1$ 几乎处处。

\emph{容量弧上的延续。}
在容量时间集合 $\{t<\tau_q:i_q(t)=K,\ s_q(t)>h\}$ 上，
引理\ref{lem:ac-level-set}及状态方程强制
$q=q_B(s_q)$ 几乎处处。
当最优轨道到达 $(s_*,K)$ 且 $s_*>s_B$ 时，
引理\ref{lem:no-early-boundary-exit}进一步保证其沿容量弧运行，
直至在唯一确定的时间到达 $(s_B,K)$。
这一步使用轨道可行性，而不使用平台上点态极小元的唯一性。

\emph{切换曲线上的行为。}
引理\ref{lem:strict-crossing}保证轨道在 $\Gamma_K$ 上的时间集合为零测集。
若 $x_q(t_0)\in\Gamma_K$，包括 $x_q(t_0)=(s_B,K)$ 的情形，
可取位于不安全区域且满足 $s>e$ 的相对小邻域。
式\eqref{eq:strict-crossing-time}给出
$\chi(x_q(t))>0$ 对充分接近 $t_0$ 的所有 $t>t_0$ 成立。
结合引理\ref{lem:chi-regions}及可行性 $i_q\le K$，
可知轨道立即进入 $\mathcal T$。
因此，切换点处的瞬时控制取值不产生另一条最优延续轨道。

\emph{各阶段轨道的唯一确定。}
在自然等待阶段，$q=0$ 几乎处处，
因而状态方程解的唯一性确定轨道，直至其首次到达切换曲线或容量边界。
两种等待分支的公共界面不改变该向量场。
首次事件的唯一性由推论\ref{cor:Gamma-labels}和相应触点的定义给出；
其有限时间达到性已在命题\ref{prop:candidate-attainment}中证明。
若到达容量平台，则上一段确定其唯一的容量弧延续。
若到达切换曲线，则轨道立即进入完全跟踪区。

在完全跟踪区，$q=1$ 几乎处处，
由引理\ref{lem:tracking-region}及状态方程解的唯一性，
轨道被唯一确定至首次到达 $\Acal$，且此前不会返回等待区。
初值已在容量平台、切换曲线或完全跟踪区的情形，
分别从对应阶段开始使用相同论证。
首次进入安全集后，$q=0$ 几乎处处，
再次由状态方程解的唯一性确定后续轨道。

因此，从同一初值出发，任意最优控制均生成同一条分段状态轨道，
各阶段的到达时间也相同。
上述控制选择条件进而给出所有最优控制在 $[0,\infty)$ 上几乎处处相等。
\end{proof}
```

## 修改四：明确容量边界导数的记号

位置：`prop:regularity` 的证明结束之后。若已有完全等价的说明，合并而不重复。

只增加导数含义的说明，不增强正则性结论。不设置 U_i(s,K)=0，不将不安全侧梯度视为安全集内的零梯度，不将 U 在不可行区域上的延拓作为问题定义。

```latex
以下在 $i=K,s>h$ 上使用的 $\nabla U(s,K)$，
均指由不安全内部 $i<K$ 取得的梯度极限。
其中 $U_s(s,K)$ 等于容量迹 $s\mapsto U(s,K)$ 的导数，
而 $U_i(s,K)$ 按内侧导数理解。
这些记号不要求在不可行区域 $i>K$ 上定义 $U$。
沿容量时间集合的链式法则另由引理\ref{lem:trajectory-verification}建立。
```

## 修改五：更新证明依赖说明

位置：`app:proof-scope` 中说明常接触率证明依赖顺序的段落之后。保留原有依赖说明，并补充以下文字：

```latex
全局最优性确立后，推论\ref{cor:verification-equality}
由沿轨道验证不等式积分得到最优控制的等号条件。
引理\ref{lem:no-early-boundary-exit}据此证明容量弧上的延续性质，
再由定理\ref{thm:unique-q}完成控制与状态轨道的唯一性证明。
上述推论和引理均不依赖定理\ref{thm:unique-q}。
```

## 合并与验收要求

### 数学依赖与范围

依赖顺序应保持为：`lem:finite-entry` 和 `lem:trajectory-verification` → `thm:verification` → `cor:verification-equality` → `lem:no-early-boundary-exit` → `thm:unique-q` → `cor:one-dimensional-min`。已有切换几何、正则性及候选达到性结果仍在各自使用的位置引用。

新增推论必须仅对有限成本可行控制陈述分解，并保留首次到达后的成本积分。不得预先要求所有竞争控制进入安全集后都取零控制；这一结论是最优控制的等号条件。不得把单个切换时刻的代表值写入几乎处处唯一性结论。

容量弧的 Hamiltonian 极小集不是单点，保留这一事实。唯一性来自验证等号条件与轨道可行性、切换横穿、状态方程解的唯一性共同作用。不得把 R_q=0 单独写成唯一性证明。

保持常接触率与时变接触率的结论范围分离；本轮不增强时变问题、正则化极限或数值全局最优性的表述。

### LaTeX 与项目检查

新增标签只出现一次，原有标签尽量保留，所有编号由 LaTeX 自动生成。检查 `\ref`、`\eqref` 和 `\cite` 是否存在未定义引用。使用原稿已有的 theorem、lemma、corollary、remark 环境以及 `\Acal`、`\Dcal`、`\Uad`、`\dd`、`\e` 等宏，不另加宏包。

按项目现有构建方式编译完整稿；如项目已有 TheoryOnly 入口，也编译理论校样。记录实际运行的命令和日志。不能执行编译时，明确报告未执行，不把静态检查报告为完整编译通过。排版或交叉引用检查不等于数学证明的形式化验证。

交付修改后的文件差异、修改位置与标签清单，以及实际完成的编译检查结果。不要为了减少篇幅删除有限时间进入引理、容量水平集链式法则、严格横穿引理或完全跟踪分区的正向性质。

## 文件说明

本目录的 `.tex` 文件都是插入或替换片段，不是可独立编译的论文，也不是完整修订后的 main.tex。本任务书尚未写入远程仓库；完整合并与项目编译由 Codex 在工作区执行。
