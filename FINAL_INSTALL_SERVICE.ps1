# ============================================
# FINAL WINDOWS SERVICE INSTALLER
# Auto-elevates to Administrator
# ============================================

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "⚠️  Script needs Administrator privileges. Restarting as Administrator..." -ForegroundColor Yellow
    
    # Re-run this script as Administrator
    Start-Process PowerShell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Change to script directory
Set-Location "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"

# Kill all Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Remove existing service
& ".\nssm-2.24\win64\nssm.exe" stop "PariuSmart-Bot" 2>$null
& ".\nssm-2.24\win64\nssm.exe" remove "PariuSmart-Bot" confirm 2>$null

Write-Host "Installing PariuSmart Bot as Windows Service..." -ForegroundColor Green

# Install service
& ".\nssm-2.24\win64\nssm.exe" install "PariuSmart-Bot" "C:\Python312\python.exe"

# Configure service
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" AppParameters "-m bot.bot"
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" AppDirectory "$PWD"
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" Description "PariuSmart AI Telegram Bot - Premium Version"
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" Start SERVICE_AUTO_START

# Setup logging
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" AppStdout "$PWD\logs\service_out.log"
& ".\nssm-2.24\win64\nssm.exe" set "PariuSmart-Bot" AppStderr "$PWD\logs\service_error.log"

# Start service
Write-Host "Starting service..." -ForegroundColor Yellow
& ".\nssm-2.24\win64\nssm.exe" start "PariuSmart-Bot"

Start-Sleep 5

# Check status
Write-Host "`n=== SERVICE STATUS ===" -ForegroundColor Cyan
& ".\nssm-2.24\win64\nssm.exe" status "PariuSmart-Bot"
Get-Service "PariuSmart-Bot" | Format-Table Name, Status, StartType -AutoSize

Write-Host "`n✅ PariuSmart Bot is now running as Windows Service!" -ForegroundColor Green
Write-Host "🔧 Bot will start automatically when computer restarts" -ForegroundColor Yellow
Write-Host "📋 Check logs in logs/ folder if needed" -ForegroundColor Blue

Write-Host "`nPress any key to continue..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")