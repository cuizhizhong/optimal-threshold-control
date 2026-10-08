# 跟踪隔离模型中双传播系数的最优控制与唯一性

本目录保留当前论文、长时域 OpenOCL 数值实验及必要参考文献。历史讨论稿、证明补充包和审查材料已从当前工作区移出；第一版代码与数据统一归档在 `archive/first_version/`。

## 当前文件结构

- `latex/main.tex`：论文的唯一 LaTeX 源文件，含数值正文和数值宏。
- `latex/main.pdf`：当前编译稿。
- `latex/references.bib`：BibTeX 文献库。
- `matlab/numerical_scenarios/`：五个长时域算例的配置、OpenOCL 求解、作图和 LaTeX 导出代码。
- `validation/numerical_scenarios/`：共享原始输入、独立 Python 解析检查点、无优化器测试及本轮执行状态。
- `data/numerical_scenarios/`：五个主算例及必要的网格、初猜和诊断复核结果。
- `figures/numerical_scenarios/`：论文使用的三张 PDF 图和 PNG 预览。
- `ref/`：论文引用或理论核对所需的原始文献。
- `archive/first_version/`：第一版 Python/MATLAB 代码、CSV 数据、十张旧图、旧 PDF 和旧基准结果。

## 数值实验

修改计划第 0–2 步已恢复独立解析检查点并修复来源和缓存。详细状态见 `validation/numerical_scenarios/REVISION_STATUS.md`。本批未运行优化；现有数据与图、正文均保留，历史数据标为 `legacy_unverified`。新图及正文导出需要后续主算例产生的 selection manifest。

固定参数为

```text
p=0.5, c=2, gamma=0.3, K=0.15, T=300, d=2
```

E1、E3、E5 使用 `N=4000`，E2、E4 使用 `N=8000`。从仓库根目录启动 MATLAB：

```matlab
addpath(fullfile(pwd, 'tracing_isolation_optimal_control_complete', ...
    'matlab', 'numerical_scenarios'));
run_numerical_scenarios();
make_numerical_figures();
export_numerical_latex();
```

`make_numerical_figures()` 和 `export_numerical_latex()` 只读取已经保存的结果。导出器直接更新 `latex/main.tex` 中两个带有 `AUTO-GENERATED NUMERICAL` 标记的区域，不生成额外 TeX 文件。

## 编译论文

Windows：

```powershell
.\build.bat
```

Linux/macOS：

```bash
bash build.sh
```

两个脚本均执行 XeLaTeX、BibTeX 和两次 XeLaTeX，输出为 `latex/main.pdf`。

## 归档说明

第一版归档只用于追溯，不参与当前论文编译和长时域数值实验。旧文件在 Git 历史中仍可恢复；归档目录保留了原来的相对分类，便于查找旧数据、绘图代码和结果。
