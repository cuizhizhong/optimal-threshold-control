# He, Tang & Xiao (2023) — TDINN 结构化笔记

> 本文件是对 Project 中 `He_Tang2023PCB.pdf` 的结构化文本整理，供检索/引用使用（读它比读原 PDF 省 token）。
> 数学公式与数值均转录自原文；个别 OCR 不确定处已注明，**精确复现时以原 PDF 为准**。

---

## 1. 文献元信息

- **标题**：Combining the dynamic model and deep neural networks to identify the intensity of interventions during COVID-19 pandemic
- **作者**：Mengqi He¹, Sanyi Tang¹, Yanni Xiao²（*通讯：yxiao@mail.xjtu.edu.cn*）
  - ¹ School of Mathematics and Statistics, Shaanxi Normal University, Xi'an
  - ² School of Mathematics and Statistics, Xi'an Jiaotong University, Xi'an
- **期刊**：PLOS Computational Biology, 19(10): e1011535
- **DOI**：https://doi.org/10.1371/journal.pcbi.1011535
- **日期**：Received 2023-04-06；Accepted 2023-09-20；Published 2023-10-18
- **开源代码/数据**：https://github.com/lebesguehmq/TDINN_rate_functions
- **实现**：Python + TensorFlow；优化器 Adam（learning rate 0.001）

---

## 2. 核心贡献（一句话）

提出 **TDINN（transmission-dynamics-informed neural network）**——把 SIR 型传播动力学模型编码进物理信息神经网络（PINN），**无需预先假设 contact rate c(t) 和 quarantine rate q(t) 的具体函数形式**，直接从多源疫情数据中反推出这两个时变速率，再从一族候选函数中挑选最优函数拟合、赋予可解释性。

---

## 3. 研究背景与动机

- 传统仓室模型常把 contact rate、quarantine/isolation rate 设为**常数**或**预设的特定时变函数**来刻画干预强度；预设函数不一定能准确刻画持续调整的干预策略，且引入过多参数，给数据拟合与参数估计带来困难，结果还依赖所假设的函数类型。
- 纯数据驱动的统计/深度学习方法（ARIMA、XGBoost、LSTM、CNN 等）缺乏传播机制约束，**可解释性差**，难以为优化防控策略提供依据。
- 本文用 PINN 思路：把时变参数用独立神经网络表示，并把流行病 ODE 系统的残差加入损失函数，让网络"遵守"传播动力学规律 → 兼顾拟合能力与可解释性。

---

## 4. 传播动力学模型

在 SIR 基础上加入 contact tracing 与 isolation。人群按是否被隔离分层：自由区（社区）易感 `S`、感染 `Ic`；隔离区易感 `Sq`、感染 `Iq`；移出 `R`（不再区分自由/隔离区）。

- `c(t)`：时变 contact rate；`q(t)`：时变 quarantine rate；`β`：每次接触的传播概率；`N`：区域总人口；`γ`、`δq`：社区/隔离区感染者的康复率。
- 被隔离者若感染进入 `Iq`（率 `βc(t)q(t)`），若未感染进入 `Sq`（率 `(1−β)c(t)q(t)`）；未被隔离且感染者进入 `Ic`（率 `βc(t)(1−q(t))`）。忽略 `Sq→S`。

**模型 (1)：**

$$
\begin{aligned}
\frac{dS}{dt} &= -\frac{\beta c(t) + c(t)q(t)(1-\beta)}{N}\,S I_c,\\
\frac{dI_c}{dt} &= \frac{\beta c(t)(1-q(t))}{N}\,S I_c - \gamma I_c,\\
\frac{dS_q}{dt} &= \frac{(1-\beta)c(t)q(t)}{N}\,S I_c,\\
\frac{dI_q}{dt} &= \frac{\beta c(t)q(t)}{N}\,S I_c - \delta_q I_q,\\
\frac{dR}{dt} &= \gamma I_c + \delta_q I_q.
\end{aligned}
$$

**累计报告病例的辅助方程 (2)：** `Ic_cum`（社区）、`Iq_cum`（隔离区）、`Ir_cum`（总报告）

$$
\frac{dI_{c,\mathrm{cum}}}{dt}=\frac{\beta c(t)(1-q(t))}{N}SI_c,\quad
\frac{dI_{q,\mathrm{cum}}}{dt}=\frac{\beta c(t)q(t)}{N}SI_c,\quad
\frac{dI_{r,\mathrm{cum}}}{dt}=\frac{\beta c(t)}{N}SI_c.
$$

