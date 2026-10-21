# 前向引用完整清单

源文件：`git:689a627:tracing_isolation_optimal_control_complete/latex/main.tex`；SHA-256：`a2562f318793cf5e55e54e254c59595ff739a46890d8badae68a0895f1ac32ac`。

检查 `ref`、`eqref`、`autoref`、`cref` 等命令及已知引用包装宏 `NumTheoryRef`，目标限于定理、引理、命题、推论和带标签公式。未转义注释不参与扫描；定义位置采用对象的 `begin` 行，另列 `label` 行。同一公式内部的自引用不计为前向。已核对 `\providecommand{\NumTheoryRef}[2]{#2~\ref{#1}}`，只按这一已知展开纳入该包装宏；目标是定义、图表等其他类型时仍按范围排除。其他任意宏不推断，主文件之外的 `input` 不展开，当前审计范围为 `main.tex`。

计数：definitions=161；references=202；wrapped_references=3；forward=22；intentional_overview=10；other_forward=12；proof_forward_outside_overview=0。

## 第 3 节概览中的有意前向引用

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 13 | 267:2 | `\eqref{eq:sum-decay}` | 3 主结果与最优分区 | 正文 | 385 / 391 | 是（第 3 节概览） |
| 14 | 299:3 | `\ref{lem:safe-invariant}` | 3 主结果与最优分区 > 3.1 安全集与可行性 | 正文 | 498 / 499 | 是（第 3 节概览） |
| 16 | 325:7 | `\ref{prop:candidate-attainment}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1159 / 1160 | 是（第 3 节概览） |
| 17 | 325:41 | `\ref{thm:verification}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1391 / 1392 | 是（第 3 节概览） |
| 18 | 325:66 | `\ref{thm:unique-q}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1572 / 1573 | 是（第 3 节概览） |
| 20 | 334:48 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 819 / 820 | 是（第 3 节概览） |
| 21 | 334:76 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 885 / 886 | 是（第 3 节概览） |
| 22 | 339:16 | `\ref{cor:optimal-synthesis}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 1676 / 1677 | 是（第 3 节概览） |
| 23 | 340:16 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 819 / 820 | 是（第 3 节概览） |
| 24 | 340:44 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 885 / 886 | 是（第 3 节概览） |

