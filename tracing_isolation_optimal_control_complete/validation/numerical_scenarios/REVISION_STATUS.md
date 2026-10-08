# 第 0–11 步执行状态

本批仅执行第10–11步；第0–9步记录保持历史证据。计划不作为结果，科学优化0次；候选检出35次可信缓存、1次独立接口smoke。原严格grid一致性失败保留。

| 步骤 | 状态 | 证据 |
|---|---|---|
| 0：冻结基准、环境预检 | completed | `BASELINE.json`、`preflight_report.json`、`preflight_tests.json`；四项回归通过 |
| 1：恢复独立解析检查点 | completed | `step1_python_tests.json`、`step1_matlab_tests.json`；Python/MATLAB 各六项通过 |
| 2：缓存与来源修复 | completed | `cache_unit_report.json`、`preparation_unit_report.json`；六项 mock 与构建接口通过 |
| 3：求解信息及分离评估 | completed | `step3_solver_tests.json`、`step3_assessment_tests.json`；10 项求解接口、12 项评估和 7 项初猜比较通过 |
| 4：独立事件区间识别 | completed | `step4_unit_tests.json`；13 项容量退出及 14 项总体事件测试通过 |
| 5：理论片段合并及编译 | completed | `step5_validation_report.json`、`step5_theory_protection.json`；main 34 页、TheoryOnly 26 页及变更页/图表渲染通过 |
| 6：冻结配置与调度器 | completed | `step67_protocol_manifest.json`：35 配置；最终 12 组单元测试通过，调度回归 19 项 |
| 7：单元测试及五例主算例 | completed | `step67_unit_report.json`、`step67_main_report.json`；五例真实求解成功，双旗标全通过 |
| 8：五例常值及固定种子随机初猜 | completed | `step89_initialization_report.json`：10 次成功，两旗标及逐例比较全通过；保存初猜复核 10/10 |
| 9：固定 T 网格、固定步长时域、阈值复核 | completed | 三组协议均实际执行完整；原 grid 一致性失败，horizon/threshold 通过，失败记录保留 |
| 10：正文、结果宏及图表更新 | completed | `step1011_postprocess_report.json`、`step1011_final_export_report.json`、`step1011_pdf_qa.json`；主结果true、协议完成true、一致性false |
| 11：干净复现与最终编译 | completed | `step1011_validation_report.json`；候选缓存35、科学重求解0、独立smoke1成功，双版本编译及渲染通过；所有先前异常保留 |

## 第 8–9 步本批状态

起始提交为 `c23a5d6bdc7fd97ea53e32a485ca03996789831b`，沿用当前分支。起始 5 条科学原始记录和 37 个受保护文件的字节基准见 `step89_baseline.json`。执行入口为 `execute_stage89.m`，逐组调用 `run_revision_validation('initialization',false)`、`grid`、`horizon` 和 `threshold`。五例主选择保持原有记录，重复配置仅在可信缓存匹配时复用。

受限启动更换了本批独立偏好目录，但未进入 MATLAB 脚本、日志为空，已终止；该环境启动尝试不计为优化失败，保存为 `step89_startup_attempts.json`。随后在获准本机环境实际启动，预检与源码/协议哈希保存为 `step89_preflight.json`、`step89_source_fingerprints.json`。默认执行入口与只读 MATLAB 初猜复核均真实退出 0。

本批新增优化 30 次，成功 30 次，求解失败 0 次，可信缓存引用 10 次。与前批五条主记录一起，默认 35 个不同配置已全部实际执行或可信复用。`completed` 表示实验执行和记录完成，不表示每条记录数值可接受：35 条中 `numeric_pass` 为 29/35，`agreement_pass` 为 29/35，两者同时通过为 28/35。

| 组 | 配置或识别数 | 本批优化 | 缓存 | 求解成功 | numeric / agreement | 原汇总一致性 |
|---|---:|---:|---:|---:|---|---|
| initialization | 10 | 10 | 0 | 10 | 10 / 10 | true |
| grid | 15 | 10 | 5 | 15 | 9 / 9 | false |
| horizon | 15 | 10 | 5 | 15 | 15 / 15 | true |
| threshold | 45 | 0 | 0 | 不适用 | 不适用 | true |

