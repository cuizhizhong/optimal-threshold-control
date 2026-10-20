# C1/C2/C4 只读结构核对建议（2026-10-21）

本记录核对 v5 `REVISION_PLAN.md` C1--C4、`REVISION_PLAN_v2_author.md` §§5 和附录 B，以及当前 `latex/main.tex` 理论主线。没有修改论文、已有验证记录或数值材料；没有调用优化器或求解 OCP。以下均为执行建议，并非已完成的正文改动。

## 1. 两层集合定义与 safe-invariant 的准确改写

在常系数假设
$c,\gamma>0$, $0<\beta<1$, $0<K<1$ 下，保留
$\mathcal D=\{s>0,0<i\le K,s+i\le1\}$ 和当前正感染适用域。
令 $\mathcal Q_{\bar q}$ 为所有可测 $[0,\bar q]$ 值控制的集合，**定义时不预先要求状态可行**。对任意这种控制，全局解与物理总量约束由现有适定性定理保证；容量阈值另作判定。

- $\mathcal A=\{x\in\mathcal D:\sup_{t\ge0}i^0_x(t)\le K\}=\mathcal D\cap\{P_0\le K\}$。
- $\mathcal A^0=\{x\in\mathcal D:\text{对每个 }q\in\mathcal Q_1,\ i_x^q(t)\le K\text{ 对所有 }t\ge0\}$。
- $\mathcal V_{\bar q}=\{x\in\mathcal D:\text{存在 }q\in\mathcal Q_{\bar q},\ i_x^q(t)\le K\text{ 对所有 }t\ge0\}$，$0\le\bar q\le1$。

不要把 $\mathcal A^0$ 中的全称控制写成已经限制为可行的 $\mathcal U_{\rm ad}(x)$，否则定义循环且会把整个 $\mathcal D$ 都误判为该集。

现 `lem:safe-invariant` 的证明可直接保留并升级为
$\mathcal A^0=\mathcal A$：若从 $\mathcal A$ 出发，在 $s>h$ 时
$\dot\Phi=-cqi(s-p)\le0$，在到达 $s\le h$ 后 $s$ 不增且
$\dot i\le\beta c(s-h)i\le0$。这证明 $\mathcal A\subset\mathcal A^0$；
反向包含只需零控制属于 $\mathcal Q_1$。若想保留辅助条带版本，同样成立，但物理域陈述必须与条带陈述区分。

$\mathcal V_1=\mathcal D$ 来自 $q=1$ 时 $\dot i=-\gamma i$，并结合总量耗散；
这不意味着每个 $[0,1]$ 控制都可行。$\mathcal V_0=\mathcal A$ 是定义的直接退化。
$i=0$ 灭绝轴不属于现有主定理；若附带说明它零成本可行，不要把正感染包络在该轴连续外推。

## 2. 安全的主结果概览前置方式

模型节之后设置主结果概览，先说明常系数假设、物理域和上述无成本集合，再给一个合并的主要结论陈述：
现候选 $U$ 和 $Q^*$（给到后文定义式的前引）实现全控制类的全局最优值；
最优状态轨道唯一、控制在全时间轴 a.e. 唯一；阶段顺序由下表确定。
几何部分可概括现 `prop:Gamma-geometry`、`cor:Gamma-labels`、`lem:strict-crossing`，
不能给“闭环反馈对所有初值的任意解唯一”的更强结论，现有证明给的是最优轨道唯一。

一个新总定理后可写“证明由命题/定理……在后文依次完成”，明确逻辑依赖是前引，不在证明中提前使用总定理。
原 `thm:verification`、`thm:unique-q` 和 `cor:optimal-synthesis` 的细化陈述与证明可保留，
或只移动其陈述并在原位置保留证明标题。引言第一项贡献应同步前引新的主结果定理，而不再列证明清单。

阶段表建议：

