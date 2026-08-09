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

Write-Host "Using configured LiveKit Cloud URL from .env.local"

Start-Process cmd.exe -ArgumentList "/k", "cd /d ""$repoRoot\backend"" && uv run python src/agent.py dev"
Start-Process cmd.exe -ArgumentList "/k", "cd /d ""$repoRoot\frontend"" && pnpm dev"

Write-Host "Started backend and frontend in separate console windows."
