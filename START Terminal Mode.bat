@echo off
title PC Doctor - Terminal Mode
cd /d "%~dp0"
echo Starting PC Doctor (Terminal Mode)...
python main.py --report --chat
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Run "install.bat" first.
    echo.
    pause
)
pause
