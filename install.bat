@echo off
title PC Doctor - Installing Dependencies
color 0B
echo.
echo  ============================================
echo       PC Doctor v2.0 - Installation
echo  ============================================
echo.

cd /d "%~dp0"

echo  [1/2] Checking Python...
py3 --version 2>nul || python --version 2>nul
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed!
    echo  Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo  [2/2] Installing required packages...
echo.
py3 -m pip install psutil rich wmi GPUtil openai requests pywin32 speedtest-cli customtkinter Pillow 2>nul || pip install psutil rich wmi GPUtil openai requests pywin32 speedtest-cli customtkinter Pillow
echo.

if errorlevel 1 (
    echo  Some packages may have failed. Try running as Administrator.
) else (
    echo  ============================================
    echo       Installation Complete!
    echo   Double-click "START PC Doctor.bat" to run
    echo  ============================================
)
echo.
pause