---

## 5. TDINN 算法

- 用**三个独立全连接神经网络**（输入均为时间 t）分别表示：
  - contact rate：`c(t) = c_NN(t; Θc)`
  - quarantine rate：`q(t) = q_NN(t; Θq)`
  - 状态变量向量：`U(t) = U_NN(t; ΘU)`，其中 `U = (S, Ic, Sq, Iq, R)`
- 依据 PINN（Raissi et al. 2019, ref [37]），把 ODE 残差作为惩罚项嵌入损失函数。激活函数 `σ = tanh(x)`；用自动微分计算 ODE 残差点上的残差。

**损失函数 (3)：**

$$
\text{Loss} = \text{MSE}_{\text{data}} + \text{MSE}_{\text{ode}}
$$

- `MSE_data`：网络输出与观测数据的均方误差，按三类数据集有不同展开式（见第 6 节）。
- `MSE_ode`：ODE 系统残差 `L1…L8`（对应模型 (1)+(2) 每个方程）在 `Te` 个残差点上的均方，作为惩罚项，强制解满足动力学系统。残差点可在整个计算域任意采样。

**网络超参数（Table 2，depth, width）：**

| 网络 | Xi'an | Guangzhou | Yangzhou | Hainan | Xinjiang | Liaoning |
|---|---|---|---|---|---|---|
| U(t) | (5,64) | (5,50) | (10,64) | (3,32) | (7,32) | (7,32) |
| c(t) | (1,10) | (1,10) | (1,20) | (1,16) | (1,16) | (3,16) |
| q(t) | (1,10) | (1,10) | (1,20) | (1,16) | (1,16) | (3,16) |
| 迭代次数 | 2×10⁴ | 3×10⁴ | 3×10⁴ | 1×10⁴ | 1×10⁴ | 3×10⁴ |

（learning rate 全部为 0.001）

---

## 6. 数据

三类数据集（`Ic_new`/`Iq_new`=社区/隔离区每日新增，`Ir_new`=每日总报告；`_cum`=对应累计）：

- **Set 1**（`Ic_new, Iq_new, Ic_cum, Iq_cum`）：**Xi'an、Guangzhou、Yangzhou**
- **Set 2**（`Ic_new, Iq_new, Ir_new, Ir_cum`，社区/隔离区数据不完整）：**Hainan、Xinjiang**
- **Set 3**（`Ir_new, Ir_cum`，多波）：**Liaoning**

**各地区时间范围与数据来源（省卫健委）：**

| 地区 | 时间窗 |
|---|---|
| Xi'an（西安） | 2021-12-09 → 2022-01-20 |
| Guangzhou（广州） | 2021-05-21 → 2021-06-18 |
| Yangzhou（扬州） | 2021-07-28 → 2021-08-26 |
| Hainan（海南） | 2022-08-01 → 2022-09-23 |
| Xinjiang（新疆） | 2022-08-04 → 2022-09-26 |
| Liaoning（辽宁，多波） | 2022-03-06 → 2022-05-21 |

---

## 7. 速率函数族（用于拟合 TDINN 反推出的时间序列）

每族含 3 种形式。含义：`c0i`=初始 contact rate，`cbi`=最小 contact rate，`r1i`=contact rate 指数下降率；`q0i`=初始 quarantine rate，`qmi`=最大 quarantine rate，`r2i`=quarantine rate 指数上升率；`m, n`=干扰常数（interference constants），i = 1,2,3。

**contact rate 族 (4)：**

$$
\begin{aligned}
c_1(t) &= (c_{01}-c_{b1})e^{-r_{11}t} + c_{b1}, \\
c_2(t) &= (c_{02}-c_{b2})e^{-(r_{12}t)^2} + c_{b2}, \\
c_3(t) &= c_{b3}\left[1 + \left(\left(\tfrac{c_{b3}}{c_{03}}\right)^{-m}-1\right)e^{-r_{13}mt}\right]^{1/m}.
\end{aligned}
$$

**quarantine rate 族 (5)：**

$$
\begin{aligned}
q_1(t) &= (q_{01}-q_{m1})e^{-r_{21}t} + q_{m1}, \\
q_2(t) &= (q_{02}-q_{m2})e^{-(r_{22}t)^2} + q_{m2}, \\
q_3(t) &= q_{m3}\left[1 + \left(\left(\tfrac{q_{03}}{q_{m3}}\right)^{-n}-1\right)e^{-r_{23}nt}\right]^{-1/n}.
\end{aligned}
$$

