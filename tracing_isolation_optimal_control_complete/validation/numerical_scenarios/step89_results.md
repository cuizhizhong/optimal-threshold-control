# 第 8--9 步真实执行摘要

本文件由保存的执行报告、原始求解记录及独立评估生成；计划中的预期值未作为实验结果。

协议执行状态：`completed`；计划建议的初猜、最细网格及时域稳定性判定：`passed`；原矩阵严格判定：`False`。
本批实际优化 30 次：成功 30、失败 0；四组执行报告缓存命中 10 次。
默认配置覆盖 35/35；阈值复核 45/45 条，优化器调用 0 次。
35 个配置中，逐条 numeric_pass=29、agreement_pass=29，两者同时通过=28。全部尝试与求解器成功不代表这些逐条诊断均通过。

各组执行记录：

| 组 | 状态 | solver | cache | 成功 | 失败 | numeric | agreement |
|---|---|---:|---:|---:|---:|---:|---:|
| initialization | completed | 10 | 0 | 10 | 0 | 10 | 10 |
| grid | failed | 10 | 5 | 15 | 0 | 9 | 9 |
| horizon | completed | 10 | 5 | 15 | 0 | 15 | 15 |
| threshold | completed | 0 | 0 | 0 | 0 | 0 | 0 |

常值及固定种子随机初猜与主结果的带符号成本差：

| 例 | 初猜 | seed | success | numeric | agreement | 初猜容量超出 | J−Jmain |
|---|---|---:|---|---|---|---:|---:|
| E1 | constant_control | -- | True | True | True | 0 | -1.44328993201e-15 |
| E2 | constant_control | -- | True | True | True | 0 | -5.78648240435e-13 |
| E3 | constant_control | -- | True | True | True | 0 | -1.7763568394e-15 |
| E4 | constant_control | -- | True | True | True | 0 | 2.88657986403e-15 |
| E5 | constant_control | -- | True | True | True | 0 | 8.881784197e-16 |
| E1 | seeded_random | 20261009 | True | True | True | 0 | -1.99840144433e-15 |
| E2 | seeded_random | 20261010 | True | True | True | 0 | -6.10178574334e-13 |
| E3 | seeded_random | 20261011 | True | True | True | 0 | -1.55431223448e-15 |
| E4 | seeded_random | 20261012 | True | True | True | 0.0568195818275 | 5.77315972805e-15 |
| E5 | seeded_random | 20261013 | True | True | True | 0 | -7.77156117238e-16 |

最细两级网格：保留原汇总判定，并独立计算计划建议判定；次细级的容量失败仍完整记录。

| 例 | N次细/最细 | numeric次细/最细 | 相对成本差 | 原严格判定 | 计划建议判定 |
|---|---|---|---:|---|---|
| E1 | 4000/8000 | True/True | 3.55546862149e-05 | True | True |
| E2 | 4000/8000 | False/True | 3.25966064817e-06 | False | True |
| E3 | 4000/8000 | True/True | 3.55721483664e-05 | True | True |
| E4 | 4000/8000 | False/True | 1.21121550776e-05 | False | True |
| E5 | 4000/8000 | True/True | 2.64211077222e-05 | True | True |

固定步长时域成本跨度及尾段：

| 例 | 完整成本跨度 | 全部尾段通过 | 计划建议判定 |
|---|---:|---|---|
| E1 | 1.00489616628e-11 | True | True |
| E2 | 1.10067510661e-12 | True | True |
| E3 | 4.26209068038e-12 | True | True |
| E4 | 3.59712259979e-14 | True | True |
| E5 | 1.76707537491e-11 | True | True |

[0,18] 的逐项控制/轨道差、全部原事件区间及宽度、最后 20 时间单位控制和终端 P0 见 JSON 与四组 `*_detailed_summary.csv`。未预设幅值接受门槛的窗口差保留为实测诊断，不追加任意阈值。

未解决差异 0 条；求解失败 0 条；数值诊断失败 6 条；解析一致性失败 6 条。

失败或未验证记录保留如下（原始数组、日志及详细事件未删除）：

| 例 | T | N | 初猜 | success/numeric/agreement | 容量超出 | 相对成本差 | q_B最大差 | 失败分量 |
|---|---:|---:|---|---|---:|---:|---:|---|
| E1 | 300 | 2000 | analytic_reference | True/True/False | 1.00656375263e-07 | 0.00010345232426 | -- | cost_agreement |
| E2 | 300 | 2000 | analytic_reference | True/False/False | 1.44612809197e-05 | 5.08520635974e-05 | -- | capacity, state_discrepancy, reintegration_state_bounds, event_detection_diagnostics, observed_structure_comparison, event_comparison |
| E2 | 300 | 4000 | analytic_reference | True/False/True | 3.33927520832e-06 | 4.71753331858e-06 | 0.00146429494789 | capacity, reintegration_state_bounds |
| E3 | 300 | 2000 | analytic_reference | True/False/False | 7.83006799127e-06 | -0.000155660933528 | -- | capacity, reintegration_state_bounds, cost_agreement |
| E4 | 300 | 2000 | analytic_reference | True/False/False | 1.24062514041e-05 | 3.94714271923e-05 | -- | capacity, reintegration_state_bounds, event_detection_diagnostics, observed_structure_comparison, event_comparison |
| E4 | 300 | 4000 | analytic_reference | True/False/False | 3.09083986516e-06 | 9.20964711069e-06 | 0.00253064911597 | capacity, reintegration_state_bounds, capacity_control_comparison |
| E5 | 300 | 2000 | analytic_reference | True/False/False | 2.56846367808e-06 | 0.000271269628182 | -- | capacity, reintegration_state_bounds, cost_agreement |

- E2，N=2000：实际识别结构 `0 -> 1 -> 0`；诊断 `long_intermediate_control`；intervention=[4.199999999999999, 5.850000000000003]（11 单元），full_start=[4.199999999999999, 5.850000000000003]（11 单元）。
- E4，N=2000：实际识别结构 `1 -> 0`；诊断 `long_intermediate_control`；full_start=[0.0, 1.2]（8 单元）。

求解来源（原始记录的来源字段未改写）：

- solve_commit `c23a5d6bdc7fd97ea53e32a485ca03996789831b`；solve_code_hash `cd7e6297bb05f11028fe6f8f543ae8a9f5bd8c41d4f98346a0dc7b7cd09cff49`；solve_dirty `True`；记录 30 条。

独立初猜积分核验和 MATLAB 种子/实际输入核验分别见 `step89_integrity_report.json`、`step89_initialization_validation.json`；完整内容与输入哈希并入本报告。
独立初猜状态积分最大差 4.45199432875e-14；原控制独立重积分节点最大差 1.11577413975e-14。
汇总实际使用 Python 3.12.8、NumPy 1.26.4、SciPy 1.13.1；入口为 `E:\anaconda\python.exe`。独立完整性复核的实际运行环境另保留在其原报告中。

本批未编译 main.pdf，未更新正文、主选择或图表，未覆写既有原始记录。浮点接受、有限网格趋势及多初猜重复收敛均不构成连续问题严格可行性、收敛定理或全局唯一性证明。
