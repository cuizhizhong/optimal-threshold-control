# 常接触率最优控制论文：Codex 分步修订与数值复核计划

## 任务定位与版本

仓库：`cuizhizhong/optimal-threshold-control`。
基础分支：`codex/integrate-theory-revision`。
本计划核对的 HEAD：`f078f41fda1a7e4b0fb495916210862a0f136558`。
项目根目录以下记为 `P=tracing_isolation_optimal_control_complete`。
论文：`P/latex/main.tex`；代码：`P/matlab/numerical_scenarios/`。

本轮读取的上传 main.tex 与上述提交的 main.tex 在统一 CRLF/LF 后具有相同 Git blob：
`8bdec804cffaafac8019d0e46b8dd1aad7945c52`。
因此下面给出的标签可以用于语义定位；不要依赖未经更新的行号。
执行时若基础分支已有更新，先对照检查并记录新基准，不回退覆盖用户的后续修改。

这是一份待执行的计划，不是已经修改的仓库或已经完成的新增实验。
附带的 `.tex` 文件是插入/替换片段，不是整篇修订稿，也不是自动应用的补丁。

## 交给 Codex 的总任务

在现有二维动力学、线性成本、可测控制类和常接触率理论框架内进行最小范围修订。
理论只补足具体的说明与标准分析步骤，不重写主定理，不增加新模型，不降低已证明结论的范围。
数值部分先修复依赖和结果溯源，再完成预先规定的主算例与补充复核，最后由真实结果更新正文。

正文继续以五个初值 E1--E5、三张图、一张成本表为中心。
初猜、网格、时域、求解器日志和阈值复核主要留在配套目录，不新增大批正文图表。
不能把“重复局部收敛”“通过浮点阈值”或“拟合理论结构”写成连续问题的全局最优性证明。

### 不允许的改动

- 不将控制类改成右连续、分段常数或预定切换次数；分段常数只属于数值离散。
- 不增加感染成本、二次正则项、终端罚函数、隔离者回流或 `q_max<1`。
- 不向主 OCP 加入 `q=q_B(s)`、预先指定的 s_B、解析解除点或阶段连接约束。
- 不把初猜的不可行性误称为原问题不可行；也不把求解后的不可行性称为“仅是初猜问题”。
- 不裁剪、平滑、重置或替换求解后的 q、s、i；尤其不使用 `min(i,K)` 伪造容量可行性。
- 不把解析参考数组写入数值结果数组。
- 不更改阈值来让某个既有结果通过；阈值修改必须说明原因并全量重新评估。
- 不删除失败、较低成本或不符合理论结构的求解记录。
- 不因源码只改了注释、正文或画图就假装原数值结果在新提交上重新求解。
- 不虚构 MATLAB、OpenOCL、CasADi、IPOPT 或编译测试的执行结果。

### 本轮完成范围

必须完成：依赖修复、来源/缓存修复、理论片段合并、五例主结果复核、非理论初猜复核、固定 T 的网格复核、固定步长的时域复核、结果导出与编译。
条件追加：更多初猜、N=1000/16000、更短 T=30、额外文献比较。
不属于本轮：新的状态空间 HJB 数值求解器、完整黏性解比较理论、形式化证明、参数不确定性研究。

---

# 第 0 步：冻结基准、检查环境，不运行大实验

## 输入与动作

