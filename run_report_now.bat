@echo off
echo Running Reports Immediately...
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

REM Use PowerShell to get properly formatted dates
for /f %%i in ('powershell -Command "Get-Date -Format 'yyyy-MM-dd'"') do set end_date=%%i
for /f %%i in ('powershell -Command "Get-Date -Format 'yyyy'"') do set current_year=%%i

REM Set start date to January 1st of current year
set start_date=%current_year%-01-01

echo Start date: %start_date%
echo End date: %end_date%
echo.

REM Run the vehicle reporting script
echo Running vehicle report...
python vehicle_reporting.py

REM Run the SPV performance report
echo.
echo Running SPV performance report...
python spv_report.py %start_date% %end_date%

echo.
echo Reports completed!
echo Press any key to exit...
pause 