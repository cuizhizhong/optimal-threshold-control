# 跟踪隔离模型中双传播系数的最优控制与唯一性

本目录保存当前论文、MATLAB/OpenOCL 数值求解与复现记录。`ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md` 是执行计划；其中的阈值、预期结构和建议结论不作为已完成实验的结果。

本轮修订的对照材料、实际结果、最终正文和复现边界见[评阅入口](REVIEW_GUIDE.md)。

## 当前结果与限制

第 6–9 步已实际取得默认矩阵的 35/35 个不同配置：35 次科学求解均返回成功，`numeric_pass` 与 `agreement_pass` 各为 29/35，同时通过为 28/35。五例预定主结果均通过这两组浮点诊断；初猜组和固定步长时域组通过，原严格网格组为 `failed`、`consistency_pass=false`。七条至少一项诊断失败的记录全部保留。第 8–9 步新增求解为 30 次、缓存引用为 10 次，主批的另 5 次求解见 `step67_main_report.json`。

`step89_results.md` 另列最细两级的计划建议比较，其通过不覆盖严格网格失败，更不表示所有网格都容量可行。E2/E4 的 N=2000 分别出现 11/8 单元的中间控制块；粗网格容量、成本及结构异常见详细记录。浮点接受、多初猜重复收敛和三个有限网格不替代正文解析证明。

第 10–11 步已由保存数据刷新正文宏、三图和一表；当前工作区科学优化调用为 0。12 组 MATLAB 单元检查、3 项旧失败清空回归、8 项实数据回归及 2 项附加结果缺失/阻断回归通过；两次最终导出文字相同。三图来源和文件哈希已核对，PNG 已目视检查。主文 34 页、TheoryOnly 26 页实际编译成功，最终日志未发现未定义引用、重复标签、缺图/缺字或溢出。

第 11 步的候选快照 `e701f69a1f6a59e3b4456417777b829323566bd0` 起始 Git status 为空。Python fixture 只读检查与 6 项测试通过；MATLAB 12 组 unit、9 项保存数据回归通过，`all,false` 实测可信缓存 35 次、科学优化 0 次、重新评估 0 次，协议完成 true、一致性 false。独立 T=1,N=4,d=2 接口 smoke 成功 1 次，不纳入科学矩阵；候选 main/TheoryOnly 也实际编译为 34/26 页，最终日志零问题。完整性核对通过，保护 93 个文件。N=16000、T=600 和额外初猜未运行，新结果不填入。

首次主文 11.08316pt 附录溢出已换段修复；首次候选展开因 Windows 长路径失败，第一次干净 MATLAB 保存数据回归又因长路径 assessment 漏拷贝报 `No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a`。源/目标复制及 MANIFEST 枚举已修复并核对全部 35 个评估文件，失败日志保留。PNG 时间戳及极少像素存在再导出差异，逐图视觉未见实际变化，不宣称字节一致。全部 15 类操作异常见 `validation/numerical_scenarios/step1011_operational_anomalies.json`；最终结果、精确命令和文件范围见同目录 `step1011_results.md`、`step1011_commands.md`、`CHANGED_FILES_STAGE1011.txt`。

## 文件与来源

- `latex/main.tex`、`main.pdf`、`references.bib`：主文源文件、实际编译稿及文献库。
- `matlab/numerical_scenarios/`：配置、求解、独立评估、调度、三张图和正文宏导出。
- `validation/numerical_scenarios/`：共享输入、独立 Python 解析 fixture、验证入口、执行日志和状态。
- `data/numerical_scenarios/runs/`：不可覆盖的原始记录及 `*.solver.json`。
- `data/numerical_scenarios/run_index.json`、`selection_manifest.json`：全部尝试索引与五例预定主选择。
- `data/numerical_scenarios/revision_checks/`：评估 sidecar、批次请求/报告及初猜、网格、时域、阈值摘要。
- `figures/numerical_scenarios/`：`FigN1_regions`、`FigN2_waiting`、`FigN3_boundary_tracking` 的 PDF/PNG。正文保留这三张主图和一个成本主表。
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

在本项目目录运行 Windows 的 `.\build.bat` 或 Linux/macOS 的 `bash build.sh`，均执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，输出 `latex/main.pdf`。TheoryOnly 检查在 `latex/` 中执行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error -jobname=theory_only '\def\TheoryOnly{1}\input{main.tex}'
bibtex theory_only
xelatex -interaction=nonstopmode -halt-on-error -jobname=theory_only '\def\TheoryOnly{1}\input{main.tex}'
xelatex -interaction=nonstopmode -halt-on-error -jobname=theory_only '\def\TheoryOnly{1}\input{main.tex}'
```

上述第 11 步检查均有实际报告，包含输入/fixture、无优化器测试、保存数据后处理、三图/一表、主文/TheoryOnly 编译、日志和页面渲染及独立 smoke。候选基于 Git HEAD 加明确成果文件，复用显式 `OPENOCL_ROOT` 指定且已核对哈希的依赖目录；这项检查验证本机候选源码和数据可检出并运行。候选与原工作区的 35 个 raw/solver、35 个 assessment、输入和 fixture 字节相同，主 TeX 相同；兼容副本只更新选择时间戳及相应哈希，其全部科学字段/数组相同。旧 `clean_checkout_report.json` 仍仅是第 0–2 步历史证据。
