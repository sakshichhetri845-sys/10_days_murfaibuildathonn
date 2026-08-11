$ErrorActionPreference = "Stop"

# ── Helpers ─────────────────────────────────────────────────────────────────
function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Assert-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Warning "Missing env file: $Path"
        Write-Warning "  → Copy the .env.example in that folder to .env.local and fill in your keys."
    }
}

# ── Preflight checks ─────────────────────────────────────────────────────────
if (-not (Test-CommandExists "uv"))   { Write-Error "Missing required command: uv  (install from https://docs.astral.sh/uv/)" }
if (-not (Test-CommandExists "pnpm")) { Write-Error "Missing required command: pnpm (run: npm i -g pnpm)" }

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Assert-EnvFile "$repoRoot\backend\.env.local"
Assert-EnvFile "$repoRoot\frontend\.env.local"

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  HealthSaathi — Day 6: Outbound Voice Telephony System  " -ForegroundColor Green
Write-Host "  10 Days of Voice Agents  (#VoiceForBharat Challenge)   " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services being launched:" -ForegroundColor Gray
Write-Host "   [1] Inbound Web Agent     → backend/src/agent.py" -ForegroundColor White
Write-Host "   [2] Outbound Telephony    → backend/src/telephony/outbound/agent.py" -ForegroundColor White
Write-Host "   [3] HTTP API Server       → backend/src/api_server.py  (port 8000)" -ForegroundColor White
Write-Host "   [4] Frontend Next.js App  → http://localhost:3000" -ForegroundColor White
Write-Host ""

# ── Launch services ───────────────────────────────────────────────────────────

# 1. Inbound Web Agent
Start-Process cmd.exe -ArgumentList "/k", `
    "title [1] HealthSaathi — Inbound Web Agent && " + `
    "cd /d ""$repoRoot\backend"" && " + `
    "echo Starting Inbound Web Agent... && " + `
    "uv run python src/agent.py dev"

Start-Sleep -Milliseconds 500

# 2. Outbound Telephony Agent
Start-Process cmd.exe -ArgumentList "/k", `
    "title [2] HealthSaathi — Outbound Telephony Agent && " + `
    "cd /d ""$repoRoot\backend"" && " + `
    "echo Starting Outbound Telephony Agent... && " + `
    "uv run python src/telephony/outbound/agent.py dev"

Start-Sleep -Milliseconds 500

# 3. HTTP API Server (call management REST API)
Start-Process cmd.exe -ArgumentList "/k", `
    "title [3] HealthSaathi — HTTP API Server (port 8000) && " + `
    "cd /d ""$repoRoot\backend"" && " + `
    "echo Starting HTTP API Server on port 8000... && " + `
    "uv run python src/api_server.py"

Start-Sleep -Milliseconds 500

# 4. Frontend Next.js App
Start-Process cmd.exe -ArgumentList "/k", `
    "title [4] HealthSaathi — Frontend (http://localhost:3000) && " + `
    "cd /d ""$repoRoot\frontend"" && " + `
    "echo Starting Next.js frontend... && " + `
    "pnpm dev"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ✔ All 4 HealthSaathi services launched in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend  →  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API       →  http://localhost:8000/api/outbound/history" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Trigger a test call:" -ForegroundColor Gray
Write-Host "    cd backend" -ForegroundColor DarkGray
Write-Host "    uv run python trigger_outbound_call.py" -ForegroundColor DarkGray
Write-Host ""
