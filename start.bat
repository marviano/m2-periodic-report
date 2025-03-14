@echo off
echo Report Scheduler Started
echo Current time: %time%

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

echo Not within reporting time window
goto End

:RunReport
echo Running report at %time%
cd /d C:\path\to\your\report\directory
python vehicle_reporting.py >> scheduler.log 2>&1
echo Report completed at %time%

:End