五例常值控制均确为 0.7；随机种子为 20261009–20261013。保存控制、节点及内部配点状态的 MATLAB 重建复核 10/10 通过，误差均为 0，优化调用为 0，见 `step89_initialization_validation.json` 与日志。独立 SciPy 实现另复核全部初猜和求解输出。E4 随机初猜的采样容量超出为 `0.05681958182745708`，保留原状态，不压平到 K；初猜超出不等于求解后不可行。非理论初猜与同一离散主例的最大成本绝对差为 `6.10178574333986e-13`。

以下七条求解成功但至少一类诊断未通过，全部原始输入、控制、状态、solver info 与评估保留：

| 案例与网格 | numeric_pass | agreement_pass | 实测未通过项 |
|---|---|---|---|
| E1，N=2000 | true | false | 成本相对差 `+1.0345232426e-4` 超过 1e-4 |
| E2，N=2000 | false | false | 容量超出 `1.446128092e-5`；状态差 `5.873068225e-6`；长混合控制，容量事件缺失 |
| E2，N=4000 | false | true | 容量超出 `3.339275208e-6` |
| E3，N=2000 | false | false | 容量超出 `7.830067991e-6`；成本相对差 `-1.5566093353e-4` |
| E4，N=2000 | false | false | 容量超出 `1.240625140e-5`；长混合控制，容量事件缺失 |
| E4，N=4000 | false | false | 容量超出 `3.090839865e-6`；容量段平均 q_B 差 `0.0025306491159656774` 超过 0.002 |
| E5，N=2000 | false | false | 容量超出 `2.568463678e-6`；成本相对差 `+2.7126962818e-4` |

原 grid 汇总要求最细与次细均 `numeric_pass`，故 E2/E4 未作比较，原 `status=failed` 和 null 差值保留。独立按计划第 9A 建议口径复核：只要求最细数值接受、最细两级实际结构/事件可比较且主要事件在网格尺度上接近，五例均满足，最细两级成本相对差最大为 `3.557214836644053e-5`。次细不可接受的旗标不改变，也未放宽阈值；据此未追加 N=16000。

固定 dt=0.0375 的三个时域全部通过，五例成本绝对跨度最大为 `1.767075374914384e-11`。比较窗口 [0,18] 的实际节点状态与控制差及所有事件、最后 20 时间单位控制、重积分终端 P0 均保存在 horizon 摘要。阈值 3×3×5 共 45 组合全部通过；同一五条主源只重识别，优化调用为 0。无需追加 T=600；没有超过预定尺度且数值可接受的 `unresolved_discrepancy`。

新 raw 来源提交为本批起始提交，求解源码原字节哈希仍为 `cd7e6297bb05f11028fe6f8f543ae8a9f5bd8c41d4f98346a0dc7b7cd09cff49`，协议哈希仍为 `537248f24a972508866e476433ab446a2cdda0f553fc70b66a32edb73f657a3b`。`solve_dirty=true` 如实反映工作区材料，旧缓存的 solve commit、时间和原字节不改写。本批没有更改求解源码、OCP、接受阈值、主选择、理论正文或图表，没有重编 `main.pdf`，不执行第 10–11 步。

汇总入口为 `summarize_stage89.py`；JSON/CSV、批次 manifest 和请求均位于 `data/numerical_scenarios/revision_checks/`。最终独立完整性复核实际退出 0，37 项受保护文件、35 条原始记录、四组 JSON/CSV 和全部检测输出通过，证据为 `step89_integrity_report.json`、`step89_integrity_attempt1.log`。SciPy 独立初猜重积分最大状态差为 `4.451994328746878e-14`，独立原控制重积分最大节点差为 `1.1157741397482823e-14`。结果摘要保存为 `step89_validation_report.json`、`step89_results.md`。数值接受、有限网格/时域比较与重复局部收敛均不构成连续可行性或全局最优性的新增证明。

