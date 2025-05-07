@echo off
echo Running Vehicle Report Immediately...
echo.

REM Set the working directory to the script location
cd /d %~dp0

REM Check if Python is in the PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python not found in PATH. Please install Python or add it to your PATH.
    pause
    exit /b 1
)

REM Run the vehicle reporting script directly
echo Running vehicle report...
python vehicle_reporting.py

REM If the script exits, pause to see any error messages
pause 