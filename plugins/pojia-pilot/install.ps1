# pojia-pilot 一键安装 (Windows PowerShell)
$ErrorActionPreference = "Stop"
$DSH_HOME = if ($env:DSH_HOME) { $env:DSH_HOME } else { "$HOME\.dsh" }
$DEST = "$DSH_HOME\plugins\pojia-pilot"
$REPO = "https://github.com/Justinuse1/pojia-breaker"

Write-Host "🎯 pojia-pilot 安装器"
if (-not (Test-Path $DSH_HOME)) { Write-Host "❌ 未找到 $DSH_HOME"; exit 1 }

New-Item -ItemType Directory -Force -Path $DEST | Out-Null
$tmp = Join-Path $env:TEMP "pojia-pilot-install"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Push-Location $tmp
git clone --depth 1 --filter=blob:none --sparse $REPO pb 2>$null
if ($LASTEXITCODE -eq 0) {
    Push-Location pb
    git sparse-checkout set plugins/pojia-pilot
    Copy-Item "plugins/pojia-pilot/*" $DEST -Recurse -Force
    Pop-Location
} else {
    # git失败走tarball
    Invoke-WebRequest "$REPO/archive/refs/heads/master.tar.gz" -OutFile "$tmp\pb.tgz"
    tar -xzf "$tmp\pb.tgz" -C $tmp --strip-components=2
    Copy-Item "$tmp\plugins\pojia-pilot/*" $DEST -Recurse -Force -ErrorAction SilentlyContinue
    if (-not $?) { Copy-Item "$tmp\pojia-pilot/*" $DEST -Recurse -Force }
}
Pop-Location
New-Item -ItemType Directory -Force -Path "$DSH_HOME\memory\targets" | Out-Null
Write-Host "✅ pojia-pilot v0.1 安装完成 -> $DEST"
Write-Host "   开局: 会话里输入 pojiaai"
Write-Host "   ⚠️  仅用于自有资产或已获书面授权的目标"