## 第 6–7 步本批状态

起始提交为 `fcd02a9365beac6dd6623cf4c699d5a36ebccaa7`，沿用 `codex/numerical-reproducibility-revision`。起始无已跟踪修改，既有未跟踪材料保留。默认矩阵是待执行的 35 个不同配置，不是 35 项实验结果；本次只运行 unit/main，其余模式的科学执行等待后续授权。

首次受限 MATLAB 启动因 `MATLAB::settings::prefdir::PrefdirNotWritable` 失败，随后获准在本机环境预检成功。实际 MATLAB 为 `25.2.0.2998904 (R2025b)`，CasADi 为 `3.4.5`，`has_nlpsol('ipopt')` 可用。OpenOCL/IPOPT 版本无法通过现有接口确认时保持 `unknown`，不从旧记录推测。见 `step67_baseline.json`、`step67_preflight.log` 与 `step67_preflight.json`。

独立 Python fixture `--check` 和六项 unittest 已实际通过，见 `step67_python_regression.json`，真实优化调用为 0。这些是解析实现回归，不能代替五例 MATLAB/OpenOCL 求解。

最终 MATLAB 单元入口 `run_revision_validation('unit',false)` 已真实退出 0，12 组全部通过，调度回归 19 项。包括原参考/依赖/缓存/求解诊断/评估/事件、E0及退化阶段、极小正感染量、原动力学不变量、完整非均匀网格计价、导出防陈旧、随机初猜重建、force 指纹去重、普通失败继续、持久化后异常计数、缺环境 blocked 和 threshold 不求解。模拟调度的 35 次执行不计为科学优化。初次 exporter 测试夹具 struct 初始化错误的失败日志为 `step67_unit_attempt1.log`，修复后完整回归通过；第二次通过日志另存 `step67_unit_attempt2.log`。

54 个 MATLAB 文件已实际执行 `checkcode(...,'-id')`，报告为 `step67_matlab_code_analyzer.json`。冻结协议哈希为 `537248f24a972508866e476433ab446a2cdda0f553fc70b66a32edb73f657a3b`；求解源码原字节哈希为 `cd7e6297bb05f11028fe6f8f543ae8a9f5bd8c41d4f98346a0dc7b7cd09cff49`，明细见 `step67_source_fingerprints.json`。本条记录只证明配置和测试，不表示科学优化已经完成。

代码冻结提交为 `be43bc6ccc5d280e9b0287a00554df1590518bea`，在此提交之后实际执行 `run_revision_validation('main',false)`，MATLAB 退出码为 0。主批次为 `batch_cb8bb06aaa314668a9e553522232368f`，实际求解 5 次、成功 5 次、失败 0 次、缓存命中 0 次、评估 5 次。MATLAB/OpenOCL 环境可用，无当前 blocked 项。默认 35 配置实际执行并通过 5/35，其余 30 配置及第 8–11 步为 `not_started`；初猜/网格/时域/阈值调度与摘要代码仅实现，不宣称科学复核已完成。

| 案例 | 实测 J_openocl | numeric_pass | agreement_pass | 数值识别结构 |
|---|---:|---|---|---|
| E1 | 0.41620500909728464 | true | true | 0 → 1 → 0 |
| E2 | 1.5295233613984434 | true | true | 0 → q_B → 1 → 0 |
| E3 | 0.43399851635235542 | true | true | 1 → 0 |
| E4 | 1.2688310955840425 | true | true | q_B → 1 → 0 |
| E5 | 0.53625636159160439 | true | true | 1 → 0 |

最大重积分容量超出为 `7.991060546608253e-7`，最大配点节点与重积分状态差为 `8.57058412018219e-8`，最大成本相对差绝对值为 `4.5879306830530925e-5`；五例尾段控制幅值均为 0。这些是实际运行的浮点诊断，不是严格可行性或误差上界。E1 完全跟踪过渡段的 i 两端约为 0.132638/0.133049，小于 K；E2 检测到正长度容量段；E3/E5 完全跟踪从 0 开始；E4 容量段从 0 开始。详细原始区间和稠密状态距离见每例 assessment。

