# Optimal threshold control

两个可复现的传染病动力学最优控制项目。

- `tracing_isolation_optimal_control_complete/`：跟踪隔离机制下双传播系数耦合模型的最优控制、切换几何和唯一性分析。
- `asymmetric_optimal_control_package/`：不同易感耗竭系数与感染生成系数模型的结构可解性、感染成本稳健性及独立控制退化分析。

两个子项目均包含中文技术报告 PDF、LaTeX 源文件、Python/MATLAB 复现脚本、数据、图形和验证记录。详细运行方式、模型假设和结果说明见各子目录中的 `README.md`。

## 模型主题

两个项目都围绕带医疗容量约束的二维感染动力学系统：

~~~text
S' = - beta_1(t) S I
I' =   beta_2(t) S I - gamma I
~~~

两个项目对 `beta_1` 与 `beta_2` 的耦合方式、控制成本和唯一性结论作了不同处理。
