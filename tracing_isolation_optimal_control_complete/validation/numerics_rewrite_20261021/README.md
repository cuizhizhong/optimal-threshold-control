# 阶段 F：数值章节重写

基准为 `89d9cc3751951fd236f304c65ca0ee7fc2e667ef`，分支为 `codex/numerical-reproducibility-revision`。本阶段仅整理已保存的无回流数值证据，单独提交，不推送，提交后等待作者审阅。

## 修改范围

第17节明确固定 `T=300` 的终端处理：只有连续轨道满足容量约束且终点进入相应安全集时，零控制延拓才给出无穷时域可行控制。发生容量超出时，与 `V_{K+ε_K}` 比较。重积分是浮点诊断，没有证明离散有限时域最优值随网格加密收敛到 `V`。

第18节保留相图、时间序列及两段实际阶段观测，新增带符号成本与容量误差表和五句残差摘要。图1与图2以及三个数值图均不修改。原来的检查、稳健性及总体结论宏整体移入“补充材料 S：数值复现、复核与诊断记录”，仍受现有 TheoryOnly 条件控制；本阶段不拆文件。

导出器只新增 `NumErrorTableRows`、`NumResidualSummary`，三套回归保留旧断言并增加新宏断言。失效清空列表同步更新。误差表下降量使用原有 `relaxed_capacity_drop`，独立脚本以保存参数复现原解析公式核对，不调用优化器、OCP 或 ODE。

## 已知证据缺口（只记录，不补算）

1. 没有网格加密收敛阶，也没有离散有限时域最优值到无穷时域值函数的收敛证明。`n=4000` 与 `8000` 的一致性比较不能补足这项证据。
2. `n=16000`、`T=600` 及额外初猜未运行。已有35项配置的网格为 `1600/2000/3200/4000/8000`，时域为 `60/120/300`；不将未运行设置写成结果。
3. E2、E4 在 `n=2000` 有阶段识别异常，保存分类为 `long_intermediate_control`，容量弧识别数均为0，观测结构分别为 `0→1→0` 和 `1→0`；容量超出分别约为 `1.44613e-5`、`1.24063e-5`。
4. E1、E3、E5 在 `n=2000` 的成本比较未通过，带符号成本差分别约为 `4.30554e-5`、`−6.75539e-5`、`1.45464e-4`。
5. E3 在 `n=2000` 的负成本差伴随约 `7.83007e-6` 的容量超出。按原有解析公式放宽容量得到的值函数下降约为 `1.07550e-4`，大于负差绝对值，故与容量超出相容；原有 `unresolved_discrepancy` 分类保留，没有重新评估或改写记录。
6. 所有重积分、终端安全及残差判断仍是浮点诊断，不是严格连续可行性的数值证书。末段控制为零和终端安全检查不能提供网格收敛证据。
7. 原判据同时通过 `28/35`，求解后修订判据同时通过 `30/35`。修订只改变浮点接受尺度，未产生新求解或新收敛证据；原始评估和未通过项均保留。
8. 原有保存评估没有持久化 `relaxed_capacity_drop` 字段；该量由现存导出器解析函数即时评价。独立脚本另行实现同一解析构造，保存函数原文哈希、参数、公式及逐项比对，明确区分原保存字段和本阶段只读复算。

各缺口的具体 run、评估路径和来源见 `evidence_gaps.json`。不开展半拉格朗日、额外初猜、网格加密或其他增强计算。

## 验证入口与记录

- `run_export_f.m`：只调用 `export_numerical_latex()` 及 S2.7 的三套导出器回归。
- `verify_error_table.py`：独立读取 `numerical_checks.json`、所选保存评估及 S2.6 报告，重算表值、判断与残差来源，保存 `audit_error_table.json` 和 `evidence_gaps.json`。
- `preserve_f.py`：保存基准文件字节哈希，核对全部旧宏和数值节以外正文逐字不变，核对图形及数据保护。
- `build_f.py`：双稿完整执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，并单列预编译/追加编译。隔离模式从 Git 暂存区导出仅 `latex/`、`figures/`，从零构建并审计输入。
- `render_f.py`：150 dpi 渲染第17、18节全部实际页面、新表页面及补充材料 S 全部页面。

删除内部执行注释前，检索了 `matlab/` 和 `validation/` 的176个脚本文件，无脚本依赖这些标记，见 `comment_dependency_search.json`。旧验证快照中保留的原稿不修改。

首次默认沙箱启动 MATLAB 因 `PrefdirNotWritable` 在执行入口前退出，错误保存在 `matlab_sandbox_failure.log`。随后在授权环境重试同一入口，不通过改变科学配置规避启动限制。

本轮优化器调用、新增 OCP 求解、ODE 积分、图形重新导出均为0。MATLAB 仅用于本阶段重新导出及三套回归。

## 实际结果与复现命令