E4 实测成本比解析值低 `3.6827584466436747e-6`，相对差为 `-2.9024728116725762e-6`，重积分容量超出为 `7.702869587733474e-7`。差异均在预定诊断容差内，没有超过预定尺度的 `unresolved_discrepancy`；不能据此声称严格可行或优于解析解，小容量超出也不提供成本影响的严格上界。原始输出完整保留，没有剪裁、平滑或替换。

原始 `.mat`、`.solver.json`、独立评估 sidecar、五例 `main_summary.csv/json`、完整 batch/request manifest 及主选择 manifest 已保存。所有新 raw 的来源提交为冻结提交，求解源码哈希与冻结版本一致；`solve_dirty=true` 准确反映既有及新生成的未跟踪材料，不声称工作区完全干净。旧五例兼容副本按原字节归档，映射为 `data/numerical_scenarios/legacy_results/archive_manifest.json`；旧 inventory 保留为历史快照。

`verify_stage67_integrity.py` 已实际通过：21 个历史数据/图/文献文件保留（其中旧 E1–E5 改为同哈希归档），四个受保护的正文/编译文件保持原字节；新 raw、compatibility、selection 和默认 35 配置 manifest 全部核对通过。源码检查无解析错误，保留 36 条可读性等提示；完整 Git 空白检查只在原始失败日志尾部发现 MATLAB 自带空白，原始日志保留，非日志暂存路径检查通过。

本批没有理论修改，没有运行正文导出、作图或 LaTeX 构建；`main.pdf` 本次未重新编译，原第 5 步编译产物不作为本次新增编译证据。最终汇总见 `step67_validation_report.json`，完整性证据为 `step67_integrity_report.json`。

正文、图和已编译 PDF 本批不导出或构建；原字节基准为 `step67_protected_files.json`。历史结果只允许在兼容主文件替换前按原字节归档；原始 runs 永不修改。完整性入口为 `verify_stage67_integrity.py`。

## 第 3–5 步本批证据

本批起始提交为 `fa9dc05229bfdcde079624fc4fe5118b97e288cf`，沿用 `codex/numerical-reproducibility-revision`。起始无已跟踪修改，既有未跟踪材料未覆盖或纳入提交。

求解入口保留原始 info、真实成功状态、return_status、迭代数及计时，可读取的最终 `inf_pr/inf_du` 按原字段口径保存。互补和 KKT 量不可取得时保存 JSON null、not_available 和原因；不以 barrier 参数或步长代替。异常与无效网格输出先保留，再标失败；每个新 attempt 另存 `.solver.json`。真实返回字段盘点见 `step3_solver_interface_fields.json`，历史 MAT 仅读取，不冒充新运行。

`numeric_pass`、`agreement_pass` 与 `provenance_pass` 分开。原控制在实际区间上重积分并加权计价，尾段安全使用重积分终点；state_discrepancy 明确指配点节点与重积分状态差。事件先独立检测，再用解析参考比较；真实区间不扩张，所有候选与长中间控制保留。容量控制按对应重积分状态求区间平均 q_B，状态段距离只作浮点诊断。显著更低且现有数值核查不能解释的成本标为 unresolved_discrepancy，原记录保留。

导出主旗标核对五例的新双旗标、当前参数/初值、预定求解请求及当前评估指纹。附加检查分别匹配自己的请求，不由主旗标代替。结果文字只从数值检测的真实事件生成，不无条件填入预期阶段。本批没有运行 `export_numerical_latex()`，原论文两组数值生成块及科学结果数值未改。

实际 MATLAB 回归合计 62 项：求解接口 10、评估 12、初猜比较 7、缓存 6、容量退出 13、总体事件 14。均已通过，日志为 `step35_matlab_tests.log` 和 `step4_matlab_tests.log`。测试使用 mock 或合成原控制轨道，真实优化执行/成功/失败/缓存命中均为 0；科学 runs 索引为空，默认矩阵仍为 0/35。缓存回归有 18 次 mock solver 调用，接口保存测试另有 1 次 mock callable 调用，均不计为科学优化。

