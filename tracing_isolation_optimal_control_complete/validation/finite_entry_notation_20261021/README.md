# 有限入集引理的积分变量补漏

将 `lem:finite-entry` 证明三个积分中的哑变量 `\tau` 统一为 `v`，同步更新 `s(v)`、`q(v)` 和 `\dd v`；引理陈述与后文的首达时刻 `\tau_{\Acal}` 保留。数学变化仅为两行纯改名，精确补丁为 `finite_entry.patch`，基线提交为 `12509e6`。独立只读复核通过；没有运行 MATLAB、优化器或新增科学求解。

实际执行 `E:\anaconda\python.exe -X utf8 -I tracing_isolation_optimal_control_complete/validation/finite_entry_notation_20261021/verify_and_build.py`，主文与 TheoryOnly 各完成 XeLaTeX → BibTeX → XeLaTeX × 2，8/8 命令退出 0。主文 37 页、TheoryOnly 28 页，最终日志无错误、未定义引用、缺字或溢出。两稿修改处均在第 9 页，已分别渲染并目视检查，三个积分、微分、首达记号及版面正常。

检查期间工作区另有模型节“与传播率控制的关系”20 行删除及两份 PDF 更新。本步保留这些改动，只在 Git 暂存区应用 `finite_entry.patch`，没有将删段或两份既有 PDF 纳入本提交。双编译针对当前工作区全文（包括该删段），其源码 SHA-256 与完整未提交来源差异保存在 `build_report.json`，因此这里的 28 页不冒充仅两行补丁对应的独立提交构建结果。

编译 PDF 和第 9 页图像放在 `tmp/finite_entry_notation_20261021/`，没有覆盖正式 PDF；构建前后的两份正式 PDF 哈希不变。本次没有修改既有数值记录、评估、判据、脚本或正文其他部分，没有推送。