在仓库根目录检查：

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git ls-tree -r --name-only HEAD | grep -E '(analytic_checkpoints|numerical_scenarios|OpenOCL|references\.bib|build\.)'
```

先阅读当前目录下的 `AGENTS.md` 等仓库说明。工作区有未提交改动时，不自动 reset、clean 或覆盖。
在干净工作区由基础分支创建工作分支，例如 `codex/numerical-reproducibility-revision`。
记录真实基础提交；提交后续代码更改不代表旧实验的产生提交发生改变。

建立 `P/validation/numerical_scenarios/REVISION_STATUS.md`，只记录步骤状态、阻断项和证据路径。
状态固定使用 `not_started / implemented / tested / blocked / failed / completed`，不要用“已完成”覆盖“只实现未运行”。

新增 `revision_preflight.m`，返回结构化报告，不启动优化。检查 MATLAB 版本、OpenOCL 路径、CasADi 可用性、IPOPT 插件、写权限、输入 JSON 与检查点文件。配置应允许以参数或环境变量指定 OpenOCL 根目录，并保留现有路径作为候选默认值。

**MATLAB 环境缺失时**：仍可完成代码修改、Python 检查点、静态测试和 LaTeX 修改；必须把优化执行标为 blocked，不用 Octave/Python 的输出冒充 MATLAB/OpenOCL 重算结果。

## 验收

保留基准摘要；确认 main.tex 标签、两段 AUTO-GENERATED 标记与本计划相容；不修改任何历史原始结果。

---

# 第 1 步：恢复解析检查点依赖

## 现有问题

`verify_numerical_reference.m` 读取 `P/validation/numerical_scenarios/analytic_checkpoints.json`。
`run_numerical_scenarios.m` 在求解前无条件调用该验证函数。
本轮对该精确路径的读取返回 404。必须检查是否在整理目录时被移动，而不是直接删掉验证入口。

## 修改文件

- `P/matlab/numerical_scenarios/verify_numerical_reference.m`
- `P/validation/numerical_scenarios/generate_analytic_checkpoints.py`（恢复或新增）
- `P/validation/numerical_scenarios/analytic_checkpoints.json`（恢复或重新生成）
- 同目录 `README.md`、`requirements.txt`
- `P/MANIFEST.txt`

先用 git tree 和历史查找旧生成器与 JSON。如果找到，核对参数、初值、成本定义和字段结构后恢复。
找不到时，新建独立 Python 实现，不从 `.mat`、`scenario_summary.csv`、`J_openocl` 或 MATLAB reference 数组复制数值。

允许 MATLAB 和 Python 共享原始参数/初值配置；不共享计算出的几何、切换时刻或成本。
可新增 `scenario_inputs.json` 作为唯一输入源，并让 `numerical_cases_config.m` 和 Python 均读取它。
字段必须按 case_id 匹配，不能假定 JSON 列表顺序等于 E1--E5 的顺序。

## 独立计算路线

按正文定义计算 h、ell、r、a、g、G、Phi；求 s_K 与 e。
切换曲线优先使用正文原始 Theta 方程进行高精度求根：先求沿特征线的峰点，再在峰点右侧括住非平凡根。
显式排除 s=z 的平凡根，不允许求根器因合并端点而返回零长度假根。
这与 MATLAB 中消去平凡根后的等价方程形成实现层面的交叉检查。

计算 z_B、s_B，各案例的等待/容量/完全跟踪时间、切换状态、解除状态、J_reference。
使用有界区间求根与高精度或收敛的自适应积分；输出精度需高于 MATLAB 测试阈值。
Python 实现“独立”仅指实现不同，不意味着提供了第二份解析最优性证明。

生成器约定：

```bash
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
```

`--check` 重新计算并比较已有 fixture，不覆盖；`--write` 是显式更新动作。
依赖版本根据实际可用且测试过的环境固定，不随意填写一个未经运行的版本号。

## 失败处理

缺少 fixture 时，正式验证入口应报错，指出缺少的精确路径和生成命令。
不要改成 warning 后继续并最终显示 verified=true。
在无优化器的开发环境中可以单独运行不依赖 fixture 的代数测试，但必须明确它不是完整参考验证。

## 验收

干净检出后文件存在；生成器 --check 通过；MATLAB 验证可读。
至少检查初值一致、总量不增、参考容量可行、完全跟踪不变量、安全解除点、成本与时间。
检查点只含计算出的解析量及元数据，不含任何优化求解器结果。

---

# 第 2 步：修复缓存与实验来源信息

## 现有问题

当前 runner 在缓存命中后也执行 `run.source_commit = 当前HEAD` 并重新保存，可能将旧结果错误标记为新提交产生。
当前缓存键只检查参数/初值/solver_settings/initialization，没有检查产生结果的代码内容。

## 设计要求

把一次优化的来源、后处理的来源和作图导出的来源分开。至少记录：

```text
run_id
parameters, case_id, x0
solver_settings, actual_grid
initialization.type, seed, knot_times, knot_values, actual_control_guess
initial_guess.node_states, integrator_states, control
provenance.solve_commit
provenance.solve_code_hash
provenance.solve_dirty
provenance.solve_started_utc
provenance.environment
assessment_provenance.code_hash
assessment_provenance.checked_utc
```

`solver_info` 原始返回值已经保存，继续保留。环境版本不可读时填 unknown，不从系统目录名推测。

建立 `solve_fingerprint`：参数 + 初值 + 全部实际求解设置 + 实际网格 + 初猜定义/随机种子 + 与求解有关的源码哈希 + 求解环境标识。
初猜生成器变更也必须使指纹失效。与求解无关的图形、正文、导出器改变不应强制重跑 NLP。
评估器的修改只触发重新评估，记录独立 `assessment_fingerprint`。

数值代码应在大实验前提交并冻结。若运行时源码未提交，保存实际文件哈希和 dirty 状态；不能仅记父提交并宣称来自干净提交。

## 存储与兼容

新增不可覆盖的原始求解目录：

```text
P/data/numerical_scenarios/runs/<run_id>.mat
P/data/numerical_scenarios/run_index.json
P/data/numerical_scenarios/revision_checks/
```

相同指纹有多次运行时，每次有独立 attempt/run_id，全部保留。
主图仍可读取 `E1.mat`--`E5.mat`，但这些文件是由 selection manifest 指定的兼容导出副本，不是运行时随意覆盖的缓存。
main 模式结束时按预先指定设置建立 `selection_manifest.json` 并发布兼容副本；all 模式汇总时重新核对这些副本的 run_id 和指纹。作图前必须断言兼容副本与 manifest 相符。
兼容副本保留原 provenance 和 run_id；生成/选择时间另记，不能替代 solve 时间。
历史结果不删除。缺少可信来源元数据者标为 `legacy_unverified`，可供比对，不自动当作新实验通过证据。

## 缓存单元测试

1. 同指纹命中，solver mock 调用数不增加，solve_commit/solve_started_utc 不改变。
2. 修改动力学、初猜生成器或实际求解设置，缓存失效。
3. 只修改 assessment，重新评估而不重新优化。
4. 只修改 main.tex 或作图，不重新优化。
5. 历史文件无元数据时，默认不复用为新实验。
6. 失败记录不能作为成功缓存命中；重试另存，不覆盖失败证据。

## 验收

消除所有缓存命中后重写 solve_commit 的路径。改变文件名称或 copy `.mat` 不会改变其产生来源。

---

# 第 3 步：保存真实求解信息，分离数值诊断与理论一致性

## 修改文件

`solve_openocl_case.m`、`assess_numerical_case.m`、`tail_diagnostic.m`、`compare_neutral_initialization.m`、`export_numerical_latex.m`。
必要时拆出 `execute_numerical_run.m` 与 `assess_theory_agreement.m`，原入口也调用相同实现，不维护两套互相不一致的逻辑。

## OCP 保持不变

继续使用现有动力学、pc*q 路径成本、初值和状态/控制界；不加入阶段或终端约束。
保留原 IPOPT 设置。不要为让 E4 的成本升高而偷偷改变目标或裁剪控制。

在重积分前断言时间、数组维度和实际控制区间一致：若评估器假设 `t_state` 与控制区间端点相同，必须检查该假设，不仅检查长度。
成本必须使用实际控制区间长度的加权和，不能对分段常数控制使用跨跳跃的梯形规则。

## 求解器信息

保存原始 info、成功状态、return_status、迭代数和运行时间。
检查实际版本返回字段后，再提取 primal/dual infeasibility、complementarity 等可取得的量。
取不到的字段为 null/not_available 并记录原因，不填零。
不能把 barrier 参数当互补残差，不能把迭代步长当 KKT 误差。
没有真实乘子及明确的缩放定义时，不“拼出”一个 KKT 证书。
这些详细信息只入配套文件，不要求加入正文。

## 两类评估旗标

```text
numeric_pass    # 求解成功、来源和问题一致、原控制重积分、状态与控制界、尾段等
agreement_pass  # 成本、识别结构、切换区间、容量控制规律与解析参考一致
```

也可以将来源单独记录为 provenance_pass，但不能将它与理论一致性混淆。
`numeric_pass=true` 仍是给定浮点容差内的数值接受，不是严格可行性证明。
`agreement_pass=false` 不代表原问题不可行，更不能据此删除该结果。
主文的 NumResultsVerified 只有在五例均完成相应复核后才为 true。
附加初猜/网格/时域检查使用独立状态，不由五例主结果的状态代替。

## 预先固定的检查目标

以下均为本轮建议的数值诊断阈值，而不是理论误差上界或已经测得的误差。
先写入配置并提交，再启动实验。

- 重积分容量超出 <= 1e-6；节点状态与重积分状态差 <= 1e-6。
- 原控制越界、原状态越界、初值误差 <= 1e-6；同时保存带符号的极值。
- 尾段控制幅值 <= 1e-6；重积分终点的 P0 <= K+1e-6。
- 主算例相对成本差 `abs(Jnum-Jref)/max(abs(Jref),1e-12) <= 1e-4`。
- 安全集零成本测试用绝对误差，不除以零成本。
- 同一 T、N、d、求解选项下，两种初猜所得成本绝对差目标 <= 1e-5。
- 容量段控制与重积分状态对应的区间平均 q_B 比较，诊断目标 <= 2e-3。

必须明确：state_discrepancy 指“配点状态 vs 重积分状态”，不是“数值最优轨道 vs 解析轨道”。
需要后者时另设 theory_state_error，并说明采样/插值及时间范围。

## 反例/异常处理

数值成本明显低于解析值时，依次检查完整计价区间、模型/参数、控制界、重积分容量、末端安全和数据来源。
若异常超过预定误差尺度且不能由这些原因解释，标为 unresolved_discrepancy，保留全部输入和原始输出。
不能将“与理论不一致”本身当作丢弃结果的理由，也不能把小容量超出等同于它对成本影响的严格上界。

---

# 第 4 步：修正事件识别和切换误差口径

## 先检测，再比较

事件识别函数只接收数值时间、控制和状态及识别阈值，不接收解析事件或 expected_structure。
`expected_structure`、s_B 和解析时刻只在独立比较器中使用。
保留现有 0/1/q_B/transition 逻辑，但扩展为结构化事件记录，不仅输出一个去掉 transition 的字符串。

建议每个事件保存：

```text
kind, status
interval=[left,right], transition_cells
detected_from_control, capacity_active
theory_time (仅比较器添加)
time_distance_to_interval
contains_theory
numerical_endpoint_states
reference_state_distance_to_event_segment
```

主要事件：初次干预、容量进入、容量退出/完全跟踪开始、解除。
初始即完全跟踪或即容量段的事件区间是 [0,0]；理论不存在的阶段用 not_applicable，不伪造 NaN 比较通过。

## 时间与状态误差

对检测到的事件区间 I_e=[t_L,t_R]，定义

`d_t = dist(t_ref, I_e) = max(t_L-t_ref, 0, t_ref-t_R)`。

默认主结果诊断要求：有限过渡块宽度 <= 2 个控制单元，且 d_t <= 该事件附近的一个最大单元宽度。
这仅表示网格尺度一致。
只有原始单网格区间确实包含解析时刻（浮点时间容差如 1e-10）时，才允许写“理论时刻位于单网格过渡区间内”。
未包含时保留真实区间；不能扩张区间后仍称原始单网格包含。
若纯阶段直接相邻，则事件区间为共享端点，并用 d_t 记录误差。

状态误差用参考状态到该数值过渡轨道段的距离，或报告整个过渡段两端的状态与跨度。
数值求最短距离时采用 ODE 稠密输出加一维搜索并说明是浮点诊断。
不要把“首个纯 q=1 单元的状态”当作连续切换状态，再机械施加 1e-6 的状态误差阈值。
主门槛可使用时间区间一致性，状态距离作为独立记录；若制定状态门槛，必须考虑该区间的状态变化尺度并在实验前固定。

## 容量阶段的特例

后期 q≈0 的自然轨道再次接触 i=K，不得识别成付费容量阶段。
容量阶段同时要求接近 K、正长度、q 严格介于 0 和 1；再比较区间平均 q_B，而不将 q_B 写入优化约束。
长时间中间控制、多个候选事件或多次离边/返边必须显式诊断，不能去掉 transition 后只留下“正确”的字符串。

## 测试

保留并扩展 `verify_capacity_exit_transition()`：缺失事件、多候选、超过两单元、理论时刻不包含、直接跳变、初始事件、后期无控制容量接触均有断言。
新增总体识别测试，验证更改 expected_structure 不改变检测出的事件。

---

# 第 5 步：合并理论 LaTeX 修订，不等待优化运行

以下片段均位于本交付包的 `latex_snippets/`。
合并依据 label 与完整语义段落，不全局字符串替换正文所有相似句子。

## 5A：适定性中的全局界

在 `thm:wellposed` 的证明中使用 `01_wellposed_bound.tex`。
特别注意该定理本身允许一般正初值，因此使用 M=s0+i0，不擅自使用 s,i<=1。

## 5B：复合绝对连续引理

在 `lem:ac-level-set` 之后加入 `02_ac_composition.tex`。
它给出简短自足证明，不需另外引入广义梯度、Clarke Hamiltonian 或新的最优性框架。

## 5C：接入验证引理

以 `03_verification_proof_opening.tex` 替换 `lem:trajectory-verification` 的证明开头。
后面的 E_K、E_A、水平集论证、容量残差和覆盖等式全部保留。
检查没有出现“U 几乎处处可微，所以沿任意轨道可直接忽略不可微集合”的替换。

## 5D：Soner 背景与适用范围

以 `04_state_constraint_background.tex` 更新 `sec:HJB` 对边界的说明。
核对并复用现有 Soner1986 文献条目；不声称直接使用其带折现问题的比较定理证明本文。

## 5E：模型内流量记账

合并 `05_model_accounting.tex`。
这是现有方程的流量恒等式，不额外加入 SIRQ 动力学或永久免疫假设。
不把 m=1-s-i 叫作累计康复人数，不从这个记账变量推出统计可识别性。

## 5F：文献定位

现有引言已经比较 Miclo 模型，保留。
必须纠正/澄清 Avram 的问题含目标约束，不能把该文献作为本文“无终端约束长时域截断”等价的依据。
计划中的数值方法替换段已处理此点。
若执行额外文献补充，须核对原文的目标函数与约束；不要把 Angulo 的时间目标、Ketcheson 的终末感染规模目标或 Balderrama 的预算约束说成本文相同问题。
本轮不强制扩展成新的文献综述。

## 验收

常接触率的主假设、U/V 定义、切换曲线、候选反馈、全局最优性及唯一性结论均未改变。
新增/旧标签不重名。用 ref/eqref 更新交叉引用，不硬编码定理编号。
可先构建 TheoryOnly 版本；无法编译时记录缺少的环境，不声称通过。

---

# 第 6 步：实现预先固定的实验调度

新增 `revision_validation_config.m` 与 `run_revision_validation.m`。
后者约定接口 `report = run_revision_validation(mode, force)`；force 默认为 false。
允许模式：`unit / main / initialization / grid / horizon / threshold / all / extended`。

`all` 的顺序为 unit -> main -> initialization -> grid -> horizon -> threshold -> 汇总。
相同求解指纹的实验只运行一次，通过标签/索引供多个检查组引用。
运行一个实验失败，不删除记录，也不抛弃其余可独立运行的实验；最终报告失败。
对代码错误或基础依赖错误立即停止，不把它当作“某个初猜不收敛”。

## 主算例与参数（保持现有值）

p=0.5，c=2，gamma=0.3，K=0.15，T=300，d=2。

| case | x0 | expected_region | expected_structure | main_N |
|---|---|---|---|---:|
| E1 | [0.75;0.01] | W_Gamma | 0 -> 1 -> 0 | 4000 |
| E2 | [0.99;0.01] | W_K | 0 -> q_B -> 1 -> 0 | 8000 |
| E3 | [0.50;0.14] | T | 1 -> 0 | 4000 |
| E4 | [0.70;0.15] | B | q_B -> 1 -> 0 | 8000 |
| E5 | [0.50;0.15] | T | 1 -> 0 | 4000 |

这些 expected 字段只用于测试和比较，不传入 OCP 约束。
主结果预先指定采用解析初猜和上表网格，以保持与既有正文可比；其他初猜不覆盖主结果。
发现更低成本的数值可接受结果时必须调查并报告，不能因为它不是预定主结果而忽略。
最终更换主结果必须在 selection manifest 中说明理由，不能按“最贴合理论”选择。

## 默认实验矩阵

| 组 | cases | T | N | 初猜 | 目的 |
|---|---|---:|---:|---|---|
| main | E1--E5 | 300 | main_N | analytic_reference | 主图与成本表 |
| initialization-constant | E1--E5 | 300 | main_N | q=0.7 | 非理论初猜 |
| initialization-random | E1--E5 | 300 | main_N | 固定种子随机曲线 | 非理论初猜 |
| grid | E1--E5 | 300 | 2000,4000,8000 | analytic_reference | 固定时域网格复核 |
| horizon | E1--E5 | 60,120,300 | 1600,3200,8000（逐项对应） | analytic_reference | 固定 dt=0.0375 |
| threshold | 已保存的最终主结果 | 不变 | 不变 | 不重求解 | 检测阈值敏感性 |

主组包含在 grid 中，horizon 的 T=300,N=8000 也包含在 grid 中。
去掉逻辑重复后，默认是 35 个不同的优化配置；实际新求解次数取决于可信缓存、失败重试和后续加密。
不对初猜×网格×T 做全笛卡尔积。

## 冻结与启动

先提交配置、调度器和求解相关代码，再运行默认矩阵。
调度器先输出完整 run manifest（参数、设置、seed、组别），检查数量和重复项，之后才调用求解器。
如任何最终主结果未达到数值诊断目标，可显式追加更细网格，默认上限 N=16000；记录升级原因，不无限递归重跑。

---

# 第 7 步：执行无优化器单元测试与五个主算例

## 单元测试组

- 原 `verify_numerical_reference()` 与其边界/单点/非零起始采样测试。
- 安全集 E0=[0.40;0.02]：参考成本为0、参考控制为0。
- Gamma 内点、(s_B,K)、等待公共界面 Phi=Phi_B：允许零长度阶段，不产生假平台。
- 区域判定不用 case_id，打乱案例次序不改变结果。
- s<=h 且极小正感染比例：不能因消去误差把 i 变为0。
- 原动力学的正性、s+i 不增、q=0/q=1 不变量。
- 缓存来源测试与事件检测测试。
- 数值成本完整计价，手工构造分段常数控制验证 sum(q*dt)。
- threshold 模式不调用优化器。
- exporter 缺少结果/失败/变更来源时不能保留旧“通过”文本。

参数之外的少量代数回归可用于发现 r=ell 仅在 p=0.5 成立的实现错误；不增加新的主 OCP 算例或参数扫描图。

## 主算例执行

运行：

```matlab
run_revision_validation('unit', false);
run_revision_validation('main', false);
```

每次求解先保存原始输出再评估。五例全部生成原始记录与数值/理论两组指标。
所有主结果必须核对完整成本、实际网格、原始控制重积分与零控制尾段。
不将这里的 passed 字段改称“严格可行”。

## 验收

E1 的完全跟踪始于 i<K；E2 有正长度容量阶段；E3/E5 初始直接完全跟踪；E4 初始容量阶段。
上述应由数值数据识别，并作为 agreement 的预期，而不是硬编码观测结果。
至少可以区分 numeric_pass 与 agreement_pass 的失败原因。

---

# 第 8 步：执行五例非理论初猜检查

对五例分别使用 q=0.7 和固定种子随机初猜，T/N/d/求解选项与对应主例完全相同。
随机种子固定为 20261008+case_index，使用局部随机流或保存/恢复全局 rng 状态。

随机初猜可由预先固定、与理论事件无关的时间节点
`unique([0:2:min(20,T),T])` 上的 [0.15,0.85] 随机值进行线性或保形插值得到。
然后在实际控制区间左端点采样得到真正传入优化器的分段常数 q_k 初猜。
节点和内部配点状态必须由这条“实际分段常数初猜控制”积分得到，
不能用未采样的光滑曲线积分状态而声称二者完全对应。

初猜可以违反容量约束，但必须记录初猜容量超出；求解器失败与优化后不可行需分别记录。
不在状态初猜中偷偷使用解析切换点或把感染比例压平到 K。

运行：

```matlab
run_revision_validation('initialization', false);
```

输出 `revision_checks/initialization_summary.csv` 和 JSON。
逐例保存各初猜是否成功、numeric_pass、结构、成本、事件区间以及与主例的成本差。
先筛数值诊断再讨论同一离散问题的成本一致性，不能只比较两个成本数。
初始化有效性不仅检查 type 字符串，还检查保存的 q 初猜数组、节点/内部配点状态和种子重建结果。对于常值0.7，检查实际输入控制确为常值；对于随机初猜，重新用所存节点、值和种子生成实际控制。

**失败时的动作**：区分接口/初猜数组错误与 NLP 局部收敛问题；后者可以额外尝试 q=0、0.5、1 或预定反向阶段初猜。
这些是额外实验，保留原失败结果。q=0 初猜不满足容量是允许的，不能据此推断原问题不可行。

**验收**：每例两种非理论初猜均有真实记录；成功且数值可接受者的结构与成本得到独立比较。
某些初猜失败时，不写“所有初猜均得到同一解”。
重复收敛不是全局唯一性证明，也不能消除所有局部极小值的可能性。

---

# 第 9 步：执行固定时域网格复核与固定步长时域复核

## 9A：网格

```matlab
run_revision_validation('grid', false);
```

各例固定 T=300,d=2,原问题和初始化类型，分别使用 N=2000,4000,8000。
不将更细网格的解析事件设置为新的网格边界。
如用粗网格结果作 warm start，单独标明；本轮默认仍为 analytic_reference，避免初猜和网格同时变化。

输出每个网格的成本、容量超出、动力学重积分差、结构、事件区间和宽度。
计算最细两级成本相对差，但不要求误差每一级严格单调：切换点落在网格中的位置会变化。
不把三点数值趋势写成连续问题的收敛定理。
粗网格可以未达到容量容差，但必须如实保留；粗网格因此不能被称为连续可行控制。

建议最终稳定性目标：最细级 numeric_pass，最细两级结构可比较且主要事件在网格尺度上接近，
最细两级相对成本差 <= 1e-4。
若不满足，追加 N=16000 并记录理由，仍不满足时停止生成整体通过结论。

## 9B：时域

```matlab
run_revision_validation('horizon', false);
```

各例按 (T,N)=(60,1600),(120,3200),(300,8000) 逐项执行，固定 dt=0.0375 与 d=2。
禁止固定 N 而增大 T 后把控制离散变粗造成的差异解释为截断效应。
所有时域均不加入新终端约束或终端成本。

比较完整成本、[0,18] 内的控制/轨道及全部主要事件、最后20时间单位控制、重积分终端 P0。
时域比较的参考解为同一步长 T=300,N=8000 的结果，不是不同步长的 main_N 结果。

建议诊断目标：各时域最终尾段通过，成本绝对跨度 <= 1e-5，主要事件在共同网格尺度内稳定。
仅当这些实际检查成立时才写“在所测试时域内，主要控制阶段及成本保持稳定”。
不能写“已证明 T=60 与无穷时域等价”。
有未稳定案例时，可追加 T=600 并保持 dt，或分析终端效应；不得悄悄加入安全终端约束来替换本实验。
本轮不要求额外解“带安全终端约束的问题”。

## 9C：阈值

```matlab
run_revision_validation('threshold', false);
```

不再优化，对同一原始结果分别取控制识别阈值 5e-4、1e-3、2e-3。
容量识别阈值可取 1e-5、2e-5、4e-5；它不是1e-6容量接受容差。
检查阶段顺序不变，以及事件区间最多有网格尺度偏移。
若阈值变化造成长混合控制被错误吞并，修复识别器而不是选择最符合理论的一组阈值。
所有识别输出保留，同一源数据不重复计为新的优化试验。

---

# 第 10 步：更新正文方法、结果宏与现有图表

## 10A：先合并不依赖实验结论的正文

把 `07_pending_macros.tex` 放入导言区。
把 `06_numerical_method.tex` 替换原 sec:numerical-method。
把 `08_results_interpretation.tex` 合并进“成本对照与结构总结”。
待新入口实际存在后，再合并 `09_reproducibility_appendix.tex`。

这些片段描述模型、方法和解释口径，不包含新增实验的虚构结果。
方法设计可以先写；“某项检查通过”的结论只能从结果中生成。

## 10B：自动生成块

仍只更新 main.tex 内已有两个块：

```text
% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES
% END AUTO-GENERATED NUMERICAL REFERENCE VALUES
% BEGIN AUTO-GENERATED NUMERICAL RESULTS
% END AUTO-GENERATED NUMERICAL RESULTS
```

保留原有成本/几何宏及 NumFindingWaiting、NumFindingTrackingBoundary、NumCheckStatement、NumOverallFinding。
新增 NumRobustnessStatement 与 NumRobustnessComplete 开关。

注意：新增宏已在导言区定义为空，导出器必须使用 `renewcommand` 填它，不能使用 `providecommand`。
旧宏不在导言区重复空定义，以免现有 providecommand 失效。
每次导出都显式刷新开关；缺失/失败不能继承上次宏内容。
更新整个生成块应采用验证成功后的临时文件原子替换，防止前半更新、后半失败留下混合版本。

## 10C：未完成结果的约定

未产生的新结果宏为空；数值单元格为 `--` 或“未完成”，不是0，不用旧数据假装重跑。
原数据可作为明确标注的历史结果保留，但不能与新源码来源混写。
NumResultsVerified 对应主算例，NumRobustnessComplete 对应默认附加协议，两者独立。
协议全部尝试过但部分失败，应区分 protocol_complete 与 consistency_pass，不混用。

建议自动摘要内容（只有实际通过后填入）：

“在所测试的常值和固定种子随机初猜下，五个算例所得主要阶段顺序一致，
同一离散设置内成本的最大差异为 [实测值]。
网格与固定步长时域复核中，[实际通过案例] 的主要切换位置在对应网格尺度内稳定。
完整记录见配套文件；这些复核不替代解析证明。”

这是一份字段模板，不是可直接填入的通过结论。
未全部通过时，应具体写完成了哪些检查、哪些不支持一致性，而不是省略失败案例后声称“五例均通过”。
正文完整附加摘要控制在约150--250汉字，细节放配套文件。

E4 低于解析成本的数值说明按当前选中结果重新计算，不永久写死旧差值。
如果更换网格后差值变正，不能保留“低于解析值”的历史句子。
如果其他案例出现负差值，按相同规则说明，不仅检查 E4。

## 10D：图表范围不扩张

保留三张主图：
1. 相平面区域、理论曲线与五例数值轨道；
2. E1/E2 的 q(t)、i(t) 对照；
3. E3/E4/E5 的 q(t)、i(t) 对照。

保留一个主表：初值、区域、理论结构、J_ref、J_OCL。
自动识别结构保存在数据中；若与理论不一致，在正文如实说明，不通过只展示理论列掩盖。
不新增 KKT 图、日志图、误差热图或大批网格表。

数值控制用阶梯线；解析控制用重复事件时刻表达跳跃，不能跨跳跃线性平滑。
增加必要的局部放大仅在现有图确实无法辨认切换差异时考虑，非默认新增图。
相平面必须保持 Phi=Phi_B 的等待分支边界，不改成整条 s=s_B 竖线。
图中阴影只限物理域 s+i<=1,i<=K，图例区分理论曲线与数值轨道。

## 验收

三张图和表中的每个数值均可追溯至 selection manifest 指定的 run_id。
重新运行导出器不会改写理论段落，第二次导出输出一致。
删除一个结果文件、故意使一个状态失败，都不会导出原来的全通过语句。

---

# 第 11 步：干净复现、编译与最终交付

## 执行入口（以下新函数均须先按计划实现）

从仓库根目录启动 MATLAB：

```matlab
addpath(fullfile(pwd, ...
 'tracing_isolation_optimal_control_complete', ...
 'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('main', false);
run_revision_validation('initialization', false);
run_revision_validation('grid', false);
run_revision_validation('horizon', false);
run_revision_validation('threshold', false);
make_numerical_figures();
export_numerical_latex();
```

正式运行完毕后，再执行一次 all,false；可信缓存应命中，不应重新执行35个优化。
若需要故意重跑，使用 force=true；新结果另存 attempt，不覆盖原始证据。

## 编译

优先使用仓库已有 build.sh/build.bat，并阅读其命令。
也可在 `P/latex` 中依次执行：

```bash
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

还要检查 TheoryOnly 编译，确认省略数值部分时宏仍有定义。
不能仅凭返回码判断排版；阅读 log 的未定义引用、重复标签、缺图、缺字和溢出警告。
渲染新增引理页、数值方法页、三张图和成本表所在页，人工核对中文、公式、图例和分页。

## 干净环境复现

在新的 worktree 或临时检出中验证：
- 输入 JSON、独立 generator、fixture、README 与 MANIFEST 全部存在；
- --check 不覆盖 fixture；
- 单元测试不依赖开发机器上未提交的路径；
- 后处理和图表导出可以仅凭已保存数据运行；
- 一次小型 smoke solve 验证求解接口；它只证明接口可执行，不作为新科学证据；
- 完整实验的状态有证据，无执行环境的部分明确 blocked。

## 提交顺序

建议独立提交：
1. 修复输入/fixture 与 preflight；
2. 修复 provenance/cache、评估器和测试；
3. 合并理论说明片段；
4. 冻结实验调度/配置/初猜实现；
5. 加入真实实验结果及配套摘要；
6. 更新正文生成块、图表、README 和编译产物。

真正产生数值结果的提交是第4步对应的代码版本，而不是包含结果的第5或第6步提交。
若第4步之后求解代码又变更，按新指纹判断哪些实验需要重新执行。

## Codex 最终回复必须列明

修改文件；理论修订位置；实际运行的命令；真实执行/成功/失败/缓存次数；
默认矩阵完成比例；未解决的不一致；main.pdf 编译状态；最终提交与求解源码指纹。
不要用“所有检查通过”概括只做过的静态检查，不捏造新增误差数值。

## 交付物

`main.tex`、真实编译的 `main.pdf`、更新的 MATLAB 脚本与独立 Python 检查点生成器、
输入/fixture、原始结果、run/selection manifest、五例主汇总、初猜/网格/时域/阈值摘要、README。
配套记录用于复现，不把工程执行计划整段写入论文正文。

---

# 可立即合并与必须等待的内容

| 内容 | 是否需等待新优化实验 |
|---|---|
| 一致连续性估计与复合引理 | 不需要 |
| 验证引理衔接与 Soner 说明 | 不需要 |
| 现有模型的流量记账 | 不需要 |
| 数值 OCP、计价方式、事件区间与截断解释 | 不需要；仅描述方法 |
| 新 README 中的命令 | 需先实现并验证对应入口 |
| 多初猜“均一致”的文字 | 必须等待 |
| 网格/时域“稳定”的文字 | 必须等待 |
| 新的最大误差、切换偏差、成本差 | 必须等待 |
| E4 当前差值的说明 | 依赖最终选中数据重新生成 |
| 编译通过/干净复现通过 | 必须真实运行 |

---

# LaTeX 片段全文

下面嵌入交付包内的全部片段，便于只把本计划一个文件交给 Codex。
每段的定位注释与前面第5、第10步要求同时有效。

## 01_wellposed_bound.tex

```latex
% 定位：thm:wellposed 的证明。
% 替换原“若 $c$ 有界，则 ... 非负一致连续且可积的函数趋于零。”两句；
% 保留后面的反证说明。不要新增 s_0+i_0<=1 假设。
若 $c$ 全局本质有界，记
$C=\|c\|_{L^\infty(0,\infty)}$、$M=s_0+i_0$。
由 $0<s(t),i(t)\le M$ 及状态方程，
\[
 |\dot i(t)|
 \le \bigl(pc(t)s(t)+\gamma\bigr)i(t)
 \le (pCM+\gamma)M
 \qquad\text{几乎处处}.
\]
由于 $i$ 在每个有限区间上绝对连续，上式说明 $i$ 在整个
$[0,\infty)$ 上为 Lipschitz 函数，因而一致连续。
再结合非负性与式\eqref{eq:i-integrable}，得到 $i(t)\to0$。
```

## 02_ac_composition.tex

```latex
% 定位：lem:ac-level-set 的证明结束后、sec:constant-problem 之前。
% 新增引理；编号使用自动交叉引用，不手工写“引理2.3”。
\begin{lemma}[相对局部 Lipschitz 函数沿绝对连续轨道的复合]
\label{lem:ac-composition}
设 $E\subset\mathbb R^m$，$F:E\to\mathbb R$ 相对局部 Lipschitz，
$x:[0,T]\to E$ 绝对连续，其中 $T<\infty$。
则 $F\circ x$ 在 $[0,T]$ 上绝对连续。
在 $F$ 具有 $C^1$ 局部表达式的状态点所对应的时间集合上，
通常的链式法则
\[
 \frac{\dd}{\dd t}F(x(t))=\nabla F(x(t))\cdot\dot x(t)
\]
几乎处处成立。
\end{lemma}
\begin{proof}
轨道像集 $x([0,T])$ 紧。
相对局部 Lipschitz 邻域给出该像集的一个有限相对开覆盖。
由 Lebesgue 数引理及 $x$ 的一致连续性，可将 $[0,T]$
分成有限个闭子区间，使每个子区间的轨道像均包含在某个
Lipschitz 邻域中。
在这样的子区间上，对任意有限个互不相交的时间区间 $(a_k,b_k)$，
存在与这些区间无关的常数 $L$，使
\[
 \sum_k |F(x(b_k))-F(x(a_k))|
 \le L\sum_k\|x(b_k)-x(a_k)\|.
\]
由 $x$ 的绝对连续性，得到该子区间上 $F\circ x$ 的绝对连续性。
有限拼接给出整个区间上的结论。
在具有 $C^1$ 局部表达式的部分，普通链式法则在 $x$ 可微的时刻成立，
而 $x$ 不可微的时刻构成零测集。
\end{proof}
```

## 03_verification_proof_opening.tex

```latex
% 定位：lem:trajectory-verification 的证明开头。
% 替换至“不使用平面面积为零所以时间可忽略的推论”这一句为止；
% 后续容量集合 E_K、安全集合 E_A 和覆盖等式全部保留。
有限时间上轨道连续且正性保持，故其像位于辅助条带中
$s,i$ 均有正下界的紧集。
由命题\ref{prop:regularity}的相对局部 Lipschitz 性及
引理\ref{lem:ac-composition}，$u=U\circ x_q$ 在 $[0,T]$ 上绝对连续。
在不安全内部 $i<K$，$U$ 为 $C^1$，
普通链式法则与命题\ref{prop:all-HJB}给出不等式。
这里包含两种等待区的公共界面和非平凡切换界面。
上述复合引理仅保证沿轨道的绝对连续性，
不将二维状态空间中的零测集自动视为零测度的时间集合；
容量边界及安全边界仍按下述水平集论证处理。
```

## 04_state_constraint_background.tex

```latex
% 定位：sec:HJB 中边界 Hamiltonian 方程之后的说明段。
% 用本段替换原对应说明段，保留原 lemma:bangbang。
% 先核对 references.bib 中已有 Soner1986 条目。
这里不预设 $V(s,K)=0$、$V_i(s,K)=0$ 或 $q=q_B$。
状态约束 HJB 的边界信息由可行轨道的限制诱导，
不能等同于另行指定的 Dirichlet 数据；相关黏性解框架可参见
\citet{Soner1986}。
该文献在其自身假设下建立的比较与正则性结论，
不在本文的无折现首次到达问题中直接调用。
本文不预设 $V$ 的可微性，而是对构造出的 $U$
证明沿任意可行轨道的积分不等式。
这一充分性逻辑与 \citet[附录A.1]{MicloSpiroWeibull2022}
及 \citet[\S5.1.4]{Liberzon2012} 一致，
但所需的具体分区、非光滑处理及有限时间到达性由本模型单独证明。
```

## 05_model_accounting.tex

```latex
% 定位：sec:model 中归一化模型的解释之后。
% 这是由现有方程直接导出的记账说明，不增添动力学状态或隔离者回流。
% 若正文已有等价说明，合并而不是重复。
\paragraph{状态变量与移出流量。}
本文的 $s$ 表示仍参与传播过程的未隔离易感比例，
$i$ 表示二维系统中参与传播的感染比例。
现有两式满足流量恒等式
\[
 c(t)[p+(1-p)q]si=pc(t)(1-q)si+c(t)qsi.
\]
因此，易感者的移出并不全部计入 $i$ 的新增项。
仅为记录二维系统以外的总量，可令 $m(t)=1-s(t)-i(t)$；
在物理初值下有
\[
 \dot m(t)=c(t)q(t)s(t)i(t)+\gamma i(t)\ge0,
 \qquad s(t)+i(t)+m(t)=1.
\]
$m$ 是未显式区分的隔离或其他移出状态的合计，
不能仅凭这两条方程将其解释为累计康复人数。
本文不描述这些移出个体的后续分流和回流。
特别地，$q=1$ 时感染生成项为零，但未隔离易感者仍可继续移出；
这一性质属于所研究约化模型的假设，而不是一般隔离措施必然满足的机制。
```

## 06_numerical_method.tex

```latex
% 整节替换 sec:numerical-method，结束位置为 sec:numerical-results 之前。
% 依赖原有 NumTheoryRef、NumIntervals、NumHorizon、NumDegree、NumMeshDetails、
% NumFindingParagraph、NumCheckStatement，以及本计划新增的 NumRobustnessStatement。
% 没有实验时，结果宏为空；不把下面的方法说明变成“检查已通过”的结论。
\section{数值方法与实验设置}
\label{sec:numerical-method}

本节围绕不同初值区域，比较解析最优策略与直接配点输出，
重点考察等待阶段、容量弧和完全跟踪阶段的出现顺序及其连接位置。
算例组织借鉴 \citet[第6节]{AvramFreddiGoreac2022} 的区域相关情景设计，
但使用本文的状态方程、控制成本及
\NumTheoryRef{def:regions}{分区定义}。
该文献的有限时域问题包含目标约束，
本文仅借鉴其几何展示方式，不将其结果作为下述无终端约束截断的等价性依据。
全局最优性与几乎处处唯一性分别由
\NumTheoryRef{thm:verification}{验证定理}和
\NumTheoryRef{thm:unique-q}{唯一性定理}给出；
数值实验用于检验这些解析结论的计算一致性。

五个主算例采用相同参数
\begin{equation}
 p=0.5,\qquad c=2,\qquad\gamma=0.3,\qquad K=0.15,
 \label{eq:numerical-common-parameters}
\end{equation}
仅改变初始状态。
$s,i$ 为相对于初始总量的比例，允许 $s_0+i_0<1$；
此时 $h=0.3$、$\ell=r=0.15$。
这些参数用于展示理论结构，不作为特定疫情的参数标定。

直接配点处理如下固定时域问题：
\begin{equation}
\begin{aligned}
 \min_q\quad &J_T(q)=\int_0^T pcq(t)\,\mathrm dt,\\
 \text{满足}\quad
 &\dot s=-c[p+(1-p)q]si,\qquad
 \dot i=[pc(1-q)s-\gamma]i,\\
 &0\le q\le1,\quad 0\le s\le1,\quad0\le i\le K,\\
 &(s(0),i(0))=(s_0,i_0).
\end{aligned}
\label{eq:numerical-ocp}
\end{equation}
该问题不增加终端状态约束、终端成本或二次控制正则化，
也不固定阶段数、切换时刻或容量控制。
解析策略可用于初始化，但不进入数值优化的目标或额外约束。

计算方法为 MATLAB/OpenOCL 直接配点\citep{Koenemann2019OpenOCL}，
通过 CasADi\citep{Andersson2019CasADi} 构造离散问题，
由 IPOPT 求解非线性规划\citep{WachterBiegler2006}。
基准设置为 $T=\NumHorizon$、$N=\NumIntervals$、$d=\NumDegree$；
控制在每个网格区间内为常数。
\NumMeshDetails
控制成本在完整求解时域上按实际区间长度计算：
\begin{equation}
 J_{\mathrm{OCL}}=pc\sum_{k=1}^{N}q_k\Delta t_k.
 \label{eq:numerical-cost-sum}
\end{equation}
绘图窗口不作为成本积分范围，求解输出不通过平滑或裁剪替换。

对于每个待报告结果，用原始分段常数控制重新积分状态方程，
检查区间内部的容量峰值、与配点状态的偏差以及终端零控制延拓。
对正状态，未来无控制峰值为
\[
 P_0(s,i)=
 \begin{cases}
  i,&s\le h,\\
  i+s-h-h\ln(s/h),&s>h.
 \end{cases}
\]
终端延拓检查对重积分得到的状态使用 $P_0(s(T),i(T))$，
同时检查终点前一段时间内的控制是否已接近零。
这些是求解后的浮点诊断，不进入问题\eqref{eq:numerical-ocp}。
它们不单独证明连续时间严格可行性，
也不将有限时域离散问题与原无穷时域问题视为严格等价。

阶段和过渡区间首先依据数值控制及容量接近程度识别，
再与解析事件比较。
跳跃附近按过渡网格区间报告位置，
不以首个纯控制单元的起点代替连续切换时刻。
附加复核分别改变初始猜测、网格和终止时刻；
网格比较固定 $T$，时域比较固定控制区间宽度，
以区分离散误差和截断效应。
详细复核保留在配套结果文件中，正文仅保留与阶段结构判断相关的摘要。
局部求解器的重复收敛及有限样本复核均不替代解析证明。

% 下列宏由实际保存数据生成；未完成时保持为空。
\NumFindingParagraph{\NumCheckStatement}
\NumFindingParagraph{\NumRobustnessStatement}
```

## 07_pending_macros.tex

```latex
% 放入导言区，紧接原有 \newif\ifNumResultsVerified 之后。
% 此处只定义新宏；不得在这里为空定义原本由 providecommand 生成的旧宏。
\newif\ifNumRobustnessComplete
\NumRobustnessCompletefalse
\newcommand{\NumRobustnessStatement}{}

% 导出器必须在现有 AUTO-GENERATED NUMERICAL RESULTS 块内使用：
% \NumRobustnessCompletetrue 或 \NumRobustnessCompletefalse
% \renewcommand{\NumRobustnessStatement}{由实际结果生成的摘要}
% 不可对本文件已定义的新宏再次使用 \providecommand，否则空定义不会被覆盖。
% 每次导出都重写开关和宏；缺失/失败不能沿用上一次的“通过”文本。
```

## 08_results_interpretation.tex

```latex
% 定位：sec:numerical-results 的“成本对照与结构总结”小节。
% 替换静态说明；保留成本表和 NumOverallFinding 的一次调用。
表\ref{tab:numerical-scenarios}中的 $J_{\mathrm{ref}}$
为解析公式的数值评价，$J_{\mathrm{OCL}}$
为数值优化返回控制按式\eqref{eq:numerical-cost-sum}计算的成本。
成本接近、阶段顺序一致和切换位置接近是相互补充的比较指标，
其中任一项都不能单独替代其余指标。
数值一致性不要求孤立切换瞬间的控制代表值相同。

数值控制允许存在与网格尺度相关的过渡单元，
故切换误差应与相应网格宽度一并解释。
配点状态与重积分状态之间的偏差反映动力学离散的一致性，
并不等同于数值状态与解析最优轨道之间的误差。
若离散成本略低于解析成本，应同时检查原控制的重积分容量约束，
不能将存在容量超出的离散结果称为优于解析最优策略的严格可行控制。

% 只允许实际结果驱动；不得从预期结构拼出“识别结构”。
\NumFindingParagraph{\NumOverallFinding}
```

## 09_reproducibility_appendix.tex

```latex
% 替换现有“数值复现说明”小节；保留外层 TheoryOnly 条件及参考文献结构。
% 仅在新入口已实现并完成对应测试后合并此段命令。
\section{数值复现说明}
\label{app:numerical-reproducibility}

数值代码位于 \path{matlab/numerical_scenarios/}。
独立解析检查点及其生成程序位于
\path{validation/numerical_scenarios/}；
检查点只评价正文中的解析构造，不调用数值优化器。
具体环境准备及检查点生成命令见该目录和数值目录的说明文件。
从仓库根目录启动 MATLAB 后运行：
\begin{lstlisting}
addpath(fullfile(pwd, ...
 'tracing_isolation_optimal_control_complete', ...
 'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
make_numerical_figures();
export_numerical_latex();
\end{lstlisting}

\texttt{all} 运行预先规定的主算例和附加复核。
各次求解分别保存初值、参数、网格、初始化、求解状态和原始控制数组，
并记录求解时的源码指纹与环境信息。
重做后处理不改写原求解的来源信息。
作图和正文数据导出只读取已保存且来源明确的结果，
不在缺少结果时以解析参考代替数值优化输出。
更详细的初猜、网格、时域及阈值复核见
\path{data/numerical_scenarios/revision_checks/}。
正文中的数值摘要与所选结果文件保持一一对应。
```
