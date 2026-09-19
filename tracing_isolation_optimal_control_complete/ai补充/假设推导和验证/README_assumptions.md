# 假设 G1–G4 的证明包

针对 `tracing_isolation_optimal_control_complete/latex/main.tex` 中的假设
`\ref{ass:geometry}`（(G1)–(G4)）。结论：**四条假设全部可证，整个假设可以删去**；
此外注 8.2 第 (iii) 项的表述需要更正。

## 文件清单

| 文件 | 内容 |
|---|---|
| `assumptions_to_theorems.tex` | 合并后的完整 LaTeX 章节，含全部定理与证明，可直接插入 |
| `verify_all.py` | 一键验证脚本，32 项符号 + 数值检查 |
| `verify_full.log` | 完整模式的运行输出（32/32 通过） |
| `G3_G4_scan_map.png` | $p$–$K$ 平面上的结构分区与四个诊断量热图 |
| `G3_G4_residual_slices.png` | 统一残差 $D(s)$ 的切片，及 $\tau$、$M$ 随容量紧度的变化 |
| `g3_g4_scan.csv` | $100\times100$ 网格的完整扫描数据（10000 行） |
| `scan_fast.py` / `scan_run2.py` / `refine.py` / `figs.py` / `figs2.py` / `export.py` | 扫描与绘图脚本 |

`no_singular_arc.tex` 与 `g3_transversality.tex` 是早前分两次给出的版本，
已被 `assumptions_to_theorems.tex` 完全覆盖，可以丢弃。

## 插入方式

把 `assumptions_to_theorems.tex` 的内容作为新的一节，置于第 8 节
（常接触率下 $q(t)$ 的唯一性）开头、定理 `\ref{thm:unique-q}` 之前；
原注 8.2 用文件末尾的 `rmk:degeneracy`（修订版）替换。

然后把假设 `\ref{ass:geometry}` 整体删除，并把正文中所有
"在假设 \ref{ass:geometry} 下" 的措辞去掉。定理 `\ref{thm:verification}`
与 `\ref{thm:unique-q}` 的陈述相应改为无条件。

依赖的已有标签（`main.tex` 中均已定义）：
`eq:normalized-model`, `eq:f0`, `eq:f1`, `eq:switching-function`, `eq:HJB`,
`eq:g`, `eq:g-minus-i`, `eq:theta-log-derivative`, `eq:JB-derivative`,
`eq:verification-ineq`, `eq:safe-boundary`, `thm:unique-q`。

## 主要结果

**(G1) 可达域。** 原文只证了端点的唯一性，没证存在性。沿 $q=1$ 弧感染不会有限时间归零，
$s$ 只趋于 $s_a e^{-i_a/\ell}$，因此特征线未必够得到安全边界。可达域有闭式刻画：

$$\mathcal D=\Big\{i>\ell\ln\frac{s}{s_{\max}}\Big\},\qquad
s_{\max}-h\ln s_{\max}=K+h-h\ln h$$

$\partial\mathcal D$ 就是过安全集角点 $(s_{\max},0)$ 的 $q=1$ 特征线。
又 $R(s)=i_w(s)-\ell\ln(s/s_{\max})$ 沿等待轨迹严格递减（两段分别为 $(r-s)/s$ 与 $-\ell/s$），
且 $R(h^+)>0$，故 $\mathcal W\cap\mathcal D$ 是单区间 $(h,s_D)$；
$\mathcal D$ 外成本为 $+\infty$，所以最优切换点必在其中。

**(G2) 切换曲线正则性。** 隐函数定理的非退化条件正是非平凡根处
$\frac{\mathrm d}{\mathrm ds}\ln\Theta\ne0$，由引理 A 严格为负；
单射性来自 $G(\bar s)=a(\bar s)-\ell\ln\bar s$ 严格递减。故 $\Gamma$ 是简单实解析曲线。

