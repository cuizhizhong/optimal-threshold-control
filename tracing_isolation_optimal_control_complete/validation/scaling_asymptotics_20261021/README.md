# D：无回流模型的量级、小容量渐近与参数来源

日期：2026-10-21。基线 `8b8f5a239193f8b5102355f9946b43eaea2b72ea`；沿用分支 `codex/numerical-reproducibility-revision`。依据 `ai/claude_revision_plan/START_HERE_CODEX.md` 与 v5 `REVISION_PLAN.md` 的 D1–D4 执行。未进入 F/G，未新建分支，不推送。

## 实际修改

- `latex/main.tex`：新增第16节的纯容量填充定义、统一比较指标、命题16.1、参数来源表和四面板解析量级图；新增附录C完整证明；摘要补一句有条件的 `K^2` 绝对节省与 `K^3` 相对节省。正文使用 `Delta J/J_fill` 与 `s_1^circ`，不另用G表示相对节省。
- `latex/references.bib`：追加 He–Tang–Xiao 2023 的独立著录。原有条目逐字保留。
- `latex/main.bbl`、`latex/main.pdf`、`latex/theory_only.pdf`：同步最终构建产物。
- 本目录：新增 D 专用解析脚本、十进制数据、图、推导片段、来源与独立审阅、保护/验收报告、全部构建尝试的日志。完整文件清单见 `changed_files.txt`；暂存路径见 `staging_paths.json`。

旧公式环境、D新增标记以外的原稿、两块自动生成数值内容均逐字不变。6645个既有记录、代码、图片、参考资料及验证文件的SHA-256不变，详见 `preservation_baseline.json` 与 `audit_report.json`。没有改写原始求解记录、旧评估或旧异常。

## 解析核算与参照差异

新实现采用最终符号，80位精度计算标量根及公共尾段差；只有独立的总成本差恒等式核对用110位处理消去。未运行历史脚本中已排除的受限能力或回流入口。

- E2解析重算：`J_fill=1.5783855039561378438`，`J*=1.5295111601514722730`，`DeltaJ=0.048874343804665570796`，以纯填充成本为分母节省 `3.0964769812041908%`。`s_B=0.54769512467954490847`，与计划历史参照相符，不称新OCP结果。
- E2正控制时长分别为 `4.7704789756077294843` 与 `2.2341774077867704414`；不包含初始免费等待。
- 固定 `beta*c=1,gamma=.3`，扫描620组K与beta，其中619组适合共同尾段比较。`beta=.13,K=.15` 的自然触点满足 `s1<s_B`，明确mask，未套用共同入口最优成本公式。
- 另用 `s0=1-K/2,i0=K/2` 的35个小容量样本核对三式及相对节省K^3，K降至1e-9。固定正初值扫描不延拓至K<i0。
- 历史示例 `beta=.155,c=10,gamma=.3504,K=1e-4` 的成本差与渐近首项偏差，以首项为分母约6.40%；计划的“约1e-4才接近首项”不能理解为统一1%保证。新图固定beta*c的参数与该历史示例分开记录。
- Zhou西安原文 `gamma=.1998+.1006=.3004`；He六地beta精确范围 `.1281–.2544`。文献来源、非零q0、时变率与人口归一化的区别见 `parameter_sources.md`。本批作者新拟合为0。
- 使用西安文献参数另设本文K与初值的常参数情景，只是解析量级评价，不是城市拟合或现实最优政策的复现。

## 实际命令与结果

以下从仓库根目录执行；完整XeLaTeX/BibTeX argv、cwd与退出码见各次 `build_report.json`。Python计算采用 `E:/anaconda/python.exe`，构建及渲染采用工作区依赖运行时Python。

```powershell
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/audit_revision.py --baseline
python tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/analytic_scan.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/compute_values.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/apply_d.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/symbolic_small_capacity.py
python -X utf8 tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/build_revision.py --attempt 4
& tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/finalize_delivery.ps1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/render_revision.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/audit_revision.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_asymptotics_20261021/acceptance.py
git diff --check -- '*.tex' '*.bib' '*.py' '*.md' '*.json'
git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check -- '*.tex' '*.bib' '*.bbl' '*.py' '*.ps1' '*.md' '*.json' '*.csv' '*.txt' '*.gitattributes'
```

上述每一行是独立入口。执行后检查退出码，再进入依赖它的下一行；不得因前一命令失败仍自动继续。基线与构建日志不能覆盖：已有 `--baseline` 文件或 attempt目录时使用现有记录，构建须换新的attempt编号。

实际解析检查包括620组扫描、35组渐近初值、18个精度阈值及2项独立积分。最大标量相对残差约 `1.49e-69`，Theta匹配相对残差约 `4.83e-73`。原有符号核对28/28；新增独立SymPy代数10/10、片段一致性2/2；范围保护审计10/10。最终汇总验收的实际逐项结果见 `acceptance_report.json`。

最终主文46页、TheoryOnly36页。两份均实际执行 XeLaTeX→BibTeX→XeLaTeX→XeLaTeX；最终8/8命令退出0，log/blg无错误、未定义引用、缺字或溢出。`attempt4/build_report.json` 保留了编译成功但Python复制失败的原始状态；`delivery_report.json` 单独确认原生PowerShell同步成功，正式PDF和bbl与attempt4产物哈希完全一致，不把旧的复制失败记录改成成功。

实际150dpi渲染并目视检查主文1、2、3、4、28、29、30、31、39、40、45、46页，TheoryOnly 1、2、3、4、27、28、29、30、31、32、35、36页，共24页。范围覆盖摘要目录、全部D正文、表图、完整证明、参考文献及相邻页；不声称逐页检查全部82页。记录见 `render_manifest.json`、`visual_main_review.md`、`visual_theory_review.md` 和 `visual_qa.json`。

本批MATLAB调用、优化器调用、新增OCP求解及ODE积分均为0次。标量求根迭代、代数核对和积分求值不是优化求解。

## 保留的异常与停止条件

- 初次保护哈希读取遇到Windows长路径问题，改用扩展绝对路径后成功建立基线，未修改旧文件。
- attempt1主文四阶段进程退出0，但最终排版日志有表格断行警告与15.50378pt文字溢出，未通过验收；仅修正D排版，未放宽日志标准。
- attempt2双稿通过；目视发现表格拆开“两篇文献”，在表后增加空行分段。
- attempt3安装修正源时Python写入既有文件失败，随后Shell仍继续编译了旧源，该次未用于最终交付。修正通过apply_patch安装后，attempt4重新独立双编译。
- attempt3/4均保留Python向映射PDF回写失败。原生Copy-Item明确诊断过用户映射区域，随后采用只同步哈希不同文件的方式成功，最终文件逐一核对哈希。
- 暂存区按局部`.gitattributes`保留记录的CRLF原始字节；默认空白检查把行尾CR误报为尾随空格。最终仅在该命令启用`cr-at-eol`，仍检查真实尾随空格、文件末多余空行和Tab前空格；两份新推导片段的末尾空行已清除，正文源码和最终PDF不变，片段SHA及独立代数核查已更新。

以上为本批内部文件/排版验收阻断及修复，没有更改数学判据、参数或模型。最终无未解决停止条件，无需作者另作技术决定。D不含作者审阅暂停标记；本次按请求止于D，不进入F。完整异常过程见 `workflow_notes.json`。

`main` 分支仍为 `496e454b34f7ce6861238041d5bd14b475e37917`。本批只在指定工作分支作独立本地提交；没有推送。
