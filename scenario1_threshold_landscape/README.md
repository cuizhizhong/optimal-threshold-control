# 情景一阈值响应图谱

本目录用于独立生成 `N=763` 情景一阈值响应图谱，不修改主论文工程，也不覆盖主项目中的 `figures/`、`tables/` 或 `code/` 结果。

## 目录结构

```text
scenario1_threshold_landscape/
├── README.md
├── run_all.m
├── current_run.mat
├── current_run.txt
├── common/
├── scripts/
├── current_run/
│   ├── output_csv/
│   ├── figures/
│   ├── tables/
│   └── logs/
└── archive_runs/
```

- `run_all.m`：推荐入口，顺序生成数据、图和表。
- `scripts/`：数据生成、单独绘图和表格脚本。
- `common/`：共享参数、指标计算、轨迹重构、读表和保存图形函数。
- `current_run/`：最新一轮完整结果。
- `archive_runs/`：重新运行前自动归档的旧 `current_run/`。

## 推荐运行

从任意位置运行：

```powershell
matlab -batch "run('C:\Me\Works\thesis\draft\3\scenario1_threshold_landscape\run_all.m')"
```

运行 `run_all.m` 时，如果已经存在 `current_run/`，脚本会先将其移动到：

```text
archive_runs/run_YYYYMMDD_HHMMSS/
```

然后重新生成新的 `current_run/`。如果 Windows 权限拒绝移动 PDF/CSV 文件，脚本会复制 `current_run/` 到归档目录，并在原 `current_run/` 中覆盖生成本轮固定输出。

## 单独运行模块

已有 `current_run/output_csv/landscape_summary.csv` 后，可以单独重画某一类图，例如：

```powershell
matlab -batch "run('C:\Me\Works\thesis\draft\3\scenario1_threshold_landscape\scripts\plot_heatmaps.m')"
```

常用脚本：

- `scripts/generate_landscape_data.m`：只生成 CSV 和诊断。
- `scripts/plot_baseline_validation.m`：生成基准验证图和基准表。
- `scripts/plot_sensitivity_curves.m`：生成一维敏感性图。
- `scripts/plot_heatmaps.m`：生成二维热图，当前包括 `heatmap_t1.pdf`。
- `scripts/plot_duration_regions.m`：生成控制时长区域图。
- `scripts/plot_representative_trajectories.m`：生成代表轨迹图。
- `scripts/plot_cumulative_decomposition.m`：生成累计感染分解图。
- `scripts/write_representative_tables.m`：生成代表组合表。

## 当前结果

当前最新结果路径记录在：

```text
current_run.txt
```

完整结果应包含：

- `current_run/output_csv/`：5 个 CSV；
- `current_run/figures/`：14 张 PDF；
- `current_run/tables/`：2 个 LaTeX 表格；
- `current_run/logs/`：各脚本运行日志。
