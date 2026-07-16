# threshold_landscape_analysis notes

本目录保存情景一单阈值控制的探索性响应图谱。控制律保持为时间开环：

```tex
q_c(t)=1-\frac{\gamma N}{\beta c_0 S_{\rm th}(t)}.
```

本模块只记录理论量、数值轨迹、成本指标和可行性状态，不写策略优劣结论。

状态字段说明：

- `ok`：理论隔离率满足可行范围，数值轨迹使用原始 `q_c(t)`。
- `q_below_q0`：理论所需隔离率低于常规隔离率，但仍在 `[0,1]` 内。
- `q_out_of_bounds`：理论隔离率超出 `[0,1]`，ODE 轨迹使用截断后的隔离率；这类轨迹不再严格等同于原始理论开环控制。
- `threshold_not_reached`：常规控制轨道未达到给定阈值。
- `not_cleared`：在设定时间上限内未达到 `I(t)<=1`。

CSV 中控制时长字段为 `control_duration`；图表和 LaTeX 表头记为
`\Delta t=t_2-t_1`。

CSV 中清零终止时刻字段为 `clear_time`；图表和 LaTeX 表头记为
`t_{\rm end}`。该时间由主论文中的相平面公式计算：先由
`I(t_{\rm end})=1` 求 `S_{\rm end}`，再从 `S_c` 积分到 `S_{\rm end}`。
隔离率强度指标使用 `q_{\max}`。在当前情景一平台段中 `q_c(t)`
随时间下降，因此最大值在启动端点取得，但图表中不把最大值指标
直接写成控制函数取值。

`representative_c0_panels/` 中，TDINN 控制固定为文献函数参照线；
情景一阈值控制和常规控制均使用文件名中的 `c0` 重新计算。

`high_c0_stress_test_panels/` 使用 `c0=14,18,20` 做高接触率压力测试。
该目录不属于主分析的 `c0 in [6,13]` 图谱。