| 初值区域（均与 $\mathcal D$ 取交） | 阶段顺序 | 首次停止付费 |
|---|---|---|
| $\mathcal A$ | $q=0$ 永久 | 初始时刻 |
| $\mathcal T\cup\Gamma_K$ | $1\to0$ | 首次进入 $\mathcal A$ |
| $\mathcal W_\Gamma$ | $0\to1\to0$ | 首次进入 $\mathcal A$ |
| $\mathcal W_K\cup\mathcal B$ | $0\to q_B\to1\to0$ | 首次进入 $\mathcal A$ |

在 $\mathcal B$ 初始的自然等待段为零；$\Phi=\Phi_B$ 时容量段为零。
正长度容量段只对应 $\mathcal W_K\cup\mathcal B$。容量退出坐标满足
$s_B>s_e>h$；$s_B$ 和辅助曲线端点可能处于物理三角形外，相关物理阶段可因此完全不出现。
不要为了相图好看另加 $h<1-K$ 等参数假设。

两层图的第一层讲 $\mathcal A^0=\mathcal A$ 与 $\mathcal V_1=\mathcal D$，
第二层才讲成本最优分区和 $\Gamma_K$。
$s=h$ 仅为感染增长阈值；$s+i=1$ 为总量边界，应使用明显不同线型和图例。

## 3. 标准实分析结果的可核对教材来源

已核对本地 Liberzon PDF：§3.3.1 给绝对连续解和 Carathéodory 解的背景；
§5.1.4 给 HJB 充分性验证。没有核实其中存在所需“水平集导数为零”或“相对局部 Lipschitz 复合”定理，
因此不要把这两条精确事实笼统归给 Liberzon。