从仓库根目录执行，下列入口的实际 argv、cwd、退出码及输入/输出哈希保存在各 JSON 与日志中：

```powershell
python -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/preserve_f.py --baseline
& 'E:/software/Matlab/bin/matlab.exe' -batch "addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios')); addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','numerics_rewrite_20261021')); run_export_f();" -logfile 'tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/matlab_authorized_console.log'
python -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/verify_error_table.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/preserve_f.py
python -X utf8 tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/build_f.py --mode workspace --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/build_f.py --mode isolated --attempt 2 --pre-xelatex 0 --post-xelatex 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/render_f.py --build-report tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/workspace_attempt2/build_report.json --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/finalize_f.py --publish
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 tracing_isolation_optimal_control_complete/validation/numerics_rewrite_20261021/finalize_f.py
```

`--baseline` 和已有 attempt 禁止覆盖；复核时直接读取已有证据或使用新的 attempt 编号。符号脚本的最终实际输出另存 `notation_checks.log`。隔离构建之前仅显式暂存 `latex/main.tex`，图形文件沿用基准，导出器测试不修改正式主稿。

- 导出 `verified=true`；三套回归分别 **11/11、3/3、2/2**。pending/failed/provenance 故障注入只发生在测试临时目录，不是新科学实验。
- 误差表 **20个数值、5个判断全部通过**；五句残差摘要的4个显示数值、终端检查、原/修订判据计数及异常名单均独立核对通过。E4 为 `−3.68e−6`、`ε_K=7.70e−7`、下降 `1.16e−5`；五例最大相对差 **0.00459%**。
- 原符号恒等式 **28/28**。保护审计 **12/12**，覆盖6605个旧文件、全部原有数值宏、参考值生成块、授权范围外正文、全部定理证明、数据与五组指定图形。
- 仓库内最终主文与 TheoryOnly 各完整四阶段退出0，最终 log/blg/stdout 无错误、警告、未定义引用、缺字或溢出；每稿还单列一次预编译。前后总页数均为 **46/36**。
- Git 暂存区导出的全新副本初始根只有 `latex/` 和 `figures/`。在副本中移除 Git 跟踪的旧 bbl/PDF 后，每稿从零执行 **XeLaTeX → BibTeX → XeLaTeX → XeLaTeX → XeLaTeX**，即完整四阶段后额外一遍 XeLaTeX；10个进程全部退出0，最终零诊断。每项导出资产的 clean-filter blob 与 index 相同，FLS 禁止回读原项目和 validation。两种构建的全部页面提取文本逐页相同；TheoryOnly 的全部36页文本还与基准相同。
- 第17节前后均触及第30–32页；第18节由第32–36页缩至第32–35页。合并去除共享页后，数值正文由 **7页变为6页**。这是实际物理页跨度，包含其间原有图2的浮动页，不冒充纯文字长度；补充材料前后均触及第43–44页。
- 实际150 dpi渲染并逐页查看 **30–35、43–44页**，共8页，覆盖第17/18节所有页、新表第33页及补充材料全部页。PNG、逐页文本和目视记录归档于 `rendered_150dpi/`、`visual_qa.json`；未声称目视全部46页。

## 保留的失败与修复

- MATLAB 默认沙箱因预设目录不可写在进入函数前退出；授权重试同一入口成功，没有改变数值设置。
- 首次仓库构建的路径段落出现4条 overfull，保留 `workspace_attempt1/`，改成逐项分行路径后 `workspace_attempt2/` 通过。
- 首次隔离构建的所有命令退出0，但最终仍有 `Label(s) may have changed`，没有将其记为通过。此前额外 XeLaTeX 放在 BibTeX 之前；在全新 `isolated_attempt2/` 中改为四阶段后追加一遍，最终通过。两个最终验收合计20个 TeX/Bib进程，两个保留的失败尝试各5个，本轮共30个。
- 独立检查器首次将末行 `\\}` 中的偶数反斜线误判为右括号转义，修正括号解析后严格通过；生产宏及数据未因此修改。保护脚本也补全 Windows 长路径的存在性检查。前者说明见 `audit_parser_initial_failure.json`。
- 首次汇总以原始文本哈希比较跨 Git 检出的源文件，因 `main.tex` 的 LF/CRLF 不同报1项失败，保留 `acceptance_initial_failure.json`。现在同时保留原始哈希差异、逐字文本行尾归一比较、Git clean-filter blob核对及完整PDF逐页文本核对；未重写文件来消除行尾差异。原始数据和图形仍按字节哈希保护，见 `git_export_source_identity.json`。

正式PDF与仓库内最终构建哈希一致，最终汇总见 `acceptance_report.json`。改动文件逐项列于 `changed_files.txt`；本报告及验证记录和生产改动一并纳入一次本地提交 `paper: 数值章节重写（F）`。不推送，不进入G，等待作者审阅终端处理、新表、残差摘要及补充材料安排。
