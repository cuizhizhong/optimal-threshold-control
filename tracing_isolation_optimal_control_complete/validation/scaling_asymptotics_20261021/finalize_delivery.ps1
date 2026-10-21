# 以原生文件API同步已通过编译的D批产物；不重跑编译或数值计算。
$ErrorActionPreference = 'Stop'
$batchDir = $PSScriptRoot
$projectDir = Split-Path (Split-Path $batchDir -Parent) -Parent
$attemptReport = Get-Content -LiteralPath (Join-Path $batchDir 'attempt4/build_report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($attemptReport.documents.Count -ne 2) { throw '文档数不为2' }
foreach ($sourceProperty in $attemptReport.source_sha256.PSObject.Properties) {
    $sourcePath = Join-Path (Join-Path $projectDir 'latex') $sourceProperty.Name
    if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLower() -ne $sourceProperty.Value) { throw "源码哈希不符：$sourcePath" }
}
foreach ($document in $attemptReport.documents) {
    if (-not $document.success -or $document.final_log_issues.Count -ne 0 -or $document.commands.Count -ne 4) { throw '编译验收未通过' }
    foreach ($command in $document.commands) { if ($command.exit_code -ne 0) { throw '编译命令未通过' } }
    $pdfPath = Join-Path $attemptReport.build_directory ($document.name + '.pdf')
    if ((Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash.ToLower() -ne $document.pdf_sha256) { throw '编译PDF哈希不符' }
}
$deliveredFiles = @()
foreach ($fileName in @('main.pdf', 'theory_only.pdf', 'main.bbl')) {
    $builtPath = Join-Path $attemptReport.build_directory $fileName
    $deliveredPath = Join-Path (Join-Path $projectDir 'latex') $fileName
    $builtHash = (Get-FileHash -LiteralPath $builtPath -Algorithm SHA256).Hash.ToLower()
    $deliveredHash = (Get-FileHash -LiteralPath $deliveredPath -Algorithm SHA256).Hash.ToLower()
    if ($builtHash -ne $deliveredHash) {
        Copy-Item -LiteralPath $builtPath -Destination $deliveredPath -Force
        $deliveredHash = (Get-FileHash -LiteralPath $deliveredPath -Algorithm SHA256).Hash.ToLower()
    }
    if ($builtHash -ne $deliveredHash) { throw "同步后哈希不符：$fileName" }
    $deliveredFiles += @{path=$deliveredPath; sha256=$deliveredHash}
}
$deliveryReport = @{source_attempt=4; compilation_success=$true; commands_exit_zero=8; pages=@{main=46; theory_only=36}; original_copy_failure_preserved='attempt4/build_report.json'; copy_api='PowerShell Copy-Item'; files=$deliveredFiles; success=$true}
$deliveryReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $batchDir 'delivery_report.json') -Encoding utf8NoBOM
Write-Output 'D delivery: 3/3 identical files; build commands 8/8; pages 46/36'
