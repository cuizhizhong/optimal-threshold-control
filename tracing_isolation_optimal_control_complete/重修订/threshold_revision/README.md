# 常接触率统一证明修订包

底稿：`cuizhizhong/optimal-threshold-control`，提交 `496e454b34f7ce6861238041d5bd14b475e37917`。
修订目标文件：`tracing_isolation_optimal_control_complete/latex/main.tex`。

本包是一份可替换的统一主稿，不是将旧补充文件依次 `\input` 的拼接稿。未对 GitHub 或你的本地项目进行任何写入。

## 放回原工程

先保留原 `latex/main.tex` 的备份或建立 Git 分支。将本包的 `latex/main.tex` 放到原工程同名位置。
`latex/references.bib` 与底稿逐字节一致，可保留原文件；本包附带它是为了理论校样能够独立编译。
`latex/theory_only.tex` 为可选的校样入口，读取同一份新 `main.tex`，不会形成另一份证明版本。

保留原工程的 `figures/`、`data/`、`python/` 和 `matlab/` 目录。
本包不覆盖原图表、CSV、数值求解程序，也不删除旧补充目录。旧补充及旧 integration notes 不再是新主稿的证明依据或修改指令。

原工程的相对布局继续为：

```text
tracing_isolation_optimal_control_complete/
  latex/
    main.tex                # 用本包文件替换
    references.bib          # 内容与底稿相同
    theory_only.tex         # 可选的新入口
  figures/                  # 使用原工程已有的十张图
  data/                     # 保留
  python/                   # 保留
  matlab/                   # 保留
```

需要在原项目中保留本次核对程序时，将本包 `verification/` 与 `revision_notes/` 复制到上述项目根目录即可。

## 编译

在 `latex/` 目录执行：

```bash
latexmk -xelatex main.tex
# 或只编译同一源文件中的常接触率理论部分：
latexmk -xelatex theory_only.tex
```

没有 latexmk 时，使用 XeLaTeX、BibTeX、XeLaTeX、XeLaTeX 的常规顺序。
默认 `main.tex` 严格要求原图形存在；没有在交付源码里加入用占位图掩盖缺失文件的机制。

本次环境的 `bibtex` 符号链接失效，实际构建使用了同一安装中的 `bibtex.original`：

```bash
latexmk -g -xelatex -interaction=nonstopmode -halt-on-error \
  -e '$bibtex="bibtex.original %O %B";' theory_only.tex
```

这是本次环境的命令替代，不要求你的本地环境做同样修改。

## 文件与检查

`constant_theory_review.pdf` 是本次实际编译并逐页查看的 19 页常接触率理论校样，不是完整带图论文。

`revision_notes/CHANGELOG.md` 说明数学和表述层面的修改。
`revision_notes/PROOF_AUDIT.md` 列出证明依赖、关键量词和仍未证明的扩展。
`revision_notes/CHECKS.md` 区分符号、数值、源码、编译和版面检查。
`revision_notes/SOURCE_MAP.md` 给出底稿版本、原材料与新定理的对应关系及源码定位。
`checks/revision_results.json` 和各构建日志记录实际运行结果。

独立核对脚本需要 Python、NumPy、SciPy 和 SymPy：

```bash
python verification/verify_revision.py --output checks/revision_results_local.json
```

脚本不导入原工程解析求解器，不联网，不会覆盖论文或原数据。它不证明全局最优性、唯一性或无穷时域命题。

## 阅读定位

新主稿的定理 11.1 是全局最优性验证，定理 12.1 是几乎处处唯一性。
有限成本入安全集为引理 5.2，切换几何在第 8 节，统一分区在第 9 节，正则性及沿任意轨道的验证在第 10 节。

当前版本对既定常接触率模型已给出完整的解析证明文本，不保留旧 G1--G4 或局部 Lipschitz/终端条件作为未证假设。
这不等于经过形式化证明系统认证或独立同行审稿。时变问题、正则化极限和其他模型扩展的未完成证明在主稿中明确限定，不作为常接触率定理的结论。
