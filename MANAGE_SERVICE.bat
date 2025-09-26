@echo off
REM ============================================
REM SERVICE MANAGEMENT TOOLS
REM ============================================

cd /d "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"

:MENU
cls
echo ======================================
echo      PariuSmart Bot Service Manager
echo ======================================
echo.
echo 1. Check Status
echo 2. Start Service
echo 3. Stop Service  
echo 4. Restart Service
echo 5. View Logs
echo 6. Uninstall Service
echo 7. Exit
echo.
set /p choice="Choose option (1-7): "

if "%choice%"=="1" goto STATUS
if "%choice%"=="2" goto START
if "%choice%"=="3" goto STOP
if "%choice%"=="4" goto RESTART
if "%choice%"=="5" goto LOGS
if "%choice%"=="6" goto UNINSTALL
if "%choice%"=="7" goto EXIT
goto MENU

:STATUS
echo.
echo === SERVICE STATUS ===
nssm-2.24\win64\nssm.exe status "PariuSmart-Bot"
sc query "PariuSmart-Bot"
echo.
pause
goto MENU

:START
echo.
echo Starting PariuSmart Bot service...
nssm-2.24\win64\nssm.exe start "PariuSmart-Bot"
echo.
pause
goto MENU

:STOP
echo.
echo Stopping PariuSmart Bot service...
nssm-2.24\win64\nssm.exe stop "PariuSmart-Bot"
echo.
pause
goto MENU

:RESTART
echo.
echo Restarting PariuSmart Bot service...
nssm-2.24\win64\nssm.exe restart "PariuSmart-Bot"
echo.
pause
goto MENU

:LOGS
echo.
echo === LATEST OUTPUT LOG ===
if exist "logs\service_out.log" (
    type "logs\service_out.log"
) else (
    echo No output log found
)
echo.
echo === LATEST ERROR LOG ===
if exist "logs\service_error.log" (
    type "logs\service_error.log"
) else (
    echo No error log found
)
echo.
pause
goto MENU

:UNINSTALL
echo.
echo ⚠️  WARNING: This will completely remove the service!
set /p confirm="Are you sure? (y/n): "
if /i "%confirm%"=="y" (
    nssm-2.24\win64\nssm.exe stop "PariuSmart-Bot"
    nssm-2.24\win64\nssm.exe remove "PariuSmart-Bot" confirm
    echo ✅ Service uninstalled
) else (
    echo Cancelled
)
echo.
pause
goto MENU

:EXIT
exit