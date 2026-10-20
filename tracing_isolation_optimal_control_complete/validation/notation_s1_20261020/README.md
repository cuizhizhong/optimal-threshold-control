# 第一批 S1：论文符号定稿执行报告

日期：2026-10-20。基准为 `420bcc760e560b5b1deeffe72e519f991632558b`，工作分支为 `codex/numerical-reproducibility-revision`。本批没有推送，没有执行 S2，没有创建 `pre-code-rename` 标签，没有使用未经作者指定的 Nature skills。

## 1. 提交与文件清单

| 步骤 | 提交 | 改动范围 |
|---|---|---|
| S1.1 | `64defdf` | 采纳决定和范围记录；184 个数据文件的执行前 SHA-256；构建脚本、双 PDF 与本步日志 |
| S1.2 | `c91dbd1` | `latex/main.tex`、专用迁移脚本、导出器显示字符串、导出来源与报告、双 PDF、本步编译日志 |
| S1.3 | `4290366` | 公式与符号库存检查脚本、作用域核对、数据守恒核对、16 项导出回归及代表页核对证据、双 PDF、本步编译日志 |
| S1.4 | 本报告所在提交 | README 符号对照、REVIEW_GUIDE、批次报告和逐提交文件清单、双 PDF、本步编译日志 |

逐提交完整文件清单见 [commit_files.json](commit_files.json)。S1.4 的提交号可用 `git log -1 --oneline` 查看。

作者采纳全部 27 条。本批完成 #3、#4、#7、#8、#9、#10、#11、#12、#14、#15、#16、#17、#18、#20、#21、#22、#24、#25、#26、#27，共 20 条；具体旧名、新名及范围见[项目 README](../../README.md#符号对照论文--代码)。#1、#2、#5、#6 留待 A1，#13 留待 C3，#19、#23 留待 D。

## 2. 实际命令与结果

命令均从仓库根目录执行。以下 `$project` 仅为展示时缩短路径；实际绝对路径、参数和工作目录已写入每步 `build_report.json` 与 `S1.3/checks_report.json`。

```powershell
$project = 'tracing_isolation_optimal_control_complete'
$buildPython = 'C:\Users\cui\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $buildPython "$project/validation/notation_s1_20261020/build_s1.py" --step S1.1
& $buildPython "$project/validation/notation_s1_20261020/build_s1.py" --step S1.2
& $buildPython "$project/validation/notation_s1_20261020/build_s1.py" --step S1.3
& $buildPython "$project/validation/notation_s1_20261020/build_s1.py" --step S1.4
```

每步均对主文和 TheoryOnly 实际执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，共 8 条编译链命令。构建从现有 `main.tex`、`theory_only.tex` 入口读取，使用本步独立输出目录，完成后发布双 PDF。

| 步骤 | 主文 | TheoryOnly | 命令退出码 | 最终日志问题 |
|---|---:|---:|---|---:|
| S1.1 | 37 页 | 29 页 | 8/8 为 0 | 0 |
| S1.2 | 37 页 | 29 页 | 8/8 为 0 | 0 |
| S1.3 | 37 页 | 29 页 | 8/8 为 0 | 0 |
| S1.4 | 37 页 | 29 页 | 8/8 为 0 | 0 |

最终日志未发现错误、未定义引用、重复标签、缺字或溢出。四步合计完成 8 个文档构建、32 次编译链命令。

```powershell
python -I "$project/ai/claude_revision_plan/checks/verify_new_notation.py"
python -I "$project/ai/claude_revision_plan/checks/symbol_inventory.py" "$project/latex/main.tex"
python -I "$project/ai/claude_revision_plan/checks/symbol_inventory.py" "$project/latex/main.tex" --check-s1
python -I "$project/validation/notation_s1_20261020/verify_preservation.py"
python -I "$project/validation/notation_s1_20261020/run_checks.py"
```

- 原有 28 条代数恒等式全部为 True，新增代数检查为 0；失败退出码改为非 0。
- 库存扫描实际完成，20 条作用域检查全部为 True。它们检查符号及范围，不替代数学证明。
- [S1.3/checks_report.json](S1.3/checks_report.json) 中四条正式核对命令均退出 0，完整输出保存于同目录。

