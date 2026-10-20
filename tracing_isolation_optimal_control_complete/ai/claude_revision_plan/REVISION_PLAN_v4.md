# 论文完善计划 v4（合并版，供 Codex 分步执行）

日期：2026-10-20

本版合并了以下三份材料：

1. **计划 v3**：`REVISION_PLAN_v3.md`，以作者与 ChatGPT 确定的 v2 为底稿，加入了 Claude 的 8 处修正。
2. **符号总表**：`SYMBOL_TABLE.md`，含 27 条冲突与改名建议。
3. **代码改名与重跑计划**：让代码使用与论文相同的符号，重跑全部 35 次优化，并与旧结果逐条对比。

**与 v3 的关键差异：** v3 §2.3 规定"代码层不改名，只在 README 加映射表"。本版改为在阶段 S2 中把代码改名并重跑，使代码、数据和论文使用同一套符号。S2 完成之前，现有映射表继续有效。

**执行入口：** Codex 先读 `START_HERE_CODEX.md`，再按本文件 §3 的步骤顺序执行。

---

## 0. 已完成的工作（不要重做）

| 提交 | 内容 |
|---|---|
| `52655cd` | 数值口径统一。并列报告原判据 28/35 与修订判据 30/35；用 $V_{K+\delta}$ 比较解释 E3、E4 的负成本差 |
| `44112cc` | 论文层符号迁移第一步：$p\to\beta$、$r\to p$、轨道下标改为上标、比较段的 $b_0=\beta c$；措辞改为"与容量超出相容"；README 加符号对照表。代码未改名 |

`ai/claude_revision_plan/checks/` 中已有的核算脚本可以直接复用：

| 脚本 | 用途 |
|---|---|
| `verify_new_notation.py` | 28 条关键公式的符号核对 |
| `migrate_notation.py` | 数学模式内的符号替换工具 |
| `symbol_inventory.py` | 符号清点 |
| `asymptotics_and_feasibility.py` | 小容量渐近与 $q\le\bar q$ 可行包络 |
| `return_checks.py` | 回流公式、$\lambda\to\infty$ 极限、R1/R2/R3 释放规则的初步仿真 |
| `theta_generalization.py` | $\theta=0$ 端点（即时回流）的二维计算 |
| `scaling_and_savings.py`、`mechanism_checks.py` | 量级与机制核算 |

---

## 1. 已确定的决定

### 1.1 模型与主线（同 v2/v3）

- 论文完整展示五仓室归一化模型 $(s,s_q,i,i_q,r)$，回流率 $\lambda\ge0$：
  $$\begin{cases}
  \dot s=-c[\beta+(1-\beta)q]si+\lambda s_q,\\
  \dot i=\beta c(1-q)si-\gamma i,\\
  \dot s_q=(1-\beta)cqsi-\lambda s_q,\\
  \dot i_q=\beta cqsi-\delta_q i_q,\\
  \dot r=\gamma i+\delta_q i_q,
  \end{cases}\qquad s+s_q+i+i_q+r=1 .$$
  其中 $\gamma=\delta_I+\gamma_I$。
- **解析主问题：** $\lambda=0$、常数 $c$、唯一控制 $q\in[0,1]$；成本 $J=\int_0^\infty\beta cq\,\mathrm dt$；约束 $i\le K$。此时五仓室与二维问题等价，$V_0(s,s_q,i,i_q,r)=U(s,i)$。
- **回流（$\lambda>0$）是扩展检验：** 不建立一般 $\theta$ 主定理。$\lambda=0$ 与 $\lambda=\infty$（即二维 $\theta=0$ 模型）作为两个可以精确求解的参照端点。
- **引言**用连续叙述，不放文献对比表；贡献集中为三项：
  1. 全域反馈与切换几何；
  2. 对全部可测可行控制的验证，以及提前离开容量的结构；
  3. 退化平台上的几乎处处唯一性。
- **$K$ 的含义**定义为社区非隔离感染负荷上限，不直接等同于 ICU 床位比例。

### 1.2 符号

