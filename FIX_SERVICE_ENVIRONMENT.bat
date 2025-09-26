@echo off
REM ============================================
REM FINAL FIX - Service with Proper Environment
REM Run as Administrator
REM ============================================

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator
) else (
    echo ⚠️  Script needs Administrator privileges. Restarting as Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"

echo 🔧 Fixing PariuSmart Bot Windows Service...

REM Kill all Python processes
taskkill /f /im python.exe >nul 2>&1

REM Remove existing service completely
nssm-2.24\win64\nssm.exe stop "PariuSmart-Bot" >nul 2>&1
nssm-2.24\win64\nssm.exe remove "PariuSmart-Bot" confirm >nul 2>&1

echo.
echo 🚀 Installing service with proper environment...

REM Install service with batch script (not Python directly)
nssm-2.24\win64\nssm.exe install "PariuSmart-Bot" "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\run_bot.bat"

REM Configure service
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppDirectory "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Description "PariuSmart AI Telegram Bot - Fixed Environment"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Start SERVICE_AUTO_START

REM Setup logging
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStdout "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_out.log"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStderr "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_error.log"

REM Set environment variables for the service
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppEnvironmentExtra "PYTHONPATH=C:\Users\Bogdan\AppData\Roaming\Python\Python312\site-packages"

echo.
echo 🚀 Starting service...
nssm-2.24\win64\nssm.exe start "PariuSmart-Bot"

timeout /t 8 /nobreak >nul

echo.
echo === SERVICE STATUS ===
nssm-2.24\win64\nssm.exe status "PariuSmart-Bot"
sc query "PariuSmart-Bot"

echo.
echo === CHECKING LOGS ===
if exist "logs\service_out.log" (
    echo Output log:
    type "logs\service_out.log"
)
if exist "logs\service_error.log" (
    echo Error log:
    type "logs\service_error.log"
)

echo.
echo ✅ Service installed with environment fix!
pause