@echo off
title AquaSync: IoT Dashboard Launcher
echo ==============================================================
echo       💧 AQUASYNC: SMART WATER TELEMETRY DASHBOARD
echo ==============================================================
echo.
echo [SYSTEM] Checking for Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 was not found on your system path.
    echo Please install Python 3.x and check "Add Python to PATH" during setup.
    echo.
    pause
    exit /b
)

echo [SYSTEM] Python detected! Launching graphical dashboard...
echo.

:: Launch the script in a separate background window
start "" python "%~dp0dashboard\dashboard.py"

echo [SYSTEM] Dashboard launched successfully. Closing launcher...
timeout /t 3 >nul
exit
