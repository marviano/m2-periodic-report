@echo off
echo Starting Vehicle Reporting System...
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

REM Run the report scheduler script
echo Running report scheduler...
python report_scheduler.py

REM If the script exits, pause to see any error messages
pause 