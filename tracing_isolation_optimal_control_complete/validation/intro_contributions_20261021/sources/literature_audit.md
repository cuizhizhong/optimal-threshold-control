# 阶段 B 最近理论文献核对

核对日期：2026-10-21。只读取 `ref/` 原论文并在本新目录保存文本提取、关键页渲染和此核对记录；未改动既有论文、参考文献或数值记录，优化器调用及 OCP 求解均为 0 次。

本文中的页码均为本地 PDF 的一基页码。MSW、Angulo 和 AFG 为正式版；`Freddi_Goreac.pdf` 为 arXiv:2306.10513v2，`Freddi.pdf` 为 arXiv:2110.11625v2，其页码不冒充正式排版页码。AFG 本地文件将 22 页原文、后附通知和两页勘误合订在一起。

## 可用于引言的比较

| 工作 | 可核查的原文位置 | 可安全采用的比较及边界 |
| --- | --- | --- |
| Miclo–Spiro–Weibull (MSW) | 正式版 PDF p.3，式 (2)–(3)；pp.4–5 Theorem 1；pp.10–12 Appendix A.1–A.2 | SIR 传播率控制 `b>=0`，以无限时域 `integral [beta-b]_+ dt` 为主成本。已有 filling-the-box 解析策略及候选成本的 Hamilton–Jacobi 充分性验证，不能把候选函数验证本身作为本文新贡献。p.3 的主控制类是有限间断的分段连续函数，附录允许更一般的右连续左极限控制；不宜说其已覆盖本文的全部可测控制。成本为零时可免费增强传播，所以安全区内的控制不普遍唯一；p.6 对第三阶段的多重性有明确解释。 |
| Angulo et al. | 正式版 PDF p.2 Fig.1 图注，p.3 Box 1；p.5 Fig.3 图注与 §2.4；p.6 §2.4 | 目标是最短时间进入此后可永久无干预的安全区，亦称最小 effective duration；不是最小累计干预强度，也不是正控制时间集合的测度。已有容量弧后重新采用最大控制的 final push，以及干预能力较弱时在感染达到阈值前开始最大干预。本文应比较不同动力学与强度成本下的切换曲线、提前离开容量和严格验证，不能宣称首先发现这两个阶段结构。 |
| Avram–Freddi–Goreac (AFG) | 正式版 PDF p.3 Definition 2.1 / Remark 2.2，p.4 Theorem 2.3(5b) 与 Problem 3.1；pp.13–14 Theorem 5.6 / Remark 5.7；p.25 勘误正文 | 明确区分无干预安全集 A、所有控制均安全的 A^0 和存在可行控制的 B，并证明 A^0=A。有限且固定的监测时域足够长，成本为 `integral_0^tf [lambda1+lambda2(beta-b)]dt`，且有严格终端 `s(tf)<gamma/beta`；以状态约束 PMP 得到反馈。Theorem 5.6 和 Remark 5.7(2) 已有时间几乎处处唯一性，所以本文第三贡献需绑定自身跟踪模型及容量平台上的 Hamiltonian 退化。附录中的可行域边界不可直接当成本稿成本最优切换曲线。勘误只恢复 §6 Scenario 2 漏印图片。 |
| Freddi–Goreac (FG) | 本地预印本 PDF p.2 引言与式 (1.2)；pp.7–10 Definition 3.1 / Theorem 3.2；p.15 Proposition 6.2 / Corollary 6.3；pp.16–18 §7；p.29 Theorem 9.9 | 无限时域 SIR 传播率削减控制，成本 `integral (lambda1 u+lambda2 i)dt`，包括感染存量成本。先做渐近与可行性，再用 Gamma 收敛连接有限时域，最后用状态约束 PMP 分析结构。最优控制有限时间达到群体免疫依赖本模型及其成本假设，不可直接替代本文有限到达证明。Theorem 9.9 已容许 `0 -> umax -> capacity -> umax -> 0`，阶段可退化；不能宣称容量后加强干预只有 Angulo 最短时间目标才出现。 |
| Freddi–Goreac–Li–Xu (FGLX) | 本地预印本 PDF pp.7–8 Problem 1 / Assumption 1 / §3.3；pp.8–10 Lemma 1 与 Theorem 2(4)；p.11 Remark 6 | 以轨道积分显式构造 greedy 成本 W，并以 Hamilton–Jacobi 验证，已有对一般状态依赖成本的研究。但非负、对控制单调等 Assumption 1 不足以保证 greedy 最优；Theorem 2(4) 要求归一化成本 `l1/(gamma i a)` 满足额外入口比较条件 (15)，Remark 6(2) 说明该条件在文中相应类别下也是必要条件。Remark 6(1) 将最优性还联系到所引用 HJ 唯一性条件。只宜承认显式候选成本与 HJB 验证先例，不把其最优反馈无条件移植到本文。 |