MATLAB 首次受限启动未产生测试输出，已中止；随后在本机获准环境执行，两批测试退出码均为 0。实际版本仍为 `25.2.0.2998904 (R2025b)`。对 45 个 MATLAB 文件实际执行 checkcode，未见解析错误；仍有 24 条可读性、抑制或未使用变量等提示，原文见 `step35_matlab_code_analyzer.json`，不称零警告。

Python 独立 fixture `--check` 与 6 项 unittest 已实际通过。`verify_stage35_integrity.py` 核对 21 个历史数据、图及文献文件的原字节不变，168 个 label 无重名，仅新增 `lem:ac-composition`；10 个保护区块和原数值生成块保持，见 `step35_integrity_report.json`。本批授权变更 main.tex/main.pdf/main.bbl，旧第 0–2 步完整性报告不覆盖重写。

理论增补分别位于模型记账、thm:wellposed 的全局导数界、lem:ac-level-set 后的复合引理、lem:trajectory-verification 证明开头、sec:HJB 的 Soner 适用范围及 sec:numerical-method 的 Avram 目标约束澄清。主假设、控制类、U/V、切换曲线、反馈、验证证明后半、主定理和唯一性结论保留。main 与 TheoryOnly 均真实完成 XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，最终日志无引用、重复标签、缺字或溢出警告。TheoryOnly 首次 BibTeX 输出路径被 openout_any=p 拒绝，切换到输出目录后成功，原失败日志保留；未更改 TeX 安全设置。已渲染核对所有变更页及主文三图一表，未见裁切、重叠或分页异常。

本批真实命令：

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage35_integrity.py
```

MATLAB -batch 实际调用 `verify_solver_diagnostics()`、`verify_numerical_assessment()`（包含 `verify_neutral_initialization()`）、`verify_numerical_cache()`、`verify_capacity_exit_transition()`、`verify_numerical_events()` 和 `checkcode(...,'-id')`。完整构建入口和 TheoryOnly 命令见 `step5_validation_report.json`。

本批求解源码原字节指纹为 `24218f1d4b7e54d605dd5f4c0eeef1505d107a02bfbcca2abdd119c38238ed00`；评估为 `908dc50df401fe346160ba65bf290c0ecde8bcecd5d53c1b45ed505d830cc6b8`；导出为 `b5f90422b521ecfaf48857c38637a728ec0fd7e647f48bf63135e3c13d3caea6`。明细见 `step35_source_fingerprints.json`。这些只表示实际源码，不表示产生了新优化结果。

暂无由本批新增科学优化产生的未解决不一致，因为优化未执行。unresolved_discrepancy 的保留路径已用合成反例实际测试；历史 E4 与其余科学结果保持原样，正式重新评估留待后续授权步骤。

## 以下为第 0–2 步历史执行记录

基准提交：`f078f41fda1a7e4b0fb495916210862a0f136558`。基础分支：`codex/integrate-theory-revision`。工作分支：`codex/numerical-reproducibility-revision`。

起始工作区无已跟踪文件修改，存在用户既有未跟踪材料，详见 `BASELINE.json`。创建分支未覆盖、移动或纳入这些材料。当前正文包含 167 个 label 和两组完整的 AUTO-GENERATED 标记；24 个历史数据、图和论文文件已记录 SHA-256。

MATLAB 沙箱启动尝试因 `PrefdirNotWritable` 失败，随后在获准运行环境执行成功。实际环境为 MATLAB `25.2.0.2998904 (R2025b)`、CasADi `3.4.5`，`has_nlpsol('ipopt')` 返回可用。OpenOCL/IPOPT 的版本无可确认接口时记为 `unknown`；实际依赖源码及二进制哈希另存。无持续阻断项。

本批真实优化调用为 0，真实成功/失败/缓存命中均为 0；默认矩阵为 0/35（`not_started`）。六项缓存测试使用 18 次 mock solver 调用，不计为科学实验。小型构建测试为 `T=1,N=4,d=2`，只构建 NLP 和初猜，不调用 solve。

本批未修改理论或 LaTeX。24 个历史数据、图和论文文件的 SHA-256 与基准一致，167 个 label 及两组生成块保持原样，见 `integrity_report.json`。主文与 TheoryOnly 本批未编译。

## 实际检查入口

从仓库根目录实际运行了：

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage02_integrity.py --write-report
```