**(G4) 无奇异弧。** 关键结构：$g=f_1-f_0=-bsi(\kappa,1)$ 恒平行于固定方向。
奇异弧需同时满足 $\Sigma=0$、$\dot\Sigma=0$、$H_0=0$。前两式行列式 $(s-r)/p\neq0$
唯一确定共态，第三式给出奇异轨迹 $i=g(s)=(s-h)(s-r)/s$——恰是原文单峰性引理里的同一函数。
沿该曲线停留所需的控制满足

$$q_{\rm sing}-1=\frac{(s-h)(s+r)}{(2p-1)s^2+r^2}$$

在 $s>h$ 上分子恒正，三种符号情形下 $q_{\rm sing}$ 都落在 $[0,1]$ 之外。
同一论证还排除了沿 $\Gamma$ 滑行和异常极值（$\lambda_0=0$）。

**(G3) 横截性与唯一交点。** 把两段等待轨迹统一成残差
$D(s)=\Theta(\bar s,\bar a)-\Theta(s,i_w(s))$，总成本满足 $F'=\lambda D$，$\lambda>0$。
不证 $D$ 单调（它不单调），而证**每个零点处 $D'>0$**，由此至多一个零点。
两段都归结为同一个不等式 $\varphi(\bar s)<\varphi(s)$，$\varphi(x)=(x-h)(x-r)^2/x$：

- 自然轨道段：$\Theta$ 项精确相消，直接得到；
- 容量段：松弛量分子恰为 $s[g(s)-K]$，由引理 A（零点必在奇异曲线下方）为正。

而 $(\ln\varphi)'=\frac1{x-h}+\frac2{x-r}-\frac1x>0$ 且 $\bar s<s$ 恒成立。

**注 8.2(iii) 的更正。** 在容量等待弧上 $V_s=p\Theta/s$、$V_i=p/(K(s-r))$，
代入得 $(1-p)V_s+pV_i=p/(Ks)$，于是 $\Sigma\equiv0$——这是恒等式，对所有参数成立。
所以第 (iii) 类退化**总是**发生，原文"基准参数下三个退化均未发生"就该项而言不成立。
但唯一性不受影响：边界正下方

$$\Sigma=pc\Big[1-\frac{i(s-r)}{K(s'-r)}\Big]>0$$

严格成立（因沿自然轨道 $\frac{\mathrm d}{\mathrm d\sigma}[\iota(\sigma-r)]=\iota-g(\sigma)<0$，
而 $\iota\le K<g(s_B)\le g(\sigma)$），任何离开边界的控制立刻受到严格惩罚。

## 运行验证

```bash
python verify_all.py            # 完整，约 3 分钟
python verify_all.py --quick    # 快速，约 30 秒
```

依赖 `numpy`, `scipy`, `sympy`。脚本自包含，不依赖其他文件。
退出码 0 表示全部通过。

完整模式的覆盖范围：$q_{\rm sing}$ 扫描 80 万样本点、$\mathcal D$ 判据 28 万样本点、
$D$ 的零点与横截性 984 个 $(p,K)$ 组合（容量段 622、自然段 362），
以及基准参数下 8 个关键量与报告表格的逐位比对（最大偏差 $9\times10^{-8}$，
差异来自根查找容差而非公式）。

## 仍需你自己处理的两点

1. **命题 `prop:sigma-zero-boundary` 用的是单侧导数。** $V$ 在 $\{i=K\}$ 上只单侧可微，
   $V_i$ 取的是从 $i<K$ 一侧的极限。这在状态约束问题中是标准做法，
   但严格写作时建议加一句脚注说明，否则审稿人会问。

2. **共态的正则性。** 定理 `thm:no-singular` 的证明里我写的是 $\lambda=\nabla V$，
   隐含 $V$ 在奇异弧附近可微。若要完全严格，把 $\lambda$ 改成 Pontryagin 极大值原理的
   共态（沿极值绝对连续，不需要 $V$ 可微），推导逐字不变，结论不动。
   `verify_all.py` 第 1 部分就是按共态 ODE 做的。