以 `SYMBOL_TABLE.md` §0 的 27 条为准，**默认全部采纳**。作者若要排除某条，在该表对应行的"级别"列写"不采纳"；Codex 执行前读取并跳过这些行。

各条的执行位置：

| 执行位置 | 条目 |
|---|---|
| 阶段 S1：纯改名，独立提交 | #3、#4、#7、#8、#9、#10、#11、#12、#14、#15、#16、#17、#18、#20、#21、#22、#24、#25、#26、#27 |
| 阶段 A1：随五仓室改写 | #1（删除 $\beta_1,\beta_2$）、#2（$m\to s_q+i_q+r$，能力上限改为 $\bar q$）、#5（$\tilde s=s+s_q$）、#6（把 $P_0$ 提前为理论对象） |
| 写到对应内容时执行 | #13（$\bar q$ 下标的常数，阶段 C3）、#19（相对节省写成 $\Delta J/J_{\rm fill}$，阶段 D）、#23（$s_1^\circ$，阶段 D） |

### 1.3 代码

- **S2 之后**，代码与论文使用同一套符号：`par.p` 改为 `par.beta`，`geom.r` 改为 `geom.p`，`geom.e` 改为 `geom.s_e`，`geom.s_K` 改为 `geom.s_A`，`scenario_inputs.json` 中的 `"p"` 改为 `"beta"`；Python 检查点生成器同步修改。
- **旧记录保留，不删除、不移动。** 旧的 35 条原始记录及其评估留在原处（`run_index.json` 只追加不删除）。改名前打标签 `pre-code-rename`；历史阶段的验证脚本（第 6–11 步、容差重评）只针对该标签运行。

---

## 2. 关键事实与数值（执行时作为验收参照）

### 2.1 基准数值（$\beta=0.5,\ c=2,\ \gamma=0.3,\ K=0.15$）

- E2：$s_B=0.547695$，$J^*=1.529511$，相对纯容量填充节省 3.10%。
- E1：完全跟踪起点为 $(0.5102,\,0.1342)$。
- 五例 $J_{\rm ref}$：0.416186、1.529511、0.433981、1.268835、0.536233。

### 2.2 原判据与修订判据下的通过数

| 判据 | numeric_pass | agreement_pass | 同时通过 |
|---|---|---|---|
| 原判据 | 29/35 | 29/35 | 28/35 |
| 修订判据 | 33/35 | 30/35 | 30/35 |

### 2.3 小容量渐近（固定 $\beta$；已用 50 位精度核对）

- $s_B-h=K/\beta-(1-\beta)K^2/(\beta^3h)+O(K^3)$
- $\Delta J\sim K^2/(24\beta^4h^3)$
- $T_{+,\rm fill}-T_+^*\to1/(\beta\gamma)$

$\beta=0.155$ 时，首项要到 $K\lesssim10^{-4}$ 才准确。

### 2.4 回流

- **两个端点（E2）：**
  - $\lambda=0$：$J=1.5295$，$s_B/h=1.826$；
  - $\lambda=\infty$：$J=2.2385$，$s_B/h=1.518$。
- **旧的释放规则 R1 超限：**
  - $\lambda=1/14$ 时约 3.3%；
  - 在所测网格上最大值出现在 $\lambda=1/2$ 附近，约 13.4%；
  - 两端为零。
- **R2（允许重启）：** 可行，$\lambda=1/14$ 时成本增加约 8%。
- **R3（跟踪到 $P_0(\tilde s,i)\le K$ 才停）：** 小 $\lambda$ 时成本增加 67–69%，过于保守。

### 2.5 重跑代价

35 次求解原耗时合计约 22 分钟（中位数 16 秒，最长 140 秒）；加上评估、出图和导出，预计约 1 小时。

---

## 3. 执行步骤

### 适用于所有步骤的规则

