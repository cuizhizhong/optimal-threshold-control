# 感染阈值约束下跟踪隔离的全域最优控制

本目录保存当前论文、MATLAB/OpenOCL 数值求解与复现记录。当前分批执行依据为 `ai/claude_revision_plan/START_HERE_CODEX.md` 与 `ai/claude_revision_plan/REVISION_PLAN.md`；`ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md` 保留历史计划；其中的阈值、预期结构和建议结论不作为已完成实验的结果。

本轮修订的对照材料、实际结果、最终正文和复现边界见[评阅入口](REVIEW_GUIDE.md)。

当前论文交付入口为[主文 PDF](latex/main.pdf)（43 页）与[独立补充材料 PDF](latex/supplementary.pdf)（2 页），对应源码为 `latex/main.tex`、`latex/supplementary.tex`。主文保留核心结果与证明附录，共 5 图、4 表，其中数值章节为 3 图、2 表；补充材料仅含附加数值设置、附加核对结果、误差判据与残差说明三小节。完整复现记录、逐条评估、日志和数据来源继续保存在仓库。G4 两份文稿已从新隔离目录完整编译，最终日志无诊断；45 页均已逐页目视检查，导出回归 16/16、符号检查 28/28、保护检查 19 项通过。Windows `build.bat` 已实际运行并退出 0，Linux/macOS `build.sh` 仅作静态检查；优化器调用、新增 OCP 求解、重新评估和图形导出均为 0 次。实际命令和验收记录见[本批报告](validation/g4_supplement_20261022/README.md)。

按作者最新决定，当前论文只研究无回流五仓室模型的最优控制；有回流问题的数值研究留作后续独立工作。第二节已按“仓室与流量—完整模型—前两式解耦—二维最优控制问题”重写，移除回流参数、五维值函数及独立等价命题。当前执行计划更新为 v5；本轮修改与验证见 [模型节返修报告](validation/model_no_return_revision_20261020/README.md)。第三批此前的模型初稿与编译记录保留为[历史报告](validation/model_a1_20261020/README.md)。

## 当前结果与限制

S2 已统一代码和论文符号，并实际执行 35 次新求解：缓存命中 0 次，求解器成功 35/35；`all,false` 总耗时 2157.5074708 秒，见[本批执行报告](validation/numerical_scenarios/rerun_20261020/S2.4/execution_report.json)。按 `configuration_id` 对应旧记录的[35 项严格比较](validation/numerical_scenarios/rerun_20261020/comparison_report.json)全部通过：成本相对差、控制数组及状态数组最大绝对差均为 0，返回状态、迭代次数、事件、阶段结构和两类旗标均相同。[本批原判据重评](validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json)新增 35 份独立评估，原判据 `numeric/agreement/双通过=29/29/28`，修订判据为 `33/30/30`，分母均为 35。粗网格失败继续保留；协议完成不等于所有科学诊断通过。

标签 `pre-code-rename` 指向 `051099fba63cd6d326f2344d2bf4322c1f651282`。旧 35 份 raw、35 份 solver sidecar 和 70 份 assessment 均保留原处且字节不变；当前累计为 70/70/140 份。本次主选择及新旧 run_id 对照见[评阅入口](REVIEW_GUIDE.md)和比较报告；`run_index.json` 只追加。S2.7 已刷新三图和正文导出，两组生成块及块外文字与重跑前基线完全相同，见[逐块核对](validation/numerical_scenarios/rerun_20261020/S2.7/macro_comparison_report.json)。三项导出器回归共 16 项检查（11+3+2）已通过，实际结果见[回归报告](validation/numerical_scenarios/rerun_20261020/S2.7/regression_report.json)；三张 PNG 及主文第 28–30 页已实际渲染目视核对，见[页面与图形检查](validation/numerical_scenarios/rerun_20261020/S2.7/visual_qa.json)。本批各步主文实际编译为 37 页。

以下第 6–11 步的执行次数、34 页及候选检出结果均为历史记录；不作为本次重跑的执行次数或页数。

第 6–9 步已实际取得默认矩阵的 35/35 个不同配置，35 次科学求解均返回成功。数值接受有两种统计口径，以下并列报告：

| 口径 | `numeric_pass` | `agreement_pass` | 同时通过 |
|---|---:|---:|---:|
| 原严格判据（求解前预定；状态/容量容差 1e-6，容量段控制 2e-3） | 29/35 | 29/35 | 28/35 |
| 修订判据（2026-10-10 求解后调整；状态/容量容差 1e-5，容量段控制 3e-3） | 33/35 | 30/35 | 30/35 |

修订判据是对同一批保存数据的后验重评，只用于说明浮点误差尺度，不提供新的收敛证据；成本相对误差容差 1e-4 和事件判据未变，详见 `validation/numerical_scenarios/tolerance_revision_20261010/README.md`。当前独立补充材料采用修订判据，并同时写明原判据计数。第 6–11 步的历史报告保留原判据计数，不能读成修订判据的统计。