MATLAB 使用 `E:\software\Matlab\bin\matlab.exe`，两次成功调用分别带 `-batch` 执行以下内容，控制台日志通过 `-logfile` 保存：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','notation_s1_20261020'));
run_s1_export('export');
```

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','validation','notation_s1_20261020'));
run_s1_export('regression');
```

`regression` 依次实际调用 `verify_saved_result_exporter()`、`verify_revision_exporter()`、`verify_pending_result_exporter()`，分别通过 11、3、2 项，共 16 项，然后调用 `export_numerical_latex()`。两个成功入口均退出 0，详见 [regression_report.json](regression_report.json)、[regression_console.log](regression_console.log)、[export_authorized_console.log](export_authorized_console.log)。故障注入测试中的 `verified=0` 是预期的失败分支核对，未影响正式正文。

本批优化器调用 **0 次**，科学求解 **0 次**。35 条保存结果的来源不变，原严格判据双通过 28/35、修订判据双通过 30/35 的原有叙述保持不变；本批没有重新评估或重新求解科学记录。

```powershell
& $buildPython "$project/validation/notation_s1_20261020/render_check.py"
```

使用 Poppler 实际渲染并目视检查主文第 7、10、13、18、19、20、25、28、29、31、34、35 页，未见裁切、重叠、缺字或公式异常。这里只报告 12 个代表页核对，不声称逐页检查了全部 37 页；记录见 [visual_pages.json](visual_pages.json)。

## 3. 公式与数据守恒

- `f(x,q)` 保持原凸组合向量场；边界写为 `f((s,K),q)`，Lie 导数写为 `L_{f(\cdot,q)}`，反馈积分正确保留状态、控制两个参数。
- 原局部函数 `L(s,\psi)` 展开后，`L_s(z,\psi)` 写为先对复合函数求偏导、再令 `s=z`，没有将其误改为全导数。
- 一维参数改为带下标变量时补足分式分组，例如 `\frac{\beta}{s_c}`；命令与普通字母之间保留所需分隔。双函数定义改为 `aligned` 两行仅用于容纳展开后的记号。
- 手写主文与指定作用域迁移结果一致；非数学正文、注释、代码与标签保持不变。独立只读差异审查未发现数学内容变化。
- 两个自动生成块逆映射 `$n=`→`$N=`、`\varepsilon_K`→`\delta` 后，与 `420bcc7` 逐字相同。
- 导出器相对基准只有 8 处 `$N=`→`$n=` 和 4 处容量超出控制词的替换；字段 `N`、局部变量 `delta` 与所有运算保持原样。
- 原有 184 个数据文件中，183 个 SHA-256 不变，仅 `export_provenance.json` 的导出源码哈希与时间更新。原始记录、solver sidecar、已有评估、选择清单和汇总数值均未改写，没有新增数据文件。详见 [preservation_report.json](preservation_report.json)。

按计划保留的其他作用域记号包括：切换映射 `\sigma(z)`、极限标量和 Lipschitz 常数 `L`、单值反馈 `Q(t,x)`、任意状态点 `y`、人口 `N`、证明内部小时间 `\delta`，以及 `lem:finite-entry` 中范围外且含义明确的局部积分变量 `\tau`。

## 4. 与验收参照的差异及停止条件

本批各项验收通过，没有公式为 False、实际 TeX 编译失败或无法判断含义的范围外旧记号。没有触发需要停止的条件，没有待作者决定的问题。

工具运行中出现过以下环境问题，均未改变论文或数学任务：

- 默认 Python 缺少 `pypdf`，构建脚本在导入阶段退出，尚未启动 TeX；改用已安装依赖的内置 Python 后，四步实际编译均成功。
- MATLAB 首次在默认沙箱内启动，因预设目录不可写出现 `PrefdirNotWritable`，尚未执行任务代码；保留 [首次启动记录](matlab_startup_attempt1.txt)，随后经工具授权在沙箱外执行相同导出入口成功，没有修改预设目录或放宽验收条件。
- 可选页面渲染首次探测发现内置 Python 无 `fitz`，随后使用现有 Poppler 与 Pillow 完成代表页核对，没有安装依赖。

已有未跟踪临时文件、归档和 LaTeX 中间文件保留原处，未纳入本批提交。本批新增构建中间文件与页面 PNG 位于项目 `tmp/notation_s1_20261020/`，正式日志、报告和复现脚本位于本目录。
