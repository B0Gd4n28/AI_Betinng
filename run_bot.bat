@echo off
REM Set Python path to include user modules
set PYTHONPATH=%PYTHONPATH%;C:\Users\Bogdan\AppData\Roaming\Python\Python312\site-packages

REM Change to bot directory
cd /d "c:\Users\Bogdan\Downloads\free-soccer-telegram-bot"

REM Run the bot
C:\Python312\python.exe -m bot.bot