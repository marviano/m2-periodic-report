# M2 Periodic Report System

A comprehensive automated reporting system for M2 Madiun and M2 Magetan vehicle sales data, including DO (Delivery Order) reports and SPV (Supervisor) performance tracking.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Scripts Overview](#scripts-overview)
- [Scheduling](#scheduling)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

## 🚀 Features

- **Automated Daily Reports**: Generate and send vehicle sales reports automatically
- **SPV Performance Tracking**: Monitor supervisor performance across locations
- **Margin Analysis**: Calculate and track profit margins for each sale
- **Multi-Location Support**: Handle data from both M2 Madiun and M2 Magetan
- **Email Integration**: Send formatted HTML reports via email
- **Scheduled Execution**: Run reports automatically at specified times
- **Year-over-Year Comparisons**: Compare current performance with previous periods

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **MySQL Database Access** to the M2 databases
- **Gmail Account** with App Password enabled for email sending
- **Windows/Linux/macOS** compatible system

## 🔧 Installation

### Quick Setup (Recommended)

#### Windows
```bash
# Run the automated setup script
setup.bat
```

#### Linux/macOS
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

### Manual Installation

#### Step 1: Clone or Download the Repository

```bash
# If using git
git clone <repository-url>
cd m2-periodic-report

# Or download and extract the ZIP file
```

#### Step 2: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install mysql-connector-python==8.0.33
pip install python-dotenv==1.0.0
```

#### Step 3: Verify Installation

```bash
# Test that all modules can be imported
python -c "import mysql.connector, dotenv; print('✅ Dependencies installed successfully!')"
```

## ⚙️ Configuration

### Step 1: Set Up Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual credentials:**
   ```env
   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-gmail-app-password

   # Email Recipients (comma-separated)
   EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

   # Database Configuration
   DB_HOST=your-database-host
   DB_USERNAME=your-database-username
   DB_PASSWORD=your-database-password
   ```

### Step 2: Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `SENDER_PASSWORD`

### Step 3: Test Configuration

```bash
# Test environment variables loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SMTP_SERVER:', os.getenv('SMTP_SERVER')); print('DB_HOST:', os.getenv('DB_HOST'))"
```

## 📖 Usage

### Manual Report Generation

#### 1. Generate Today's Report
```bash
python vehicle_reporting.py
```

#### 2. Generate Report for Specific Date
```bash
# Format: DDMMYYYY
python vehicle_reporting.py 05062025
```

#### 3. Generate SPV Performance Report
```bash
# YTD report for specific date
python spv_report.py 05062025

# Custom date range
python spv_report.py 2025-01-01 2025-06-05
```

#### 4. Check Margin Calculation
```bash
python vehicle_margin_batch.py --start-date 2025-05-05 --end-date 2025-05-05
```

### Automated Scheduling

#### Windows Task Scheduler
1. **Open Task Scheduler**
2. **Create Basic Task:**
   - Name: "M2 Report Scheduler"
   - Trigger: Daily
   - Action: Start a program
   - Program: `python`
   - Arguments: `D:\path\to\m2-periodic-report\report_scheduler.py`

#### Linux/macOS Cron
```bash
# Edit crontab
crontab -e

# Add entry to run every 2 hours
0 */2 * * * cd /path/to/m2-periodic-report && python report_scheduler.py
```

#### Manual Scheduler Execution
```bash
# Run the scheduler (keeps running)
python report_scheduler.py
```

## 📊 Scripts Overview

### 1. `vehicle_reporting.py`
**Purpose**: Generate and send daily vehicle sales reports

**Features**:
- Daily and monthly sales summaries
- Payment method breakdown (Cash vs Credit)
- Margin analysis and profit tracking
- Year-over-year and month-over-month comparisons
- Beautiful HTML email formatting

**Usage**:
```bash
python vehicle_reporting.py [DDMMYYYY]
```

### 2. `spv_report.py`
**Purpose**: Generate SPV (Supervisor) performance reports

**Features**:
- Today, MTD (Month-to-Date), and YTD (Year-to-Date) performance
- Multi-location data aggregation
- Performance ranking by total sales
- Color-coded HTML table format

**Usage**:
```bash
python spv_report.py [DDMMYYYY]
python spv_report.py [start_date] [end_date]
```

### 3. `report_scheduler.py`
**Purpose**: Automated report execution scheduler

**Features**:
- Runs reports at scheduled times (12:00, 14:00, 16:00, 18:00, 20:00)
- 15-minute grace period for each scheduled time
- Prevents duplicate runs
- Comprehensive logging

**Usage**:
```bash
python report_scheduler.py
```

### 4. `db_operations.py`
**Purpose**: Database connection and data retrieval functions

**Features**:
- MySQL database connectivity
- Vehicle data extraction
- SPV performance data queries
- Error handling and connection management

## ⏰ Scheduling

### Default Schedule Times
- **12:00 PM** - Lunch break report
- **2:00 PM** - Afternoon update
- **4:00 PM** - End of business day
- **6:00 PM** - Evening summary
- **8:00 PM** - Final daily report

### Customizing Schedule
Edit `report_scheduler.py`:
```python
# Modify these lines to change schedule
SCHEDULE_HOURS = [12, 14, 16, 18, 20]  # Hours to run reports
GRACE_MINUTES = 15  # Grace period in minutes
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: mysql.connector.errors.ProgrammingError: 1045 (28000): Access denied
```
**Solution**: Check database credentials in `.env` file

#### 2. Email Sending Failed
```
Error: SMTPAuthenticationError: (535, '5.7.8 Username and Password not accepted')
```
**Solution**: 
- Verify Gmail app password is correct
- Ensure 2FA is enabled on Gmail account
- Check `SENDER_EMAIL` and `SENDER_PASSWORD` in `.env`

#### 3. Module Not Found
```
ModuleNotFoundError: No module named 'mysql'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Variables Not Loading
```
None values for environment variables
```
**Solution**: 
- Ensure `.env` file exists in project root
- Check file format (no spaces around `=`)
- Verify `python-dotenv` is installed

### Debug Mode
Enable debug logging by modifying the scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Database Connection
```bash
python -c "from db_operations import connect_to_database; conn = connect_to_database(); print('✅ Database connection successful!'); conn.close()"
```

### Test Email Configuration
```bash
python -c "from vehicle_reporting import send_email; send_email('Test', '<h1>Test Email</h1>', ['your-email@example.com'])"
```

## 🔒 Security Notes

### Environment Variables
- **Never commit `.env` file** to version control
- **Use `.env.example`** as a template for team members
- **Rotate credentials regularly** for enhanced security

### Database Security
- **Use dedicated database user** with minimal required permissions
- **Enable SSL connections** if supported by your MySQL server
- **Regular password updates** for database accounts

### Email Security
- **Use App Passwords** instead of main Gmail password
- **Enable 2-Factor Authentication** on Gmail account
- **Monitor email sending logs** for unusual activity

### File Permissions
```bash
# Set appropriate permissions on .env file
chmod 600 .env  # Linux/macOS
```

## 📁 Project Structure

```
m2-periodic-report/
├── .env                    # Environment variables (excluded from git)
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── setup.bat              # Windows setup script
├── setup.sh               # Linux/macOS setup script
├── db_operations.py       # Database functions
├── vehicle_reporting.py   # Main reporting script
├── spv_report.py          # SPV performance script
├── report_scheduler.py    # Automated scheduler
├── report_schedule.bat     # Windows batch file
├── run_report_now.bat     # Windows batch file
└── scheduler.log          # Scheduler log file
```

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the log files (`scheduler.log`)
3. Verify environment variable configuration
4. Test individual components (database, email)

## 📝 License

This project is proprietary software for M2 Madiun and M2 Magetan internal use.