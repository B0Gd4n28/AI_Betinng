@echo off
REM ============================================
REM FINAL WINDOWS SERVICE INSTALLER (BAT VERSION)
REM Auto-elevates to Administrator
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

echo Installing PariuSmart Bot as Windows Service...

REM Kill all Python processes
taskkill /f /im python.exe >nul 2>&1

REM Remove existing service
nssm-2.24\win64\nssm.exe stop "PariuSmart-Bot" >nul 2>&1
nssm-2.24\win64\nssm.exe remove "PariuSmart-Bot" confirm >nul 2>&1

echo.
echo 🔧 Installing service...
nssm-2.24\win64\nssm.exe install "PariuSmart-Bot" "C:\Python312\python.exe"

echo 🔧 Configuring service...
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppParameters "-m bot.bot"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppDirectory "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Description "PariuSmart AI Telegram Bot - Premium Version"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Start SERVICE_AUTO_START

echo 🔧 Setting up logging...
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStdout "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_out.log"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStderr "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_error.log"

echo.
echo 🚀 Starting service...
nssm-2.24\win64\nssm.exe start "PariuSmart-Bot"

timeout /t 5 /nobreak >nul

echo.
echo === SERVICE STATUS ===
nssm-2.24\win64\nssm.exe status "PariuSmart-Bot"
sc query "PariuSmart-Bot"

echo.
echo ✅ PariuSmart Bot is now running as Windows Service!
echo 🔧 Bot will start automatically when computer restarts
echo 📋 Check logs in logs\ folder if needed
echo.
pause