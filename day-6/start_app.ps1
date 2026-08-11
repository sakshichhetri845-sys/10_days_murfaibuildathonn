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

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " HealthSaathi - Day 6 Outbound Voice Telephony System" -ForegroundColor Green
Write-Host " 10 Days of Voice Agents (#VoiceForBharat Challenge)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "Launching 3 core services in separate terminal windows:" -ForegroundColor Gray
Write-Host " 1. [Terminal 1] Inbound Web Agent Worker  (src/agent.py)" -ForegroundColor White
Write-Host " 2. [Terminal 2] Outbound Telephony Worker and API Server (src/telephony/outbound/agent.py + src/api_server.py)" -ForegroundColor White
Write-Host " 3. [Terminal 3] Frontend Next.js Web App (http://localhost:3000)" -ForegroundColor White

Start-Process cmd.exe -ArgumentList "/k", "title HealthSaathi Terminal 1: Inbound Web Agent && cd /d ""$repoRoot\backend"" && uv run python src/agent.py dev"
Start-Process cmd.exe -ArgumentList "/k", "title HealthSaathi Terminal 2: Outbound Worker and API Server && cd /d ""$repoRoot\backend"" && start /b uv run python src/api_server.py && uv run python src/telephony/outbound/agent.py dev"
Start-Process cmd.exe -ArgumentList "/k", "title HealthSaathi Terminal 3: Frontend Web App && cd /d ""$repoRoot\frontend"" && pnpm dev"

Write-Host "`nAll 3 HealthSaathi services launched successfully!" -ForegroundColor Green
Write-Host "Open your web browser at: http://localhost:3000" -ForegroundColor Cyan
