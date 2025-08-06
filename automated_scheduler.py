#!/usr/bin/env python3
"""
Automated Scheduler for Lottery System
Combines daily automation with weekly predictions
"""

import os
import sys
import time
import threading
import logging
import schedule
from datetime import datetime, timezone, timedelta
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# South African timezone (UTC+2)
SA_TIMEZONE = timezone(timedelta(hours=2))

class AutomatedScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def run_daily_automation(self):
        """Run daily lottery result automation"""
        logger.info("=== RUNNING DAILY AUTOMATION ===")
        try:
            from simple_daily_scheduler import SimpleLotteryScheduler
            daily_scheduler = SimpleLotteryScheduler()
            daily_scheduler.run_automation_now()
            logger.info("Daily automation completed")
        except Exception as e:
            logger.error(f"Daily automation failed: {e}")
    
    def run_weekly_predictions(self):
        """Run weekly prediction generation"""
        logger.info("=== RUNNING WEEKLY PREDICTIONS ===")
        try:
            # Run the weekly prediction scheduler
            result = subprocess.run([
                sys.executable, 'weekly_prediction_scheduler.py'
            ], capture_output=True, text=True, timeout=1800)  # 30 minute timeout
            
            if result.returncode == 0:
                logger.info("Weekly predictions completed successfully")
                logger.info(f"Output: {result.stdout}")
            else:
                logger.error(f"Weekly predictions failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Weekly predictions timed out after 30 minutes")
        except Exception as e:
            logger.error(f"Weekly predictions failed: {e}")
    
    def schedule_jobs(self):
        """Setup the scheduling"""
        # Daily automation at 10:30 PM SA time
        schedule.every().day.at("22:30").do(self.run_daily_automation)
        
        # Weekly predictions on Sunday at 9:00 AM SA time
        schedule.every().sunday.at("09:00").do(self.run_weekly_predictions)
        
        logger.info("Scheduled jobs:")
        logger.info("- Daily automation: 10:30 PM SA time")
        logger.info("- Weekly predictions: Sunday 9:00 AM SA time")
    
    def run_scheduler(self):
        """Main scheduler loop"""
        self.running = True
        logger.info("Automated scheduler started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
        
        logger.info("Automated scheduler stopped")
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if not self.running:
            self.schedule_jobs()
            self.thread = threading.Thread(target=self.run_scheduler)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Automated scheduler thread started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Automated scheduler thread stopped")
    
    def run_weekly_now(self):
        """Manual trigger for weekly predictions"""
        logger.info("Manual trigger: Running weekly predictions now")
        self.run_weekly_predictions()
    
    def get_next_runs(self):
        """Get information about next scheduled runs"""
        jobs_info = []
        for job in schedule.jobs:
            next_run = job.next_run
            if next_run:
                # Convert to SA timezone for display
                sa_time = next_run.replace(tzinfo=timezone.utc).astimezone(SA_TIMEZONE)
                jobs_info.append({
                    'job': str(job.job_func.__name__),
                    'next_run': sa_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'next_run_utc': next_run.isoformat()
                })
        return jobs_info

def main():
    """Main function for standalone execution"""
    try:
        scheduler = AutomatedScheduler()
        
        # Check if we should run weekly predictions now
        if len(sys.argv) > 1 and sys.argv[1] == '--weekly-now':
            scheduler.run_weekly_now()
            return
        
        # Start the scheduler
        scheduler.start()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        return 1

if __name__ == "__main__":
    main()