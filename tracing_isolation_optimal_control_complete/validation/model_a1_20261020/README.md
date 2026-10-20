# 第三批 A1：五仓室模型与二维等价

日期：2026-10-20。执行依据为 `ai/claude_revision_plan/START_HERE_CODEX.md`、`REVISION_PLAN.md` 的 A1 及 `SYMBOL_TABLE.md` §0。A1 的 #1、#2、#5、#6 均未标为“不采纳”。基线为 `be23df7dedcec8d61c9b0283b5a10af98a3d53cf`，所在分支为 `codex/numerical-reproducibility-revision`；第二批 S2 已完成。本批没有进入 B 或后续步骤，没有推送。

## 提交与文件

独立提交标题：`paper: 五仓室模型与二维等价（A1）`；提交号为本报告所在提交，末尾附本仓库既有的 `Co-Authored-By: Codex <noreply@openai.com>`。

主要改动为 `latex/main.tex`、`latex/main.pdf`、`latex/theory_only.pdf`、本项目 `README.md`，以及本目录的构建、审计、原始日志和报告。完整文件清单见 `changed_files.txt`。没有修改原始数值、已有评估、求解器代码、图形、参数或成本定义。

## 实际完成的内容

- 写入五仓室归一化方程、非负单纯形与守恒，明确 `gamma=delta_I+gamma_I`。`r` 聚合住院与康复仓室；`i+i_q` 不包含已转入住院移出状态的个体。
- 无回流命题先由投影和提升证明两问题有相同的可行控制与成本，得 `V_0=V`，再引用后文独立验证的 `V=U`。限定正投影初值、常接触率、只依赖跟踪强度的成本和感染阈值约束。
- #1：删除 `beta_1,beta_2` 及“双传播系数”说法，反演内容压缩为两句；#2：合计量改为 `s_q+i_q+r`，能力上限改为 `bar q`，局部空间维数由 `m` 改为 `d`；#5：引入 `tilde s=s+s_q` 及其导数；#6：把 `P_0` 提前到第4节，以 `P_0<=K` 定义安全集，数值节改为引用该定义。
- `P_0` 的正感染公式与疾病灭绝轴分开：`P_0(s,0)=0`。安全集仍限制在原正感染状态域，没有扩大主定理。
- 题名、PDF 元数据及页眉统一为《感染阈值约束下跟踪隔离的全域最优控制》。摘要、引言和结论仅作与 A1 模型相关的最低限度同步。

## 实际命令与结果

以下命令从仓库根目录运行。`python` 为 `E:/anaconda/python.exe`；构建使用带 `pypdf` 的 bundled Python：`C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。

```powershell
python tracing_isolation_optimal_control_complete/validation/model_a1_20261020/audit_a1.py --capture
python tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
python tracing_isolation_optimal_control_complete/validation/model_a1_20261020/verify_model.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_a1_20261020/build_a1.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_a1_20261020/build_a1.py --attempt 2
python tracing_isolation_optimal_control_complete/validation/model_a1_20261020/audit_a1.py
```

| 检查 | 实际结果 |
|---|---|
| 既有符号恒等式 | 28/28 为 True，见 `notation_checks.log` |
| A1 独立代数恒等式 | 8/8 通过，见 `model_algebra_report.json`；不代替命题证明 |
| 源符号、定义位置、题名、引用审计 | 20/20 通过，见 `audit_report.json` |
| 原始数据与已有产物保护 | 535 个保护文件字节不变；两块自动生成数值内容不变 |
| 成功构建 | 主文 38 页、TheoryOnly 29 页；最终 `.log/.blg` 无错误、警告、未定义引用、缺字或溢出 |
| 页面目视检查 | 主文第 1、3、4、5、7、8、26、27、34 页；TheoryOnly 第 1、4、5、7、8、26、27 页，均正常 |
| MATLAB / 优化器 / 科学求解 / 缓存调用 | 0 / 0 / 0 / 0 |

构建实际执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，主文和 TheoryOnly 均使用同一份 `main.tex`。完整可复核的 argv、cwd、退出码、源文件和 PDF 哈希见 `attempt2/build_report.json`；原始阶段输出及最终日志也保存于该目录。TheoryOnly 入口为现有 `latex/theory_only.tex`，内容为定义 `TheoryOnly` 后输入 `main.tex`，与 README 的命令等价。

首次构建的四个 TeX/BibTeX 命令均成功，但检查器把宏包清单中的 `Providing info/warning/error messages` 和 BibTeX 的零计数 `warning$ -- 0` 当成了真实警告，因此构建脚本返回失败；该误判记录完整保留在 `attempt1/`。只修正了检查器的真实诊断匹配，未修改正文以绕过检查。随后 `attempt2` 完整重编两份文档并通过，不是复用首次 PDF。另一次环境依赖探测发现 Anaconda Python 缺少 `pypdf`，实际构建改用预装该库的 bundled Python。

页面使用本机 `pdftoppm`，逐页参数为 `-f <页> -l <页> -scale-to 1400 -png -singlefile`；Python/Pillow 仅将已渲染页面并排组成检查图。渲染图在 `tmp/model_a1_20261020/qa/`；页码、PDF 哈希及目视结论见 `visual_qa.json`。没有声称逐页检查全部 38/29 页。

## 来源与论证边界

直接读取本地 `ref/Tang_Zhou_2024_JMB.pdf` 第4–5页：第4页 §2.1、式(2.1)的原模型为六仓室，非隔离感染者经诊断进入住院仓室或自然康复，隔离感染者经诊断进入住院仓室。本稿合并住院与康复后得到所用的 `r` 和 `gamma=delta_I+gamma_I`。第5页“波次较短”和抗体保护的理由针对康复者不再感染；它没有论证隔离易感者不回流。

| 主张 | 核对依据 | 边界 |
|---|---|---|
| 五仓室守恒及二维投影 | 方程逐项相加、8 项代数核对、独立通读 | 既定流量与非负参数假设 |
| `V_0=V=U` | 相同可行控制与成本；后文验证定理 | `lambda=0`、常 `c`、现有控制集与成本 |
| `A={P_0<=K}` | 自然轨道峰值与原 `Phi<=Phi_A` 等价 | 限制在原物理正感染域 |
| 住院与康复聚合 | Zhou 原文第4页的仓室及流量 | 本稿 `r` 不等于原文单独的康复比例 |
| `lambda=0` 的使用 | 作者批准的解析基准 | 不作为真实隔离解除过程的经验验证 |

## 与计划验收参照的差异

A1 未规定页数；相对第二批最终主文的 37 页，本批为 38 页，TheoryOnly 仍为 29 页。增加完整模型与等价说明，并压缩反演内容，属于本批预定范围。五仓室方程、等价命题、四项符号条目、题名和来源边界均已完成，没有数学或科学验收差异。保护核对包含全部已有新旧记录，不仅是 `pre-code-rename` 的旧 35 条。

## 停止条件与作者审阅

没有触发实际编译失败、公式核对失败或符号含义不明等停止条件。检查器的首次误判及修复如上保留，不作为论文编译失败。

按执行入口“完成后暂停，等作者审阅模型节”的规则，在本次独立提交后暂停。请作者审阅第2节初稿，重点确认：五仓室中的住院与康复聚合表述；`lambda=0` 解析基准及其适用范围；`K` 的社区负荷含义；新题名。以上为表述与题名审阅，不涉及新增数值实验或扩展最优性结论。
