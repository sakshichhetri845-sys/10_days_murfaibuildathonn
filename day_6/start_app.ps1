$ErrorActionPreference = "Stop"

function Test-CommandExists {
  param([string]$CommandName)

  return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "uv")) {
  Write-Error "Missing required command: uv"
}

if (-not (Test-CommandExists "pnpm")) {
  Write-Error "Missing required command: pnpm"
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$localLivekitExe = Join-Path $repoRoot "livekit-server.exe"

$envFile = Join-Path $repoRoot "backend\.env.local"
$isCloud = $false
$lkUrl = ""
$lkKey = ""
$lkSecret = ""

if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -match "^\s*LIVEKIT_URL\s*=\s*(.+)$") { $lkUrl = $matches[1].Trim() }
    if ($line -match "^\s*LIVEKIT_API_KEY\s*=\s*(.+)$") { $lkKey = $matches[1].Trim() }
    if ($line -match "^\s*LIVEKIT_API_SECRET\s*=\s*(.+)$") { $lkSecret = $matches[1].Trim() }
  }
  if ($lkUrl -match "wss://") {
    $isCloud = $true
  }
}

# Clean up any existing running agent worker processes to prevent worker conflicts
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*agent.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Start each service in its own PowerShell window so logs remain visible.
if (-not $isCloud) {
  if (Test-Path $localLivekitExe) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; .\livekit-server.exe --dev"
  } elseif (Test-CommandExists "livekit-server") {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; livekit-server --dev"
  }
} else {
  Write-Host "Connecting to LiveKit Cloud ($lkUrl)..." -ForegroundColor Cyan
}

$backendCmd = "Set-Location '$repoRoot\backend';"
if ($lkUrl -and $lkKey -and $lkSecret) {
  $backendCmd += " uv run python src/agent.py dev --url '$lkUrl' --api-key '$lkKey' --api-secret '$lkSecret'"
} else {
  $backendCmd += " uv run python src/agent.py dev"
}

$outboundCmd = "Set-Location '$repoRoot\backend';"
if ($lkUrl -and $lkKey -and $lkSecret) {
  $outboundCmd += " uv run python src/telephony/outbound/agent.py dev --url '$lkUrl' --api-key '$lkKey' --api-secret '$lkSecret'"
} else {
  $outboundCmd += " uv run python src/telephony/outbound/agent.py dev"
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $outboundCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\frontend'; pnpm dev"

Write-Host "Started Web Agent, Outbound Telephony Agent, and Frontend UI in separate PowerShell windows." -ForegroundColor Green
