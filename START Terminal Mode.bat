<<<<<<< HEAD
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
=======
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
>>>>>>> d4976186ee1858695101339c4be95621452f871e
