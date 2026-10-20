# 修订评阅入口

本分支保留历史五批修订（第0–11步），并新增 S1 论文符号定稿及 S2 代码符号统一、35 次实际重跑的源码、正文、编译产物和实际实验记录。评阅时以保存数据和执行报告为依据；执行计划、预期结构和 LaTeX 模板片段不属于已完成实验的结果。

## 建议阅读顺序

1. [当前分批入口](ai/claude_revision_plan/START_HERE_CODEX.md)与[当前计划](ai/claude_revision_plan/REVISION_PLAN.md)：检查 S1/S2 要求和证据口径；[历史执行计划](ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md)保留第0–11步口径。`latex_snippets/` 保留原始修订片段作对照，最终正文以 `latex/main.tex` 为准。
2. [执行状态](validation/numerical_scenarios/REVISION_STATUS.md)：五批的执行证据和历史记录。
3. 先读[S2 执行记录](validation/numerical_scenarios/rerun_20261020/S2.4/README.md)、[35 项新旧比较](validation/numerical_scenarios/rerun_20261020/comparison_report.json)与[本次原判据对照](validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json)。历史[第8–9步实际结果](validation/numerical_scenarios/step89_results.md)与[第10–11步交付记录](validation/numerical_scenarios/step1011_results.md)：先读这两份较小的摘要，再按需查完整JSON和原始MAT文件。
4. [最终主文源码](latex/main.tex)、[主文PDF](latex/main.pdf)和[TheoryOnly PDF](latex/theory_only.pdf)：S2 各步主文实际编译为37页；TheoryOnly 最近一次 S1 核对为29页。保留三张主图和一个主表。S2.7 两组生成块及块外文字与重跑前基线相同，见[核对报告](validation/numerical_scenarios/rerun_20261020/S2.7/macro_comparison_report.json)；三项导出器回归已通过，见[S2.7 保存报告](validation/numerical_scenarios/rerun_20261020/S2.7/regression_report.json)。S1 符号核对见[历史报告](validation/notation_s1_20261020/README.md)。
5. [MATLAB复现说明](matlab/numerical_scenarios/README.md)、[验证说明](validation/numerical_scenarios/README.md)及[实际命令](validation/numerical_scenarios/step1011_commands.md)：核对算法、来源、缓存和运行范围。

## 需要重点评阅的结论边界

- S2 实际执行35次新求解、缓存命中0次，求解器成功35/35；`all,false` 总耗时2157.5074708秒。与标签 `pre-code-rename` 的旧35配置严格比较35/35通过，成本、控制数组、状态数组最大差均为0，返回状态、迭代、事件、结构和旗标完全相同。默认35个不同配置全部有真实记录。按求解前预定的原严格判据，numeric与agreement各通过29/35，同时通过28/35；按2026-10-10求解后调整的修订判据（状态/容量容差1e-5、容量段控制3e-3），分别为33/35、30/35，同时通过30/35。正文复现附录采用修订判据并写明原判据计数；修订判据不提供新的收敛证据，本次结果见[原判据重评报告](validation/numerical_scenarios/rerun_20261020/S2.6/assessment_revision_report.json)；[历史容差重评说明](validation/numerical_scenarios/tolerance_revision_20261010/README.md)仍保留原批次记录。求解成功、数值接受、理论一致性和协议执行完成是不同判据。
- 七条至少一类诊断未通过的记录保留；E2/E4的原严格网格一致性仍失败。独立最细级比较没有覆盖这些失败，也没有把次细级容量违规改为可行。
- 五例预定主结果均通过两类浮点诊断。E4选中结果（负成本差3.68e-6、容量超出 $\varepsilon_K=7.70\times10^{-7}$）和E3的 $n=2000$ 记录（负成本差6.76e-5、$\varepsilon_K=7.83\times10^{-6}$，评估分类为`unresolved_discrepancy`）的负成本差，均小于把容量放宽为 $K+\varepsilon_K$ 后解析最优值的下降（1.16e-5、1.08e-4）。因此两者都与容量超出相容，不能据此声称发现了低于解析值的严格可行控制；原评估分类不变。
- 非理论初猜、有限网格和有限时域的结果不构成连续可行性、收敛定理或全局最优性的新增证明。$n=16000$、$T=600$和额外初猜未运行，未填入新结果。
- 历史第10–11步科学优化调用为0；本机候选检出复用35个可信缓存，另有1次独立小型接口smoke。依赖文件有实际哈希与跟踪核对；本轮没有在另一台机器重装环境。
- [运行异常清单](validation/numerical_scenarios/step1011_operational_anomalies.json)保留15类异常、警告和差异，包括首次编译溢出、长路径遗漏、检查器误判及图像元数据/微像素变化。

