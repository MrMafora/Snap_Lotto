"""
Automated Scheduler for Daily Lottery Data Processing
Runs the complete workflow automatically every day at a specified time
"""

import schedule
import time
import threading
import logging
from datetime import datetime
from daily_automation import run_daily_automation

logger = logging.getLogger(__name__)

class LotteryScheduler:
    """Manages automated scheduling of daily lottery processing"""
    
    def __init__(self, app, run_time="01:00"):
        self.app = app
        self.run_time = run_time
        self.running = False
        self.scheduler_thread = None
        self.last_run = None
        self.last_results = None
        
    def daily_job(self):
        """Execute the daily automation job"""
        try:
            logger.info(f"Starting scheduled daily automation at {datetime.now()}")
            results = run_daily_automation(self.app)
            
            self.last_run = datetime.now()
            self.last_results = results
            
            if results['overall_success']:
                logger.info("Scheduled daily automation completed successfully")
            else:
                logger.error("Scheduled daily automation completed with errors")
                
        except Exception as e:
            logger.error(f"Critical error in scheduled daily automation: {str(e)}")
            self.last_results = {'error': str(e), 'overall_success': False}
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        # Schedule the daily job
        schedule.every().day.at(self.run_time).do(self.daily_job)
        
        logger.info(f"Scheduler started - Daily automation will run at {self.run_time}")
        
        def run_scheduler():
            self.running = True
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
    def stop_scheduler(self):
        """Stop the automated scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")
        
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
        
    def get_status(self):
        """Get current scheduler status"""
        return {
            'running': self.running,
            'run_time': self.run_time,
            'next_run': self.get_next_run_time(),
            'last_run': self.last_run,
            'last_results': self.last_results
        }

# Global scheduler instance
lottery_scheduler = None

def init_scheduler(app, run_time="01:00"):
    """Initialize the global scheduler"""
    global lottery_scheduler
    lottery_scheduler = LotteryScheduler(app, run_time)
    lottery_scheduler.start_scheduler()
    return lottery_scheduler

def get_scheduler():
    """Get the global scheduler instance"""
    return lottery_scheduler