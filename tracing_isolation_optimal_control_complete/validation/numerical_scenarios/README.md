# 独立解析检查点

`scenario_inputs.json` 是 MATLAB 配置和 Python 生成器共享的原始参数、初值和案例定义。
每条记录通过 `case_id` 匹配；修改 JSON 案例排列顺序不会改变解析量或 MATLAB 主案例配置。
`main_N` 只记录预先指定的主网格，不参与解析公式。参数与五个主初值保持既有设置。

旧程序与 fixture 可追溯至 Git 提交 `e08b0ba`，本地整理副本位于
`archive/pending_deletion/validation/numerical_scenarios/`。旧程序还会写论文，故本轮新增独立生成器，
未执行旧写入入口，也未改动旧归档。

从仓库根目录执行：

```powershell
python -m pip install -r tracing_isolation_optimal_control_complete/validation/numerical_scenarios/requirements.txt
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --check
```

`--check` 以 50 位小数精度重新计算并只读比较已有 fixture；绝对比较容差为 `5e-12`。
只有明确更新解析 fixture 时使用：

```powershell
python tracing_isolation_optimal_control_complete/validation/numerical_scenarios/generate_analytic_checkpoints.py --write
```

生成器从正文的 `a`、`g`、`G`、`Phi` 与原始 `Theta` 方程出发，先求沿特征线的峰点，
再在峰点右侧括住非平凡根，显式排除 `s=z`。有界二分法容差为 `1e-40`；
等待时间采用自适应积分并用更高精度复算确认收敛。fixture 存储双精度可读值、生成精度与输入摘要。
它不读 `.mat`、`scenario_summary.csv`、`J_openocl` 或 MATLAB 计算数组，不含求解器结果。
该独立实现用于计算交叉核查，不提供新的解析最优性证明。

无需 OpenOCL 的测试命令：

```powershell
python -m unittest discover -s tracing_isolation_optimal_control_complete/validation/numerical_scenarios -p test_analytic_checkpoints.py -v
```

MATLAB 从仓库根目录执行：

```matlab
addpath(fullfile(pwd,'tracing_isolation_optimal_control_complete','matlab','numerical_scenarios'));
verify_numerical_reference();
verify_reference_dependency_tests();
```

MATLAB 核查参数、全部几何量、初值、等待/容量/完全跟踪时间、切换/解除状态、成本、
容量可行性、正性、总量不增、完全跟踪不变量和安全解除点，保留原有稀疏采样及退化弧回归。
正式入口缺少 fixture 时立即报错，并给出精确路径和生成命令。
依赖测试验证输入/fixture 的顺序无关性，以及缺失、重复 ID、篡改初值和成本时严格失败。
这些入口均不执行优化，不能作为五例 OpenOCL 重算或数值最优性验证的证据。

已实际使用 Python `3.12.8`、`mpmath==1.3.0`；后者是唯一固定 Python 依赖。
本轮测试记录及步骤状态见 `REVISION_STATUS.md`，求解来源与缓存测试见 MATLAB 目录说明。

`verify_stage02_integrity.py` 默认比较原工作区受保护文件的原字节。跨目录检出时 Git 可能转换文本换行，使用 `--root <检出目录> --normalized-text` 只对文本规范 CRLF/LF 后核对；二进制仍按原字节。该检查不改变源码哈希或原始求解来源。
