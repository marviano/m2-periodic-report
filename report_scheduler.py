#C:\Users\alvus\Desktop\m2-periodic-report\report_scheduler.py
#untuk bikin .exe
#pyinstaller --onefile report_scheduler.py

import schedule
import time
import subprocess
import sys
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
        # Use the following line if running the Python file directly
        result = subprocess.run(["python", "vehicle_reporting.py"], 
                               capture_output=True, text=True)
        
        # Or use this if using the compiled exe
        # result = subprocess.run(["vehicle_reporting.exe"], 
        #                       capture_output=True, text=True)
        
        logging.info(f"Report completed with return code: {result.returncode}")
        if result.stdout:
            logging.info(f"Output: {result.stdout}")
        if result.stderr:
            logging.error(f"Error: {result.stderr}")
    except Exception as e:
        logging.error(f"Failed to run report: {e}")

# Schedule jobs every 2 hours starting from 12:00
schedule.every().day.at("12:00").do(run_report)
schedule.every().day.at("14:00").do(run_report)
schedule.every().day.at("16:00").do(run_report)
schedule.every().day.at("18:00").do(run_report)
schedule.every().day.at("20:00").do(run_report)
schedule.every().day.at("22:00").do(run_report)

logging.info("Scheduler started. Reports will run every 2 hours starting from 12:00")
print("Scheduler started. Reports will run every 2 hours starting from 12:00")
print("Scheduled times: 12:00, 14:00, 16:00, 18:00, 20:00, 22:00")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute