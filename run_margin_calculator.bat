@echo off
:: Vehicle Margin Calculator Launcher
:: This script helps launch the vehicle margin calculator with common options

echo Vehicle Margin Calculator
echo ========================
echo.

if "%1"=="" goto :noparams

echo Running search for: %1
python vehicle_margin_calculator.py %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:noparams
echo Choose from the following options:
echo.
echo 1. Search by frame number
echo 2. Search by SPK number
echo 3. Search by BAST number
echo 4. Batch calculation (recent vehicles)
echo 5. Batch calculation (custom date range)
echo 6. Exit
echo.

set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto :search_frame
if "%choice%"=="2" goto :search_spk
if "%choice%"=="3" goto :search_bast
if "%choice%"=="4" goto :batch_recent
if "%choice%"=="5" goto :batch_custom
if "%choice%"=="6" goto :end

echo Invalid choice. Please try again.
goto :noparams

:search_frame
set /p frame=Enter frame number: 
python vehicle_margin_calculator.py %frame% --type frame
goto :end

:search_spk
set /p spk=Enter SPK number: 
python vehicle_margin_calculator.py %spk% --type spk
goto :end

:search_bast
set /p bast=Enter BAST number: 
python vehicle_margin_calculator.py %bast% --type bast
goto :end

:batch_recent
set /p limit=Enter number of recent vehicles to show (or press Enter for all): 
if "%limit%"=="" (
    python vehicle_margin_batch.py --summary-only
) else (
    python vehicle_margin_batch.py --limit %limit% --summary-only
)
set /p detail=Show detailed calculation for individual vehicles? (y/n): 
if /i "%detail%"=="y" (
    if "%limit%"=="" (
        python vehicle_margin_batch.py
    ) else (
        python vehicle_margin_batch.py --limit %limit%
    )
)
goto :end

:batch_custom
set /p start_date=Enter start date (YYYY-MM-DD): 
set /p end_date=Enter end date (YYYY-MM-DD): 
python vehicle_margin_batch.py --start-date %start_date% --end-date %end_date% --summary-only
set /p detail=Show detailed calculation for individual vehicles? (y/n): 
if /i "%detail%"=="y" (
    python vehicle_margin_batch.py --start-date %start_date% --end-date %end_date%
)
goto :end

:end
echo.
pause 