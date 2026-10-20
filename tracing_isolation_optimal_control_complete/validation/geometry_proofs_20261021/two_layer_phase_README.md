# C1 两层理论相图

`make_two_layer_phase.py` 新增生成 `figures/numerical_scenarios/FigN1_two_layers.pdf` 与同名 PNG。图只表示解析几何，不叠加 OpenOCL 轨道，不调用优化器、OCP 或 MATLAB，不产生新的数值最优解。

左图采用当前基准参数与能力上限 `qbar=0.4`，显示物理域、`A=V0`、`V0.4` 和 `V1=D`。受限能力包络遵循 C3 命题，先按 `i<=I_qbar(s)` 构造，再与 `i<=K`、`s+i<=1` 相交。右图沿用正文的完整控制区间 `q in [0,1]`，显示安全区、两种等待区、完全跟踪区、切换曲线、分界自然轨道和容量平台。两图均用点线表示 `s=h`、虚线表示 `s+i=1`，图例分别列出。

在仓库根目录运行：

```powershell
python tracing_isolation_optimal_control_complete/validation/geometry_proofs_20261021/make_two_layer_phase.py
```

基准参数只读取 `validation/numerical_scenarios/scenario_inputs.json`；几何定义独立实现 `matlab/numerical_scenarios/build_theory_geometry.m` 的解析标量求根，并与现有高精度 `analytic_checkpoints.json` 比较。最大几何差为 `1.11e-16`，701 个切换点的原始 Theta 条件最大残差为 `3.55e-15`；六个已有初值的解析分类均与输入标签一致。上述只是解析公式复核，不是新 OCP 求解。

`two_layer_phase_checks.json` 保存来源与输出 SHA256、嵌套包络检查、物理截断检查、初值分类及旧图和原 `figure_provenance.json` 的运行前后指纹。原 `FigN1_regions.pdf/.png`、其他数值图和数值 provenance 未覆盖。

已目视检查导出 PNG 及由 Poppler 单独栅格化的新 PDF；字体、图例、线型、曲边与物理截断正常。目视记录见 `two_layer_phase_visual_review.json`，并以输出 SHA256 绑定这次结果。
