# TheoryOnly 六页与 C 返修差异的独立复核

## 范围与证据

- 复核对象：相对 `a2909a8` 的 `latex/main.tex` 工作区差异，以及本轮 `tmp/geometry_review_20261021/attempt1/` 的编译日志和辅助文件。
- 按 PDF 技能的只读流程，实际目视 `tmp/geometry_review_20261021/qa/theory_only_sheet_1.png` 至 `theory_only_sheet_3.png`，覆盖 TheoryOnly 第 **5、6、7、8、10、27** 页，共 **6 页**。
- 本次只读核查，没有修改论文源文件、没有重新编译或渲染，没有运行 ODE、OCP 或优化器。

## 源文差异核查

1. **常接触率的适用范围正确。** `sec:main-results` 开头改为“本节及第 `sec:constant-problem`--`sec:constant-uniqueness` 节固定”，本轮辅助文件解析为第 3 节及第 5--14 节，排除了第 4 节 `sec:wellposed`。第 4 节仍保留时变有界可测 `c(t)` 的假设。
2. **概览已有足够的符号说明。** `\Phi(s,i)=i+s-h\ln s` 的带标签定义前移至主定理前；原位置改为交叉引用，辅助文件中 `eq:Phi` 只定义一次。文字将它限定为零控制自然轨道标签，并解释 `\Gamma_K`、辅助条带容量交点 `(s_B,K)`、`\Phi_B` 与按区域选取控制的 `Q^*`。精确构造继续前引后文，未复制证明。
3. **五行策略表准确。** 分别列出 `\Acal`、`\mathcal T\cup\Gamma_K`、`\mathcal W_\Gamma`、`\mathcal W_K`、`\mathcal B`。`\mathcal B` 直接列 `q_B→1→0`，表后明确限定 `i=K,s>s_B`，并说明等待为零和 `\Phi=\Phi_B` 的容量段为零；与既有区域定义和最优策略推论一致。
4. **安全集引理的去重安全。** `lem:safe-invariant` 继续证明前向不变性及 `\mathcal A^0=\Acal`，删掉重复的 `\mathcal V_0`、`\mathcal V_1` 陈述和指数解。概览将可行域端点的依据明确指向 `prop:restricted-feasibility`。命题、引理及标签保留，没有新的循环依赖。
5. **水平集引用仅增加定位。** 原有相关短语改为指向 `eq:ac-level-set`，不改变绝对连续性、容量时间集或严格横穿证明中的假设和推导。
6. **C4 明确采用常接触率。** `sec:switching-mechanism` 新增“本节采用式 `eq:constants` 的常接触率假设”，与其不变量坐标恒等式适用范围一致。

## Main-only 相平面对照图

- 恢复的 `\NumFigureOrBlank{FigN1_regions.pdf}{4.2cm}` 位于源文从 `\ifdefined\TheoryOnly\else` 开始、至数值及扩展章节末尾 `\fi` 结束的条件块内。
- 本轮 `attempt1/main.aux` 有 `fig:numerical-regions`，解析为 **图 2、第 31 页**，图注明确比较 E1--E5 的初始点、OpenOCL 轨道和理论分区。
- 本轮 `attempt1/theory_only.aux` 无 `fig:numerical-regions`，因此 TheoryOnly 没有包含该恢复图。两层理论图 `fig:two-layer-regions` 在两稿均保留。
- 检查采用本轮 `attempt1` 辅助文件；`latex/` 根目录下的旧辅助文件不作为本轮证据。

## 六页目视结果

| TheoryOnly 页码 | 核查内容 | 结果 |
|---|---|---|
| 5 | 第 3 节开头的常数范围、物理域和目标泛函 | “本节及第 5--14 节”可读；公式和段落完整，无裁切或溢出 |
| 6 | 两层集合、前置 `\Phi` 定义、`Q^*` 概念和主定理 | 新符号解释在定理前；交叉引用正常，未见缺字或重叠 |
| 7 | 五行文字表、零长度说明、两层图、第 4 节起始 | 表格四列排列完整，行与列无重叠；图文清楚；第 4 节仍明确使用 `c(t)` |
| 8 | 第 4 节续证、水平集性质、第 5 节自然不变量 | 式 (18) 正常；自然不变量明确回引式 (13)，没有第二份定义 |
| 10 | 受限能力端点、退化说明、安全集引理 | 引理仅保留不变性与 `\mathcal A^0=\Acal`；证明收束完整，公式无裁切 |
| 27 | C4 机制说明及常接触率声明 | 常数假设句可见；式 (101)、(102) 与机制解释衔接正常，无排版问题 |

本轮最终日志复核：`main.log` 报告 **43 页**，`theory_only.log` 报告 **33 页**；对两份日志搜索错误、未定义引用、LaTeX/Package 警告以及 Overfull/Underfull 未发现命中。此为独立读取最终日志，没有另行运行编译。

结论：本次委托范围内未发现需要继续修改的问题；六页目视通过，主文恢复 N1 的条件边界符合 main-only 要求。