五例预定主结果在两种口径下均通过这两组浮点诊断；初猜组和固定步长时域组通过。原严格网格组为 `failed`、`consistency_pass=false`；修订判据下最细两级（$n=4000/8000$）的成本与事件比较五例均实际执行并通过。原判据下七条至少一项诊断失败的记录全部保留。第 8–9 步新增求解为 30 次、缓存引用为 10 次，主批的另 5 次求解见 `step67_main_report.json`。

负成本差：E4 选中结果（$n=8000$）比解析参考低 3.68e-6，重积分容量超出 $\varepsilon_K=7.70\times10^{-7}$；E3 的 $n=2000$ 记录低 6.76e-5，$\varepsilon_K=7.83\times10^{-6}$，评估分类为 `unresolved_discrepancy`。把容量放宽为 $K+\varepsilon_K$ 后，解析最优值分别下降 1.16e-5 和 1.08e-4，均大于对应负差。两者因此都与容量超出相容，不构成低于解析最优值的可行反例。该比较只用解析公式，由 `export_numerical_latex.m` 在导出时计算；原评估记录及其分类不变。

`step89_results.md` 另列最细两级的计划建议比较，其通过不覆盖严格网格失败，更不表示所有网格都容量可行。E2/E4 的 $n=2000$ 分别出现 11/8 单元的中间控制块；粗网格容量、成本及结构异常见详细记录。浮点接受、多初猜重复收敛和三个有限网格不替代正文解析证明。

历史第 10–11 步已由保存数据刷新正文宏、三图和一表；该阶段工作区科学优化调用为 0。12 组 MATLAB 单元检查、3 项旧失败清空回归、8 项实数据回归及 2 项附加结果缺失/阻断回归通过；两次最终导出文字相同。三图来源和文件哈希已核对，PNG 已目视检查。主文 34 页实际编译成功，最终日志未发现未定义引用、重复标签、缺图/缺字或溢出。

第 11 步的候选快照 `e701f69a1f6a59e3b4456417777b829323566bd0` 起始 Git status 为空。Python fixture 只读检查与 6 项测试通过；MATLAB 12 组 unit、9 项保存数据回归通过，`all,false` 实测可信缓存 35 次、科学优化 0 次、重新评估 0 次，协议完成 true、一致性 false。独立 T=1,N=4,d=2 接口 smoke 成功 1 次，不纳入科学矩阵；候选 main 也实际编译为 34 页，最终日志零问题。完整性核对通过，保护 93 个文件。N=16000、T=600 和额外初猜未运行，新结果不填入。

首次主文 11.08316pt 附录溢出已换段修复；首次候选展开因 Windows 长路径失败，第一次干净 MATLAB 保存数据回归又因长路径 assessment 漏拷贝报 `No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a`。源/目标复制及 MANIFEST 枚举已修复并核对全部 35 个评估文件，失败日志保留。PNG 时间戳及极少像素存在再导出差异，逐图视觉未见实际变化，不宣称字节一致。全部 15 类操作异常见 `validation/numerical_scenarios/step1011_operational_anomalies.json`；最终结果、精确命令和文件范围见同目录 `step1011_results.md`、`step1011_commands.md`、`CHANGED_FILES_STAGE1011.txt`。

## 历史数据字段对照

S2 已使当前求解、评估代码及新保存记录与论文使用同一套符号。标签 `pre-code-rename` 及此前 JSON/MAT 和历史报告保留旧字段；历史第 6–11 步与容差重评脚本只针对该标签运行。S1 当时仅同步导出器生成文字中的区间数与容量超出记号；S2 改名改变了源码与参数指纹，并已实际重跑 35 次。读取历史数据时按下表换算：

| 含义 | 论文与当前代码 | 历史数据字段（`pre-code-rename` 及此前） | 旧稿 |
|---|---|---|---|
| 单次接触传播概率 | $\beta$；`par.beta`、`cfg.parameters.beta`、输入键 `"beta"` | 参数结构中的 `p` | $p$ |
| 切换几何常数 $(1-\beta)h$ | $p$；`geom.p` | 几何结构中的 `r` | $r$ |
| 安全边界与切换函数的交点横坐标 | $s_e$；`geom.s_e` | 几何结构中的 `e` | $e$ |
| 安全集边界在横轴的交点 | $s_A$；`geom.s_A` | 几何结构中的 `s_K` | $s_K$ |
| 无干预增长阈值 $\gamma/(\beta c)$ | $h$；`geom.h` | `h` | $h$ |
| 完全跟踪常数 $\gamma/c=\beta h$ | $\ell$；`geom.ell` | `ell` | $\ell$ |
| 控制 $q$ 下的轨道、首达时间、验证残差 | $x^q,s^q,i^q,\tau^q,\rho^q$ | 不出现 | $x_q,s_q,i_q,\tau_q,R_q$ |
| 与传播率控制比较时的总传播率 | $b_0=\beta c$ | 不出现 | $\beta=pc$ |

