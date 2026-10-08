# 长时域数值验证

固定 `p=0.5, c=2, gamma=0.3, K=0.15`，使用 MATLAB/OpenOCL 对五个初值求解同一个单阶段最优控制问题。`expected_structure` 只用于结果比较，不进入优化约束。

从仓库根目录启动 MATLAB：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
verify_numerical_reference();
run_numerical_scenarios();             % 五例、E2 加密、E1/E2 常值初猜复核
make_numerical_figures();              % 只读已保存结果
export_numerical_latex();              % 只读已保存结果
```

也可调用 `run_numerical_scenarios('E2')` 运行单例，或使用 `'main'` / `'checks'` 分别运行主实验和附加复核。`run_numerical_scenarios('neutral_E2')` 仅运行 E2 的常值初猜复核，使用 `T=300, N=8000, d=2`，结果单独存入 `checks/neutral_E2/E2.mat`。参数、求解设置和初始化完全相同的已有结果可复用；传入第二参数 `true` 强制重新求解。重跑会覆盖对应结果文件，修改参数或设置后应完整重跑再导出。

## 模型与独立性

- 状态方程为 `s'=-c[p+(1-p)q]si`、`i'=[pc(1-q)s-gamma]i`，成本为 `integral(pc*q dt)`。
- 原始约束为 `0<=s<=1`、`0<=i<=K`、`0<=q<=1` 和固定初值。无终端约束、终端成本、控制正则化或预设阶段。
- 解析参考通过求根、显式弧段和自然段积分生成；控制初猜取真实区间左端点，状态初猜包含内部配点。
- `T=300, N=4000, d=2` 为基准设置。若重积分容量或状态误差未达目标，保留原结果到 `coarse/` 并使用 `N=8000` 加密；本次 E2 和 E4 最终采用加密网格。显示窗口与计价区间分开；成本按实际区间长度求和，不使用 `trapz` 或控制截断。
- 额外复核为 E2 的 `N=8000` 与 E1/E2 的常值 `q=0.7` 初猜。E2 常值初猜的控制、节点状态和内部配点状态保存在 `initial_guess` 中，状态由原 ODE 积分生成。最终采用设置及退出状态保存在每个结果文件内。

## 结果与追溯

`data/numerical_scenarios/E1.mat` 至 `E5.mat` 保存普通数值数组、求解设置、初始化、求解状态、解析参考、数值事件及重积分。`checks/` 保存附加复核，`coarse/` 和 `diagnostics/` 保存最终设置所需的网格及边界诊断。`scenario_summary.csv` 和 `numerical_checks.json` 提供简明汇总。

`figures/numerical_scenarios/` 保存三张 PDF 和 PNG。数值正文及数值宏均位于 `latex/main.tex`；导出器只更新其中带有 `AUTO-GENERATED NUMERICAL` 标记的两个块，不再生成拆分的 TeX 文件。正文的阶段、有效位数及误差解释仍须结合图形和原始数据核对。

五例及原有 E1 初猜/E2 加密核查通过后，导出器标记 `NumResultsVerifiedtrue`；新增 E2 初猜复核单独记录为 `neutral_E2_check`，不由主算例状态代替。其近似一致标准为原数值核查通过、阶段顺序相同、问题设置相同且两次成本绝对差不超过 `1e-5`。失败或缺失时正文不生成通过结论。算法按原始分段常数控制逐区间重积分，不裁剪感染比例；区间内峰值由常值控制下的 `s=gamma/[pc(1-q)]` 条件定位。持续容量弧同时要求非零内部控制与接近容量，后期零控制下的容量接触不会被算作容量控制阶段。

`capacity_exit_transition` 只提取相邻 `q_B -> transition -> 1` 的过渡区间。缺失、多个候选、多网格单元、不连续或理论时刻落在区间外时输出诊断，不能导出单网格包含结论；回归检查入口为 `verify_capacity_exit_transition()`。

第一版 MATLAB/Python 绘图代码、CSV 数据、十张图和旧 E2 基准已统一移至 `archive/first_version/`。旧正文及已删除的审查记录仍可通过 Git 历史追溯。