可直接核对的作者官方教材：
D. H. Fremlin, *Measure Theory*, Volume 2: *Broad Foundations*。
官网目录确认书名与卷次：[官方主页](https://www1.essex.ac.uk/maths/people/fremlin/mt.htm)。

- [Chapter 22 官方 PDF](https://www1.essex.ac.uk/maths/people/fremlin/chap22.pdf)，§222K：
  任意集合除去其单侧聚点后的集合至多可数；§225C(b)：AC 函数为 BV，因而 a.e. 可微。
  二者直接推出水平集结论：在水平集非孤立点且导数存在处，沿同水平点序列的差商为零。
  不需要保留现有独立引理及完整证明，正文可用一小段标准事实，保留标签用于后文引用。
- [Chapter 26 官方 PDF](https://www1.essex.ac.uk/maths/people/fremlin/chap26.pdf)，§262X(l)：
  标量 AC 内函数与其像上的 Lipschitz 外函数复合仍 AC；§262B(b)：欧氏子集上 Lipschitz 函数有欧氏空间 Lipschitz 延拓。
  当前二维轨道、相对局部版本可保留一行适用说明：轨道像紧，有限局部化，并用
  $\sum|F(x(b_k))-F(x(a_k))|\le L\sum\|x(b_k)-x(a_k)\|$。
  这不是声称教材该练习原文就是“相对局部二维”版本。
- Leoni, *A First Course in Sobolev Spaces*, GSM 105, AMS, 2009，§3.2 Theorem 3.68 (Superposition)
  可作另一教材来源；[AMS 官方预览](https://www.ams.org/bookstore/pspdf/gsm-105-prev.pdf) 的搜索索引已直接给出定理陈述，
  但原文是 $\mathbb R\to\mathbb R$ 标量外函数，直接打开预览在本轮返回 403，不能冒称本轮已逐页核对全文。
  不建议额外引入该条，Fremlin 官方来源已经足够准确。

建议正文改成简短“后文使用的标准实分析事实”，列水平集事实和 Lipschitz 复合事实并教材引用；
保留局部 $C^1$ 延拓时链式法则的适用说明。后文专门处理容量时间集/安全时间集的证明必须保留，
不能用状态空间二维 a.e. 可微替代沿轨道一维 a.e. 论证。

本轮为核对 Liberzon 做过临时本地全文提取，已删除新生成的临时提取文件；没有把全文提取留在本建议目录。

## 4. 可无损移入附录的长计算

最稳妥的移动单位是 `prop:regularity` 的**完整证明**，正文保留命题、容量梯度式和 3--5 行证明路线，
并前引新附录。这样不会拆坏以下专门论证：

1. 非平凡切换界面与两种等待分支公共界面的函数值/梯度匹配；
2. 展平图像的 $\Xi(\zeta_1,\zeta_2)$ 局部坐标、梯度连续拼接积分、$o(\|\zeta\|)$ 可微性；
3. 正感染安全边界的连续性（包括 $(h,K)$ 的处理）；
4. 容量迹及 $s=s_B$ 的三分支匹配；
5. 一致梯度界、水平/竖直线段至多有限次穿越、两段坐标折线给相对局部 Lipschitz 估计。

现 `lem:waiting-gradient` 的证明很短，可留正文；
`lem:waiting-HJB` 的严格符号需要自然弧单调性，亦宜留正文。
`rem:safe-gradient` 可随技术附录移动，正文保留“安全边界使用水平集事实，不要求梯度匹配”的一句。
`lem:trajectory-verification`、`lem:no-early-boundary-exit`、
`lem:strict-crossing` 的专门时间集与延续论证不可作为标准技术细节删掉；
这些是平台 Hamiltonian 极小集为区间仍能得唯一性的核心。

## 5. C4 的严格解释与边界

在 $i>0,s>p$ 上，现有恒等式直接给
$\beta cq\,dt=-\beta\,d\Phi/[i(s-p)]$。
首次进入安全集之前有 $s>h>p$，因此分母严格为正。
$\Phi-\Psi=s-p\ln s$，且
$\det D(\Phi,\Psi)=1-p/s>0$；
$s-p\ln s$ 在 $s>p$ 严格递增，故这两个不变量坐标在该域给到其像的一一参数化。
不要声称其覆盖整个 $s>0$ 物理域。

对 $x\in\mathcal E$，令 $x^0(t)$ 为从 $x$ 出发的自然轨道，在该局部可达域内：
$$
\left.\frac{d}{dt}W(x^0(t))\right|_{t=0}
=H_W(x,0)
=\frac{\beta c}{h}i(s-p)[\Theta(s,i)-\Theta(\bar s,\bar i)].
$$
因此 $\Theta$ 匹配等价于“先免费等待一小段，再完全跟踪到安全集”的后续成本一阶变分为零。
这里只谈指定策略成本 $W$，不是预先把 $W$ 当作全域最优值函数。
现 `eq:JD-derivative` 是同一变分用切换易感坐标表示；
容量阶段不免费，但 $C_B+W$ 的全成本变分同样由 `eq:JB-derivative` 的 $\Theta$ 差确定。

在容量线上，减少单位 $\Phi$ 的成本 $\beta/[K(s-p)]$ 随 $s$ 减小而上升，
这只解释“继续维持平台会越来越贵”的一种趋势。完全跟踪后 $i$ 也下降，
同样会使 $\beta/[i(s-p)]$ 上升，因此单价图景不能单独证明容量退出阈值。
严格最优退出仍靠完整成本比较与 HJB 验证。
不变量坐标的几何组织应在此归功于 Angulo 等的方法；本模型的恒等式由本模型重新求导。

## 6. 其他同步点

- C3 完成后，现 `rem:unproved-extensions` 中“$\bar q<1$ 需重新建立可行域和验证函数”
  必须改为“其可行域已由新命题给出，但成本最优反馈/验证函数尚未构造”。
- 概览与表只覆盖常接触率基准；时变、正则化和联合控制段的条件性表述不可并入无条件总定理。
- 保留原有限成本入安全集引理，不更换其成本/终端假设。
- C 阶段无新增优化求解；受限能力仿真若运行，只称包络数值核对，不称完整最优综合。
