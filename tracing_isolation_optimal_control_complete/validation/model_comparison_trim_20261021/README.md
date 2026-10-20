# 第二节局部精简：删除逐式文献对照

对应作者在主文原第5页的批注：模型节不需要技术报告式的逐式比较。本轮删除整个“与传播率控制的关系”段落，模型节在可行控制定义与二维问题说明后直接进入适定性分析。引言已有的机制差异和文献定位不扩写，B 尚未开始。

编译期间检测到另一个编辑将引理6.2证明中两行积分变量由 `tau` 改为 `v`。作者明确回复“是，可以一并提交这两行改名”，因此一并保留。除删除该段和这两行已授权改名之外，主稿其余内容与基线 `12509e6995af626c87f2fd09b3cce96127fd3b74` 逐字相同；控制问题、定理与数值含义未变。

实际命令从仓库根目录运行：

```powershell
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_comparison_trim_20261021/build.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_comparison_trim_20261021/build.py --attempt 2
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tracing_isolation_optimal_control_complete/validation/model_comparison_trim_20261021/build.py --attempt 3
python tracing_isolation_optimal_control_complete/ai/claude_revision_plan/checks/verify_new_notation.py
```

每次完整构建执行主文和 TheoryOnly 的 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX。首次构建成功；之后把复用构建器的临时输出隔离到本轮目录。第二次四阶段主文命令均成功，但发现源文件正在被并行修改，保护检查中止且未发布其 PDF。取得作者对两行改名的明确确认后，第三次完整构建成功，交付文件与 `attempt3/build_report.json` 的源文件和 PDF 哈希一致。所有尝试分别留档。

最终主文37页、TheoryOnly 28页，最终日志无错误、警告、未定义引用、缺字或溢出。原有28条符号恒等式全部通过；未新增测试。535个已有数据、评估、代码、图形等保护文件字节不变。优化器调用、新增科学求解均为0次。

主文与 TheoryOnly 均实际目视检查第4、5、9页，删除段落后的衔接及积分记号正常，无裁切、重叠或缺字。只检查上述页面，未声称检查全部37/28页。渲染使用 `pdftoppm -f PAGE -l PAGE -scale-to 1400 -png -singlefile`，完整参数见 `render_manifest.json`。

相对返修前的37/29页，主文页数不变、TheoryOnly 减少1页，来自删除比较段后的自然重排。没有放宽数学验收条件。提交标题为 `paper: 删除模型节逐式文献比较并统一积分变量`，提交号为本报告所在提交；文件列表见 `changed_files.txt`。不推送，保持 A1 作者审阅节点。