- 每一步对应一次独立提交，提交信息写清"改了什么、怎么核对的"，末尾附上本仓库约定的 Co-Authored-By 行。**不得推送**。
- 每一步完成后都要实际编译：主文用 `build.bat`（或 XeLaTeX→BibTeX→XeLaTeX×2）；改动理论部分时，TheoryOnly 也按 README 的命令编译。日志不得有错误、未定义引用或溢出。
- 不改写、不删除 `data/numerical_scenarios/runs/` 下已有的原始记录和已有的评估文件。
- 只有 S2 和 E2 两步可以调用优化器；其余步骤调用次数必须为 0。
- 遇到"停止条件"时，停下并向作者报告，不要自行变通。
- 带"作者审阅"标记的步骤：完成初稿后提交，并在报告中列出需要作者决定的问题。
- MATLAB 在本机的路径为 `E:\software\Matlab\bin\matlab`，可用 `-batch` 运行；所有 MATLAB 命令从仓库根目录执行，并先执行
  ```matlab
  addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'))
  ```

---

### 阶段 S1：论文符号定稿（纯改名，不改内容）

**S1.1 读取决定**

- 读取 `SYMBOL_TABLE.md` §0，列出本步要执行的条目（§1.2 表中"阶段 S1"那一行，去掉作者标注为"不采纳"的条目）。

**S1.2 按条目做定点修改**

只在数学模式内修改，并限定在指定的环境范围内。可以扩展 `migrate_notation.py`，也可以逐处编辑。

| 条目 | 修改 | 范围 |
|---|---|---|
| #3 | $\lambda(y)\to\mu(y)$ | 仅 `lem:tracking-region` 的证明 |
| #4 | 残差 $D(s,i)\to\Delta_\Theta(s,i)$；医疗附录 $D(t),D_0,D_{\rm init}\to D_{\rm ICU}(t),D_{{\rm ICU},0},D_{\rm ICU,init}$ | 残差在第 7 节及引用处；医疗部分在附录 D。不要碰 `\Dcal` |
| #7 | 闭矩形 $R\to\Pi$；验证残差 $R^q\to\rho^q$ | 矩形在 `prop:regularity` 的证明中；残差在推论（验证等号条件）、注记和 `thm:unique-q` 中 |
| #8 | 配点区间数 $N\to n$ | 数值节；同时改 `export_numerical_latex.m` 中生成的 `$N=%d$` 文字 |
| #9 | 容量超出 $\delta\to\varepsilon_K$ | 改导出器生成文字；README、REVIEW_GUIDE 中的对应描述同步修改 |
| #10 | 点 $e\to s_e$ | 全文，只改斜体的点 $e$，不碰 `\e` |
| #11 | $s_K\to s_A$ | 全文 |
| #12 | 定理 3.1 证明中 $C\to\bar c$；附录 D 中 $C\to C_{\rm ICU}$ | 两处各自的范围 |
| #14 | `prop:Gamma-geometry` 证明中的 $L(s,\psi)$ 改写为 $\ln\Theta(s,\psi+\ell\ln s)$；附录 D 中 $L\to L_{\rm ICU}$ | — |
| #15 | $Q_K\to\mathcal Q_K$；时变节 $Q(t,s,i)\to\mathcal Q(t,s,i)$；`prop:regularity` 证明中的小矩形 $Q\to\Pi_0$ | 反馈 $Q^*$ 保留 |
| #16 | 一维策略族参数 $\sigma\to s_c$；$F_{x_0}\to\mathcal J_{x_0}$；$i_w(\sigma)\to i_w(s_c)$ | 仅"一维切换成本"小节及 `cor:one-dimensional-min` |
| #17 | $\iota(\xi)\to i_{\rm nat}(\xi)$ | `lem:waiting-HJB` |
| #18 | 定理 3.1 中的积分变量 $\tau\to v$；时变节的时间变换 $\tau(t)\to\vartheta(t)$；$\tau_A\to\tau_{\mathcal A}$ | 三处各自的范围 |
| #20 | $I_z\to\mathcal I_z$、$I_\Gamma\to\mathcal I_\Gamma$ | 全文（作者可标"不采纳"） |
| #21 | $f_q\to f(x,q)$，相应的 Lie 导数写法 | 全文（作者可标"不采纳"） |
| #22 | `\epsilon` 改为 `\varepsilon` | 全文 |
| #24 | 医疗核 $\kappa(a)\to\kappa(\theta)$ | 附录 D |
| #25 | 容量迹 $b(s)\to U_K(s)$ | `lem:trajectory-verification` 与 `prop:regularity` |
| #26 | 部分分式系数 $A,B\to A_1,A_2$ | 附录 B |
| #27 | 拼接梯度 $P\to\mathbf P$；局部坐标 $y_1,y_2\to\zeta_1,\zeta_2$ | `prop:regularity` 的证明 |

