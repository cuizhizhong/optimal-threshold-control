# 长时域数值验证与复现

本目录实现同一无终端约束 OCP 的配置、求解、评估和导出。结果仅来自保存的原始输出；执行计划、`expected_region` 和 `expected_structure` 只用于配置或独立比较。第 6–9 步的科学矩阵覆盖 35/35，求解器成功 35/35，`numeric_pass=29/35`、`agreement_pass=29/35`、双通过 28/35。七条未通过记录和原严格网格失败继续保留。

## 入口

从仓库根目录启动 MATLAB：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
make_numerical_figures();
export_numerical_latex();
```

`revision_preflight` 检查 MATLAB、OpenOCL、CasADi、IPOPT 插件、输入、fixture 和写权限，不调用优化器。`run_revision_validation(mode,force)` 支持 `unit / main / initialization / grid / horizon / threshold / all / extended`。`all` 先 unit，再依次 main → initialization → grid → horizon → threshold → 汇总。各组也可独立调用，例如 `run_revision_validation('grid',false)`；grid 返回失败诊断时保留完整记录，不能因 MATLAB 进程退出 0 就改写为通过。`extended` 无显式追加配置时保持 `not_started`，不自动加密。

`all,false` 是检查已有可信缓存的入口，仍会构建请求、核对来源并按需重新评估。只有求解指纹不匹配或没有可信成功原始记录才重新优化。真实调用次数从返回 report 的 `solver_calls`、`cache_hits`、`assessment_calls` 读取。`force=true` 保存新 attempt，绝不覆盖原始 run。批次先保存 manifest，同一指纹在批次内去重；NLP 不收敛保留输出并继续可独立配置，代码/来源/依赖错误立即停止。

## 默认矩阵和模型

固定 `p=0.5,c=2,gamma=0.3,K=0.15,d=2`。动力学为
`s'=-c[p+(1-p)q]si`、`i'=[pc(1-q)s-gamma]i`，成本为完整时域的 `pc*sum(q_k*dt_k)`。约束为 `0<=s<=1,0<=i<=K,0<=q<=1` 及固定初值；不加入终端约束、终端成本、二次正则化或阶段连接约束。控制逐区间常值，求解输出不裁剪、平滑或替换。显示窗口不改变计价范围。

| 组 | 案例 | T | N | 初猜 |
|---|---|---:|---|---|
| main | E1–E5 | 300 | E1/E3/E5:4000；E2/E4:8000 | analytic_reference |
| initialization | E1–E5 | 300 | 各例 main_N | 常值 0.7；固定种子随机 |
| grid | E1–E5 | 300 | 2000、4000、8000 | analytic_reference |
| horizon | E1–E5 | 60、120、300 | 分别 1600、3200、8000 | analytic_reference |
| threshold | 五例已选主源 | 不变 | 不变 | 不重新优化 |

去除 main/grid/horizon 的重叠后共 35 个配置。随机种子为 `20261008+case_index`，固定节点 `unique([0:2:min(20,T),T])` 的值在 `[0.15,0.85]`；实际控制取区间左端点，节点和内部配点状态由这条分段常值控制积分。初猜可以违反容量，但容量超出必须保存。E4 随机初猜实际超出约 0.0568196，最终求解的两组诊断通过；二者不混淆。

## 实际科学记录

第 6–7 步执行 5 次主求解；第 8–9 步新增 30 次求解全部成功，四组报告缓存引用 10 次。主 selection 由预定网格和解析初猜发布，未按贴合理论程度挑选。常值和随机初猜的 10 次结果全部通过两组诊断；固定步长时域 15 个组内引用全部通过；阈值复核 45/45 通过且优化调用为 0。

原严格 grid 组为 `failed`、`protocol_complete=true`、`consistency_pass=false`，15 个组内引用中两旗标各通过 9 条。最细两级的计划建议比较通过五例，但次细级失败不因此消失。详细证据见 `validation/numerical_scenarios/step89_results.md`、原批次报告及四组 `*_detailed_summary.csv`。

| 配置 | numeric/agreement | 失败分量 |
|---|---|---|
| E1,T=300,N=2000 | true/false | 成本相对差超过 1e-4 |
| E2,T=300,N=2000 | false/false | 容量、重积分状态、节点状态差；11 单元中间控制块及事件/结构 |
| E2,T=300,N=4000 | false/true | 容量及重积分状态界 |
| E3,T=300,N=2000 | false/false | 容量、重积分状态界及成本 |
| E4,T=300,N=2000 | false/false | 容量、重积分状态界；8 单元中间控制块及事件/结构 |
| E4,T=300,N=4000 | false/false | 容量、重积分状态界及容量控制平均差 |
| E5,T=300,N=2000 | false/false | 容量、重积分状态界及成本 |

## 来源、环境和诊断

缓存指纹包含参数、初值、全部实际设置、网格、初猜定义/真实数组、求解源码原字节哈希及环境。修改评估器仅重新评估，保存独立 sidecar；正文或图形变化不强制重求解。缓存命中不修改 `solve_commit` 或 `solve_started_utc`。原始数组、`solver_info`、真实迭代/计时字段和失败均保存；不可查询的字段为 `null/not_available`，不填零，不用 barrier 参数或步长伪造 KKT 证书。

`OPENOCL_ROOT` 覆盖仓库候选 `optimal/OpenOCL-master 0104`；`revision_preflight(openoclRoot)` 显式参数优先。环境指纹包含依赖绝对路径、版本和文件原字节哈希，跨目录缓存验证须指定相同实际依赖目录。调度器在 preflight 后临时设置 `OCL_CASADI_SETUP=true`，退出恢复旧值，避免自动安装。实际 MATLAB R2025b、CasADi 3.4.5 已记录；OpenOCL/IPOPT 版本 API 不可读时为 `unknown`。

`numeric_pass` 检查成功、来源、原问题一致、完整成本、原控制重积分峰值、状态/控制界、初值、配点节点与重积分节点差、末尾 20 单位控制及重积分终点零控制峰值 `P0`。`agreement_pass` 独立比较成本、实际识别结构、事件区间及区间平均 `q_B`。容量/状态/尾段目标为 1e-6，成本相对差 1e-4，零成本采用绝对误差，容量控制平均差 2e-3。以上是冻结的浮点诊断目标，不是严格误差界。

事件检测只读取数值控制和重积分状态，不读取理论事件或 expected 字段。比较器保留全部候选、原区间、端点和跨度；时间距离为解析时刻到原区间的距离。只有原始单过渡单元确含理论时刻才标记 `single_cell_contains_theory`，不扩区间。后期零控制容量接触不被识别为付费容量阶段。

## 保存数据的图表和正文导出

`load_selected_numerical_runs` 核对 manifest、五例兼容副本、原始文件 SHA-256、run_id、指纹、provenance 和每个原始字段。`make_numerical_figures` 只读取已选数据，保留三张主图；数值控制用阶梯线、解析跳跃用重复事件时间，相平面保留 `Phi=Phi_B` 边界及物理域阴影。正文保留一张成本表。

`export_numerical_latex` 只更新 `latex/main.tex` 内两组 AUTO-GENERATED 标记块。结果缺失/失败/来源不匹配时刷新开关和文字，尚未运行的数值留空或 `--`。`NumResultsVerified` 与附加协议的 `NumRobustnessComplete` 独立；协议全部尝试不等于一致性通过。五例主结果和附加异常都由实际数据解释。

本轮第 10–11 步当前工作区后处理科学优化调用为 0：12 组 unit、3 项旧失败回归、8 项保存数据回归及 2 项缺失/阻断回归通过，最终重复导出文字不变。三图来源/哈希和 PNG 视觉已检查；main 34 页、TheoryOnly 26 页实际编译成功，最终日志没有上述排版/引用问题。首次复现附录有 11.08316pt 溢出，换段修复并保留首次日志。

隔离候选首次因 Windows 长路径展开失败，未进入 MATLAB；第一次干净 MATLAB 保存数据回归因源目录普通 `is_file` 静默漏掉长路径评估文件而报 `No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a`。原数据完整。源/目标长路径前缀、短目录及 Git `core.longpaths=true` 修复后，候选 `e701f69a1f6a59e3b4456417777b829323566bd0` 初始 status 为空，全部 35 个评估文件复制并核对完整。MATLAB 12 组 unit、9 项保存数据回归通过；all,false 实测缓存 35、科学优化 0、assessment 0，numeric/agreement 各 29、双通过 28、protocol_complete=true、consistency_pass=false。一次 T=1,N=4,d=2 独立 smoke 成功，排除于科学矩阵；候选 main34/TheoryOnly26 页编译通过，最终日志零问题。Python fixture 检查和 6 项测试通过，fixture 字节不变。

所有失败日志及 15 类操作异常见 `validation/numerical_scenarios/step1011_operational_anomalies.json`，包括首次溢出、长路径、比较器过严断言、宏参数误判、矢量导出提醒及来源快照刷新。候选 raw/solver/assessment、输入/fixture 字节与原工作区相同；兼容副本只更新选择时间和对应哈希，科学字段/数组相同。三 PNG 再导出存在时间戳和 3/1/0 像素差，逐图视觉未见实际变化。详细执行见 `step1011_results.md`、`step1011_commands.md` 和最终完整性报告。N=16000、T=600及额外初猜未运行，宏中不填这些结果。历史 `run_numerical_scenarios`、`checks/`、`coarse/` 和 `legacy_results/` 仅供追溯，不代替默认矩阵。
