# 最终交付校验清单

校验日期：2026-07-28

## A. 交付内容

- [x] 完整中文 LaTeX 主文件：`latex/main.tex`。
- [x] BibTeX 文献库：`latex/references.bib`。
- [x] 已生成参考文献表：`latex/main.bbl`。
- [x] 十个独立启动的 Python 图形程序：`python/Figure_1_*.py` 至 `python/Figure_10_*.py`。
- [x] Python 公共解析/数值模块与数据生成器：`python/common_tracing.py`、`python/generate_data.py`。
- [x] 十个独立启动的 MATLAB 图形程序：`matlab/Figure_1_*.m` 至 `matlab/Figure_10_*.m`。
- [x] 十幅 300 dpi JPG：`figures/Figure_1_*.jpg` 至 `figures/Figure_10_*.jpg`。
- [x] 十二个 CSV 数据文件。
- [x] 最终 PDF：`tracing_isolation_optimal_control.pdf`。
- [x] Linux/macOS 与 Windows 编译脚本：`build.sh`、`build.bat`。
- [x] 统一说明：`README.md`。

## B. Python 与数据验证

- [x] 对全部 12 个 Python 文件执行 `python -m py_compile`，无语法错误。
- [x] 十个 `Figure_*.py` 均在当前环境实际执行成功。
- [x] `python/generate_data.py` 实际执行成功。
- [x] `python/generate_data.py --recompute-tv` 实际执行成功；三组时变正则化直接配置重新求解完成。
- [x] 时变基准方案返回 `success=True`，SLSQP 信息为 `Optimization terminated successfully`。
- [x] 常接触率解析成本与分段闭式计算完全一致：误差 `0.000e+00`。
- [x] 稠密时间网格积分与解析成本之差约 `1.135e-05`。
- [x] 常接触率轨道满足 `max i(t)=K=0.15`，数值超越量为 `0.000e+00`。
- [x] 解除隔离点位于最大安全边界，残差为 `0.000e+00`。
- [x] 完全跟踪弧不变量残差为 `8.327e-17`。
- [x] 切换条件残差约 `-4.292e-08`。
- [x] 一维成本在切换点的一阶差分约 `4.40e-08`，二阶差分约 `3.6346>0`。
- [x] 时变接触率优化轨道的容量超越量为 `5.551e-17`；无隔离峰值约 `0.4599709187`。

详细结果见：

- `validation/python_validation.txt`
- `validation/numerical_validation.txt`
- `validation/logs/data_generation.log`
- `validation/logs/time_varying_recompute.log`
- `validation/logs/python_run.log`

## C. MATLAB 校验

- [x] 十个 MATLAB 文件均使用脚本自身位置解析根目录，避免依赖当前工作目录。
- [x] 十个文件的目标输出名均与对应 JPG 一致。
- [x] 十个文件均指定 `-r300` 输出。
- [x] 对括号、方括号、花括号、`function/if/for/while/try/end` 控制块进行了静态配对检查，10/10 通过。
- [x] 图 1--5 各自包含所需局部函数；图 6--10 独立读取包内 CSV。
- [ ] 未进行 MATLAB/Octave 运行时执行：当前容器没有 MATLAB 或 Octave 可执行文件。

静态检查记录见 `validation/matlab_static_check.txt`。因此，本文件包不把 MATLAB 运行结果表述为“已实际执行”；JPG 由已实际运行的 Python 程序生成。

## D. JPG 校验

- [x] 十幅图均可打开。
- [x] 十幅图均记录为 300×300 dpi。
- [x] 像素尺寸约为 2429--2490 像素宽、1517--1698 像素高。
- [x] 图形总览已生成：`figures/contact_sheet.jpg`。

逐图元数据见 `validation/figure_metadata.csv`。

## E. LaTeX 编译验证

- [x] 使用 XeLaTeX 编译。
- [x] 使用 `bibtex8` 生成参考文献，并继续多轮 XeLaTeX 处理交叉引用。
- [x] 根目录 `build.sh` 已完成一次端到端测试，退出状态为 0。
- [x] 最终 `main.log` 扫描无未定义引用、未定义引文、overfull/underfull、宏包警告或 LaTeX 警告。
- [x] 最终 PDF 复制到根目录。

相关记录：

- `validation/latex_final_warning_scan.txt`
- `validation/logs/latex_build.log`
- `validation/logs/build_sh_test.log`

## F. PDF 预检与视觉验证

- [x] 最终 PDF 可由 PyMuPDF 打开。
- [x] 26 页，全部为 A4，页面方向一致。
- [x] 未加密，无 XFA 表单，无 JavaScript。
- [x] 判定为文本型 PDF，而非扫描图像 PDF。
- [x] 所有列出的字体均嵌入并子集化。
- [x] 以 180 dpi 渲染全部 26 页，无渲染失败。
- [x] 检查了 26 页总览；对第 1、3、17、23、26 页进行全分辨率检查。
- [x] 未发现文字裁切、图表越界、黑方块、乱码、重叠或缺图。
- [x] 第 3 页的大面积留白是目录最后一页的正常排版，不是缺失页面。

相关记录：

- `validation/pdf_preflight.txt`
- `validation/pdf_inspect.txt`
- `validation/pdfinfo.txt`
- `validation/pdffonts.txt`
- `validation/pdf_contact_sheet.jpg`

## G. 理论结论的表述边界

- [x] 常接触率下的唯一性定理明确列出端点唯一、横截相交和无正长度奇异弧等条件。
- [x] 未把一般时变 `c(t)` 的线性成本问题误述为无条件唯一。
- [x] 时变算例明确标注为严格凸正则化后的离散直接配置结果。
- [x] 区分了解析证明、在显式条件下的验证定理和基准数值证据。

## H. 最终状态

**通过。** 除 MATLAB 运行时执行受当前环境缺少 MATLAB/Octave 限制外，用户要求的 LaTeX、Python、MATLAB、JPG、CSV、最终 PDF、校验记录和统一压缩包内容均已准备完成。
