#report_scheduler.py
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

# Schedule jobs
schedule.every().day.at("14:00").do(run_report)
schedule.every().day.at("19:00").do(run_report)

logging.info("Scheduler started. Waiting for scheduled times...")
print("Scheduler started. Waiting for scheduled times...")
print("Scheduled times: 14:00 and 19:00")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute