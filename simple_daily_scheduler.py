#!/usr/bin/env python3
"""
Simple Daily Scheduler for Lottery Automation
Just calls the existing working automation workflow at 10:30 PM SA time
"""

import os
import sys
import time
import threading
import logging
import schedule
from datetime import datetime, timezone, timedelta
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# South African timezone (UTC+2)
SA_TIMEZONE = timezone(timedelta(hours=2))

class SimpleLotteryScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.schedule_time = "22:30"  # 10:30 PM SA time
        
    def run_automation_now(self):
        """Run the automation workflow immediately using existing working system"""
        logger.info("🚀 Starting scheduled automation using working workflow...")
        
        start_time = datetime.now(SA_TIMEZONE)
        
        try:
            # Import Flask app and working automation system
            sys.path.append('.')
            from app import app
            from complete_automation_workflow import run_complete_automation
            
            logger.info(f"Calling existing automation workflow at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Run within Flask application context to ensure proper resource access
            with app.app_context():
                # Set environment variables for browser context
                os.environ['DISPLAY'] = ':0'
                
                # Call the working automation workflow with proper context
                result = run_complete_automation()
            
            end_time = datetime.now(SA_TIMEZONE)
            duration_seconds = int((end_time - start_time).total_seconds())
            
            if result and result.get('success'):
                message = f"Scheduled automation completed successfully: {result.get('message', 'Success')}"
                logger.info(f"✅ {message}")
                self._log_automation_run(start_time, end_time, True, message)
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                logger.error(f"❌ Scheduled automation failed: {error_msg}")
                self._log_automation_run(start_time, end_time, False, error_msg)
                
        except Exception as e:
            logger.error(f"💥 Error in scheduled automation: {e}")
            end_time = datetime.now(SA_TIMEZONE)
            self._log_automation_run(start_time, end_time, False, f"Exception: {str(e)}")
        
        logger.info("📋 Scheduled automation complete")
    
    def _log_automation_run(self, start_time, end_time, success, message):
        """Log the automation run to database"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id SERIAL PRIMARY KEY,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    success BOOLEAN NOT NULL,
                    message TEXT,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            duration_seconds = int((end_time - start_time).total_seconds())
            
            cur.execute("""
                INSERT INTO automation_logs (start_time, end_time, success, message, duration_seconds)
                VALUES (%s, %s, %s, %s, %s)
            """, (start_time, end_time, success, message, duration_seconds))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"📊 Logged automation run: success={success}, duration={duration_seconds}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to log automation run: {e}")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("⏰ Scheduler thread started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler thread: {e}")
                time.sleep(60)
        
        logger.info("⏹️ Scheduler thread stopped")
    
    def start(self):
        """Start the simple scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return False
        
        logger.info("🎯 Starting simple lottery automation scheduler...")
        logger.info(f"⏰ Daily automation scheduled for {self.schedule_time} South African time")
        
        # Clear existing schedules
        schedule.clear()
        
        # Schedule daily automation at 10:30 PM
        schedule.every().day.at(self.schedule_time).do(self.run_automation_now)
        
        # Start scheduler thread
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("✅ Simple scheduler started successfully")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return False
        
        logger.info("🛑 Stopping simple scheduler...")
        
        self.running = False
        schedule.clear()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("✅ Simple scheduler stopped")
        return True
    
    def get_status(self):
        """Get current scheduler status"""
        now = datetime.now(SA_TIMEZONE)
        
        # Calculate next run
        today_run = now.replace(hour=22, minute=30, second=0, microsecond=0)
        if now < today_run:
            next_run = today_run
        else:
            tomorrow = now + timedelta(days=1)
            next_run = tomorrow.replace(hour=22, minute=30, second=0, microsecond=0)
        
        return {
            'running': self.running,
            'schedule_time': self.schedule_time,
            'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S'),
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': 'South Africa (UTC+2)',
            'last_run': None  # Can be enhanced to fetch from database
        }

# Global scheduler instance
_scheduler = SimpleLotteryScheduler()

def start_scheduler():
    """Start the scheduler"""
    return _scheduler.start()

def stop_scheduler():
    """Stop the scheduler"""
    return _scheduler.stop()

def run_automation_now():
    """Run automation immediately"""
    _scheduler.run_automation_now()
    return True

def get_scheduler_status():
    """Get scheduler status"""
    return _scheduler.get_status()

if __name__ == "__main__":
    # Test the scheduler
    logger.info("Testing simple scheduler...")
    
    if start_scheduler():
        logger.info("Scheduler started, will run at 22:30 daily")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            stop_scheduler()
    else:
        logger.error("Failed to start scheduler")