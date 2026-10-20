# C3：受限跟踪能力可行域核查

日期：2026-10-21。范围：无回流、常接触率、正文参数 `c,gamma>0`、`0<beta<1`、`0<K<1`、`0<=qbar<=1`；只推导约束可行性，不做受限能力的成本最优综合。

本目录的 `c3_feasibility.tex` 是可直接合并的中文 LaTeX 片段，含命题、充分性与必要性的完整证明、切点和退化情形。未修改 `latex/main.tex`。依据：`REVISION_PLAN.md` v5 C3，`SYMBOL_TABLE.md` #13/#20，`REVISION_PLAN_v2_author.md` 附录 B，以及现稿 `eq:normalized-model`、`eq:constants`、`eq:value-definition`、`eq:qB`。

## 数学核查

- `varpi_qbar=beta+(1-beta)qbar>0`，`nu_qbar=beta(1-qbar)/varpi_qbar>0`（`qbar<1`），`d_qbar=gamma/(c varpi_qbar)>0`，且 `d_qbar=nu_qbar h_qbar`。
- 不变量导数精确为 `beta c (qbar-q)(s-p)i/varpi_qbar`。必要性仅在 `s>=h_qbar>=h>p` 的轨道段使用单调性；不能在整个状态域无条件声称它不减。
- 任意控制 `q<=qbar<1` 在 `s>h_qbar` 时感染非减且 `i>=i0`，并有 `s'<=-beta c i0 s`，故必在不超过 `log(s0/h_qbar)/(beta c i0)` 的有限时间到达 `s=h_qbar`。这补齐了必要性证明中不能只假定的到达性。
- 最大控制峰值是 `i0+nu_qbar(s0-h_qbar)-d_qbar log(s0/h_qbar)`；`s0<=h_qbar` 时峰值为 `i0`。因此最大控制给出充分性，任意受限控制的不变量单调性给出必要性。
- 曲边右导数 `-nu_qbar+d_qbar/s` 在切点为零，切点以右严格为负。

## 退化与物理域

- `qbar=0`：`varpi=beta,nu=1,d=h,h_qbar=h`，包络恰是无控制峰值条件，因此 `V_0=A`。
- `qbar=1`：另行用 `i(t)=i0 exp(-gamma t)` 得 `V_1=D`；不定义有限的 `h_1`。
- 主文物理域是正状态 `s>0,0<i<=K,s+i<=1`。所有辅助包络必须与它相交。包络非正的截面没有正感染可行初值。
- `h_qbar>=1` 时辅助曲边不在物理域内。更强的核查是：`h_qbar>=1-K` 即足以保证 `V_qbar=D`，即便 `h_qbar<1`。证明见片段中 `I_qbar(s)-(1-s)` 的导数。事实上，该条件也是 `V_qbar=D` 的必要条件：若 `h_qbar<1-K`，取 `h_qbar<s0<=1-K,i0=K` 即立刻超限。
- `i0=0` 是吸收轴，所有物理初值可行；不能按正感染包络排除它。主文正感染域本来不含此轴。
- 若额外扩充到 `s0=0`，则 `s=0,i=i0 exp(-gamma t)`，所有初值不超过 `K` 的轴点也可行；对数公式不在该轴使用。
- 对正文允许的任意 `0<beta<1`，证明无需 beta 与端点保持统一距离。核算包含 `beta=1e-8` 和 `beta=1-1e-10`，均为正文范围内的固定参数点；没有声称 `beta=0`、`beta=1` 的理论推广，也没有执行 C5。
- 固定 `c,gamma` 而 beta 很小时，`h` 增大；只要 `h_qbar>=1-K` 即转为整个物理域可行，不应外推一个虚假的物理曲边。`beta=0` 不在正文定义域，不能直接代入 `h=gamma/(beta c)`。
- `K=0` 时本文正感染初值域为空，`K>=1` 时容量约束对归一化物理域冗余；二者均不属于本命题采用的 `0<K<1` 假设。
- 本命题的可行性不预设有限成本。其最大常控制只是安全性见证；若 `qbar>0` 恒控制到无穷，该见证成本可以无穷。本文没有把它称为受限问题的最优策略。

## 实际执行

命令（从仓库根目录）：

```powershell
python tracing_isolation_optimal_control_complete/validation/geometry_proofs_20261021/c3_check.py
```

`c3_check_results.json` 是本轮实际产生的解析与 ODE 核对记录：

- SymPy 不变量导数恒等式残差：精确为 `0`。
- 27 个常控制 IVP 核对；包含物理曲边下方、曲边、曲边上方，`qbar=0`、`qbar=1`、接近两个能力端点、`h_qbar=1-K`、`h_qbar=1`、`h_qbar>1`、beta 接近正文参数边界等情形。
- 最大感染峰值误差为 `1.231209578733683e-12`（预定阈值 `2e-10`）。
- 6 组参数各 500 个物理截面核对 `h_qbar>=1-K` 时包络不低于物理上界。
- 常控制积分使用 `scipy.integrate.solve_ivp`，属于 ODE 初值问题核对；优化器调用次数 **0**，新增 OCP 求解次数 **0**。
- 初次脚本执行发现“包络上方”抽样点的微小扰动没有受 `i0<=K` 约束，因而触发样本合法性断言；已把扰动同时限制为 `(K-I_qbar(s))/4` 后重跑。该失败属于核查样本构造，不涉及包络公式或证明修改。已有原始数值记录未改写、删除或移动。

片段的集成编译与页面检查由主任务执行，不能把本目录的数学/ODE检查表述为已独立完成两稿编译。
