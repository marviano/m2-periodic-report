#!/bin/bash

echo "========================================"
echo "M2 Periodic Report System - Setup"
echo "========================================"
echo

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi
echo "✅ Python is installed"

echo
echo "[2/4] Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed successfully"

echo
echo "[3/4] Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo
    echo "⚠️  IMPORTANT: Please edit .env file with your actual credentials"
    echo "   - Database connection details"
    echo "   - Gmail credentials for sending emails"
    echo "   - Email recipients list"
    echo
else
    echo "✅ .env file already exists"
fi

echo
echo "[4/4] Testing configuration..."
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Environment variables loaded successfully!')"
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Environment variables test failed"
    echo "Please check your .env file configuration"
fi

echo
echo "========================================"
echo "Setup completed!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Test the system: python3 vehicle_reporting.py"
echo "3. Set up scheduling: python3 report_scheduler.py"
echo
echo "For detailed instructions, see README.md"
echo
