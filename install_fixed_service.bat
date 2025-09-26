@echo off
echo === FINAL FIX: Installing PariuSmart Bot as Windows Service ===

cd /d "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"

echo.
echo 1. Stopping any running Python processes...
taskkill /f /im python.exe 2>nul

echo.
echo 2. Stopping existing service...
net stop "PariuSmart-Bot" 2>nul
nssm-2.24\win64\nssm.exe stop "PariuSmart-Bot" 2>nul

echo.
echo 3. Removing existing service...
nssm-2.24\win64\nssm.exe remove "PariuSmart-Bot" confirm

echo.
echo 4. Installing service with FIXED bot...
nssm-2.24\win64\nssm.exe install "PariuSmart-Bot" "C:\Python312\python.exe"

echo.
echo 5. Setting application parameters...
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppParameters "-m bot.bot"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppDirectory "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Description "PariuSmart AI Telegram Bot Service - FIXED VERSION"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" Start SERVICE_AUTO_START

echo.
echo 6. Setting logging...
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStdout "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_out.log"
nssm-2.24\win64\nssm.exe set "PariuSmart-Bot" AppStderr "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot\logs\service_error.log"

echo.
echo 7. Starting service...
nssm-2.24\win64\nssm.exe start "PariuSmart-Bot"

echo.
echo 8. Checking status...
timeout /t 5 /nobreak
nssm-2.24\win64\nssm.exe status "PariuSmart-Bot"
sc query "PariuSmart-Bot"

echo.
echo === SERVICE INSTALLED WITH FIXED BOT! ===
echo Test bot commands in Telegram now!
pause