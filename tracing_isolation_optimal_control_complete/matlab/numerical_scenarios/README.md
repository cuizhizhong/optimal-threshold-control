# 长时域数值验证

当前已完成修改计划第 0–5 步：独立解析检查点、来源缓存修复、求解信息保存、数值接受与理论比较分离、事件区间识别及理论正文增补。本批未运行新增优化，历史数值和图原样保留为 `legacy_unverified`；它们不自动命中新缓存。第 6–11 步及默认 35 个科学求解配置仍未执行。

固定 `p=0.5, c=2, gamma=0.3, K=0.15`，使用 MATLAB/OpenOCL 对五个初值求解同一个单阶段最优控制问题。`expected_structure` 只用于结果比较，不进入优化约束。

无需优化的检查入口如下；独立 Python fixture 的生成与测试见 `validation/numerical_scenarios/README.md`：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
revision_preflight();                 % 结构化环境报告，不下载或调用优化器
verify_revision_preflight();
verify_numerical_reference();
verify_reference_dependency_tests();
verify_numerical_cache();              % mock 六项缓存测试，真实优化调用为 0
verify_solver_diagnostics();          % 真实接口字段与 mock 保存路径回归
verify_numerical_assessment();         % 原控制合成轨道、双旗标及导出门槛回归
verify_neutral_initialization();       % 初猜比较与理论一致性分开
verify_capacity_exit_transition();     % 原始单单元包含与网格尺度一致分开
verify_numerical_events();             % 数值检测不接收理论参考
```

OpenOCL 根目录可作为 `revision_preflight(openoclRoot)` 参数或 `OPENOCL_ROOT` 环境变量提供；显式参数优先，默认仍为仓库的 `optimal/OpenOCL-master 0104`。MATLAB、CasADi 版本取实际接口；无法查询的 OpenOCL/IPOPT 版本记为 `unknown`，另保存实际依赖文件哈希。

以下优化及导出入口供后续已授权批次使用，本批没有执行：

从仓库根目录启动 MATLAB：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
verify_numerical_reference();
run_numerical_scenarios();             % 五例、E2 加密、E1/E2 常值初猜复核
make_numerical_figures();              % 只读已保存结果
export_numerical_latex();              % 只读已保存结果
```

也可调用 `run_numerical_scenarios('E2')` 运行单例，或使用 `'main'` / `'checks'` 分别运行主实验和附加复核。`run_numerical_scenarios('neutral_E2')` 仅运行 E2 的常值初猜复核，使用 `T=300, N=8000, d=2`。所有尝试均以独立 `run_id` 保存在 `runs/`；附加检查不覆盖主算例兼容文件。传入第二参数 `true` 强制另存一个 attempt，不覆盖既有原始记录。

缓存指纹包含参数、初值、实际求解选项与网格、初猜定义及实际数组、求解源码哈希、环境标识。只有索引中来源完整且成功的原始记录可命中。源码未提交时，保存实际文件哈希与 dirty 状态；缓存命中不重写 `solve_commit` 或 `solve_started_utc`。

评估使用独立 `assessment_fingerprint` 与 sidecar，更新评估器不重新求解。图和正文导出各保存独立来源记录。主模式按共享输入中预定的 `main_N` 选择结果并生成 `selection_manifest.json`；`E1.mat`–`E5.mat` 只是其兼容副本。作图和导出核对 manifest、原始文件哈希、run_id、指纹与来源。没有新 manifest 时严格报错；本批保留的旧图和正文可以继续查看，但不冒充新来源复核。

五例主旗标要求每例 `numeric_pass` 与 `agreement_pass` 均通过，且输入、预定求解请求和当前评估指纹匹配。附加检查有独立状态，不合并进主旗标，也不由主旗标代替。第 6/10 步尚未把完整实验组汇总接入新索引；旧 `checks/` 不作为新增通过证据。本批不运行导出器，正文两组历史数值生成块保持原样。

## 第 3–4 步评估口径

`numeric_pass` 检查求解成功、记录来源及原问题一致、完整时域加权成本、原控制重积分容量峰值、状态/控制界、初值、配点节点与重积分状态差、尾段和重积分终点的零控制安全延拓。`passed` 仅为该字段的兼容别名。带符号极值另存，不通过裁剪修正原输出。

`agreement_pass` 独立比较成本、实际识别结构、事件区间及容量单元平均 `q_B`。成本相对差目标为 `1e-4`，安全集零成本用绝对误差 `1e-6`；容量控制平均误差目标为 `2e-3`。这些都是预先固定的浮点诊断目标，不是严格误差界。

