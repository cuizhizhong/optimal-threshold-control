# 解析检查点与数值复现证据

`scenario_inputs.json` 是 MATLAB 与独立 Python 生成器共享的原始参数、初值和预定 main_N。按 `case_id` 匹配，打乱案例排列不改变解析量。输入和 `expected_*` 是预定配置，不能作为优化已完成的结果。

## 独立解析 fixture

从仓库根目录执行：

```powershell
python -m pip install -r tracing_isolation_optimal_control_complete/validation/numerical_scenarios/requirements.txt
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
```

已实际使用 Python 3.12.8、`mpmath==1.3.0`。`requirements.txt` 仅固定 fixture 的 mpmath 依赖；第 8–9 步的独立数值后处理另使用 NumPy 1.26.4、SciPy 1.13.1，实际版本保存在原报告。

`--check` 以 50 位精度重新计算、只读比较已有 fixture，绝对容差 5e-12，不覆盖。仅显式更新解析 fixture 时运行同一生成器的 `--write`。生成器由正文的 a、g、G、Phi 和原始 Theta 方程求解，先求特征线峰点、在右侧括住非平凡根，排除 s=z；二分容差为 1e-40，等待时间自适应积分并更高精度复算。它不读取 `.mat`、`J_openocl`、summary 或 MATLAB reference 数组，不含优化结果；独立实现用于交叉检查，不构成新的最优性证明。

MATLAB 从仓库根目录执行：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
revision_preflight();
verify_numerical_reference();
verify_reference_dependency_tests();
run_revision_validation('unit', false);
```

核查初值、几何、各阶段时间、切换/解除状态、成本、容量可行性、正性、总量不增、完全跟踪不变量和安全解除点；保留稀疏/非零起始/退化弧回归。fixture 缺失或篡改时正式验证立即报错，不 warning 后继续。以上均不执行科学优化。

## 真实实验和异常

第 6–7 步主算例证据为 `step67_*`；第 8–9 步为 `step89_*`。后批科学执行入口 `execute_stage89.m` 实际依次调用 initialization/grid/horizon/threshold；初猜数组重建入口为 `execute_stage89_initialization_check.m`。启动命令和失败启动尝试见 `step89_commands.md`、`step89_startup_attempts.json`。

默认 35 配置全部有真实记录，求解器成功 35/35；numeric 和 agreement 各为 29/35，双通过 28/35。后批新增 30 次求解、缓存引用 10 次，阈值模式对同一主源进行 45 次识别，优化调用 0。七条诊断未通过记录和原严格 grid 的 `failed/consistency_pass=false` 不隐去。`step89_results.md`、`step89_validation_report.json` 和四组详细 CSV 保存容量、成本、事件/结构及容量控制异常。

`step89_validation_report.json` 的 `plan_suggested_consistency_pass=true` 是单独按计划建议的最细级/最细两级口径计算；`original_stricter_execution_consistency_pass=false` 和 `all_default_configurations_numeric_and_agreement_pass=false` 同时保留。它不支持“全部 35 个配置通过”。所有报告中的缺失值保留 null/未完成，不填预期值或零。

只读复核第 8–9 步保存的数值摘要：

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/summarize_stage89.py --check-only
```

`verify_stage89_integrity.py` 保护该批基准中的 main.tex/PDF/图原字节；第 10 步更新后不作为当前工作区通用检查，也不覆盖原历史报告。第 0–2、3–5、6–7 步 verifier 同样只对应各自基准。旧 `clean_checkout_report.json` 是第 0–2 步的历史检出证据，不能代替本轮第 11 步。

## 第 10–11 步入口和验收口径

`execute_stage1011.m` 的当前工作区后处理已实际执行，科学优化调用为 0。`step1011_unit_report.json` 记录 12 组通过；`step1011_exporter_report.json`、`step1011_saved_exporter_report.json`、`step1011_pending_exporter_report.json` 分别记录 3 项旧失败回归、8 项保存数据回归及 2 项附加结果缺失/阻断回归通过。`finalize_stage1011_export.m` 的两次最终导出文字相同，图表来源/哈希及 PNG 视觉已检查。

