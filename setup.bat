@echo off
echo ========================================
echo M2 Periodic Report System - Setup
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo ✅ Python is installed

echo.
echo [2/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

echo.
echo [3/4] Setting up environment variables...
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file from template
    echo.
    echo ⚠️  IMPORTANT: Please edit .env file with your actual credentials
    echo    - Database connection details
    echo    - Gmail credentials for sending emails
    echo    - Email recipients list
    echo.
) else (
    echo ✅ .env file already exists
)

echo.
echo [4/4] Testing configuration...
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Environment variables loaded successfully!')"
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Environment variables test failed
    echo Please check your .env file configuration
)

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Test the system: python vehicle_reporting.py
echo 3. Set up scheduling: python report_scheduler.py
echo.
echo For detailed instructions, see README.md
echo.
pause
