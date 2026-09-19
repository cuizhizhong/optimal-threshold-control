# 来源与新稿定位

## 固定的输入版本

仓库：`cuizhizhong/optimal-threshold-control`。
目录：`tracing_isolation_optimal_control_complete`。
本次底稿：`496e454b34f7ce6861238041d5bd14b475e37917`。
父提交（前次审查对象）：`9d74c88c6bb685faf224a5f23615c203e00fd4b9`。
新提交仅新增参考 PDF 和 HJB 定义笔记，主稿 Git blob 仍为 `4ca903f272c8f60ddb308df8f4b550f7364cb971`。

`references.bib` 原 Git blob：`3a92a56b10e39128781902934f5e8f70ffa25482`。
将本包 bibliography 的字节按 Git blob 规则重新计算 SHA-1，所得值完全相同；本次没有改动该文件的条目。
主稿的段落、结构与证明有实质修改；本说明为章节/标签级对照，不是声称逐字保留的 diff。

## 采用和修正的源材料

| 来源（相对于仓库项目目录） | 使用方式 |
|---|---|
| `latex/main.tex` | 保留模型、成本、正确的弧和导数计算，重写验证及唯一性 |
| `假设推导和验证/G1-G4-theory-audit.md` | 统一残差、可达域修复、平台唯一性和终端论证的主线 |
| `假设推导和验证/assumptions_to_theorems.tex` | 采用可达判据等正确推导；不采用过大容量等待域及全部异常极值不存在的结论 |
| `论文证明补充/switching_curve_monotonicity.tex` | 采用非平凡分支的参数化符号推导，并展开全分支端点 |
| `论文证明补充/prerequisites_for_verification.tex` | 采用等待梯度和容量打平恒等式；重写离边步骤 |
| `论文证明补充/global_geometry_and_uniqueness.tex` | 采用几何横穿思想；不用错误安全边界广义梯度等式和漏掉立即控制的判别 |
| `论文证明补充/transversality_and_verification.tex` | 终端处理用更强的有限时间到达引理统一替换 |
| `问题定义/HJB问题流程.md` | 采用先定义 V、区分目标 Dirichlet 数据与容量方向约束的组织方式 |

旧补充不作为新主稿的 `input` 依赖；后续应只维护这份统一 main.tex。

## 外部数学来源的确切角色

Miclo, Spiro and Weibull (2022), *Journal of Mathematical Economics* 101, 102669，
期刊版附录 A.1–A.2（PDF 第 10–12 页）给出 U<=V、U>=V 的 HJB 验证框架、状态约束控制集以及平台点态打平计算。
实际参照的是期刊版 `1-s2.0-S0304406822000258-main.pdf`，而不是误把 2020 年预印本的不同证明作为同一个附录。

Liberzon (2012), *Calculus of Variations and Optimal Control Theory: A Concise Introduction*，
§5.1.4，印刷第 165–167 页（上传 PDF 第 184–186 页），用于区分充分性验证、全局比较和控制唯一性。
该节明确不把验证得到的最优控制自动称为唯一。

新模型的 Gamma、全域 U、可达域、正则性及轨道唯一性由本稿推导，不能由以上引用代替。
Avram–Freddi–Goreac 的上传论文不作为本次新增主证明的外部定理依赖。

## 新主稿关键位置

下表源码行号针对本包交付版本。编号来自实际编译的常接触率校样；时变部分仅在全文入口中出现。

| 内容 | LaTeX 标签 | 理论校样编号 | main.tex 行号 |
|---|---|---:|---:|
| 问题、模型和控制类 | `sec:model` | 1 | 88 |
| 真正的值函数 | `eq:value-definition` | 11 | 189 |
| 有限成本比较策略 | `lem:finite-feasible` | 5.1 | 332 |
| 有限成本有限时间入安全集 | `lem:finite-entry` | 5.2 | 351 |
| 首次到达等价问题 | `prop:exit-equivalence` | 5.3 | 371 |
| HJB 与边界条件 | `sec:HJB` | 6 | 393 |
| 完全跟踪可达域 | `prop:reachable` | 7.1 | 445 |
| 单峰性与分支存在性 | `lem:unimodal` | 8.1 | 542 |
| 切换曲线完整参数化 | `prop:Gamma-geometry` | 8.2 | 572 |
| 容量截断与 Phi 标号 | `cor:Gamma-labels` | 8.3 | 621 |
| 任意控制方向横穿 | `lem:strict-crossing` | 8.4 | 646 |
| 全域分区 | `def:regions` | 9.1 | 688 |
| 完全跟踪区的可达与保持 | `lem:tracking-region` | 9.2 | 704 |
| 候选 U 与反馈 | `def:candidate` | 9.3 | 734 |
| 候选达到性 | `prop:candidate-attainment` | 9.4 | 764 |
| 统一等待梯度 | `lem:waiting-gradient` | 10.1 | 805 |
| 等待区 HJB 严格符号 | `lem:waiting-HJB` | 10.2 | 835 |
| 正则性与拼接 | `prop:regularity` | 10.3 | 861 |
| 各区 Hamiltonian | `prop:all-HJB` | 10.5 | 935 |
| 沿任意轨道的验证不等式 | `lem:trajectory-verification` | 10.6 | 963 |
| 全局最优性 | `thm:verification` | 11.1 | 993 |
| 几乎处处唯一性 | `thm:unique-q` | 12.1 | 1021 |
| 一维策略族唯一极小 | `cor:one-dimensional-min` | 12.2 | 1087 |
| 未完成的扩展 | `rem:unproved-extensions` | 仅全文入口显示 | 1361 |

交付主稿 SHA-256：`1e65689a32b2dc9331ec8813001eb4d186e50e651677966b0be7a22fc2824bf8`。
