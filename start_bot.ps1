param([string]$RepoPath = "C:\Users\Bogdan\Downloads\free-soccer-telegram-bot")
$ErrorActionPreference = "Stop"

Write-Host "PariuSmart AI Bot Launcher" -ForegroundColor Cyan

# Check if bot is already running
$botProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "python" }
if ($botProcesses) {
    Write-Host "Bot is already running! Stopping existing instance..." -ForegroundColor Yellow
    $botProcesses | Stop-Process -Force
    Start-Sleep -Seconds 3
}

Set-Location $RepoPath

# Choose Python command
$python = "python"
if (Get-Command py -ErrorAction SilentlyContinue) { 
    $python = "py" 
}
Write-Host "Using Python: $python" -ForegroundColor Green

# Setup virtual environment
if (-not (Test-Path ".venv")) { 
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $python -m venv .venv 
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing/updating requirements..." -ForegroundColor Yellow
& pip install -r requirements.txt --quiet

# Create logs directory
New-Item -ItemType Directory -Path logs -ErrorAction SilentlyContinue | Out-Null

Write-Host "Starting PariuSmart AI Bot..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Gray

try {
    & $python bot\bot.py
} catch {
    Write-Host "Bot stopped with error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Bot stopped." -ForegroundColor Yellow