**S1.3 核对**

- 更新并运行 `verify_new_notation.py`（只需更换改了名的量），全部为 True。
- 运行 `symbol_inventory.py`，确认上表中的旧记号不再出现在相应范围内。
- 导出器回归测试 `verify_saved_result_exporter`、`verify_revision_exporter`、`verify_pending_result_exporter` 全部通过；用 `export_numerical_latex()` 重新导出（优化器 0 次）。
- 主文和 TheoryOnly 编译通过。

**S1.4 文档与提交**

- README 符号对照表补上本步的改名。
- 提交信息："refactor: 论文符号定稿（S1，SYMBOL_TABLE 条目 …）"。

**停止条件：** 任何一条公式核对为 False；编译失败；某个旧记号在指定范围外也出现、无法判断其含义。

---

### 阶段 S2：代码改名并重跑全部优化

**S2.1 打标签与清点**

- 在 S1 的提交上打标签 `pre-code-rename`。
- 清点代码中所有要改的名字，写成清单 `ai/claude_revision_plan/code_rename_inventory.md`，列出文件、行号、旧名、新名和含义。范围：
  - `matlab/numerical_scenarios/*.m`（目前有 14 个文件使用 `par.p` 或 `geom.r`）；
  - `revision_validation_config.m` 中对参数结构的断言；
  - `validation/numerical_scenarios/scenario_inputs.json`；
  - `generate_analytic_checkpoints.py`、`test_analytic_checkpoints.py`。

  `verify_stage89_integrity.py` 等历史阶段脚本**不改**，在其文件头注明"只针对标签 `pre-code-rename` 运行"。

**S2.2 改名**

- 映射：`par.p`→`par.beta`；`geom.r`→`geom.p`；`geom.e`→`geom.s_e`；`geom.s_K`→`geom.s_A`；JSON 键 `"p"`→`"beta"`；Python 中的 `self.p`→`self.beta`、`geo.r`→`geo.p` 等。
- 只改名，不改任何运算或运算顺序。
- 给保存数据的读取路径加一个旧格式适配：读到旧记录里的 `p` 时显式映射为 `beta`，并加注释说明。

**S2.3 解析检查点**

- 运行 `generate_analytic_checkpoints.py --write` 重新生成检查点，再运行 `--check` 和 `test_analytic_checkpoints.py`。
- 新旧检查点的数值必须逐项相同（允许的相对差不超过 $10^{-12}$），只有键名不同。

**S2.4 重跑（唯一允许调用优化器的步骤之一）**

```matlab
revision_preflight();
run_revision_validation('unit', false);
run_revision_validation('all', false);
```

因为求解源码哈希改变，缓存会全部失效，应实际执行 35 次求解。记录实际求解次数、缓存命中次数和总耗时。

**S2.5 新旧逐条对比**

- 新写脚本 `matlab/numerical_scenarios/compare_rerun_results.m`（不放进任何指纹清单），按 `configuration_id` 配对：旧 run_id 取自标签 `pre-code-rename` 下的各组摘要，新 run_id 取自当前摘要。
- 比较项：
  - `return_status`、迭代次数；
  - `J_openocl`；
  - 控制数组与状态数组的最大绝对差；
  - 事件区间；
  - `numeric_pass`、`agreement_pass`；
  - 观测到的阶段结构。