- `c1/q1`：指数衰减/增长型，源自既有文献（Tang 等，ref [48–50]）。
- `c2/q2`：**Gaussian 衰减**型，刻画持续强化的控制策略（ref [51]）。
- `c3/q3`：基于 **Rosenzweig 模型解析解**构造（ref [52]），`m, n` 为干扰常数。

> ✅ 已按原文校正：`c3` 内层指数为 `-m`、外层为 `1/m`；`q3` 内层指数为 `-n`、外层为 `-1/n`（注意 c3 与 q3 外层指数不对称）。
> 可自洽验证边界值：c3(0)=c03、c3(∞)=cb3；q3(0)=q03、q3(∞)=qm3。

---

## 8. 关键参数估计

**Table 1 — 模型 (1) 的时间无关参数（来源：TDINN 推断）：**

| 参数 | Xi'an | Guangzhou | Yangzhou | Hainan | Xinjiang | Liaoning |
|---|---|---|---|---|---|---|
| β（每次接触传播概率） | 0.1498 | 0.1893 | 0.1493 | 0.1281 | 0.1977 | 0.2544 |
| γ（社区康复率） | 0.2953 | 0.2337 | 0.2994 | 0.2830 | 0.1773 | 0.3691 |
| δq（隔离区康复率） | 0.3531 | 0.2507 | 0.1950 | 0.2737 | 0.3519 | 0.2155 |

**Table 3 — 速率函数 c_i(t)、q_i(t) 的参数估计（LS 拟合；Liaoning 因多波未列）：**

| 参数 | Xi'an | Guangzhou | Yangzhou | Hainan | Xinjiang |
|---|---|---|---|---|---|
| c01 | 14.6054 | 12.7988 | 14.2205 | 10.3253 | 14.5078 |
| c02 | 12.8872 | 10.0039 | 11.7293 | 9.0234 | 13.0733 |
| c03 | 15.2903 | 10.8316 | 13.2506 | 10.0992 | 14.5899 |
| cb1 | 2.6624 | 2.9691 | 2.5979 | 2.8232 | 2.0714 |
| cb2 | 3.4625 | 3.1812 | 3.2593 | 3.5705 | 2.0515 |
| cb3 | 2.5073 | 3.3792 | 3.1596 | 3.0476 | 2.1241 |
| r11 | 0.0483 | 0.1703 | 0.1342 | 0.0313 | 0.1328 |
| r12 | 0.0463 | 0.1213 | 0.1176 | 0.0306 | 0.1038 |
| r13 | 0.0404 | 0.0802 | 0.0836 | 0.0189 | 0.0929 |
| m（干扰常数，assumed） | 2 | 12 | 8 | 4 | 8 |
| q01 | 0.2299 | 0.2912 | 0.3383 | 0.2020 | 0.7210 |
| q02 | 0.3230 | 0.4199 | 0.4416 | 0.2854 | 0.7219 |
| q03 | 0.3070 | 0.3870 | 0.3972 | 0.2483 | 0.7149 |
| qm1 | 0.9633 | 0.9847 | 0.9555 | 0.9744 | 0.8969 |
| qm2 | 0.9844 | 0.9039 | 0.8642 | 0.9775 | 0.8100 |
| qm3 | 0.9405 | 0.9695 | 0.8789 | 0.9899 | 0.8233 |
| r21 | 0.0541 | 0.0571 | 0.0481 | 0.0840 | 0.0126 |
| r22 | 0.0452 | 0.0566 | 0.0519 | 0.0665 | 0.0332 |
| r23 | 0.0388 | 0.0392 | 0.0364 | 0.0911 | 0.0171 |
| n（干扰常数，assumed） | 12 | 4 | 4 | 2 | 2 |

---

## 9. 主要结果

**函数选择准则**：先把 TDINN 学到的 c(t)、q(t) 当作"观测数据"`ĉ(t)`、`q̂(t)`，用最小二乘拟合族 (4)/(5)，按 **RMSE** 最小选最优单函数；再把各组合代回模型 (1) 重拟合多源数据，按 **ARMSE** 最小验证组合。两种准则结论一致。

**各地区最优 (contact, quarantine) 函数组合：**

| 地区 | 最优 c(t) | 最优 q(t) |
|---|---|---|
| Xi'an | c2 | q2 |
| Guangzhou | c3 | q2 |
| Yangzhou | c3 | q2 |
| Hainan | c3 | q3 |
| Xinjiang | c2 | q1 |

