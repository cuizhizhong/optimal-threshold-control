# 数学定点修订与 Codex 交接

本包落实已讨论的数学补写，不加入右连续控制相容性推论。原模型、运行成本、全部可测可行控制、候选分区和几乎处处唯一性结论保持不变。

## 合并基线

- 仓库：`cuizhizhong/optimal-threshold-control`
- 分支：`codex/integrate-theory-revision`
- 本轮实际读取的分支提交：`f33f8b591cefb8226e2c4196d739b841c368fb47`
- 目标：`tracing_isolation_optimal_control_complete/latex/main.tex`
- 基线文件 Git blob：`51aaa6b923b92f22a7039b42bab713cf46264530`

通过 GitHub 连接重新读取分支引用及该提交的文件元数据；会话中已挂载的 `main.tex` 经 Git blob 哈希核对，与仓库文件逐字节一致。修订由这个已核对副本生成，不是从聊天片段重建正文。

## 文件用途

| 文件 | 用途 |
|---|---|
| `tracing_isolation_optimal_control_complete/latex/main.tex` | 完整修订稿，不需要再拼接任何补充 `.tex` |
| `math_revision.patch` | 只修改仓库中 `latex/main.tex` 的 Git full-index 补丁 |
| `tracing_isolation_optimal_control_complete/latex/references.bib` | 与基线逐字节相同，仅为方便检查而附带；无文献增删 |
| `base/main.tex` | 本补丁的原始输入，可供三方比对；不是最终稿 |
| `base/references.bib` | 未修改的参考文献检查副本 |
| `revision_notes/CHANGELOG.md` | 改动范围和定位 |
| `revision_notes/PROOF_CHECK.md` | 新增推导及其依赖关系的人工核对说明 |
| `revision_notes/CHECKS.md` | 本轮实际执行的检查和未执行事项 |
| `checks/check_revision.py` | 本轮检查入口；包括原有公式回归与新增分区样本 |
| `checks/check_report.json` | 本轮实际运行结果；不是之前的旧日志 |
| `MANIFEST.json`、`SHA256SUMS.txt` | 输入、输出和文件完整性记录 |

本包不是完整数值工程，没有重复打包原图、CSV、MATLAB 文件或参考书 PDF。合并和全文编译应在已有原工程中进行。

## 推荐合并流程

先把本包解压到仓库以外的目录。在仓库根目录检查当前状态和目标文件：

```bash
git status --short
git rev-parse HEAD
git hash-object tracing_isolation_optimal_control_complete/latex/main.tex
```

不要覆盖未提交改动。若目标文件 blob 与上述基线一致，可直接检查并应用补丁：

```bash
# PATCH_FILE 替换为解压后的补丁绝对路径。
PATCH_FILE=/absolute/path/threshold_math_revision_v2/math_revision.patch
git apply --check "$PATCH_FILE"
git apply "$PATCH_FILE"
git diff --check
git diff -- tracing_isolation_optimal_control_complete/latex/main.tex
```

若目标文件 blob 已变化，先比较本包 `base/main.tex`、当前本地文件与修订稿，只合并相关改动；不得整份覆盖掉新内容。若目标文件已等于 `MANIFEST.json` 中的修订 blob，则无需重复应用。`base_commit` 是仓库原有提交，`revised_git_blob` 仅是修订文件内容哈希，不是已经提交到 GitHub 的新提交。

补丁已经在临时 Git 仓库中通过 `git apply --check`、实际应用、输出逐字节比对、反向恢复及 `git diff --check`。这不保证将来所有已修改工作树都能无冲突应用。

## 编译交接

本轮按分工仅交付数学源码和检查文件，没有运行 XeLaTeX/BibTeX，也没有生成新的 PDF。保留原工程的 `figures/` 和构建文件，从原 `latex/` 目录编译，例如：

```bash
cd tracing_isolation_optimal_control_complete/latex
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

若无 `latexmk`，使用原工程的 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX 流程。新增编号由 LaTeX 自动更新，不能手工按旧 PDF 的数字替换交叉引用。注意原有 PDF、`.aux`、`.bbl`、`.toc` 和旧检查日志不自动代表本次修订的结果。

## 给本地 Codex 的任务说明

> 请在现有工程中合并本包的 `math_revision.patch`。先检查工作树和目标文件 blob；若目标已偏离 `f33f8b5` 的原稿，按 `base/main.tex`、当前文件和新稿做三方比对，保留无关本地改动。只合并这轮数学补写和相应措辞，不添加右连续控制相容性推论，不改变模型、线性成本、可测控制类、候选分区或几乎处处唯一性的结论。然后在原工程中检查交叉引用并编译完整 PDF，报告实际错误和警告。排版问题优先只调整断行和环境；若必须改数学内容，单独列出原因及差异，不得为消除报错而删除证明步骤。不自动提交或推送。

## 复跑本包检查

在具备 Python 3.10+、Git 和所列 Python 依赖的环境中，从本包根目录运行：

```bash
python -m pip install -r checks/requirements.txt
python checks/check_revision.py
```

该命令重新写入检查报告与标签定位文件；运行后的日志哈希自然不再与交付时 `SHA256SUMS.txt` 一致。原始公式回归代码 `checks/verify_revision.py` 从上一修订包原样复用；请使用本轮入口 `check_revision.py`，它明确检查本包的新稿路径。