- 结果写入 `validation/numerical_scenarios/rerun_<日期>/comparison_report.json` 和一份简短的 `README.md`。
- **通过标准：** 结构、标志和事件完全一致；成本相对差 $\le10^{-10}$；数组最大差 $\le10^{-8}$。

**S2.6 原判据重评**

- 仿照 `refresh_tolerance_assessments.m`，对新的 35 条记录用原判据（状态与容量容差 $10^{-6}$、容量段控制容差 $2\times10^{-3}$）再评估一次，并生成新的判据对照报告。
- `export_numerical_latex.m` 中 `original_criterion_text` 改为读取这份新报告。

**S2.7 刷新产物**

- `make_numerical_figures(); export_numerical_latex();`
- 运行 3 个导出器回归测试，编译论文。
- 正文数值宏应与重跑前逐字相同；只有措辞或已改名的符号可以不同。

**S2.8 文档**

- README 的"符号对照"一节改为"历史数据字段对照"：说明标签 `pre-code-rename` 及之前保存的 JSON/MAT 中，`p` 表示 $\beta$，`r` 表示 $p$；当前代码与论文一致。
- `matlab/numerical_scenarios/README.md` 中"不要改名"的提醒改为说明这次重跑。
- 在 `MANIFEST` 和 `REVIEW_GUIDE` 中登记新的 run_id 与对比报告。

**S2.9 提交**

- 提交信息："refactor: 代码符号与论文统一并重跑 35 次优化（S2）"，写明求解次数、对比结论、原判据和修订判据下的计数。
- 新的原始记录与评估文件一并提交。

**停止条件：**

- 预检失败（OpenOCL 或 CasADi 环境不可用）；
- 实际求解次数不是 35；
- 对比超出通过标准：哪怕只差 $10^{-9}$ 也停下报告，不要自行放宽标准；
- 原判据或修订判据下的计数与 28/35、30/35 不同。

---

### 阶段 A1：五仓室模型改写

**任务**

- 模型节改写为 §1.1 的五仓室模型：写明守恒关系、$\gamma=\delta_I+\gamma_I$ 的聚合、$r$ 的含义（$i+i_q$ 不含已进入 $r$ 的住院者），以及 $K$ 是社区负荷上限。
- 加一个短命题：$\lambda=0$ 时，$V_0=U(s,i)$。
- 执行符号条目：
  - #1：删除 $\beta_1,\beta_2$ 和"双传播系数"的说法，相关反演小节压缩为一两句；
  - #2：$m\to s_q+i_q+r$，注 2.2 中的 $q_{\max}\to\bar q$；
  - #5：引入 $\tilde s$，在回流部分使用；
  - #6：把 $P_0(s,i)$ 定义在第 4 节，安全集写成 $\mathcal A=\{P_0\le K\}$。
- 题名改为《感染阈值约束下跟踪隔离的全域最优控制》（作者可另定）；同步修改 `pdftitle` 和页眉。
- 引用 Zhou 2024 时注意：其第 5 页的"波次短"理由针对的是 $R\to S$，不能作为隔离易感者不回流的依据。

**核对：** 编译；`verify_new_notation.py`；人工通读模型节。

**提交：** "paper: 五仓室模型与二维等价（A1）"。

**作者审阅：** 模型节的表述。

---

### 阶段 B：引言与贡献（作者审阅）

- 引言按"控制问题 → 最接近的研究（MSW、Angulo、Freddi 系列）→ 跟踪动力学的差异 → 本文结果"的顺序连续叙述。
- 准确承认先例：Angulo 的 final push、MSW 与 FGLX 的候选函数验证、AFG 的分区方法；"不用 PMP"只作为方法特点说明，不列为贡献。
- 引言末尾写三项贡献，每项对应正文的定理或命题编号。
- 摘要先写骨架；效应量级和回流部分等阶段 D、E 完成后再写实。
- 参考文献补充：
  - Freddi–Goreac, JCA **31(2)**, 525–562 (2024)；
  - Freddi–Goreac–Li–Xu, AMO 86:23 (2022)；
  - Kretzschmar 2020；
  - Morris 2021。

  三篇 Freddi 系列论文各自独立著录。