实际通过 MATLAB `-batch` 调用了：

```matlab
revision_preflight();
verify_revision_preflight();
verify_numerical_reference();
verify_reference_dependency_tests();
verify_numerical_cache();
verify_numerical_preparation();
```

Python fixture 的 `--check` 前后 SHA-256 不变。MATLAB 解析交叉核查最大成本差为 `1.5543122344752192e-15`，最大解除时间差为 `5.9729998724833422e-14`。这些仅是解析实现之间的浮点差异，不是 NLP 精度或最优性结论。

`checkcode(...,'-id')` 已实际执行，无解析错误；原有及新增代码仍有少量可读性、未使用变量和抑制提示，见 `matlab_code_analyzer.json`，不将其描述为零警告。

## 文件和来源

共享输入和独立解析生成链位于本目录；MATLAB 配置、正式参考验证及依赖回归同步按 case_id 读取输入。求解构建、执行和评估分别由 `prepare_openocl_case.m`、`execute_numerical_run.m`、`assess_saved_numerical_run.m` 负责。

runner 不再在缓存命中时改写来源，也不按结果自动加密主网格。真实求解记录存于 `data/numerical_scenarios/runs/`，索引为 `run_index.json`；兼容副本只通过显式主选择 manifest 产生。图、正文导出和重新评估入口已改用独立来源与校验。历史 12 个 MAT 文件只在 `legacy_inventory.json` 标记为 `legacy_unverified`，原字节保留。

最终工作区求解源码哈希为 `32ab1ff9f71011b5caffa2e9abf696c15d5d0e4e925244fac76a00d1a7a613fe`，明细及独立评估/作图/导出哈希见 `source_fingerprints.json`。此哈希只表示源码检查，本批没有由它产生的优化结果；实际每次 solve_fingerprint 还必须加入参数、设置、实际网格、初猜与环境。

附加实验汇总尚未连接新 runs 索引，留待第 6/10 步。现有导出器拒绝历史附加 checks 作为新增通过证据，当前不能生成新的整体 verified 结论。新的评估/事件/调度/正文修改均为 `not_started`。

## 提交与独立检出

代码提交：`8446e1677fc55504d2bff74c5fb0e69b8262c058`。只按显式路径列表提交本批文件，未纳入原有未跟踪材料，也未 push。

从已提交索引通过 `git checkout-index` 导出独立目录，再实际通过 Python `--check`、六项 Python 测试、MATLAB 解析验证、六项依赖测试与六项缓存 mock 测试。fixture 前后字节不变，真实优化为 0。证据为 `clean_checkout_report.json`、`clean_checkout_python.log`、`clean_checkout_matlab_tests.json`、`clean_checkout_matlab.log`。

Git 的 `core.autocrlf=true` 在新检出时把四个历史文本文件及四个未改动 MATLAB 源文件从 LF 转为 CRLF。原工作区仍按原字节核对 24 个历史文件；跨检出核对只对文本规范 CRLF/LF，二进制仍按原字节比较，24 个文件内容一致。独立检出的求解源码原字节哈希为 `519f44278cd65db38e36b6545531d447a10ac6cc47f90c96c0b47bd4732a7592`，与工作区哈希分开记录，不把不同原字节来源当作同一次求解。

第 0–2 步相关文件列表见 `CHANGED_FILES.txt`；本批第 3–5 步文件列表见 `CHANGED_FILES_STAGE35.txt`。第 6–11 步尚未开始。


## 第10–11步当前交付

详见 `step1011_results.md`、`step1011_validation_report.json`。当前科学主结果/源码来源与原始字节未改变，三图一表保留；N=16000、T=600及额外初猜未运行。完成表示本批复现与导出执行完成，不代表原严格grid一致性全通过。
