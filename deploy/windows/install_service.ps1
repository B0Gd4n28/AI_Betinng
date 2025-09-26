# PariuSmart AI Bot - Windows Service Installer
# Rulează ca Administrator în PowerShell

param(
    [Parameter(Mandatory=$false)]
    [string]$BotPath = "C:\Users\$env:USERNAME\Downloads\free-soccer-telegram-bot",
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "PariuSmartBot",
    [Parameter(Mandatory=$false)]
    [string]$ServiceDisplayName = "PariuSmart AI Telegram Bot"
)

Write-Host "🤖 Installing PariuSmart AI Bot as Windows Service..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "❌ This script must be run as Administrator!"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if bot directory exists
if (-not (Test-Path $BotPath)) {
    Write-Error "❌ Bot directory not found: $BotPath"
    Write-Host "Please update the BotPath parameter" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if .env file exists
$envFile = Join-Path $BotPath ".env"
if (-not (Test-Path $envFile)) {
    Write-Warning "⚠️  .env file not found. Creating template..."
    
    $envTemplate = @"
# PariuSmart AI Bot - Environment Variables
TELEGRAM_BOT_TOKEN=your_bot_token_here
FOOTBALL_DATA_TOKEN=your_football_data_token
ODDS_API_KEY=your_odds_api_key
OPENWEATHER_API_KEY=your_weather_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
GDELT_API_KEY=your_gdelt_key

# Bot Configuration
BOT_LOG_LEVEL=INFO
BOT_AUTO_RESTART=true
BOT_MAX_RETRIES=5
"@
    
    $envTemplate | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "📝 Created .env template at: $envFile" -ForegroundColor Yellow
    Write-Host "Please edit this file with your actual API keys before continuing." -ForegroundColor Yellow
    
    # Open .env file for editing
    notepad $envFile
    
    Read-Host "Press Enter after you've configured your API keys"
}

# Create service wrapper script
$wrapperScript = Join-Path $BotPath "service_wrapper.py"
$wrapperContent = @"
#!/usr/bin/env python3
"""
PariuSmart AI Bot - Windows Service Wrapper
Handles service lifecycle and automatic restart
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add bot directory to Python path
bot_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(bot_dir))

# Configure logging
log_dir = bot_dir / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "service.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file"""
    env_file = bot_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        logger.info("Environment variables loaded from .env")
    else:
        logger.warning(".env file not found")

def run_bot():
    """Run the bot with automatic restart"""
    max_retries = int(os.getenv('BOT_MAX_RETRIES', '5'))
    restart_delay = 10  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Starting PariuSmart AI Bot (attempt {attempt + 1}/{max_retries})")
            
            # Change to bot directory
            os.chdir(bot_dir)
            
            # Run bot
            result = subprocess.run([
                sys.executable, "-m", "bot.bot"
            ], cwd=bot_dir, check=True)
            
            logger.info("Bot exited normally")
            break
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Bot crashed with exit code {e.returncode}")
            
            if attempt < max_retries - 1:
                logger.info(f"Restarting in {restart_delay} seconds...")
                time.sleep(restart_delay)
                restart_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Service stopping.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(restart_delay)
            else:
                sys.exit(1)

if __name__ == "__main__":
    logger.info("PariuSmart AI Bot Service Starting...")
    load_env_file()
    run_bot()
"@

$wrapperContent | Out-File -FilePath $wrapperScript -Encoding UTF8
Write-Host "📝 Created service wrapper: $wrapperScript" -ForegroundColor Green

# Find Python executable
$pythonExe = ""
$pythonPaths = @(
    "python",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        $version = & $path --version 2>$null
        if ($version -match "Python 3\.(1[0-9]|[8-9])") {
            $pythonExe = (Get-Command $path).Source
            Write-Host "✅ Found Python: $pythonExe ($version)" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonExe) {
    Write-Error "❌ Python 3.8+ not found. Please install Python first."
    pause
    exit 1
}

# Stop existing service if running
try {
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "🛑 Stopping existing service..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force
        
        Write-Host "🗑️ Removing existing service..." -ForegroundColor Yellow
        & sc.exe delete $ServiceName
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "No existing service found" -ForegroundColor Gray
}

# Create Windows Service using NSSM (Non-Sucking Service Manager)
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$nssmZip = Join-Path $env:TEMP "nssm.zip"
$nssmDir = Join-Path $env:TEMP "nssm-2.24"
$nssmExe = Join-Path $nssmDir "win64\nssm.exe"

if (-not (Test-Path $nssmExe)) {
    Write-Host "📥 Downloading NSSM (Windows Service Manager)..." -ForegroundColor Blue
    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
    Expand-Archive -Path $nssmZip -DestinationPath $env:TEMP -Force
}

# Install service with NSSM
Write-Host "⚙️ Installing Windows Service..." -ForegroundColor Blue

& $nssmExe install $ServiceName $pythonExe $wrapperScript
& $nssmExe set $ServiceName DisplayName $ServiceDisplayName
& $nssmExe set $ServiceName Description "PariuSmart AI Telegram Bot - Advanced Football Betting Analytics"
& $nssmExe set $ServiceName Start SERVICE_AUTO_START
& $nssmExe set $ServiceName AppDirectory $BotPath
& $nssmExe set $ServiceName AppStdout (Join-Path $BotPath "logs\service_stdout.log")
& $nssmExe set $ServiceName AppStderr (Join-Path $BotPath "logs\service_stderr.log")
& $nssmExe set $ServiceName AppRotateFiles 1
& $nssmExe set $ServiceName AppRotateOnline 1
& $nssmExe set $ServiceName AppRotateSeconds 86400  # Daily rotation
& $nssmExe set $ServiceName AppRotateBytes 10485760  # 10MB max

Write-Host "✅ Service installed successfully!" -ForegroundColor Green

# Start the service
Write-Host "🚀 Starting PariuSmart AI Bot service..." -ForegroundColor Green
Start-Service -Name $ServiceName

# Wait a moment and check status
Start-Sleep -Seconds 3
$service = Get-Service -Name $ServiceName
Write-Host "📊 Service Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })

if ($service.Status -eq 'Running') {
    Write-Host "🎉 SUCCESS! PariuSmart AI Bot is now running as a Windows Service!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔧 Service Management Commands:" -ForegroundColor Yellow
    Write-Host "   Start:   Start-Service $ServiceName" -ForegroundColor Gray
    Write-Host "   Stop:    Stop-Service $ServiceName" -ForegroundColor Gray
    Write-Host "   Restart: Restart-Service $ServiceName" -ForegroundColor Gray
    Write-Host "   Status:  Get-Service $ServiceName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 Logs located at: $BotPath\logs\" -ForegroundColor Cyan
    Write-Host "🌐 The bot will now run 24/7, even after system restart!" -ForegroundColor Green
    
    # Show service info
    Get-Service -Name $ServiceName | Format-Table -AutoSize
} else {
    Write-Error "❌ Service failed to start. Check logs for details."
    Write-Host "Log files:" -ForegroundColor Yellow
    Write-Host "  - $BotPath\logs\service.log" -ForegroundColor Gray
    Write-Host "  - $BotPath\logs\service_stdout.log" -ForegroundColor Gray
    Write-Host "  - $BotPath\logs\service_stderr.log" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")