## 其他前向引用

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 1 | 141:3 | `\ref{thm:main-overview}` | 1 引言 | 正文 | 316 / 317 | 是 |
| 2 | 141:40 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 329 / 330 | 是 |
| 3 | 147:3 | `\ref{lem:finite-entry}` | 1 引言 | 正文 | 591 / 592 | 是 |
| 4 | 148:3 | `\ref{thm:verification}` | 1 引言 | 正文 | 1391 / 1392 | 是 |
| 5 | 149:3 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 329 / 330 | 是 |
| 6 | 157:3 | `\ref{cor:verification-equality}` | 1 引言 | 正文 | 1419 / 1420 | 是 |
| 7 | 157:44 | `\ref{lem:no-early-boundary-exit}` | 1 引言 | 正文 | 1495 / 1496 | 是 |
| 8 | 159:3 | `\ref{thm:unique-q}` | 1 引言 | 正文 | 1572 / 1573 | 是 |
| 53 | 984:5 | `\ref{prop:regularity}` | 11 全域候选反馈与候选成本 | 正文 | 1268 / 1269 | 是 |
| 69 | 1190:8 | `\ref{thm:verification}` | 11 全域候选反馈与候选成本 | 正文 | 1391 / 1392 | 是 |
| 70 | 1191:18 | `\ref{cor:optimal-synthesis}` | 11 全域候选反馈与候选成本 | 正文 | 1676 / 1677 | 是 |
| 79 | 1292:17 | `\ref{lem:trajectory-verification}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 正文 | 1344 / 1345 | 是 |

## 概览以外证明中的前向引用

无。

## 全部引用（按源码顺序）

| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |
|---:|---|---|---|---|---|---|
| 1 | 141:3 | `\ref{thm:main-overview}` | 1 引言 | 正文 | 316 / 317 | 是 |
| 2 | 141:40 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 329 / 330 | 是 |
| 3 | 147:3 | `\ref{lem:finite-entry}` | 1 引言 | 正文 | 591 / 592 | 是 |
| 4 | 148:3 | `\ref{thm:verification}` | 1 引言 | 正文 | 1391 / 1392 | 是 |
| 5 | 149:3 | `\ref{prop:main-structure}` | 1 引言 | 正文 | 329 / 330 | 是 |
| 6 | 157:3 | `\ref{cor:verification-equality}` | 1 引言 | 正文 | 1419 / 1420 | 是 |
| 7 | 157:44 | `\ref{lem:no-early-boundary-exit}` | 1 引言 | 正文 | 1495 / 1496 | 是 |
| 8 | 159:3 | `\ref{thm:unique-q}` | 1 引言 | 正文 | 1572 / 1573 | 是 |
| 9 | 206:2 | `\eqref{eq:five-compartment-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 176 / 184 | 否 |
| 10 | 244:45 | `\eqref{eq:normalized-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 214 / 219 | 否 |
| 11 | 245:22 | `\eqref{eq:capacity}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 226 / 228 | 否 |
| 12 | 249:37 | `\eqref{eq:normalized-model}` | 2 模型与控制问题 > 2.2 二维约化与控制问题 | 正文 | 214 / 219 | 否 |
| 13 | 267:2 | `\eqref{eq:sum-decay}` | 3 主结果与最优分区 | 正文 | 385 / 391 | 是（第 3 节概览） |
| 14 | 299:3 | `\ref{lem:safe-invariant}` | 3 主结果与最优分区 > 3.1 安全集与可行性 | 正文 | 498 / 499 | 是（第 3 节概览） |
| 15 | 318:3 | `\eqref{eq:constants}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 256 / 259 | 否 |
| 16 | 325:7 | `\ref{prop:candidate-attainment}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1159 / 1160 | 是（第 3 节概览） |
| 17 | 325:41 | `\ref{thm:verification}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1391 / 1392 | 是（第 3 节概览） |
| 18 | 325:66 | `\ref{thm:unique-q}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 1，thm:main-overview | 1572 / 1573 | 是（第 3 节概览） |
| 19 | 331:4 | `\ref{thm:main-overview}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 316 / 317 | 否 |
| 20 | 334:48 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 819 / 820 | 是（第 3 节概览） |
| 21 | 334:76 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 正文 | 885 / 886 | 是（第 3 节概览） |
| 22 | 339:16 | `\ref{cor:optimal-synthesis}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 1676 / 1677 | 是（第 3 节概览） |
| 23 | 340:16 | `\ref{prop:Gamma-geometry}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 819 / 820 | 是（第 3 节概览） |
| 24 | 340:44 | `\ref{cor:Gamma-labels}` | 3 主结果与最优分区 > 3.2 全域反馈与阶段结构 | 证明 2，prop:main-structure | 885 / 886 | 是（第 3 节概览） |
| 25 | 384:3 | `\eqref{eq:normalized-model}` | 4 解的适定性、正性与基本耗散 | 正文 | 214 / 219 | 否 |
| 26 | 415:9 | `\eqref{eq:i-integrable}` | 4 解的适定性、正性与基本耗散 | 证明 3，thm:wellposed | 394 / 396 | 否 |
| 27 | 438:6 | `\eqref{eq:constants}` | 5 常接触率问题、自然轨道与安全目标集 | 正文 | 256 / 259 | 否 |
| 28 | 438:31 | `\eqref{eq:value-definition}` | 5 常接触率问题、自然轨道与安全目标集 | 正文 | 271 / 273 | 否 |
| 29 | 449:3 | `\eqref{eq:Phi}` | 5 常接触率问题、自然轨道与安全目标集 > 5.1 自然传播不变量与峰值 | 正文 | 307 / 309 | 否 |
| 30 | 460:20 | `\eqref{eq:uncontrolled-future-peak}` | 5 常接触率问题、自然轨道与安全目标集 > 5.1 自然传播不变量与峰值 | 正文 | 280 / 286 | 否 |
| 31 | 469:16 | `\eqref{eq:safe-set}` | 5 常接触率问题、自然轨道与安全目标集 > 5.2 安全集与目标边界 | 正文 | 294 / 296 | 否 |
| 32 | 470:3 | `\eqref{eq:uncontrolled-future-peak}` | 5 常接触率问题、自然轨道与安全目标集 > 5.2 安全集与目标边界 | 正文 | 280 / 286 | 否 |
| 33 | 479:3 | `\eqref{eq:natural-peak}` | 5 常接触率问题、自然轨道与安全目标集 > 5.2 安全集与目标边界 | 证明 4，prop:safe-exact | 455 / 457 | 否 |
| 34 | 504:10 | `\eqref{eq:Phi-derivative}` | 6 两类控制弧与显式成本 > 6.1 一般控制下的不变量导数 | 证明 5，lem:safe-invariant | 487 / 489 | 否 |
| 35 | 506:9 | `\eqref{eq:sum-decay}` | 6 两类控制弧与显式成本 > 6.1 一般控制下的不变量导数 | 证明 5，lem:safe-invariant | 385 / 391 | 否 |
| 36 | 543:15 | `\eqref{eq:ac-level-set}` | 6 两类控制弧与显式成本 > 6.3 容量弧 | 正文 | 422 / 424 | 否 |
| 37 | 583:11 | `\eqref{eq:boundary-duration}` | 7 有限成本可行性与首次到达问题 | 证明 6，lem:finite-feasible | 557 / 559 | 否 |
| 38 | 583:41 | `\eqref{eq:boundary-cost}` | 7 有限成本可行性与首次到达问题 | 证明 6，lem:finite-feasible | 561 / 566 | 否 |
| 39 | 606:59 | `\eqref{eq:i-integrable}` | 7 有限成本可行性与首次到达问题 | 证明 7，lem:finite-entry | 394 / 396 | 否 |
| 40 | 623:19 | `\ref{lem:finite-entry}` | 7 有限成本可行性与首次到达问题 | 证明 8，prop:exit-equivalence | 591 / 592 | 否 |
| 41 | 681:3 | `\eqref{eq:H-affine}` | 8 HJB 方程与验证所需的边界条件 | 证明 9，lem:bangbang | 642 / 645 | 否 |
| 42 | 718:7 | `\eqref{eq:endpoint-system}` | 9 完全跟踪成本的有限可达域及导数 | 证明 10，prop:reachable | 699 / 703 | 否 |
| 43 | 731:24 | `\ref{lem:finite-feasible}` | 9 完全跟踪成本的有限可达域及导数 | 正文 | 572 / 573 | 否 |
| 44 | 769:3 | `\eqref{eq:Ws}` | 9 完全跟踪成本的有限可达域及导数 | 证明 11，prop:W-HJB | 740 / 742 | 否 |
| 45 | 769:18 | `\eqref{eq:Wi}` | 9 完全跟踪成本的有限可达域及导数 | 证明 11，prop:W-HJB | 740 / 744 | 否 |
| 46 | 789:3 | `\eqref{eq:q1-backward}` | 10 切换曲线的存在、单调性及严格横穿 | 正文 | 777 / 779 | 否 |
| 47 | 864:4 | `\ref{lem:unimodal}` | 10 切换曲线的存在、单调性及严格横穿 | 证明 13，prop:Gamma-geometry | 787 / 788 | 否 |
| 48 | 878:37 | `\ref{lem:unimodal}` | 10 切换曲线的存在、单调性及严格横穿 | 证明 13，prop:Gamma-geometry | 787 / 788 | 否 |
| 49 | 904:14 | `\eqref{eq:Gamma-slope}` | 10 切换曲线的存在、单调性及严格横穿 | 证明 14，cor:Gamma-labels | 834 / 839 | 否 |
| 50 | 922:5 | `\eqref{eq:Gamma-slope}` | 10 切换曲线的存在、单调性及严格横穿 | 证明 15，lem:strict-crossing | 834 / 839 | 否 |
| 51 | 929:2 | `\eqref{eq:ac-level-set}` | 10 切换曲线的存在、单调性及严格横穿 | 证明 15，lem:strict-crossing | 422 / 424 | 否 |
| 52 | 958:49 | `\eqref{eq:Gamma-hit-map}` | 11 全域候选反馈与候选成本 | 正文 | 895 / 898 | 否 |
| 53 | 984:5 | `\ref{prop:regularity}` | 11 全域候选反馈与候选成本 | 正文 | 1268 / 1269 | 是 |
| 54 | 1004:3 | `\ref{cor:Gamma-labels}` | 11 全域候选反馈与候选成本 | 证明 16，lem:chi-regions | 885 / 886 | 否 |
| 55 | 1013:38 | `\eqref{eq:chi-regions}` | 11 全域候选反馈与候选成本 | 证明 16，lem:chi-regions | 993 / 997 | 否 |
| 56 | 1031:4 | `\ref{lem:chi-regions}` | 11 全域候选反馈与候选成本 | 正文 | 989 / 990 | 否 |
| 57 | 1069:40 | `\ref{prop:reachable}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 690 / 691 | 否 |
| 58 | 1074:4 | `\ref{prop:reachable}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 690 / 691 | 否 |
| 59 | 1080:4 | `\ref{lem:unimodal}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 787 / 788 | 否 |
| 60 | 1110:5 | `\ref{lem:strict-crossing}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 910 / 911 | 否 |
| 61 | 1122:15 | `\ref{lem:chi-regions}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 989 / 990 | 否 |
| 62 | 1124:11 | `\eqref{eq:strict-crossing-time}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 934 / 936 | 否 |
| 63 | 1124:45 | `\ref{lem:chi-regions}` | 11 全域候选反馈与候选成本 | 证明 17，lem:tracking-region | 989 / 990 | 否 |
| 64 | 1163:6 | `\eqref{eq:candidate-feedback}` | 11 全域候选反馈与候选成本 | 正文 | 1132 / 1139 | 否 |
| 65 | 1172:8 | `\eqref{eq:boundary-duration}` | 11 全域候选反馈与候选成本 | 证明 18，prop:candidate-attainment | 557 / 559 | 否 |
| 66 | 1173:10 | `\ref{lem:tracking-region}` | 11 全域候选反馈与候选成本 | 证明 18，prop:candidate-attainment | 1057 / 1058 | 否 |
| 67 | 1174:3 | `\eqref{eq:sum-decay}` | 11 全域候选反馈与候选成本 | 证明 18，prop:candidate-attainment | 385 / 391 | 否 |
| 68 | 1175:9 | `\eqref{eq:candidate-U}` | 11 全域候选反馈与候选成本 | 证明 18，prop:candidate-attainment | 1142 / 1150 | 否 |
| 69 | 1190:8 | `\ref{thm:verification}` | 11 全域候选反馈与候选成本 | 正文 | 1391 / 1392 | 是 |
| 70 | 1191:18 | `\ref{cor:optimal-synthesis}` | 11 全域候选反馈与候选成本 | 正文 | 1676 / 1677 | 是 |
| 71 | 1224:39 | `\eqref{eq:Ws}` | 12 全域梯度、拼接正则性与验证不等式 > 12.1 两种等待分支的统一导数 | 证明 19，lem:waiting-gradient | 740 / 742 | 否 |
| 72 | 1224:54 | `\eqref{eq:Wi}` | 12 全域梯度、拼接正则性与验证不等式 > 12.1 两种等待分支的统一导数 | 证明 19，lem:waiting-gradient | 740 / 744 | 否 |
| 73 | 1253:4 | `\eqref{eq:waiting-gradient}` | 12 全域梯度、拼接正则性与验证不等式 > 12.1 两种等待分支的统一导数 | 证明 20，lem:waiting-HJB | 1217 / 1220 | 否 |
| 74 | 1259:20 | `\ref{lem:unimodal}` | 12 全域梯度、拼接正则性与验证不等式 > 12.1 两种等待分支的统一导数 | 证明 20，lem:waiting-HJB | 787 / 788 | 否 |
| 75 | 1263:3 | `\eqref{eq:Lambda-natural}` | 12 全域梯度、拼接正则性与验证不等式 > 12.1 两种等待分支的统一导数 | 证明 20，lem:waiting-HJB | 1255 / 1257 | 否 |
| 76 | 1281:11 | `\eqref{eq:waiting-gradient}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 证明 21，prop:regularity | 1217 / 1220 | 否 |
| 77 | 1281:40 | `\eqref{eq:Ws}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 证明 21，prop:regularity | 740 / 742 | 否 |
| 78 | 1281:55 | `\eqref{eq:Wi}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 证明 21，prop:regularity | 740 / 744 | 否 |
| 79 | 1292:17 | `\ref{lem:trajectory-verification}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 正文 | 1344 / 1345 | 是 |
| 80 | 1305:8 | `\eqref{eq:ac-level-set}` | 12 全域梯度、拼接正则性与验证不等式 > 12.2 内部界面与局部 Lipschitz 性 | 正文 | 422 / 424 | 否 |
| 81 | 1330:7 | `\ref{lem:waiting-HJB}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，prop:all-HJB | 1242 / 1243 | 否 |
| 82 | 1330:37 | `\ref{lem:tracking-region}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，prop:all-HJB | 1057 / 1058 | 否 |
| 83 | 1330:65 | `\ref{prop:W-HJB}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，prop:all-HJB | 758 / 759 | 否 |
| 84 | 1332:8 | `\eqref{eq:capacity-gradient}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，prop:all-HJB | 1274 / 1276 | 否 |
| 85 | 1333:39 | `\eqref{eq:capacity-tie}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 22，prop:all-HJB | 1324 / 1326 | 否 |
| 86 | 1337:2 | `\eqref{eq:capacity-tie}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 正文 | 1324 / 1326 | 否 |
| 87 | 1339:2 | `\eqref{eq:HJB-table}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 正文 | 1312 / 1320 | 否 |
| 88 | 1355:4 | `\ref{prop:regularity}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 1268 / 1269 | 否 |
| 89 | 1358:10 | `\ref{prop:all-HJB}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 1309 / 1310 | 否 |
| 90 | 1364:37 | `\eqref{eq:ac-level-set}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 422 / 424 | 否 |
| 91 | 1366:32 | `\ref{prop:regularity}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 1268 / 1269 | 否 |
| 92 | 1370:13 | `\eqref{eq:boundary-cost}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 561 / 566 | 否 |
| 93 | 1375:3 | `\eqref{eq:ac-level-set}` | 12 全域梯度、拼接正则性与验证不等式 > 12.3 容量 Hamiltonian 与沿任意轨道的链式法则 | 证明 23，lem:trajectory-verification | 422 / 424 | 否 |
| 94 | 1393:3 | `\eqref{eq:constants}` | 13 全局最优性验证 | 正文 | 256 / 259 | 否 |
| 95 | 1394:6 | `\eqref{eq:candidate-U}` | 13 全局最优性验证 | 正文 | 1142 / 1150 | 否 |
| 96 | 1394:48 | `\eqref{eq:value-definition}` | 13 全局最优性验证 | 正文 | 271 / 273 | 否 |
| 97 | 1400:13 | `\ref{prop:candidate-attainment}` | 13 全局最优性验证 | 正文 | 1159 / 1160 | 否 |
| 98 | 1401:22 | `\ref{prop:candidate-attainment}` | 13 全局最优性验证 | 正文 | 1159 / 1160 | 否 |
| 99 | 1401:54 | `\ref{prop:regularity}` | 13 全局最优性验证 | 正文 | 1268 / 1269 | 否 |
| 100 | 1401:78 | `\ref{lem:finite-entry}` | 13 全局最优性验证 | 正文 | 591 / 592 | 否 |
| 101 | 1404:3 | `\ref{prop:candidate-attainment}` | 13 全局最优性验证 | 证明 24，thm:verification | 1159 / 1160 | 否 |
| 102 | 1406:19 | `\ref{lem:finite-entry}` | 13 全局最优性验证 | 证明 24，thm:verification | 591 / 592 | 否 |
| 103 | 1407:4 | `\ref{lem:trajectory-verification}` | 13 全局最优性验证 | 证明 24，thm:verification | 1344 / 1345 | 否 |
| 104 | 1421:4 | `\ref{thm:verification}` | 13 全局最优性验证 | 正文 | 1391 / 1392 | 否 |
| 105 | 1453:4 | `\ref{lem:finite-entry}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 591 / 592 | 否 |
| 106 | 1455:16 | `\ref{lem:trajectory-verification}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 1344 / 1345 | 否 |
| 107 | 1467:3 | `\ref{thm:verification}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 1391 / 1392 | 否 |
| 108 | 1468:4 | `\eqref{eq:verification-gap}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 1433 / 1439 | 否 |
| 109 | 1471:2 | `\eqref{eq:verification-gap}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 1433 / 1439 | 否 |
| 110 | 1475:13 | `\eqref{eq:verification-equality-conditions}` | 13 全局最优性验证 | 证明 25，cor:verification-equality | 1442 / 1447 | 否 |
| 111 | 1485:15 | `\ref{lem:trajectory-verification}` | 13 全局最优性验证 | 正文 | 1344 / 1345 | 否 |
| 112 | 1487:3 | `\ref{cor:verification-equality}` | 13 全局最优性验证 | 正文 | 1419 / 1420 | 否 |
| 113 | 1497:4 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1391 / 1392 | 否 |
| 114 | 1538:3 | `\ref{cor:verification-equality}` | 14 常接触率下控制与轨道的唯一性 | 证明 26，lem:no-early-boundary-exit | 1419 / 1420 | 否 |
| 115 | 1539:3 | `\ref{lem:waiting-HJB}` | 14 常接触率下控制与轨道的唯一性 | 证明 26，lem:no-early-boundary-exit | 1242 / 1243 | 否 |
| 116 | 1550:2 | `\eqref{eq:ac-level-set}` | 14 常接触率下控制与轨道的唯一性 | 证明 26，lem:no-early-boundary-exit | 422 / 424 | 否 |
| 117 | 1555:13 | `\eqref{eq:optimal-boundary-continuation}` | 14 常接触率下控制与轨道的唯一性 | 证明 26，lem:no-early-boundary-exit | 1509 / 1513 | 否 |
| 118 | 1574:4 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1391 / 1392 | 否 |
| 119 | 1588:4 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1391 / 1392 | 否 |
| 120 | 1589:3 | `\ref{cor:verification-equality}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1419 / 1420 | 否 |
| 121 | 1597:3 | `\ref{lem:waiting-HJB}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1242 / 1243 | 否 |
| 122 | 1601:3 | `\ref{prop:all-HJB}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1309 / 1310 | 否 |
| 123 | 1609:3 | `\ref{lem:trajectory-verification}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1344 / 1345 | 否 |
| 124 | 1637:2 | `\eqref{eq:ac-level-set}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 422 / 424 | 否 |
| 125 | 1640:3 | `\ref{lem:no-early-boundary-exit}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1495 / 1496 | 否 |
| 126 | 1645:3 | `\ref{lem:strict-crossing}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 910 / 911 | 否 |
| 127 | 1648:2 | `\eqref{eq:strict-crossing-time}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 934 / 936 | 否 |
| 128 | 1650:5 | `\ref{lem:chi-regions}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 989 / 990 | 否 |
| 129 | 1658:12 | `\ref{cor:Gamma-labels}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 885 / 886 | 否 |
| 130 | 1659:13 | `\ref{prop:candidate-attainment}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1159 / 1160 | 否 |
| 131 | 1664:4 | `\ref{lem:tracking-region}` | 14 常接触率下控制与轨道的唯一性 | 证明 27，thm:unique-q | 1057 / 1058 | 否 |
| 132 | 1678:4 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1391 / 1392 | 否 |
| 133 | 1678:29 | `\ref{thm:unique-q}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1572 / 1573 | 否 |
| 134 | 1694:18 | `\eqref{eq:direct-structure}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1194 / 1196 | 否 |
| 135 | 1695:3 | `\eqref{eq:capacity-structure}` | 14 常接触率下控制与轨道的唯一性 | 正文 | 1200 / 1202 | 否 |
| 136 | 1703:3 | `\ref{prop:candidate-attainment}` | 14 常接触率下控制与轨道的唯一性 | 证明 28，cor:optimal-synthesis | 1159 / 1160 | 否 |
| 137 | 1704:3 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 | 证明 28，cor:optimal-synthesis | 1391 / 1392 | 否 |
| 138 | 1705:3 | `\ref{thm:unique-q}` | 14 常接触率下控制与轨道的唯一性 | 证明 28，cor:optimal-synthesis | 1572 / 1573 | 否 |
| 139 | 1739:26 | `\ref{thm:verification}` | 14 常接触率下控制与轨道的唯一性 > 14.1 一维切换成本与全局结论的关系 | 正文 | 1391 / 1392 | 否 |
| 140 | 1753:3 | `\ref{thm:unique-q}` | 14 常接触率下控制与轨道的唯一性 > 14.1 一维切换成本与全局结论的关系 | 证明 29，cor:one-dimensional-min | 1572 / 1573 | 否 |
| 141 | 1764:6 | `\eqref{eq:constants}` | 15 不变量坐标与切换机制 | 正文 | 256 / 259 | 否 |
| 142 | 1767:16 | `\eqref{eq:Phi-derivative}` | 15 不变量坐标与切换机制 | 正文 | 487 / 489 | 否 |
| 143 | 1777:2 | `\eqref{eq:cost-in-Phi}` | 15 不变量坐标与切换机制 | 正文 | 1768 / 1770 | 否 |
| 144 | 1803:5 | `\ref{lem:unimodal}` | 15 不变量坐标与切换机制 | 正文 | 787 / 788 | 否 |
| 145 | 1803:25 | `\eqref{eq:theta-log-derivative}` | 15 不变量坐标与切换机制 | 正文 | 790 / 793 | 否 |
| 146 | 1805:3 | `\eqref{eq:theta-characteristic-derivative}` | 15 不变量坐标与切换机制 | 正文 | 1798 / 1801 | 否 |
| 147 | 1805:52 | `\eqref{eq:JD-derivative}` | 15 不变量坐标与切换机制 | 正文 | 1732 / 1734 | 否 |
| 148 | 1805:78 | `\eqref{eq:JB-derivative}` | 15 不变量坐标与切换机制 | 正文 | 1732 / 1736 | 否 |
| 149 | 1824:65 | `\eqref{eq:H0-theta}` | 15 不变量坐标与切换机制 | 正文 | 761 / 764 | 否 |
| 150 | 1833:19 | `\ref{thm:verification}` | 15 不变量坐标与切换机制 | 正文 | 1391 / 1392 | 否 |
| 151 | 1837:22 | `\eqref{eq:JB-derivative}` | 15 不变量坐标与切换机制 | 正文 | 1732 / 1736 | 否 |
| 152 | 1841:3 | `\eqref{eq:JB-curvature-integral}` | 15 不变量坐标与切换机制 | 正文 | 1806 / 1811 | 否 |
| 153 | 1843:6 | `\ref{cor:one-dimensional-min}` | 15 不变量坐标与切换机制 | 正文 | 1741 / 1742 | 否 |
| 154 | 1843:52 | `\ref{thm:verification}` | 15 不变量坐标与切换机制 | 正文 | 1391 / 1392 | 否 |
| 155 | 1865:3 | `\eqref{eq:boundary-cost}` | 16 比较基准、小容量渐近与参数量级 > 16.1 纯容量填充与比较指标 | 正文 | 561 / 566 | 否 |
| 156 | 1865:28 | `\eqref{eq:q1-cost}` | 16 比较基准、小容量渐近与参数量级 > 16.1 纯容量填充与比较指标 | 正文 | 530 / 532 | 否 |
| 157 | 1913:2 | `\eqref{eq:small-K-switch}` | 16 比较基准、小容量渐近与参数量级 > 16.2 固定传播概率下的小容量命题 | 正文 | 1892 / 1894 | 否 |
| 158 | 1913:29 | `\eqref{eq:small-K-time}` | 16 比较基准、小容量渐近与参数量级 > 16.2 固定传播概率下的小容量命题 | 正文 | 1892 / 1898 | 否 |
| 159 | 1927:17 | `\eqref{eq:common-capacity-comparison}` | 16 比较基准、小容量渐近与参数量级 > 16.2 固定传播概率下的小容量命题 | 正文 | 1866 / 1872 | 否 |
| 160 | 2065:1 | `\NumTheoryRef{thm:verification}{验证定理}` | 17 数值方法与实验设置 | 正文 | 1391 / 1392 | 否 |
| 161 | 2066:1 | `\NumTheoryRef{thm:unique-q}{唯一性定理}` | 17 数值方法与实验设置 | 正文 | 1572 / 1573 | 否 |
| 162 | 2113:8 | `\eqref{eq:uncontrolled-future-peak}` | 17 数值方法与实验设置 | 正文 | 280 / 286 | 否 |
| 163 | 2117:21 | `\ref{lem:safe-invariant}` | 17 数值方法与实验设置 | 正文 | 498 / 499 | 否 |
| 164 | 2142:5 | `\NumTheoryRef{thm:verification}{验证定理}` | 18 不同初值区域下的数值验证 > 18.1 代表初值与相平面分区 | 正文 | 1391 / 1392 | 否 |
| 165 | 2298:3 | `\eqref{eq:time-boundary-set}` | 19 \texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论} > 19.1 非自治 HJB 方程 | 正文 | 2289 / 2291 | 否 |
| 166 | 2298:33 | `\eqref{eq:time-switch}` | 19 \texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论} > 19.1 非自治 HJB 方程 | 正文 | 2294 / 2296 | 否 |
| 167 | 2333:14 | `\eqref{eq:time-boundary-set}` | 19 \texorpdfstring{时变接触率 $c(t)$：条件性结论}{时变接触率：条件性结论} > 19.2 有限时域严格凸正则化 | 正文 | 2289 / 2291 | 否 |
| 168 | 2344:29 | `\eqref{eq:linear-cost}` | 20 同时控制接触率与跟踪比例时的限制 | 正文 | 232 / 234 | 否 |
| 169 | 2359:10 | `\ref{prop:main-structure}` | 21 模型假设与理论边界 | 正文 | 329 / 330 | 否 |
| 170 | 2380:32 | `\ref{thm:verification}` | 22 主要结论 | 正文 | 1391 / 1392 | 否 |
| 171 | 2383:3 | `\ref{thm:unique-q}` | 22 主要结论 | 正文 | 1572 / 1573 | 否 |
| 172 | 2420:6 | `\eqref{eq:endpoint-derivatives}` | A 完全跟踪成本导数的逐步计算 | 正文 | 734 / 737 | 否 |
| 173 | 2444:9 | `\eqref{eq:boundary-cost}` | B 容量边界成本积分的逐步计算 | 正文 | 561 / 566 | 否 |
| 174 | 2448:17 | `\ref{prop:small-capacity}` | C 小容量渐近的完整推导 | 证明 32，prop:small-capacity | 1886 / 1887 | 否 |
| 175 | 2481:18 | `\eqref{eq:small-K-switch}` | C 小容量渐近的完整推导 | 证明 32，prop:small-capacity | 1892 / 1894 | 否 |
| 176 | 2495:3 | `\eqref{eq:small-K-cost}` | C 小容量渐近的完整推导 | 证明 32，prop:small-capacity | 1892 / 1896 | 否 |
| 177 | 2514:5 | `\eqref{eq:small-K-time}` | C 小容量渐近的完整推导 | 证明 32，prop:small-capacity | 1892 / 1898 | 否 |
| 178 | 2524:53 | `\eqref{eq:small-K-relative}` | C 小容量渐近的完整推导 | 证明 32，prop:small-capacity | 1907 / 1911 | 否 |
| 179 | 2532:8 | `\ref{prop:regularity}` | D 梯度拼接与相对正则性的详细证明 | 正文 | 1268 / 1269 | 否 |
| 180 | 2537:3 | `\eqref{eq:waiting-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 1217 / 1220 | 否 |
| 181 | 2590:4 | `\ref{cor:Gamma-labels}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 885 / 886 | 否 |
| 182 | 2596:42 | `\eqref{eq:waiting-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 1217 / 1220 | 否 |
| 183 | 2596:73 | `\eqref{eq:capacity-gradient}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 1274 / 1276 | 否 |
| 184 | 2634:14 | `\eqref{eq:boundary-value}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 1153 / 1155 | 否 |
| 185 | 2634:42 | `\eqref{eq:boundary-cost}` | D 梯度拼接与相对正则性的详细证明 | 证明 33，prop:regularity | 561 / 566 | 否 |
| 186 | 2660:3 | `\ref{cor:one-dimensional-min}` | E 证明依赖与校验口径 | 正文 | 1741 / 1742 | 否 |
| 187 | 2661:12 | `\ref{cor:verification-equality}` | E 证明依赖与校验口径 | 正文 | 1419 / 1420 | 否 |
| 188 | 2663:3 | `\ref{lem:no-early-boundary-exit}` | E 证明依赖与校验口径 | 正文 | 1495 / 1496 | 否 |
| 189 | 2664:5 | `\ref{thm:unique-q}` | E 证明依赖与校验口径 | 正文 | 1572 / 1573 | 否 |
| 190 | 2665:14 | `\ref{thm:unique-q}` | E 证明依赖与校验口径 | 正文 | 1572 / 1573 | 否 |
| 191 | 2668:9 | `\ref{prop:reachable}` | E 证明依赖与校验口径 | 正文 | 690 / 691 | 否 |
| 192 | 2668:32 | `\ref{lem:tracking-region}` | E 证明依赖与校验口径 | 正文 | 1057 / 1058 | 否 |
| 193 | 2669:13 | `\ref{prop:Gamma-geometry}` | E 证明依赖与校验口径 | 正文 | 819 / 820 | 否 |
| 194 | 2669:41 | `\ref{cor:Gamma-labels}` | E 证明依赖与校验口径 | 正文 | 885 / 886 | 否 |
| 195 | 2670:7 | `\ref{lem:strict-crossing}` | E 证明依赖与校验口径 | 正文 | 910 / 911 | 否 |
| 196 | 2670:50 | `\ref{lem:chi-regions}` | E 证明依赖与校验口径 | 正文 | 989 / 990 | 否 |
| 197 | 2671:21 | `\eqref{eq:ac-level-set}` | E 证明依赖与校验口径 | 正文 | 422 / 424 | 否 |
| 198 | 2672:25 | `\ref{prop:regularity}` | E 证明依赖与校验口径 | 正文 | 1268 / 1269 | 否 |
| 199 | 2672:49 | `\ref{lem:finite-entry}` | E 证明依赖与校验口径 | 正文 | 591 / 592 | 否 |
| 200 | 2704:10 | `\eqref{eq:medical-total-incidence}` | F 感染阈值与医疗需求 | 正文 | 2692 / 2695 | 否 |
| 201 | 2724:7 | `\eqref{eq:medical-incidence-bound}` | F 感染阈值与医疗需求 | 正文 | 2700 / 2702 | 否 |
| 202 | 2745:3 | `\eqref{eq:medical-threshold}` | F 感染阈值与医疗需求 | 正文 | 2736 / 2740 | 否 |

## 解释限制

前向引用属于排版次序事实；是否构成循环依赖还需阅读对应证明。附录中的独立计算或详细证明在正文陈述之后出现，不能单凭其位置判为循环。`self_reference` 只表示证明中指向其所证明对象的引用，不能代替证明依赖判断。
