# 使用原生 XeLaTeX/BibTeX，避免 PATH 中 MSYS Perl 对 Windows 路径的转换。
$ErrorActionPreference = 'Stop'
$reportRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$repoRoot = Split-Path $reportRoot -Parent
$latexRoot = Join-Path $reportRoot 'latex'
$buildRoot = Join-Path $repoRoot 'tmp\numerical_revision_build'
$oldBibInputs = $env:BIBINPUTS
$env:BIBINPUTS = "$latexRoot;"
Push-Location $latexRoot
try {
    foreach ($name in @('main', 'theory_only')) {
        $out = Join-Path $buildRoot $name
        New-Item -ItemType Directory -Force $out | Out-Null
        $arg = '-output-directory=' + $out.Replace('\','/')
        & xelatex -interaction=nonstopmode -halt-on-error $arg "$name.tex" *> (Join-Path $out 'pass1.txt')
        if ($LASTEXITCODE -ne 0) { throw "XeLaTeX first pass failed: $name" }
        Push-Location $out
        try {
            & bibtex $name *> (Join-Path $out 'bibtex.txt')
        } finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) { throw "BibTeX failed: $name" }
        foreach ($pass in 2..3) {
            & xelatex -interaction=nonstopmode -halt-on-error $arg "$name.tex" *> (Join-Path $out "pass$pass.txt")
            if ($LASTEXITCODE -ne 0) { throw "XeLaTeX pass $pass failed: $name" }
        }
        $log = Get-Content -Raw (Join-Path $out "$name.log")
        if ($log -match 'There were undefined references|There were undefined citations|multiply defined|Float too large') {
            throw "Unresolved LaTeX warning: $name"
        }
        Write-Output "LATEX_BUILD_OK $name"
    }
} finally {
    Pop-Location
    $env:BIBINPUTS = $oldBibInputs
}
