# 修订评阅入口

本分支交付五批修订（第0–11步）的源码、正文、编译产物和实际实验记录。评阅时以保存数据和执行报告为依据；执行计划、预期结构和 LaTeX 模板片段不属于已完成实验的结果。

## 建议阅读顺序

1. [执行计划](ai/codex_revision_plan/CODEX_EXECUTION_PLAN.md)：检查要求和证据口径。`latex_snippets/` 保留原始修订片段作对照，最终正文以 `latex/main.tex` 为准。
2. [执行状态](validation/numerical_scenarios/REVISION_STATUS.md)：五批的执行证据和历史记录。
3. [第8–9步实际结果](validation/numerical_scenarios/step89_results.md)与[第10–11步交付记录](validation/numerical_scenarios/step1011_results.md)：先读这两份较小的摘要，再按需查完整JSON和原始MAT文件。
4. [最终主文源码](latex/main.tex)、[主文PDF](latex/main.pdf)和[TheoryOnly PDF](latex/theory_only.pdf)：S1 主文实际编译为37页，理论版29页；保留三张主图和一个主表。S1 仅定稿符号，核对证据见[本批报告](validation/notation_s1_20261020/README.md)。
5. [MATLAB复现说明](matlab/numerical_scenarios/README.md)、[验证说明](validation/numerical_scenarios/README.md)及[实际命令](validation/numerical_scenarios/step1011_commands.md)：核对算法、来源、缓存和运行范围。

## 需要重点评阅的结论边界

- 默认35个不同配置全部有真实记录，求解器均返回成功。按求解前预定的原严格判据，numeric与agreement各通过29/35，同时通过28/35；按2026-10-10求解后调整的修订判据（状态/容量容差1e-5、容量段控制3e-3），分别为33/35、30/35，同时通过30/35。正文复现附录采用修订判据并写明原判据计数；修订判据不提供新的收敛证据，见[容差重评说明](validation/numerical_scenarios/tolerance_revision_20261010/README.md)。求解成功、数值接受、理论一致性和协议执行完成是不同判据。
- 七条至少一类诊断未通过的记录保留；E2/E4的原严格网格一致性仍失败。独立最细级比较没有覆盖这些失败，也没有把次细级容量违规改为可行。
- 五例预定主结果均通过两类浮点诊断。E4选中结果（负成本差3.68e-6、容量超出 $\varepsilon_K=7.70\times10^{-7}$）和E3的 $n=2000$ 记录（负成本差6.76e-5、$\varepsilon_K=7.83\times10^{-6}$，评估分类为`unresolved_discrepancy`）的负成本差，均小于把容量放宽为 $K+\varepsilon_K$ 后解析最优值的下降（1.16e-5、1.08e-4）。因此两者都与容量超出相容，不能据此声称发现了低于解析值的严格可行控制；原评估分类不变。
- 非理论初猜、有限网格和有限时域的结果不构成连续可行性、收敛定理或全局最优性的新增证明。$n=16000$、$T=600$和额外初猜未运行，未填入新结果。
- 第10–11步科学优化调用为0；本机候选检出复用35个可信缓存，另有1次独立小型接口smoke。依赖文件有实际哈希与跟踪核对；本轮没有在另一台机器重装环境。
- [运行异常清单](validation/numerical_scenarios/step1011_operational_anomalies.json)保留15类异常、警告和差异，包括首次编译溢出、长路径遗漏、检查器误判及图像元数据/微像素变化。

## 来源和文件范围

正式发布提交不会改变原始记录的 `solve_commit`、`solve_dirty`、求解时间或实际源码哈希。第10–11步报告中的原HEAD、候选快照及“尚未提交/推送”描述是发布前的执行快照；当前发布提交以Git历史为准，不能把它改写成数值结果的产生提交。

[MANIFEST](MANIFEST.txt)列出精确交付文件。本机临时检出、待删除归档、编译中间文件、Python缓存和正文修改前备份未纳入发布。完整JSON包含较多保存数组，评阅入口优先提供摘要和最终正文，完整证据仍保留。

发布前完整 `git diff --cached --check` 在25份原始日志中报告格式空白；源码、正文、说明和结构化数据的单独空白检查通过。原始日志保留尾随空格、控制字符和原有换行，仓库 `.gitattributes` 对第8–11步日志关闭换行转换。首次暂存完整性检查曾误把第8–9步新增原始记录列入“不得暂存”范围；已修正为允许发布这些真实新记录，同时核对受保护源码、兼容副本和全部93项基准字节不变，暂存的理论正文也与原正文相同。远程原先没有本修订分支，本次首次发布完整修订历史。

Python解析检查点只需原 `requirements.txt`；独立SciPy核对及候选图像比较另依赖NumPy、SciPy和Pillow。本轮实际使用Python3.12.8，已验证版本列于[复现依赖](validation/numerical_scenarios/requirements_reproducibility.txt)：

```powershell
python -m pip install -r validation/numerical_scenarios/requirements_reproducibility.txt
```