注意：历史参数结构中的 `p` 是传播概率；当前 `geom.p` 和论文中的 $p$ 是几何常数。`numerical_normalize_parameters` 只把历史参数计算副本的 `p` 映射为 `beta`，拒绝缺失或冲突字段；原始 run、指纹载荷及磁盘记录保持原格式。A1 已将旧稿的合计量 $m=1-s-i$ 改写为显式五仓室中的 $s_q+i_q+r$；$r$ 包含已退出社区传播的住院者与康复者。

S1 按 `SYMBOL_TABLE.md` 的指定范围完成以下 20 条改名；旧记号仅在该范围内替换，其他已明确含义的局部记号保留。

| 条目 | 旧记号 → 定稿记号 | 范围或代码对应 |
|---|---|---|
| #3 | $\lambda(y)\to\mu(y)$ | `lem:tracking-region` 的证明 |
| #4 | $D(s,i)\to\Delta_\Theta(s,i)$；$D(t),D_0,D_{\rm init}\to D_{\rm ICU}(t),D_{{\rm ICU},0},D_{\rm ICU,init}$ | 匹配残差与医疗需求；`\Dcal` 保留 |
| #7 | $R,M_R\to\Pi,M_\Pi$；$R^q\to\rho^q$ | 正则性证明的矩形与验证残差 |
| #8 | $N\to n$ | 配点区间数；代码字段 `N`、`solver_settings.N` 保留；人口 $N$ 保留 |
| #9 | $\delta\to\varepsilon_K$ | 容量超出与 $V_{K+\varepsilon_K}$ 比较；代码 `capacity_excess` 与局部 `delta` 保留 |
| #10 | $e\to s_e$ | 特殊点；当前代码为 `geom.s_e`，历史字段为 `geom.e`；指数宏 `\e` 保留 |
| #11 | $s_K\to s_A$ | 安全边界在 $s$ 轴上的端点；当前代码为 `geom.s_A`，历史字段为 `geom.s_K` |
| #12 | $C\to\bar c$ 或 $C_{\rm ICU}$ | 适定性证明的接触率界与医疗附录容量；$C_B$ 保留 |
| #14 | $L(s,\psi)\to\ln\Theta(s,\psi+\ell\ln s)$；$L\to L_{\rm ICU}$ | 切换曲线证明及医疗平均占用时长；$L_s$ 写为相应复合函数的偏导 |
| #15 | $Q_K,Q(t,s,i),Q\to\mathcal Q_K,\mathcal Q(t,s,i),\Pi_0$ | 允许控制集与局部小矩形；反馈 $Q^*$、$Q(t,x)$ 保留 |
| #16 | $\sigma,F_{x_0}\to s_c,\mathcal J_{x_0}$ | 一维策略族及推论；$i_w(\sigma)\to i_w(s_c)$；切换映射 $\sigma(z)$ 保留 |
| #17 | $\iota(\xi)\to i_{\rm nat}(\xi)$ | `lem:waiting-HJB` |
| #18 | 积分变量 $\tau\to v$；$\tau(t)\to\vartheta(t)$；$\tau_A\to\tau_{\mathcal A}$ | 适定性证明、时变节与首达时间；其他范围含义明确的局部积分变量保留 |
| #20 | $I_z,I_\Gamma\to\mathcal I_z,\mathcal I_\Gamma$ | 特征线与切换曲线图像函数 |
| #21 | $f_q\to f(x,q)$；$L_{f_q}\to L_{f(\cdot,q)}$ | 全文向量场与 Lie 导数，参数统一为状态、控制 |
| #22 | $\epsilon\to\varepsilon$ | 全文 |
| #24 | $\kappa(a)\to\kappa(\theta)$ | 医疗核的感染后时间变量 |
| #25 | $b(s)\to U_K(s)$ | 容量迹及其导数；传播率控制 $b(t)$ 保留 |
| #26 | $A,B\to A_1,A_2$ | 附录 B 的部分分式系数 |
| #27 | $P,y,y_1,y_2\to\mathbf P,\zeta,\zeta_1,\zeta_2$ | 正则性证明的局部坐标拼接段；其后任意状态点 $y$ 保留 |

作者已采纳全部 27 条；#1、#2、#5、#6 留待 A1，#13 留待 C3，#19、#23 留待 D。S1 的命令、核对结果和分步提交文件清单见[本批报告](validation/notation_s1_20261020/README.md)。

## 文件与来源

