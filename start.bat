@echo on
echo ===================================
echo Report Scheduler Started
echo Current time: %time%
echo ===================================

:: Get current hour and minute
for /f "tokens=1,2 delims=:" %%a in ("%time%") do (
    set hour=%%a
    set minute=%%b
)
:: Remove leading space if hour is single digit
set hour=%hour: =%

:: Check if current hour is one of our target hours (12, 14, 16, 18, 20, 22)
:: and if minute is less than 15 (within grace period)
set /a minute_num=%minute%
if %minute_num% LSS 15 (
    if %hour%==12 goto RunReport
    if %hour%==14 goto RunReport
    if %hour%==16 goto RunReport
    if %hour%==18 goto RunReport
    if %hour%==20 goto RunReport
    if %hour%==22 goto RunReport
)

echo Current hour: %hour%
echo Current minute: %minute%
echo Not within reporting time window (need hour=12,14,16,18,20,22 and minute<15)
goto End

:RunReport
echo Running report at %time%
cd /d C:\Users\USER\Desktop\m2-periodic-report
echo Current directory: %CD%
echo Attempting to run vehicle_reporting.py
if exist "vehicle_reporting.py" (
    echo File found: vehicle_reporting.py
    python vehicle_reporting.py >> batch_log.txt 2>&1
) else (
    echo ERROR: vehicle_reporting.py not found in %CD%
    dir >> batch_log.txt
)
echo Report completed at %time%

:End
echo ===================================
echo Execution completed at %time%
echo Check batch_log.txt for details
echo ===================================
pause