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
    logging.info(f"Running vehicle report at {current_time}")
    try:
        # Get the directory where the script is running from
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vehicle_script_path = os.path.join(script_dir, "vehicle_reporting.py")
        
        # Check if the Python script exists
        if os.path.exists(vehicle_script_path):
            logging.info(f"Running Python script at: {vehicle_script_path}")
            result = subprocess.run(["python", vehicle_script_path], 
                                  capture_output=True, text=True)
        # If Python script doesn't exist, try the executable in the same directory
        else:
            vehicle_exe_path = os.path.join(script_dir, "vehicle_reporting.exe")
            if os.path.exists(vehicle_exe_path):
                logging.info(f"Running executable at: {vehicle_exe_path}")
                result = subprocess.run([vehicle_exe_path], 
                                      capture_output=True, text=True)
            else:
                # If neither exists, log an error
                logging.error(f"Could not find vehicle_reporting.py or vehicle_reporting.exe in {script_dir}")
                return
        
        logging.info(f"Report completed with return code: {result.returncode}")
        if result.stdout:
            logging.info(f"Output: {result.stdout}")
        if result.stderr:
            logging.error(f"Error: {result.stderr}")
    except Exception as e:
        logging.error(f"Failed to run report: {e}")

# Schedule times (hour) at which reports should run
SCHEDULE_HOURS = [12, 14, 16, 18, 20, 22]
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