**定性发现：**

1. **单波疫情**（西安、广州、扬州、海南、新疆）中，contact rate `c(t)` 随时间**下降**，quarantine rate `q(t)` 随时间**上升**——对应动态清零下的封控 + 强化密接追踪隔离。
2. `c(t)`、`q(t)` 的演化曲线**具有区域依赖性**（形状差异明显）→ 各地控制强度不同，导致疫情峰值/峰时各异；**难以用一个通用函数组合刻画所有地区**，防控模式不能简单跨区照搬。
3. **辽宁（多波）**：`c(t)`、`q(t)` 呈**振荡**，揭示一个反馈回路：
   > 疫情起 → 隔离率升、接触率降 → 疫情消退 → 干预放松、隔离率降、接触率升 → 疫情反弹 …
   多波情形下的 c(t)/q(t) 行为复杂，用平滑函数族 (4)/(5) 难以精确刻画（留作 future work）。
4. 所有速率函数参数都有现实含义，因此所选函数增强了深度学习推断结果的可解释性。

---

## 10. 结论与局限

- **结论**：TDINN 双向融合——既用深度网络学到的时变函数扩展了传统动力学模型，又用传播机制约束扩展了神经网络。相比传统动力学模型有更强的数据学习与未知速率函数推断能力；相比端到端深度学习有更好的可解释性；可推广到更复杂的仓室模型。
- **局限**：
  1. 模型 (1) 较简单，忽略了医疗资源容量、行为响应、疫苗接种等重要因素；
  2. 多波疫情反推出的 c(t)/q(t) 难以用平滑函数精确刻画。

---

## 11. 图表索引（需要看图时按此定位原 PDF）

- **Fig 1**：多源疫情数据（a 辽宁；b 西安/广州/扬州；c 海南；d 新疆）+ (e) 仓室流程图。
- **Fig 2**：TDINN 结构示意（绿色区=状态变量网络；紫色区=时变参数 c(t)/q(t) 网络；σ=激活，d/dt=自动微分）。
- **Fig 3**：西安/广州/扬州的数据拟合与 c(t)、q(t) 推断（品红五角星=TDINN 推断，实线=函数拟合，虚线=代回模型解）。
- **Fig 4**：海南/新疆的拟合与 c(t)、q(t) 推断。
- **Fig 5**：西安/广州/扬州的 RMSEci、RMSEqi 及组合 ARMSE。
- **Fig 6**：海南/新疆的 RMSE 与 ARMSE。
- **Fig 7**：辽宁多波拟合 (a) 及推断的 c(t) (b)、q(t) (c)，呈振荡。

---

## 12. 与「阈值控制」项目的关联点

- 本文的 `c(t)`（下降）、`q(t)`（上升）时序及其函数族，是量化"接触/隔离干预强度"的直接工具，可与本项目中西安管控（`Xianguankong.xlsx`）、flatten-curve、threshold landscape 等分析对接。
- 参考文献 **[9] Tang et al. 2023, BMC Public Health**："Threshold conditions for curbing COVID-19 with a dynamic zero-case policy derived from 101 outbreaks in China" —— 与"阈值控制"主题最相关，值得单独查阅。
- `c1(t)/q1(t)` 的来源 **[48–50]**（Tang 团队 2020–2022 系列）是接触率/隔离率建模的经典出处。

---

## 13. 关键参考文献（精选）

- **[9]** Tang S, Wang X, Tang B, He S, Yan D, Huang C, et al. *Threshold conditions for curbing COVID-19 with a dynamic zero-case policy derived from 101 outbreaks in China.* BMC Public Health. 2023; 23(1). doi:10.1186/s12889-023-16009-8
- **[37]** Raissi M, Perdikaris P, Karniadakis GE. *Physics-informed neural networks…* J. Comput. Phys. 2019; 378:686–707.（PINN 原始文献）
- **[13]** Wang H, et al. *Lessons drawn from Shanghai…（分段 contact/quarantine rate，Omicron）* BMC Infect Dis. 2023.
- **[14]** Li Q, Bai Y, Tang B. *Modelling the pulse population-wide nucleic acid screening…* BMC Infect Dis. 2023.
- **[48–50]** Tang B, et al. 2020–2022（c1/q1 指数型速率函数来源）
- **[52]** Rosenzweig ML. *Paradox of enrichment…* Science. 1971; 171:385–387.（c3/q3 构造依据）
