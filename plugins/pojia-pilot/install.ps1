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

# ── 环境层: dsh-purge (可选但强推荐, 装了自动打宿主补丁+rules桥生效) ──
$PURGE_DEST = "$DSH_HOME\plugins\dsh-purge"
if (Test-Path "$PURGE_DEST\package.json") {
    Write-Host "✅ dsh-purge 已存在, 跳过"
} else {
    Write-Host "🔧 安装环境层 dsh-purge ..."
    $purgeTmp = Join-Path $env:TEMP "dsh-purge-install"
    if (Test-Path $purgeTmp) { Remove-Item $purgeTmp -Recurse -Force }
    git clone --depth 1 https://github.com/YuJunZhiXue/dsh-purge $purgeTmp 2>$null
    if ($LASTEXITCODE -eq 0) {
        New-Item -ItemType Directory -Force -Path $PURGE_DEST | Out-Null
        Copy-Item "$purgeTmp\*" $PURGE_DEST -Recurse -Force
        Remove-Item "$PURGE_DEST\.git" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ dsh-purge 已安装 -> $PURGE_DEST (重启DSH后自动应用宿主补丁)"
    } else {
        Write-Host "⚠️  dsh-purge 拉取失败(不影响pojia基础功能)。手动安装: git clone https://github.com/YuJunZhiXue/dsh-purge"
    }
}

Write-Host "✅ pojia-pilot v0.3.4 安装完成 -> $DEST"
Write-Host "   开局: 会话里输入 pojiaai <你的目标域名>"
Write-Host "   挂机: /autopilot <目标> [阶段]   停止: /autopilot stop"
Write-Host "   ⚠️  仅用于自有资产或已获书面授权的目标"
Write-Host ""
Write-Host "── pojia-pilot v0.3.4 · Powered by pojia.ai · © 2026 POJIA.AI ──"
