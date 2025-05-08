#C:\Users\alvus\Desktop\m2-periodic-report\report_scheduler.py
#untuk bikin .exe
#pyinstaller --onefile report_scheduler.py

import time
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def run_report():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Running reports at {current_time}")
    try:
        # Get current date for YTD report
        today = datetime.now()
        start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        # Run vehicle report
        logging.info("Running vehicle report...")
        vehicle_result = subprocess.run(["python", "vehicle_reporting.py"], 
                                      capture_output=True, text=True)
        
        # Run SPV report
        logging.info("Running SPV performance report...")
        spv_result = subprocess.run(["python", "spv_report.py", start_date, end_date],
                                  capture_output=True, text=True)
        
        # Log results
        logging.info(f"Vehicle report completed with return code: {vehicle_result.returncode}")
        if vehicle_result.stdout:
            logging.info(f"Vehicle report output: {vehicle_result.stdout}")
        if vehicle_result.stderr:
            logging.error(f"Vehicle report error: {vehicle_result.stderr}")
            
        logging.info(f"SPV report completed with return code: {spv_result.returncode}")
        if spv_result.stdout:
            logging.info(f"SPV report output: {spv_result.stdout}")
        if spv_result.stderr:
            logging.error(f"SPV report error: {spv_result.stderr}")
            
    except Exception as e:
        logging.error(f"Failed to run reports: {e}")

# Schedule times (hour) at which reports should run
SCHEDULE_HOURS = [12, 14, 16, 18, 20]
GRACE_MINUTES = 15

# Keep track of which report periods have already run today
already_run = set()

def check_and_run_reports():
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    current_minute = now.minute
    
    # Check if the current hour is a scheduled hour
    if current_hour in SCHEDULE_HOURS:
        # Check if within grace period (first 15 minutes of the hour)
        if current_minute < GRACE_MINUTES:
            # Create a unique key for this scheduled period
            period_key = f"{current_date}-{current_hour}"
            
            # Only run if we haven't already run for this period
            if period_key not in already_run:
                logging.info(f"Running report within grace period: {current_hour}:00-{current_hour}:{GRACE_MINUTES}")
                run_report()
                already_run.add(period_key)
    
    # Reset the already_run set at midnight to prepare for a new day
    if current_hour == 0 and current_minute == 0:
        already_run.clear()

logging.info("Scheduler started with 15-minute grace periods")
print("Scheduler started with 15-minute grace periods")
print(f"Reports will run at {SCHEDULE_HOURS} with a {GRACE_MINUTES}-minute grace period")

# Keep the scheduler running
while True:
    check_and_run_reports()
    time.sleep(60)  # Check every minute