- **提交：** "paper: 重写引言与贡献（B）"。

---

### 阶段 C：几何与证明整理

**C1 两层分区**

- 先给出 $\mathcal A$、$\mathcal A^0$、$\mathcal V_{\bar q}$ 的定义，再介绍成本最优分区。
- $\mathcal A^0=\mathcal A$ 由现有的 `lem:safe-invariant` 改写；$\mathcal V_1$ 等于整个物理约束域。
- 相图 N1 改成两层，图例中区分 $s=h$ 与 $s+i=1$ 的线型。

**C2 主结果前置**

- 在模型节之后放"主结果概览"：定理陈述、相图和阶段表。
- 标准实分析引理（绝对连续函数的水平集、Lipschitz 复合）改为引用教材；局部梯度拼接的长计算移入附录。

**C3 受限跟踪能力的可行域命题**

- 按 `REVISION_PLAN_v2_author.md` 附录 B 写成短命题，使用 #13 的 $\bar q$ 下标记号：
  - 包络 $\mathcal I_{\bar q}(s)$：充分性用 $q=\bar q$，必要性用 $F_{\bar q}$ 的单调性；
  - $q_B\le\bar q$ 当且仅当 $s\le h_{\bar q}$；
  - 核查各种退化情形。
- 可以用 `asymptotics_and_feasibility.py` 的包络仿真作数值核对。

**C4 机制短说明**

- 在 $s>p$ 上写出 $\beta cq\,\mathrm dt=-\beta\,\mathrm d\Phi/(i(s-p))$，说明 $\Theta$ 匹配就是沿免费等待方向的边际成本为零。
- 写明"容量线上单价上升"只是直观线索；方法上归功于 Angulo 的不变量坐标。

**C5（可选）$\lambda=\infty$ 端点的严格性**

- 逐条核对主定理在 $p\to0$（即 $\theta=0$ 模型）时是否成立。
- 若成立，在讨论中写一则注记；若不成立，只保留数值事实。

**提交：** C1–C4 一次提交，C5 单独提交。

---

### 阶段 D：效应量级、渐近与参数来源

**D1 比较基准**

- 精确定义"纯容量填充"。
- 分开报告：$\Delta J$、$\Delta J/J_{\rm fill}$（#19）、正控制时长 $T_+$、退出位置。

**D2 小容量命题**

- 写出 §2.3 的三式和适用条件，完整证明放在附录：
  - 初值族 $i_0(K)\le K$，且 $s_1(K)\to s_1^\circ>h$（#23）；
  - 固定 $\beta>0$。
- 正文写明首项只给标度，并说明它在小 $\beta$ 时的精度限制。

**D3 参数来源表**

- 区分三类参数：示例参数、文献拟合参数、作者新拟合参数。
- Zhou 2024 的西安拟合：$\gamma=0.1998+0.1006=0.3004$；注明其基线追踪 $q_0\ne0$ 与本文"$q=0$ 为无控制"的定义差异。
- He–Tang–Xiao 2023 拟合的 $\beta$ 约为 0.13–0.25。

**D4 扫描与出图**

- 扫描 $K\times\beta$（同时固定 $\beta c$ 与 $\gamma$）。
- 极小的差值用高精度计算，不用两个双精度总成本相减。

**完成：** 脚本放入 `validation/` 下新开的子目录；提交 "paper: 量级与小容量渐近（D）"。

---

### 阶段 E：回流、安全退出与实施误差

**E1 前向仿真实验（不调用优化器）**

- 在新目录 `validation/return_experiments/` 中正式实现 R1、R2、R3 三种释放规则：使用事件检测和步内峰值。
- $\lambda$ 网格为 $\{0,1/28,1/14,1/7,1/2,5,\infty\}$，其中 $\infty$ 用二维 $\theta=0$ 模型计算。
- 报告：超限幅度、成本、正控制时长、滑动段长度、解除时的 $s_q$。
- 验收：$\lambda=0$ 时复现基准 $J=1.5295$；结果与 §2.4 的初步数值一致到第二位有效数字。

