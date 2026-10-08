# 第一版归档

本目录保存论文第一版的数值代码、数据和输出，不参与当前论文编译或当前长时域 OpenOCL 实验。

- `python/`：第一版数据生成和十张图的 Python 代码。
- `matlab/`：第一版十张图的 MATLAB 代码，以及旧 `CUI_q` 基准运行入口。
- `data/`：第一版 CSV 数据和旧 E2 基准结果。
- `figures/`：第一版十张 JPG 图及总览。
- `tracing_isolation_optimal_control.pdf`：第一版报告。
- `build.bat`、`build.sh`、`requirements.txt`、`MANIFEST.txt`：第一版环境及文件说明，仅供追溯；第一版 LaTeX 源稿由 Git 历史保存。

如需完整恢复第一版，应从 Git 历史取回相应 LaTeX 源稿，并在独立目录中运行旧脚本，避免覆盖当前 `data/numerical_scenarios/` 和 `figures/numerical_scenarios/`。