- `latex/main.tex`、`main.pdf`、`references.bib`：主文源文件、实际编译稿及文献库。
- `latex/supplementary.tex`、`supplementary.pdf`：独立补充材料源码与编译稿；阅读主文后按需查阅三节附加证据。
- `latex/generated/numerical_values.tex`：主文和补充材料共用的数值导出宏；`generated/scaling_values.tex` 为解析量级宏。
- `matlab/numerical_scenarios/`：配置、求解、独立评估、调度、三张图和正文宏导出。
- `validation/numerical_scenarios/`：共享输入、独立 Python 解析 fixture、验证入口、执行日志和状态。
- `data/numerical_scenarios/runs/`：不可覆盖的原始记录及 `*.solver.json`。
- `data/numerical_scenarios/run_index.json`、`selection_manifest.json`：全部尝试索引与五例预定主选择。
- `data/numerical_scenarios/revision_checks/`：评估 sidecar、批次请求/报告及初猜、网格、时域、阈值摘要。
- `figures/numerical_scenarios/`：`FigN1_regions`、`FigN2_waiting`、`FigN3_boundary_tracking` 的 PDF/PNG，以及主结果节的 `FigN1_optimal_partition`；数值章节保留三图、成本表和误差表，另有 `figures/scaling/FigD_magnitude` 量级图。
- `validation/numerical_scenarios/rerun_20261020/comparison_report.json`：C01–C35 的新旧 run_id、原始文件与评估来源、逐项差值及严格验收结果。
- `validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json`：本次 35 个新 run 的原判据与修订判据对照。
- `MANIFEST.txt`：复现文件清单；`archive/first_version/` 与 `legacy_results/` 仅用于历史追溯。

`E1.mat`–`E5.mat` 是 selection manifest 指定原始 `run_id` 的兼容副本。作图和导出核对副本、原始哈希、求解指纹及来源；解析参考不会代替缺少的求解数据。求解、评估、图和正文导出分别记来源，重做后处理不修改 `solve_commit`、`solve_started_utc` 或原始数组。

## 复现命令

以下命令从仓库根目录执行。实际记录使用 MATLAB R2025b、CasADi 3.4.5；OpenOCL/IPOPT 无法从当前接口取得的版本保留 `unknown`。Python fixture 使用 Python 3.12.8、`mpmath==1.3.0`；第 8–9 步独立后处理使用 NumPy 1.26.4、SciPy 1.13.1。完整环境和依赖文件哈希在保存的 provenance 中。

```powershell
python -m pip install -r tracing_isolation_optimal_control_complete/validation/numerical_scenarios/requirements.txt
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
```

`--check` 只读比较 fixture。显式更新才使用 `--write`。

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
make_numerical_figures();
export_numerical_latex();
```

`all,false` 先运行无优化器测试，再按 main → initialization → grid → horizon → threshold 汇总。同一指纹成功记录命中缓存；它可能重新评估和发布主兼容副本，不表示重新完成 35 次优化。依赖、源码或设置不同会使缓存失效。需要另一次真实求解才使用 `force=true`，新 attempt 另存。阈值模式仅对同一主源作 45 次识别，优化调用为 0。

`OPENOCL_ROOT` 可指定已安装的依赖目录，默认候选为仓库的 `optimal/OpenOCL-master 0104`。`revision_preflight(openoclRoot)` 显式参数优先，仅检查环境，不下载安装或运行优化。环境指纹包含依赖绝对路径和原字节哈希；隔离目录若要核对已有缓存，必须保持相同实际依赖目录和求解源码字节。`OCL_CASADI_SETUP` 由调度器在已检查依赖后设为 `true` 并恢复。

## 编译与隔离检出

在本项目目录运行 Windows 的 `.\build.bat` 或 Linux/macOS 的 `bash build.sh`，依次编译 `latex/main.tex` 和 `latex/supplementary.tex`。每份文稿执行 XeLaTeX → BibTeX（仅在首轮 `.aux` 含文献库时）→ XeLaTeX → XeLaTeX，输出 `latex/main.pdf` 与 `latex/supplementary.pdf`。两份文稿各自独立编译，共享宏通过 `generated/numerical_values.tex` 读取；补充材料不依赖主文 `.aux`。

上述第 11 步检查均有实际报告，包含输入/fixture、无优化器测试、保存数据后处理、三图/一表、主文编译、日志和页面渲染及独立 smoke。候选基于 Git HEAD 加明确成果文件，复用显式 `OPENOCL_ROOT` 指定且已核对哈希的依赖目录；这项检查验证本机候选源码和数据可检出并运行。候选与原工作区的 35 个 raw/solver、35 个 assessment、输入和 fixture 字节相同，主 TeX 相同；兼容副本只更新选择时间戳及相应哈希，其全部科学字段/数组相同。旧 `clean_checkout_report.json` 仍仅是第 0–2 步历史证据。
