@echo off
title PC Doctor AI - Installing Dependencies
color 0B
echo.
echo  ============================================
echo       PC Doctor AI - Installation
echo  ============================================
echo.

cd /d "%~dp0"

echo  [1/3] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed!
    echo  Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo  [2/3] Creating Virtual Environment...
echo.
python -m venv .venv

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo  Virtual environment created and activated!
) else (
    echo  ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo  [3/3] Installing required packages...
echo.
pip install psutil rich wmi GPUtil openai requests pywin32 speedtest-cli 2>nul

if errorlevel 1 (
    echo  Some packages may have failed. Try running as Administrator.
) else (
    echo  ============================================
    echo       Installation Complete!
    echo   Run: .venv\Scripts\activate
    echo   Then: python main.py --quick
    echo  ============================================
)
echo.
pause