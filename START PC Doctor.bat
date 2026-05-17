@echo off
title PC Doctor
cd /d "%~dp0"
py3 app.py 2>nul || python app.py 2>nul || (
    echo.
    echo  ERROR: Could not start PC Doctor.
    echo  Run "install.bat" first to install dependencies.
    echo.
    pause
)
