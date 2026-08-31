# 一键重出 §8 三张占优图（图 20/21/22）并复制到主论文 figures/。
# 用法（PowerShell）:  .\run_all.ps1
# 前提：conda 环境 thesis 可用。脚本已自带 sys.path 定位，无需设 PYTHONPATH。
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUTF8 = "1"

function Run($label, $script) {
    Write-Host "== $label : $script ==" -ForegroundColor Cyan
    conda run --no-capture-output -n thesis python $script
    if ($LASTEXITCODE -ne 0) { throw "$script 运行失败 (exit $LASTEXITCODE)" }
}

Run "图 20"            "dom_pretty.py"
Run "图 21 Panel A"    "panels.py"
Run "图 22 重算(~25s)" "compute_B.py"
Run "图 22 Panel B"    "plot_B.py"
Run "图 23 轨迹分解"   "plot_B_decomp.py"

# 名单须与 panels.py 的 PANEL_A_CASES 输出名一致（曾长期写成已废弃的
# N1e4/N40377/N91727，导致 copy 阶段报错）：正文用 fig_panel_A（=N2e4 的别名），
# 附录三例为 Ncumstar / Nstar45 / Nstarinf。
$fig = Join-Path $PSScriptRoot "..\figures"
foreach ($f in "fig_dom_combined", "fig_panel_A", "fig_panel_A_N2e4",
                 "fig_panel_A_Ncumstar", "fig_panel_A_Nstar45", "fig_panel_A_Nstarinf",
                 "fig_panel_B", "fig_panel_B_trajectory_decomposition") {
    Copy-Item (Join-Path "dominance_panels" "$f.pdf") $fig -Force
    Write-Host "  copied $f.pdf -> figures/" -ForegroundColor Green
}
Write-Host "完成。正文图与 Panel A 附录图已更新到 $((Resolve-Path $fig).Path)" -ForegroundColor Green