`detect_numerical_events` 只接收数值时间、原控制、重积分状态和阈值；`compare_numerical_events` 才接收解析参考。事件保留原始过渡区间、全部候选、端点状态及跨度。时间距离为解析时刻至真实区间的距离，主门槛为至多两过渡单元且距离不超过邻近一个最大单元宽度。只有真实一个过渡单元包含解析时刻，才标记 `single_cell_contains_theory`。稠密 ODE 输出用于容量区间积分和参考状态至过渡轨道段的浮点最短距离，后者不机械套用 `1e-6` 状态差门槛。

每次新求解保留原始 `solver_info`，另存不可覆盖的 `runs/<run_id>.solver.json`。迭代数、计时、最后迭代的 `inf_pr/inf_du` 只从真实返回字段提取；取不到时保存 JSON `null`、`not_available` 与原因。barrier 参数和步长不代替互补残差，当前接口不提供 KKT 证书。异常记录和显著较低成本的 `unresolved_discrepancy` 均保留。

## 模型与独立性

- 状态方程为 `s'=-c[p+(1-p)q]si`、`i'=[pc(1-q)s-gamma]i`，成本为 `integral(pc*q dt)`。
- 原始约束为 `0<=s<=1`、`0<=i<=K`、`0<=q<=1` 和固定初值。无终端约束、终端成本、控制正则化或预设阶段。
- 解析参考通过求根、显式弧段和自然段积分生成；控制初猜取真实区间左端点，状态初猜包含内部配点。
- `T=300, d=2`，主网格预定为 E1/E3/E5 的 `N=4000` 和 E2/E4 的 `N=8000`；不依据结果是否接近理论自动更换主网格。历史 `coarse/` 结果原样保留。显示窗口与计价区间分开；成本按实际区间长度求和，不使用 `trapz` 或控制截断。
- 额外复核为 E2 的 `N=8000` 与 E1/E2 的常值 `q=0.7` 初猜。E2 常值初猜的控制、节点状态和内部配点状态保存在 `initial_guess` 中，状态由原 ODE 积分生成。最终采用设置及退出状态保存在每个结果文件内。

## 结果与追溯

下述五例结果及已有核查说明对应本轮修订前的历史材料，不表示本轮重算。新科学记录目录当前为空，步骤状态和真实测试证据见 `validation/numerical_scenarios/REVISION_STATUS.md`。

`data/numerical_scenarios/E1.mat` 至 `E5.mat` 保存普通数值数组、求解设置、初始化、求解状态、解析参考、数值事件及重积分。`checks/` 保存附加复核，`coarse/` 和 `diagnostics/` 保存最终设置所需的网格及边界诊断。`scenario_summary.csv` 和 `numerical_checks.json` 提供简明汇总。

`figures/numerical_scenarios/` 保存三张 PDF 和 PNG。数值正文及数值宏均位于 `latex/main.tex`；导出器只更新其中带有 `AUTO-GENERATED NUMERICAL` 标记的两个块，不再生成拆分的 TeX 文件。正文的阶段、有效位数及误差解释仍须结合图形和原始数据核对。

五例主结果均通过独立数值接受和理论比较后，导出器才标记 `NumResultsVerifiedtrue`。初猜比较要求两次输出数值可接受、实际问题设置与网格相同、成本绝对差不超过 `1e-5`；阶段和理论一致性另记为 `agreement_pass`。失败或缺失时不生成通过结论。算法按原始分段常数控制逐区间重积分，不裁剪感染比例；区间内峰值由常值控制下的 `s=gamma/[pc(1-q)]` 条件定位。持续容量弧同时要求正长度、内部正控制与接近容量，后期零控制下的容量接触不会被算作容量控制阶段。

`capacity_exit_transition` 保留兼容接口，可检测 `q_B -> transition -> 1` 和纯阶段直接相邻的共享端点。`supported` 仅表示真实单单元包含，`grid_scale_pass` 单独表示新的网格尺度诊断；区间不因解析时刻改变。接口与异常说明见 `validation/numerical_scenarios/step4_event_contract.md`。

第一版 MATLAB/Python 绘图代码、CSV 数据、十张图和旧 E2 基准已统一移至 `archive/first_version/`。旧正文及已删除的审查记录仍可通过 Git 历史追溯。
