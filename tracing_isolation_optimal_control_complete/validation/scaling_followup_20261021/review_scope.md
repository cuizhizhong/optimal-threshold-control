# D 后续独立范围审阅

基准提交为 `9a67992248f41dada8c02b2e1851fc87ffa54f4f`。本审阅只检查论文范围、解释及保护项，不调用 MATLAB、优化器或新增 OCP 求解。

## 可保护的原稿锚点

- 模型节 `sec:model` 整节应逐字保留。
- 所有原有 `theorem`、`proposition`、`lemma`、`corollary`、`assumption`、`definition`、`proof` 环境应逐字保留，特别是 `prop:small-capacity` 和附录 `app:small-capacity-proof`。
- 公共尾段关系 `eq:common-capacity-comparison` 及其他所有原陈列公式保持原样。
- 两组 `BEGIN/END AUTO-GENERATED` 标记及其内容逐字保留。
- 原 D 文件 `computed_values.tex` 中 17 个宏的数值字符串保持原样；新文件可以追加新宏。
- 四组指定数值图的 PDF/PNG 与原 D 验证目录的全部历史记录按字节保护。

`scope_review.py` 对上述内容做可复核的 Git 基线对比，并把结果写入 `scope_review.json`。文本比较只归一化 CRLF/LF；二进制图和历史证据直接比较原始字节。

## 时长解释的边界

本文目标为带权强度积分 `J`，正控制时长为 `q>0` 集合的测度。容量弧在 `s` 接近 `h` 时控制强度趋零，因而可以出现耗时较长但强度成本很小的尾段。最优策略以短时完全跟踪替代这段尾部，成本收益为高阶小量而时长差趋于正常数，两者并不矛盾。

`1/(βγ)` 的极限依赖固定正 `β` 及共同容量入口的初值族；它不表示对小 `β` 一致收敛，也不应被表述为正控制时长最优性。西安的有限 `K=0.01` 时长收益必须直接使用公共尾段求值，不能拿极限代替有限容量的结果。

## 自包含编译所需证据

临时测试根应只含并列的 `latex/` 与 `figures/`。不复制旧 `.aux`、`.bbl`、`.toc` 等构建残留，且测试根及其上层不存在可被相对引用命中的 `validation/`。在临时 `latex/` 中分别对 `main.tex`、`theory_only.tex` 执行 `XeLaTeX → BibTeX → XeLaTeX → XeLaTeX`，保留每阶段命令、退出码、最终日志和页数。

建议编译加 `-recorder`，保存 `.fls`，核对项目内输入只来自复制的 `latex/` 和 `figures/`；TeX 发行版、字体和系统配置依赖属于运行环境，不能把这些依赖误报为稿件不自包含。源码中的正文 `\path{validation/...}` 只是可见文本，不构成编译依赖。

## 本次实际审阅结果

已运行 `python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/scope_review.py`，25/25 项通过。模型整节、69 个原定理类及证明环境、114 个原陈列公式、两组自动生成数值块、原 17 个 D 宏的展示数字保持原样；指定 8 个 PDF/PNG 和原 D 验证目录 84 个受 Git 跟踪的文件按字节相同。

新增正文把 E2 的时长差写为 `2.536302`、缩短 `53.17%`，西安情景写为 `8.263905` 日、缩短 `25.41%`；西安固定参数的时长差极限写为 `24.343` 日。有限容量的差值使用公共尾段公式，不以两个总时长相减获得。正文保留“正控制时长不是本文的优化目标，成本最优策略并不同时最小化正控制时长”，没有把该比较推广为时长最优性。

本独立范围审阅没有亲自调用编译器或执行目视检查；编译结论通过下述原始 recorder、BibTeX 日志及命令记录的独立复核获得，页面外观仍以主执行者的渲染检查为依据。

## 自包含编译的独立复核

已阅读 `build_followup.py`，并独立重新解析 `isolated_attempt2/main_final.fls` 与 `theory_only_final.fls` 的全部 `INPUT`。解析结果与保存的 `main_inputs.json`、`theory_only_inputs.json` 一致。

全新隔离根在开始时仅有并列的 `figures/` 与 `latex/`，复制清单共 14 个输入资产，不含 `.aux`、`.bbl`、`.log` 等旧构建文件。全部复制输入的 SHA-256 同时匹配隔离副本与本次原稿。主文 recorder 共 153 个唯一输入，其中 11 个在隔离根，另 142 个为 TeX Live 或 Windows 字体；TheoryOnly 共 151 个唯一输入，其中 9 个在隔离根，另 142 个为同类系统依赖。两份文档均未回读原项目的 `validation/`、原 `latex/`、原 `figures/` 或其他原项目文件，也没有未解释的外部输入。

BibTeX 的数据库不进入 XeLaTeX 的 recorder，因此另查两份 `.blg`：均只读 `references.bib`。命令环境中的 `BIBINPUTS` 指向隔离副本的 `latex/`，该数据库的复制 SHA-256 已核对；`TEXINPUTS`、`BSTINPUTS`、`TEXMFOUTPUT` 均已清除继承值。

最终验收的两份文档各执行 `XeLaTeX → BibTeX → XeLaTeX → XeLaTeX`，共 8 条命令退出码全部为 0，最终日志没有错误、警告、未定义引用、字符缺失或版面溢出/不足；主文 46 页，TheoryOnly 36 页。原始失败尝试仍完整保留：`isolated_attempt1` 的首次干净四阶段主文最后仍有交叉引用重跑警告。`isolated_attempt2` 重新创建干净副本，在最终 8 条验收命令之前执行了 8 条引用初始化命令；这些初始化的中间产物来自该隔离副本自身，没有借用仓库旧辅助文件。本结论因此是“全新隔离副本自行初始化后，最终双稿四阶段严格验收通过”，不把它缩写为“首次干净四阶段即零警告”。

`scope_review.py` 已再次运行，范围核查仍为 25/25，并在 `scope_review.json` 的 `selfcontained_review` 中保存上述独立输入分类、命令和数据库核对结果。`source_sha256` 同时记录基线与本次 `main.tex` 的原始字节哈希。
