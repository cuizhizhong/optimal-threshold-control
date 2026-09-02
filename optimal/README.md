# optimal：最优控制与传染病动力学代码

本目录整理了一套基于 MATLAB 的最优控制实验代码。内容以 [OpenOCL](https://openocl.org/) 为主要数值优化框架，并包含传染病动力学、种群/生态动力学和 SIR 模型的自定义示例。

这里的代码更适合作为研究计算、模型复现和算法试验工作区，而不是已经封装好的 MATLAB Toolbox。不同脚本中的参数、状态变量、控制变量和目标函数需要结合具体模型阅读。

## 目录结构

```text
optimal/
├── OpenOCL-master 0104/
│   ├── ocl.m                         # OpenOCL 初始化入口
│   ├── +ocl/                         # OpenOCL 主 MATLAB package
│   │   ├── Problem.m                 # 单阶段最优控制问题接口
│   │   ├── MultiStageProblem.m       # 多阶段/多相问题接口
│   │   ├── Simulator.m               # 动力系统仿真接口
│   │   ├── Solver.m                  # 兼容性封装接口
│   │   ├── Stage.m                   # 阶段、网格和边界管理
│   │   ├── +casadi/                  # CasADi 求解器接口
│   │   ├── +acados/                  # 可选的 acados 接口
│   │   ├── +model/                   # 模型、代价和约束转换
│   │   ├── +simultaneous/            # simultaneous transcription 工具
│   │   ├── +collocation/             # 配点方法工具
│   │   ├── +types/                   # 变量、边界和初值类型
│   │   ├── +utils/                   # 初始化、测试和辅助函数
│   │   └── +examples/                # OpenOCL 自带示例
│   ├── 最优控制代码/                 # 自定义最优控制模型
│   ├── cui/                          # 传染病模型、解析解和绘图代码
│   ├── doc/                          # MATLAB 生成的 API/示例文档
│   ├── Lib/                          # 外部库目录，主要是 CasADi
│   ├── Workspace/                    # CasADi 压缩包、测试和自动生成文件
│   ├── Log/                          # 历史运行日志
│   └── LICENSE                       # OpenOCL 许可文件
└── 示例/                             # 独立示例、解释文档和结果文件
```

其中，`+ocl` 是 MATLAB package 目录，因此代码中通过 `ocl.Problem`、`ocl.Simulator` 等名称访问接口。`doc/+ocl` 是随 OpenOCL 保存的文档源码/副本，不是使用时优先添加的另一套实现目录。

## OpenOCL 的基本工作流

大多数 OpenOCL 示例按照下面的方式组织：

1. 用 `ocl.Problem` 创建一个有限时间最优控制问题；
2. 在 `varsfun` 中声明状态、控制量、代数变量和参数，并设置边界；
3. 在 `daefun` 中用 `daeh.setODE` 定义状态方程；
4. 在 `pathcosts`、`gridcosts` 或 `terminalcost` 中定义目标函数；
5. 用 `setParameter` 和 `setInitialBounds` 设置参数与初始条件；
6. 调用 `getInitialGuess` 和 `solve` 求解，并从 `solution`、`times` 中提取结果。

典型代码骨架如下：

```matlab
problem = ocl.Problem(T, @varsfun, @daefun, @pathcosts, ...
    'N', 100, 'd', 3);

problem.setParameter('beta', beta);
problem.setInitialBounds('S', S0);
problem.setInitialBounds('I', I0);

initialGuess = problem.getInitialGuess();
[solution, times, solverInfo] = problem.solve(initialGuess);

function varsfun(vh)
    vh.addState('S', 'lb', 0, 'ub', 1);
    vh.addState('I', 'lb', 0, 'ub', 0.02);
    vh.addControl('u', 'lb', 0, 'ub', 1);
    vh.addParameter('beta');
end

function daefun(daeh, x, ~, u, p)
    daeh.setODE('S', -(1-u.u) * p.beta * x.S * x.I);
    daeh.setODE('I',  (1-u.u) * p.beta * x.S * x.I);
end

function pathcosts(ch, ~, ~, u, ~)
    ch.add(u.u^2);
end
```

`N` 控制时间网格数量，`d` 为每个控制区间的插值多项式阶数。实际脚本中的 `N` 和 `d` 会因模型和数值精度要求而不同。

## 自定义模型

### `最优控制代码/`

这一目录主要保存基于 `ocl.Problem` 的单阶段最优控制实验：

| 文件 | 内容 | 主要变量/控制量 |
| --- | --- | --- |
| `example.m` | 最小的标量状态和双控制量示例，用于检查 OpenOCL 调用流程 | `x`；`u1`、`u2` |
| `example_vanderpol2.m` | 受控 Van der Pol 型系统 | `x`、`y`；`F` |
| `test0104.m` | `P-N` 动力学模型，使用两个控制量并以积分代价实现终止时间优化 | `P`、`N`；`delta`、`mu` |
| `xp1218.m` | 两状态种群/环境模型 | `Xt`、`pt`；`delta0`、`delta1` |
| `xyp0102.m` | 三状态种群/捕食或资源模型 | `Xt`、`Yt`、`pt`；`beta0`、`beta1` |
| `xyp_2_0102.m` | 与 `xyp0102.m` 相同的动力学结构，但加入额外的路径代价项 | `Xt`、`Yt`、`pt`；`beta0`、`beta1` |
| `CUI.m` | S-I 传染病模型，以 `b(t)` 调节传播过程 | `S`、`I`；`b` |
| `CUi_p.m` | 文件名与函数声明存在不一致，函数声明为 `CUI_q`；使用前应先确认调用目标 | 见脚本内部定义 |

这些脚本通常在文件末尾定义 `varsfun`、`daefun` 和 `pathcosts`。因此修改模型时，优先从这三个函数以及主函数中的参数、初值和网格设置入手。

### `cui/`

`cui` 目录集中放置传染病动力学控制实验：

- `CUI.m`：用控制量 `b(t)` 调节 S-I 系统，并输出 `CUI.pdf`；
- `CUI_q.m`：用 `q(t)` 控制传播过程，同时将数值最优控制与一段 Lambert W 解析构造进行比较，并输出 `CUI_q.pdf`；
- `CUI_c.m`：用 `c(t)` 建模控制强度，并输出 `CUI_c.pdf`；
- `CUI_qc.m`：同时使用 `c(t)` 和 `q(t)` 两个控制量，并输出 `CUI_qc.pdf`；
- `ODEODEODE.m` 与 `ODE_SI.m`：根据阈值 `I_m` 计算控制起止时间 `t1`、`t2`，再用 `ode45` 仿真分段控制策略；
- `CUI*.pdf`、`ode.pdf`：已有的计算结果或图形输出，不是求解器实现本身。

这些 S-I 脚本普遍使用状态约束 `I <= I_m`，并绘制 `S(t)`、`I(t)`、控制量以及阈值线。脚本中的具体目标函数和控制边界应以对应 `.m` 文件为准。

### `示例/`

该目录既包含 OpenOCL 示例的整理版本，也包含一套不依赖 `ocl.Problem` 的 SIR 直接离散化示例：

- `SIR_OPC.m`：先用 `ode45` 生成无控制轨迹，再用 MATLAB `fmincon`、RK4 多重打靶连续性约束和 `I <= Imax` 状态上界求解 SIR 控制问题；
- `xp1218.m`：`最优控制代码/xp1218.m` 的示例版本；
- `代码解释.md`、`SIR代码解释.md`：对应代码的中文说明；
- `API documentation v7 - OpenOCL.pdf`：OpenOCL API 资料；
- `.fig`、`.eps`、`.mat`：示例绘图和数值结果文件。

`SIR_OPC.m` 使用 MATLAB Optimization Toolbox 中的 `fmincon`，它与 `OpenOCL-master 0104/+ocl` 的 CasADi 求解流程是两条独立路线。

## 环境与初始化

### 基本依赖

- MATLAB：需要支持 package、`classdef`、`ode45` 和脚本/函数中的相关语法；
- OpenOCL：已包含在 `OpenOCL-master 0104` 中；
- CasADi：OpenOCL 默认通过 CasADi 接口构造 NLP 并调用 IPOPT；
- MATLAB Optimization Toolbox：仅运行 `示例/SIR_OPC.m` 等直接调用 `fmincon` 的脚本时需要；
- acados：仅在明确使用 `+ocl/+acados` 接口时需要，不是普通 `ocl.Problem` 示例的必需依赖。

当前仓库中已有 `Lib/casadi` 和 `Workspace` 相关文件。CasADi 的具体二进制文件具有平台和 MATLAB 版本依赖，跨平台使用时不要假定仓库内的 Windows 版本可以直接工作。

### 初始化 OpenOCL

在 MATLAB 命令窗口执行：

```matlab
repoRoot = 'path\to\optimal-threshold-control';
projectRoot = fullfile(repoRoot, 'optimal', 'OpenOCL-master 0104');
cd(projectRoot);
addpath(projectRoot);
ocl;
```

`ocl` 会调用 `ocl.utils.startup`，完成 OpenOCL、`doc`、`Lib` 和 `Workspace` 路径设置，并检查 CasADi。若 CasADi 不存在或不可用，初始化过程可能要求输入并下载/解压 CasADi；这一步需要网络访问和用户确认。

### 运行一个最小示例

```matlab
repoRoot = 'path\to\optimal-threshold-control';
projectRoot = fullfile(repoRoot, 'optimal', 'OpenOCL-master 0104');
cd(projectRoot);
addpath(projectRoot);
ocl;

addpath(fullfile(projectRoot, '最优控制代码'));
[solution, times, problem] = example;
```

### 运行传染病示例

建议一次只把一个自定义模型目录加入 MATLAB path，以减少同名函数冲突：

```matlab
repoRoot = 'path\to\optimal-threshold-control';
projectRoot = fullfile(repoRoot, 'optimal', 'OpenOCL-master 0104');
cd(projectRoot);
addpath(projectRoot);
ocl;

cd(fullfile(projectRoot, 'cui'));
addpath(pwd);
[solution, times, problem] = CUI_q;
```

运行独立的 SIR 多重打靶版本时，不需要调用 OpenOCL：

```matlab
repoRoot = 'path\to\optimal-threshold-control';
exampleRoot = fullfile(repoRoot, 'optimal', '示例');
cd(exampleRoot);
SIR_OPC;
```

## 结果与文件位置

部分脚本使用相对路径写出结果。例如 `cui/CUI_q.m` 会把 `CUI_q.pdf` 写入 MATLAB 当前工作目录，`示例/SIR_OPC.m` 会保存 `OPC.mat`。为避免结果散落到其他目录，运行前应先 `cd` 到对应示例目录，或修改脚本中的输出路径。

`Workspace/` 还可能产生测试目录、自动生成代码和求解器临时文件。不要把这些自动生成文件当作模型源代码；清理前请确认其中没有需要保留的实验结果。

## 使用注意事项

1. **避免同名函数冲突。** `最优控制代码/`、`cui/` 和 `示例/` 中存在同名或近似同名文件，例如 `CUI.m`、`xp1218.m`。使用 `which CUI -all`、`which xp1218 -all` 检查 MATLAB 实际调用的文件。
2. **注意文件名与函数名。** `最优控制代码/CUi_p.m` 内部函数声明为 `CUI_q`，在大小写敏感的系统上尤其容易导致调用失败；建议后续将文件名与主函数名统一。
3. **检查初值和边界。** OpenOCL 的 `setInitialBounds`、状态上下界和控制上下界共同决定可行域。修改 `I_m`、初值或控制边界后，应重新检查初始猜测是否可行。
4. **区分状态网格与控制网格。** `solution.states.*` 与 `solution.controls.*` 对应的时间数组通常分别来自 `times.states.value` 和 `times.controls.value`，绘图和积分时不要直接假定二者长度相同。
5. **结果不等于全局最优性证明。** CasADi/IPOPT 或 `fmincon` 给出的通常是离散非线性规划问题的数值解；结果依赖网格、插值阶数、初始猜测、容差和参数设置。
6. **保留原始许可信息。** OpenOCL 源文件带有 University of Freiburg 等原作者的版权声明，重新分发或修改相关代码时应一并遵守 `LICENSE` 和源文件中的 3-Clause BSD License 声明。

## 相关资料

- [OpenOCL 官方网站](https://openocl.org/)
- [OpenOCL API 文档](https://openocl.org/api-docs/)
- [OpenOCL 原始仓库](https://github.com/OpenOCL/OpenOCL)
- [本项目仓库](https://github.com/cuizhizhong/optimal-threshold-control)
- [CasADi 官方网站](https://web.casadi.org/)
