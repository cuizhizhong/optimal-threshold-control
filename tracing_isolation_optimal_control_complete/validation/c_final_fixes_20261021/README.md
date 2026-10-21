# C 阶段收尾的三处修正

基准：`6b50f2b`，分支 `codex/numerical-reproducibility-revision`。本地提交，不推送。

## 修改范围

- **定理 3.1**：补回"分区反馈 $Q^*$ 实现最优值"。上一轮拆分时漏掉了这一句。现在定理写明：沿闭环轨道 $x^*$，控制 $q^*(t)=Q^*(x^*(t))$（至多有限个切换时刻除外）满足 $J_{x_0}(q^*)=U(x_0)=V(x_0)$。证明增引命题 `prop:candidate-attainment`，该命题给出 $q^*$ 是反馈的 Carathéodory 轨道且成本为 $U(x_0)$。
- **第 15 节**：E2 例子写明"图 1 中初值为 $(0.99,0.01)$ 的 E2"，使 TheoryOnly 版（无数值节）的读者也能定位该例。
- **图 1**：主图选区框改为与放大图相同的范围 $s\in[0.42,0.60]$、$i\in[0.10,0.153]$（原选区框上沿为 0.166）。为让 $s_B$ 标签的下标不压到新的框上沿，$h$、$s_B$ 两个标签改为底边对齐在 $i=0.1545$。其余内容、样式和几何不变。

新脚本 `make_optimal_partition.py` 以 `validation/polish_mechanism_20261021/` 中的版本为底稿，旧脚本不改。新增一项核查：原脚本只检查文字与曲线（Line2D）的相交，不覆盖选区框（Rectangle），新脚本另外检查主图全部文字框与选区框四条边是否相交。

## 命令与结果

从项目目录执行：

```bash
python validation/c_final_fixes_20261021/make_optimal_partition.py --attempt 1
python ai/claude_revision_plan/checks/verify_new_notation.py
```

- 图 1 脚本的全部断言通过：
  - 几何检查点最大差 1.11e-16，切换点 Θ 残差 3.55e-15，$s_e$ 端点方程最大残差 9.71e-17；
  - E1/E2 轨道端点和 E2 成本与上一版一致，节省比例 3.0965%；
  - 文字与曲线、文字与文字、文字与选区框边的相交均为 0；
  - FigN1_regions、FigN2、FigN3 字节不变。

  覆盖前后的 SHA256 见 `analytic_checks.json`。
- 符号恒等式 28/28 通过。
- 两个自动生成数值块与 `6b50f2b` 逐字相同。
- 主文与 TheoryOnly 各执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，全部退出 0。最终页数为 42 和 32，与基准相同。最终日志没有错误、警告、未定义引用、缺字或溢出；最终 log/blg 保存在本目录。
- 以 80 dpi 渲染主文第 7、8、28 页目视检查：定理 3.1、图 1 和第 15 节的例子显示正常。

本轮 MATLAB、优化器和新增 OCP 求解均为 0 次。