`step1011_build_report.json` 记录 main 34 页、TheoryOnly 26 页均实际编译成功，最终日志零问题。首次主文的复现附录出现 11.08316pt 溢出，换段修复后重编；`step1011_build_attempt1_report.json` 与 `step1011_main_attempt1_final.log` 保留首次问题。

`execute_stage1011_clean.m` 负责隔离候选检出的 preflight、unit、all,false 缓存复核、保存数据作图/导出和独立 smoke solve。首次展开因 Windows 长路径失败，未进入 MATLAB。调整较短目录、目标 Python 长路径前缀和 Git `core.longpaths=true` 后，第一次干净 MATLAB 的 12 组 unit 通过，但保存数据回归报 `No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a`，日志 `step1011_clean_attempt1.log` 保留。根因是源目录普通 `is_file` 静默略过长路径 assessment，原工作区 35 个评估文件完整；现改为源/目标均用长路径前缀，且断言全部评估文件名集合等于复制集合。旧 MANIFEST 同样漏了这 35 项，已使用长路径枚举修正。

修复后的候选快照 `e701f69a1f6a59e3b4456417777b829323566bd0` 初始 Git status 为空；`step1011_clean_report.json` 实际记录 12 组 unit 和 9 项保存数据回归通过、all,false 可信缓存 35、科学优化 0、assessment 0，numeric/agreement 各 29、双通过 28、protocol_complete=true、consistency_pass=false。独立 T=1,N=4,d=2 接口 smoke 成功 1 次；`step1011_clean_python_report.json` 记录 generator 退出 0、6 项测试退出 0且 fixture 字节未变。`step1011_clean_build_report.json` 记录候选 main34/TheoryOnly26 页编译成功，最终 issues 为空。

`verify_stage1011.py` 已实际运行并核对通过，保护 93 个文件；最终证据为 `step1011_validation_report.json`、`step1011_results.md` 和 `REVISION_STATUS.md`。候选比较确认 35 个 raw/solver、35 个 assessment、输入/fixture 及主 TeX 字节相同，兼容副本科学字段/数组相同，仅选择时间及其哈希更新。PNG 元数据与少量像素再导出差异如实记录，三图逐图视觉未见实际差别。15 类操作异常、日志及修复见 `step1011_operational_anomalies.json`，没有因最终通过而删除首次失败或比较器/宏参数误判。未运行 N=16000、T=600和额外初猜，未填对应新结果。全部实际命令见 `step1011_commands.md`，交付改动见 `CHANGED_FILES_STAGE1011.txt`。

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/verify_stage1011.py
```

`all,false` 可以重新评估、汇总和发布主副本，不能当作新的 35 次科学求解。跨目录复用缓存需要保持求解源码原字节，并将 `OPENOCL_ROOT` 指向保存来源中的同一实际依赖目录；环境指纹包含绝对路径。源码换行经 Git 转换时原字节指纹会变，不能假装来源相同。`OCL_CASADI_SETUP` 由调度器临时设为 true 并恢复。显式 `revision_preflight(openoclRoot)` 参数优先于环境变量。

隔离检出必须有共享输入、generator、fixture、MATLAB 源码、真实 runs/solver sidecar、run/selection manifest、评估/组摘要及图表与 LaTeX 依赖。文件清单见项目 `MANIFEST.txt`；不能借用开发工作区未列出的结果。一次小型 T=1,N=4,d=2 的常值初猜 smoke solve 只验证 OpenOCL 接口，不计入论文科学矩阵。编译检查包括 main 和 TheoryOnly、最终日志及新增引理/方法/三图/成本表页面渲染。尚未执行和异常分别记录，不以退出码或计划内容声称通过。
