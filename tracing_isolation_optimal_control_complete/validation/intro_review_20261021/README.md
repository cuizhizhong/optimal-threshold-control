# B 作者审阅修订

基线 `80074ec37c0827e38552f3255f46a1a73a223cc4`。落实作者收到 B 初稿后的三项意见，并补齐两篇开放获取参考文献。此报告所在提交为本轮 B 修订独立提交；不推送。

引言补明 AFG 定理5.6/注5.7(2)的时间几乎处处唯一性，以及 Angulo 图3b在干预能力受限时提前启动的先例。本文的提前完全跟踪另以 `q=1` 时 `dot i=-gamma i<0` 和成本比较解释；唯一性难点明确为容量平台上的整个 `[q_B(s),1]` 点态极小区间。摘要恢复“始终维持感染阈值直至自然感染增长阈值并非最低成本的选择”，删减定理技术清单。

式 `eq:linear-cost` 后仅补两行说明 `b0=beta c`、`b=beta c(1-q)`、`beta c q=[b0-b]_+`，说明该系数代表非隔离感染生成项的传播系数削减，与 MSW 成本同形；保留不按实际隔离人数计费的说明。引言首段补入已有文献引用。没有改动 tau/v、状态方程、控制约束、理论证明或数值记录；作者栏与日期留到 G。

## 实际核对

从项目目录实际执行：

```powershell
python validation/intro_review_20261021/audit_revision.py
python ai/claude_revision_plan/checks/verify_new_notation.py
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/intro_review_20261021/build_revision.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/intro_review_20261021/render_qa.py
git diff --check
```

- 范围、来源承认与记录保护审计 14/14 通过；既有符号恒等式 28/28 为 True。
- 主文与 TheoryOnly 各实际执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，8/8 进程退出0，页数仍为38/29；两份最终日志无错误、警告、未定义引用、缺字或溢出。
- 主任务目视主文1–5、37页；独立任务目视TheoryOnly1–5、28页。文字、公式、引用及跨页正常，见 `b_visual_review.md`。渲染清单另包含两稿全部参考文献页。
- 535个既有原始数据、评估、代码及图形文件哈希不变。优化器调用0、新增OCP求解0、MATLAB调用0。

## 参考文献与远程核查

新增 `ref/Morris2021_epidemic_control.pdf` 和 `ref/Kretzschmar2020_contact_tracing_delays.pdf`，均为8页正式版本。前者来自出版社，CC BY 4.0；后者在出版社、PMC及作者机构入口受403限制后，从 Bordeaux 大学的公开文献库获取，CC BY-NC-ND 4.0。没有绕过付费或登录限制。题名、作者、DOI、版本、许可证、来源URL、下载状态及SHA-256见 `reference_sources.json`；首尾页已实际目视。

只读实时确认仓库为 public。核查时本地HEAD为80074ec，工作分支远程为b039bdc，ahead/behind=21/0；全部四个远程分支均不含B提交，GitHub按完整SHA查询亦未找到该提交。故B全文提取尚未随该提交发布到远程。完整只读证据见 `remote_visibility.json`。本轮保留未推送历史和已有全文提取记录，不改写历史、不推送；以后发布前须另行明确这些全文材料的范围。

## 参照差异与后续范围

与B初稿相比页数不变，新增两份参考PDF；原理论和数值含义未变。没有触发公式或编译停止条件。作者已经审阅B并给出具体修改意见，本提交落实后继续原请求的C1–C4；第一项贡献将随C主结果前置同步引用新总定理。C5、D、F、G和新增优化均未因本轮审阅而获得执行范围。

完整本次提交路径见 `changed_files.txt`，构建源及PDF指纹见 `attempt1/build_report.json`。