## 来源和文件范围

S2 的基线标签 `pre-code-rename` 指向 `051099fba63cd6d326f2344d2bf4322c1f651282`。旧35份 raw、35份 solver sidecar 和70份 assessment 均保留原处且字节不变；本次追加35份 raw、35份 solver sidecar 与70份 assessment（修订判据35份、原判据35份），当前累计为70/70/140份。`run_index.json` 只追加。当前代码使用 `beta/p/s_e/s_A`；旧字段含义及副本适配见项目 README 的“历史数据字段对照”。

本次35项 `configuration_id`、新旧 run_id、raw/评估路径与逐项验收见[完整对照报告](validation/numerical_scenarios/rerun_20261020/comparison_report.json)。五例主选择遵循预定 `main_N` 和解析初猜，由[selection manifest](data/numerical_scenarios/selection_manifest.json)登记，不按结果贴合程度选择：

| 主例 | 本次选中 run_id |
|---|---|
| E1 | `run_90557e2d9fa045528eddf70fec1f17cc` |
| E2 | `run_be88a14b0f1a4a80a12ea40d2e9e18db` |
| E3 | `run_b5125bf7309e446d9ff6146d257d28c0` |
| E4 | `run_67ce8234939a4f4b81aa86ca7b197b74` |
| E5 | `run_3f672e8955914131af6d36a208c67727` |

S2.8 文档及 S2.9 最终提交报告将在 `validation/numerical_scenarios/rerun_20261020/S2.8/` 和 `validation/numerical_scenarios/rerun_20261020/S2.9/` 汇总；最终提交尚待完成，未推送，不在此预填 commit。

正式发布提交不会改变原始记录的 `solve_commit`、`solve_dirty`、求解时间或实际源码哈希。第10–11步报告中的原HEAD、候选快照及“尚未提交/推送”描述是发布前的执行快照；当前发布提交以Git历史为准，不能把它改写成数值结果的产生提交。

[MANIFEST](MANIFEST.txt)列出精确交付文件。本机临时检出、待删除归档、编译中间文件、Python缓存和正文修改前备份未纳入发布。完整JSON包含较多保存数组，评阅入口优先提供摘要和最终正文，完整证据仍保留。

发布前完整 `git diff --cached --check` 在25份原始日志中报告格式空白；源码、正文、说明和结构化数据的单独空白检查通过。原始日志保留尾随空格、控制字符和原有换行，仓库 `.gitattributes` 对第8–11步日志关闭换行转换。首次暂存完整性检查曾误把第8–9步新增原始记录列入“不得暂存”范围；已修正为允许发布这些真实新记录，同时核对受保护源码、兼容副本和全部93项基准字节不变，暂存的理论正文也与原正文相同。远程原先没有本修订分支，本次首次发布完整修订历史。

Python解析检查点只需原 `requirements.txt`；独立SciPy核对及候选图像比较另依赖NumPy、SciPy和Pillow。历史第10–11步实际使用Python3.12.8，已验证版本列于[复现依赖](validation/numerical_scenarios/requirements_reproducibility.txt)：

```powershell
python -m pip install -r validation/numerical_scenarios/requirements_reproducibility.txt
```
