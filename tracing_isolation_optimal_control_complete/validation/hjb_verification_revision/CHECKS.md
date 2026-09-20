# HJB 修订验收记录

日期：2026-09-20。基线提交：e04803d7e40d4e99ba4f97f7b7638738dc963794；主稿基线 blob：5e43b4af7db0871726ad1a4e977f17f75ed87570。

## 修改与论证衔接

按标签整合五个片段，保留全局验证定理及其原证明，增加等号条件和容量弧延续引理，替换唯一性证明，补充内侧导数和证明依赖说明。

- 等号条件保留有限成本限定、首次到达后的成本积分和初值已安全情形。
- 容量弧引理只针对最优轨道，保留开放时间分支反证和延续论证。
- 唯一性证明保留容量边界下段零测集、切换横穿、分段状态方程唯一性和安全集后的零控制。
- 全局验证定理未反向引用新增结果；新增推论和引理不依赖唯一性定理。一维推论仍位于唯一性定理之后。
- 模型、成本、控制类、分区及参数范围未改；时变与数值部分未改，未重跑数值实验。

## 静态检查

171 个标签，原标签保留、新增 7 个；无重复标签、未定义引用和缺失文献键；环境配对通过。受保护环境和时变与数值部分逐字节检查通过，详见 static_checks.json。

新增标签位置（main.tex）：
- `cor:verification-equality`：第 1116 行。
- `eq:optimal-boundary-continuation`：第 1209 行。
- `eq:trajectory-verification-residual`：第 1125 行。
- `eq:verification-equality-conditions`：第 1143 行。
- `eq:verification-gap`：第 1135 行。
- `lem:no-early-boundary-exit`：第 1192 行。
- `rem:verification-equality-uniqueness`：第 1175 行。

## 编译与页面检查

在原 latex 目录执行，两条命令退出码均为 0：

```powershell
latexmk -xelatex -synctex=1 -interaction=nonstopmode -halt-on-error main.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error theory_only.tex
```

控制台日志为 build_main.log 和 build_theory.log，最终 LaTeX 日志为 main_final.log 和 theory_only_final.log。最终日志无 Warning、缺字、未定义引用、重复标签、Overfull 或 Underfull 记录，SyncTeX 文件非空。

全文 33 页，理论校样 22 页，使用真实图片。全部页面已渲染检查，全文第 18—20 页另作放大检查；未见裁切、重叠或图表缺失，页眉正常。自动编号为推论 11.2、引理 12.1、唯一性定理 12.2。

根目录全文 PDF 已同步，与 latex/main.pdf 的 SHA-256 一致，详见 static_checks.json。页面图像保存在本地 QA 目录，不纳入 Git。

上述检查分别核对论证衔接、静态结构、实际编译和页面排版，不构成形式化证明认证或独立数学同行审稿。