**E2 低维策略族优化**

- 策略结构为"等待 → $q_B$ → 完全跟踪 → 沿旧安全边界以 $q_{\rm eq}$ 滑动 → 解除"，以少数切换参数为自变量，在 $(s,s_q,i)$ 上优化。
- 结果是 $V_\lambda$ 的可行上界，与 R2 比较。
- 完整的三维 OCP 列为增强项：只有在低维族与 R2 差距明显时才做；做的话需另行提交并说明终端处理。

**E3 安全诊断与证书**

- 写入两条推导：旧的无裕度释放在 $\lambda>0$ 时必然超限（`REVISION_PLAN_v2_author.md` 附录 A.1）；$P_0(\tilde s,i)\le K$ 是充分安全证书（同文件附录 A.2）。
- 写明该证书很保守，不作为重新优化的主要终端条件。

**E4 参数失配与设计裕度**

- 冻结名义反馈，在真实参数偏离时检验；用 $K_{\rm design}=(1-\varepsilon)K$ 加设计裕度。
- 与 R2 型边界滑动画在同一张图上比较成本。

**E5 成本扰动（可选）**

- 混合成本 $J_\omega=\int\beta cq(1+\omega i)\,\mathrm dt$，只在单参数策略族内计算。

**提交：** E1–E4 分开提交；正文新增"回流与实施稳健性"一节（作者审阅）。

---

### 阶段 F：数值证据与呈现

- 正文图表：
  1. 两层相图；
  2. 代表性时间序列；
  3. 成本与约束误差表（带符号成本差、最大容量超出 $\varepsilon_K$、$V_{K+\varepsilon_K}$ 对照）；
  4. 量级图；
  5. 回流分面图：左为 R1 超限随 $\lambda$ 的变化，右为各规则的成本，画出 $\lambda=0$ 与 $\lambda=\infty$ 两条参照线。
- 写明 $T=300$ 的配点加尾段检查只是一种终端处理，不等同于无穷时域问题。
- 日志、全部网格、判据修订和异常追踪移到补充材料；正文用一小段概括剩余残差。
- 半拉格朗日全域网格作为增强项：只有当存在具体的验证缺口时才做。
- **提交：** "paper: 数值章节重写（F）"。

---

### 阶段 G：全文定稿（作者审阅）

- 正文结构：
  1. 引言
  2. 五仓室模型与控制问题
  3. 主结果与两层几何
  4. 最优策略的构造与证明
  5. 机制与量级
  6. 数值结果
  7. 回流与实施稳健性
  8. 讨论
  9. 附录
- 时变接触率、正则化、联合控制三部分压缩为讨论中的段落；删除重复的防御性陈述，只保留一次适用范围说明。
- 3.10% 移到结果部分并写明比较基准。
- 结论中区分三类结果：无回流的严格最优性、两个端点的结论、有限 $\lambda$ 的数值表现。
- 投稿前清理：作者栏、日期、PDF 元数据、开发注释；中文定稿后再统一转成英文。
- 按 `REVISION_PLAN_v2_author.md` §12 的清单逐项核对。

---

## 4. 建议的提交顺序

```
S1 → S2 → A1 → B → C → D ┐
                    E1 ──┴→ E2–E4 → F → G
```

- D 与 E1 可以并行。
- S1、S2 必须在所有内容修改之前完成，之后所有新文字和新代码都直接使用最终符号。

## 5. 相关文件

| 文件 | 用途 |
|---|---|
| `REVISION_PLAN_v3.md` | 上一版计划，含 Claude 的 8 处修正和初步数值 |
| `REVISION_PLAN_v2_author.md` | 作者与 ChatGPT 确定的底稿（复制自 `C:\Users\cui\Desktop\ai\REVISION_PLAN_v2.md`），含 §11 文献用途、§12 检查清单，附录 A、B 的推导 |
| `SYMBOL_TABLE.md` | 符号总表与 27 条决定 |
| `START_HERE_CODEX.md` | 给 Codex 的分批执行指令 |
