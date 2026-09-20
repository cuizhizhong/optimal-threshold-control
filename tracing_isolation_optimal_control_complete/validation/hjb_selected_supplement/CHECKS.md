# HJB 精选增补验收记录

日期：2026-09-20。基线主稿 blob：929a3a523c059adcd74efc4e47c774e0c38a1c11；基线提交：20b3bdc76ba45a5b7edeea691043fda2bcf7a0f8。

## 实际修改

- snippets/01_internal_C1_patching.tex：内部界面的梯度延拓与 C^1 拼接；已按指定位置完成。
- snippets/02_relative_local_lipschitz.tex：相对局部 Lipschitz 的显式估计；已按指定位置完成。
- snippets/03_implicit_function_domain.tex：隐函数定理的局部定义域；已按指定位置完成。
- snippets/04_tracking_zero_set_and_normals.tex：切换零集与法向量关系；已按指定位置完成。
- snippets/05_relative_open_regions.tex：等待区与完全跟踪区的相对开放性；已按指定位置完成。
- snippets/06_interval_flow_argument.tex：从几乎处处的控制选择到分段状态方程；已按指定位置完成。
- snippets/07_time_set_coverage.tex：验证引理中的时间集合覆盖；已按指定位置完成。
- snippets/08_platform_hamiltonian_clarification.tex：平台 Hamiltonian 与允许控制集的区分；已按指定位置完成。
- snippets/09_candidate_integral_equation.tex：候选反馈轨道的积分表述；已按指定位置完成。
- snippets/10_model_comparison.tex：与 MSW 的动力学及成本差别；已按指定位置完成。
- snippets/11_optimal_synthesis.tex：最优策略的分区汇总；已按指定位置完成。

12_small_edits.md 前七项完成；第八项的核心含义已在 sec:HJB 表达，不重复追加。源码差异见 source.diff，标签位置见 static_checks.json。

## 静态及论证衔接检查

- 171 个原标签全部保留，新增两个标签，共 173 个；没有重复标签、未定义引用或缺失文献键。环境及分组括号配对通过。
- thm:verification、cor:verification-equality、lem:no-early-boundary-exit 的环境与证明逐字节保留。唯一性证明剔除指定插入段落后与原稿一致。
- 原有 equation、align 和 table 环境逐字节保留，模型、成本、控制类和候选公式没有变化。
- 内部 C1 拼接使用局部坐标与梯度匹配，不依赖后续 Lipschitz 结论；容量迹估计使用已有公式的有界导数。
- 新相对开放性注记位于 chi-regions 之后；时间区间论证位于容量下段零测集论证之后。
- 最优结构汇总位于唯一性证明之后，作为已有结果的推论；前置定理不反向使用该推论。
- MSW 对照核对本地期刊 PDF 第 3 页式（1）、（2）：b=0 时易感坐标不变而感染衰减，成本为 [beta-b]_+，b 高于自然水平时零成本。

## 编译

在原 latex 目录实际运行，退出码均为 0：

```powershell
latexmk -xelatex -synctex=1 -interaction=nonstopmode -halt-on-error main.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error theory_only.tex
```

控制台输出：build_main.log、build_theory.log。最终日志：main_final.log、theory_only_final.log。最终日志无 Warning、缺字、未定义引用、重复标签、Overfull 或 Underfull 记录。main.synctex.gz 非空。

## 页面与输出

全文 36 页，理论校样 25 页。全部页面已渲染检查：公式、图表、页眉和分页未见裁切或重叠，十张原图保留。新增策略汇总为推论 12.3；一维全局极小推论自动调整为 12.4。原有目录末页较稀疏，本次未改目录版式。

根目录 PDF 已同步，哈希与 latex/main.pdf 一致，详见 static_checks.json。渲染图片保留在本地 QA 目录，不纳入提交。

## 未执行事项与边界

未修改或重跑数值实验，未改变时变结论，未新增数学假设。静态检查、论证衔接核对及实际编译不构成形式化证明认证或独立同行审稿。
