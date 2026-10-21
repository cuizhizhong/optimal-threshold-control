# 论文源修改记录

基准 `84a8943`；仅修改 `latex/main.tex`。本记录由论文源编辑子任务生成，编译与独立范围审计由主任务执行。

- 第3节改为“主结果与最优分区”，3.1改为“安全集与可行性”。移出受限能力定义、端点与整段可行域命题及证明。
- Ω 与 D 一并在第3节定义；A 仅在 Ω 上定义一次，保留 `eq:safe-set` 并前移。物理安全状态明确为 A∩D；涉及实际初值、轨道和值函数时采用该交集。`prop:safe-exact` 保留，对 V=0 的陈述限定于 A∩D。
- 任意控制只自动保持总量约束 s+i≤1；容量约束 i≤K 由可行性定义保证。未写“D 对任意控制正向不变”这一不成立的陈述。可行轨道留在 D，在 Ω 建立的几何和候选函数限制到 D 用于物理问题。
- 删除旧安全集重复定义后，余下 widehat A 逐处替换为 A，覆盖可达域、分区、候选反馈、候选成本及正则性。安全集引理保留前向不变性及其原证明论证，仅删全控制安全集的等式与对应句子。
- 将 AFG/FG 的比较写为：在物理域中，无干预安全集与全控制不变集均为 A∩D，可行域为整个 D；这是与新记号一致的范围说明。
- 图1改为 `FigN1_optimal_partition.pdf`，标签 `fig:optimal-partition`，两处引用同步。图注包含 E1/E2 阶段、放大图、容量对照路径与约3.10%成本降幅、线型和参数。降幅分母沿用正文对照成本；未写成“对照比最优高3.10%”。
- 受限能力仅保留未研究说明、容量边界必要约束及不可直接替换最大控制的提醒；理论边界补充 q=1 是理想化完美追踪。
- 未修改模型、保留定理/证明逻辑、数值结果或两个自动生成块。值函数定义仅因 Ω/D 前移作必要排版与定义域说明调整。

## 删除的标签

- `eq:all-control-safe`
- `eq:overview-safe`
- `eq:restricted-capacity-tangent`
- `eq:restricted-constants`
- `eq:restricted-envelope`
- `eq:restricted-invariant-derivative`
- `eq:restricted-viability`
- `eq:viability-definition`
- `eq:viability-endpoints`
- `fig:two-layer-regions`
- `prop:restricted-feasibility`
- `rem:restricted-degeneracies`
- `sec:restricted-feasibility`

`eq:safe-set` 保留前移；旧图标签改为 `fig:optimal-partition`。其余删除标签在主文中无残留引用。