关键渲染已人工查看：`afg_pdf3.png`、`fglx_pdf10.png`、`angulo_pdf5.png`。其中 FGLX 式 (15) 的分母 `gamma i a` 经图像核对；AFG 的三类区域定义以及 Angulo final push 图注经图像核对。

## 三篇 Freddi 系列的独立著录信息

1. Avram, Florin; Freddi, Lorenzo; Goreac, Dan. **Optimal control of a SIR epidemic with ICU constraints and target objectives**. *Applied Mathematics and Computation* **418**, 126816 (2022). DOI: `10.1016/j.amc.2021.126816`。出版方记录：https://www.sciencedirect.com/science/article/pii/S0096300321008997/pdf 。独立勘误为 **423**, 127012 (2022), DOI `10.1016/j.amc.2022.127012`。
2. Freddi, Lorenzo; Goreac, Dan. **Infinite Horizon Optimal Control of a SIR Epidemic Under an ICU Constraint**. *Journal of Convex Analysis* **31**(2), 525–562 (2024). DOI: `10.68381/jca31028`。实时核实正式期刊页面：https://journalofconvexanalysis.com/articles/jca31028/ 。
3. Freddi, Lorenzo; Goreac, Dan; Li, Juan; Xu, Boxiang. **SIR Epidemics with State-Dependent Costs and ICU Constraints: A Hamilton–Jacobi Verification Argument and Dual LP Algorithms**. *Applied Mathematics & Optimization* **86**(2), article 23 (2022). DOI: `10.1007/s00245-022-09884-x`。此正式卷期、文章号在上述 FG 正式期刊页面参考文献第 21 条核实；本地预印本及 https://arxiv.org/abs/2110.11625 核实作者全名与题名。Springer DOI 页面本轮工具无法直接打开，不声称已查看正式全文。

三篇工作应使用三个 BibTeX 项；不把 2023 年 FG 预印本作为另一个独立工作。不用内部中文读书资料替代原文。

## 建议引言措辞

“Miclo 等已通过候选成本的 Hamilton–Jacobi 验证证明线性传播率削减成本下的容量填充策略；Avram 等区分无干预安全集、全控制不变集与可行域，并在固定有限时域和严格终端目标下构造最优反馈。Freddi 等进一步给出显式候选成本的 HJB 验证和无限时域分析。Angulo 等最短时间进入安全区的研究已有容量弧后的 final push；含感染存量成本的无限时域问题也允许容量后再次最大干预。因此，本文比较的对象是跟踪流量引起的切换几何及其在指定强度成本下的充分性和唯一性证明。”

其中本文三项贡献宜分别绑定：全域反馈/切换几何；全部可测可行控制的验证及本模型中的提前离开容量；容量平台 Hamiltonian 极小元退化时的几乎处处唯一性。上述来源不支持“首次采用 HJB”“不使用 PMP 因而更优”“首次容量后加强干预”或无条件的首次唯一性表述。

## 尚未核对的边界

Angulo 本地补充材料是扫描件，`pdftotext` 仅得 20 个空白分页；本轮未 OCR 或逐页审阅补充材料。因此本记录不独立确认其标量极小点唯一性假设、Green 定理证明或全部补充论证；若引言写这些细节，需另查对应原文。本引言所需的最短退出时间、安全区与 final push 已由正式主文明确支持。

所有历史数值均未重算；本记录不构成新的数值结论或优化验证。
