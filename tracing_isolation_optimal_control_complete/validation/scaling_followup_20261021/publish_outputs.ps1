# 同步本批已通过四阶段验收的PDF；以哈希核对源和产物，映射文件时保留备份后原子替换。
$ErrorActionPreference = 'Stop'
$batchDir = $PSScriptRoot
$projectDir = Split-Path (Split-Path $batchDir -Parent) -Parent
$r = Get-Content -LiteralPath (Join-Path $batchDir 'workspace_attempt1/build_report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $r.success -or $r.documents.Count -ne 2) { throw '仓库内双稿构建尚未通过' }
foreach ($sourceItem in $r.source_sha256.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $projectDir $sourceItem.Name)).Hash.ToLower() -ne $sourceItem.Value) { throw "源已变化：$($sourceItem.Name)" }
}
if ((Get-FileHash -LiteralPath (Join-Path $projectDir 'figures/scaling/FigD_magnitude.pdf')).Hash.ToLower() -ne $r.figure_sha256) { throw '图已变化' }
$backupDir = Join-Path $projectDir 'tmp/scaling_followup_20261021/previous_formal_outputs'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$files = @()
foreach ($name in @('main.pdf', 'theory_only.pdf', 'main.bbl')) {
    $src = Join-Path $r.build_directory $name
    $dst = Join-Path (Join-Path $projectDir 'latex') $name
    $newHash = (Get-FileHash -LiteralPath $src).Hash.ToLower()
    $oldHash = (Get-FileHash -LiteralPath $dst).Hash.ToLower()
    $method = 'already_identical'
    $copyFailure = $null
    if ($newHash -ne $oldHash) {
        $backup = Join-Path $backupDir $name
        if (-not (Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $dst -Destination $backup }
        try {
            Copy-Item -LiteralPath $src -Destination $dst -Force
            $method = 'Copy-Item'
        } catch {
            $copyFailure = $_.Exception.Message
            $tempPath = Join-Path (Join-Path $projectDir 'latex') ('followup_replacement_' + $name)
            Copy-Item -LiteralPath $src -Destination $tempPath -Force
            [System.IO.File]::Replace($tempPath, $dst, $null)
            $method = 'File.Replace_after_backup'
        }
    }
    if ((Get-FileHash -LiteralPath $dst).Hash.ToLower() -ne $newHash) { throw "产物哈希不符：$name" }
    $files += @{name=$name; sha256=$newHash; previous_sha256=$oldHash; method=$method; native_copy_failure=$copyFailure}
}
@{success=$true; source_report='workspace_attempt1/build_report.json'; files=$files; pushes=0} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $batchDir 'delivery_report.json') -Encoding utf8NoBOM
Write-Output 'D followup output delivery: 3/3 files verified'
