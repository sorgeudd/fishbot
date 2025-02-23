@echo off
echo ===================================
echo    Starting Fishing Bot...
echo ===================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo Please run this script as Administrator!
    echo Right-click the file and select "Run as Administrator"
    pause
    exit /b 1
)

REM Start the bot
python fishing_bot.py
pause
