# D阶段后续：时长结果、自包含源码、图2格式与E2去重

日期：2026-10-21。基准提交 `9a67992248f41dada8c02b2e1851fc87ffa54f4f`；沿用 `codex/numerical-reproducibility-revision`。仅执行作者本次四项后续，不进入F/G，不推送。提交后停下等待作者审阅。

## 修改文件与范围

- `latex/main.tex`：摘要同时报告成本小量与时长差；16.2节解释低强度尾段替代、实例时长与慢收敛；第15节重复E2例子改为转引；原D六个开发标记删除，两组导出器AUTO-GENERATED标记保留。
- `latex/generated/scaling_values.tex`：原17个D宏的名字和展示数字保持，新增10个时长及摘要宏；导言区引入，正文不再读取validation目录。局部`.gitattributes`保留宏的构建字节。
- `figures/scaling/FigD_magnitude.pdf/.png`：按正文实际宽度出图，原生尺寸插入；图(d)改为归一时长差与y=1参考线；使用Times New Roman/STIX，外置子图标记及一次顶部图例。旧D图和旧脚本保留。
- `latex/main.pdf`、`latex/theory_only.pdf`：同步通过验收的46/36页产物；`main.bbl`与原版一致，无需修改。
- 本目录：新解析脚本、JSON、图形尝试、独立审阅、保护基线、仓库内/隔离构建日志、依赖清单和页面核查。完整清单见 `changed_files.txt`，显式暂存路径见 `staging_paths.json`。

模型整节、69个原定理类/证明环境、114个原陈列公式逐字保持。两个自动数值块与17个原D宏不变；8个保护图、旧D目录84个跟踪文件和全部6730个既有保护文件SHA-256不变。证据分别见 `scope_review.json` 和 `audit_report.json`。

## 80位时长核算

时长差直接计算

`Delta_T = T_B(s_B,h) - log(K/i_bar)/gamma`，

其中容量尾段使用 `log1p((s_B-h)/(beta*h))/(c*K)`；没有把两个总正控制时长相减。缩短百分比为 `100*Delta_T/T_fill`。新数值不是新的OCP求解。

| 情景 | 公共尾段时长差 | 以纯填充时长为分母的缩短 | 指定舍入 |
|---|---:|---:|---|
| E2 | 2.536301567820959042920853 | 53.1666019447837505% | 2.536302；53.17% |
| 西安来源情景 | 8.263905044693500351096536日 | 25.40848207069568355% | 8.263905日；25.41% |

西安参数的时长差极限 `1/(beta*gamma)=24.34292363381426836` 日，显示为24.343日。它与有限K下最优总时长24.260293日是不同量，正文明确区分。所有新宏、精确值、参照比对和残差见 `duration_values.json`、`duration_checks.json`；30/30项通过，包含10个新展示值、3个图(d)参照值、17个旧宏不变性。

图2(d)在beta=.5、c=2、gamma=.3时：

| K | beta*gamma*Delta_T | 四位小数参照 |
|---:|---:|---:|
| .01 | 0.8667214134111084311 | 0.8667 |
| .001 | 0.9837600059185233274 | 0.9838 |
| .0001 | 0.9983377262024803439 | 0.9983 |

全部与作者参照相符。前三面板、620点网格和1个mask与旧图逐项相同，30/30项通过。每个格点由公共尾段直接计算时长差；不适用共同入口的beta=.13、K=.15仍不画，并在中文图注解释。51个文字框、全部文字框对、全局图例框与密采样曲线的相交数均为0。最终PDF字体实际嵌入和150dpi图形复核记录位于 `figure_attempt3/`。

正文实际linewidth由两种构建的日志独立测得469.47049 TeX pt，与新图一致；PDF宽467.7165529265 bp，插入比例1，刻度8pt、标签9pt。

## 实际运行入口与结果

从仓库根目录逐条执行。依赖前一命令的下一步只在其退出码通过后执行。计算用 `E:/anaconda/python.exe`，PDF构建/渲染/汇总用工作区依赖Python。

```powershell
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/audit_followup.py --baseline
python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/duration_values.py
python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/figure_followup.py --attempt 3
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/scope_review.py
python -X utf8 tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/build_followup.py --mode workspace --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/build_followup.py --mode isolated --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/build_followup.py --mode isolated --attempt 2 --stabilize-first
& tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/publish_outputs.ps1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/render_followup.py
python -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/audit_followup.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/acceptance.py
```

以上是实际入口，其中isolated attempt1未通过最终引用稳定性验收，记录保留。已有baseline和attempt不可覆盖，复核时使用已有证据或另取新编号。

- 原符号核对28/28；时长/宏参照30/30；图前三面板与网格保护30/30；独立范围审阅25/25；全文件保护审计12/12；最终汇总23/23。
- 仓库内两稿各实际运行XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，最终8/8命令退出0，46/36页，最终日志零诊断。实际argv、cwd、源码及图哈希见 `workspace_attempt1/build_report.json`。
- 全新隔离副本初始根只有latex和figures，共14个编译资产，不复制aux/bbl等残留。首次clean四阶段主文的最后日志仍有“Label(s) may have changed”，不把它报为通过。
- isolated attempt2重新建立全新副本，先8条命令在副本内生成自己的引用，再独立执行两稿完整四阶段验收；最终8/8命令退出0、最终零诊断，46/36页。初始化与最终命令分开记录，不能声称“首次干净四阶段即零警告”。本轮两种最终验收共16条命令；加上隔离初始化8条及首次未通过的4条，共28个实际TeX/Bib进程。
- `.fls`由构建脚本和独立审阅脚本分别解析：主文153个输入为副本内11个及TeX/字体系统142个；TheoryOnly151个输入为副本内9个及系统142个，原项目回读0。BibTeX只读副本references.bib，BIBINPUTS仅指向副本latex及系统默认。两稿的全部页面提取文本与仓库内实际构建逐页一致。详见 `isolated_attempt2/*_inputs.json` 和 `scope_review.json` 的selfcontained_review。
- 正式PDF逐一与仓库内产物核对哈希；主文46页、TheoryOnly36页。已实际150dpi渲染并查看主文1、27–31页，TheoryOnly1、26–30页，共12页；覆盖摘要、第15节末、第16节各页与图2。没有声称目视检查全部82页。证据见 `render_manifest.json`、两份visual审阅和 `visual_qa.json`。

MATLAB、优化器、新增OCP求解与ODE积分均为0次。未改原求解数据、已有评估或历史D记录。

## 异常、参照差异与审阅节点

新数字与作者给出的全部参照在指定舍入下一致。第一幅新图的核查发现窗外log刻度与角部刻度间距问题，失败JSON保留于figure_attempt1；按实际可见窗筛选刻度并增加间距后通过，未改曲线数据或碰撞标准。首次隔离引用警告及后续额外初始化过程如上完整保留，没有放宽最终日志要求。

最终没有未解决的技术阻断。按本次指令，独立提交后停下等待作者审阅；请重点审阅时长解释、图2(d)和自包含构建证据。本次不进入F，不推送，不改变main分支。
