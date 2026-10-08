# 第 4 步：数值事件检测与独立比较

## 输入和检测记录

`detect_numerical_events(t_control,q_control,t_state,state_xy,K,opts)` 只读取数值时间、控制、重积分节点、容量及识别阈值。`state_xy` 为 `(N+1)×2`，两列为 `s,i`；控制起点必须与状态区间左端点一致。解析时刻、`s_B` 和 `expected_structure` 不用于检测。

输出保留完整 `arcs`、`cell_labels`、含全部过渡块的 `observed_sequence`，以及 `intervention / capacity_enter / capacity_exit / full_start / release` 五种事件。`observed_structure` 是纯阶段摘要；过渡块隔开的同名阶段也不合并。门槛判断同时检查 `diagnostics`，不能只比较这一摘要字符串。

每个事件保存所有 `candidates`。单个候选的 `interval` 使用原始网格端点；纯阶段直接相邻时为共享端点；初始纯完全跟踪或初始容量段的进入事件为 `[0,0]`。`numerical_endpoint_states` 两列分别是区间左右端点的 `[s;i]`，并保存 `state_span`。多个候选不会按解析参考选择其中一个。

容量单元同时要求两个重积分节点接近 `K`、正区间长度和严格中间控制。零控制自然轨道的容量接触只记录在 `natural_capacity_contact_cells`，不会生成付费容量阶段。超过两个单元的中间控制、多个事件候选、异常连接和求解时域末端仍未归类的过渡均有独立诊断。

## 独立比较

`compare_numerical_events(detected,ref,par,opts,trajectory)` 在检测完成后读取解析参考。`trajectory.dense_solutions{k}` 是原控制第 `k` 个区间重积分的 `ode45` 解。主要输出为 `events`、`structure_pass`、`event_pass`、`diagnostic_pass`、`capacity_control`、`agreement_pass`。

时间距离使用 `max(t_L-t_ref,0,t_ref-t_R)`，默认允许至多两个过渡控制单元、距离至多一个邻近最大实际单元宽度。真实事件区间不会扩张。`contains_theory` 只表示原始闭区间在 `1e-10` 时间容差下包含理论时刻；`single_cell_contains_theory` 还要求恰有一个过渡单元。理论阶段不存在时状态为 `not_applicable`，时刻和距离为空，不把 `NaN` 比较记作通过。

参考状态到过渡轨道段的距离使用 ODE 稠密输出、逐控制单元的一维有界搜索及端点比较，标记为浮点诊断；主门槛不机械施加 `1e-6` 的切换状态误差要求。没有稠密输出时保留端点和状态跨度，并明确记录距离不可取得。

容量控制比较使用 `q_B(s)=1-gamma/(p*c*s)` 在每个实际控制区间上的时间平均，与原始常值控制相减，默认最大绝对差门槛为 `2e-3`。主评估入口采用重积分稠密输出的区间积分。独立调用未提供稠密输出时，只能使用明确标记的节点线性插值积分，不能把它报告为 ODE 稠密积分。

`capacity_exit_transition(arcs,theoryTime,opts)` 保留旧导出接口。无理论参数时只检测；`supported` 仍严格表示真实单单元包含，新增 `grid_scale_pass` 表示上述网格尺度一致性，两个含义不会互相替代。

## 单元验证入口

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete', ...
    'matlab','numerical_scenarios'));
capacityReport=verify_capacity_exit_transition();
eventReport=verify_numerical_events();
```

两个入口分别返回 13 项与 14 项合成单元测试报告，均不调用 OpenOCL、CasADi 或 IPOPT，不产生优化结果。覆盖缺失、多候选、超过两个单元、真实区间不包含、直接跳变、初始事件、自然容量回触、预期结构独立性、不等距网格、容量控制区间平均、稠密状态段距离以及真实时间区间校验。

实际执行状态以同目录 `step4_unit_tests.json`、`step4_matlab_tests.log` 为准；该说明文件本身不构成测试通过证据。
