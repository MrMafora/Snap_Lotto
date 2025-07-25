#!/usr/bin/env python3
"""
Daily Lottery Automation Scheduler
Runs lottery data collection workflow at 10:30 PM South African time daily
"""

import os
import sys
import time
import threading
import logging
import schedule
from datetime import datetime, timezone, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

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

class LotteryScheduler:
    def __init__(self):
        self.running = False
        self.last_run = None
        self.next_run = None
        self.thread = None
        self.schedule_time = "22:30"  # 10:30 PM
        
    def run_automation_workflow(self):
        """Run the complete lottery automation workflow"""
        logger.info("=== STARTING SCHEDULED LOTTERY AUTOMATION ===")
        
        try:
            # Import automation modules
            from complete_automation_workflow import run_complete_automation
            
            # Record start time
            start_time = datetime.now(SA_TIMEZONE)
            self.last_run = start_time
            
            logger.info(f"Starting automation at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Run the complete workflow
            result = run_complete_automation()
            
            # Log results
            end_time = datetime.now(SA_TIMEZONE)
            duration = end_time - start_time
            
            if result.get('success'):
                logger.info(f"✅ Automation completed successfully in {duration}")
                logger.info(f"Results: {result.get('message', 'No message')}")
                
                # Save successful run to database
                self._save_automation_log(start_time, end_time, True, result.get('message'))
                
            else:
                logger.error(f"❌ Automation failed after {duration}")
                logger.error(f"Error: {result.get('error', 'Unknown error')}")
                
                # Save failed run to database
                self._save_automation_log(start_time, end_time, False, result.get('error'))
                
        except Exception as e:
            logger.error(f"Critical error in scheduled automation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Save error to database
            end_time = datetime.now(SA_TIMEZONE)
            self._save_automation_log(start_time, end_time, False, str(e))
        
        # Calculate next run time
        self._calculate_next_run()
        
        logger.info("=== SCHEDULED LOTTERY AUTOMATION COMPLETED ===")
    
    def _save_automation_log(self, start_time, end_time, success, message):
        """Save automation run log to database"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            # Create automation_logs table if not exists
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
            
            logger.info(f"Automation log saved: success={success}, duration={duration_seconds}s")
            
        except Exception as e:
            logger.error(f"Failed to save automation log: {e}")
    
    def _calculate_next_run(self):
        """Calculate next scheduled run time"""
        now = datetime.now(SA_TIMEZONE)
        # Get today's scheduled time
        today_run = now.replace(hour=22, minute=30, second=0, microsecond=0)
        
        if now < today_run:
            # If we haven't reached today's run time yet
            self.next_run = today_run
        else:
            # Schedule for tomorrow
            tomorrow = now + timedelta(days=1)
            self.next_run = tomorrow.replace(hour=22, minute=30, second=0, microsecond=0)
        
        logger.info(f"Next automation scheduled for: {self.next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return False
        
        logger.info("Starting lottery automation scheduler...")
        logger.info(f"Daily automation scheduled for {self.schedule_time} South African time")
        
        # Clear any existing schedules
        schedule.clear()
        
        # Schedule the job for 10:30 PM daily
        schedule.every().day.at(self.schedule_time).do(self.run_automation_workflow)
        
        # Calculate initial next run
        self._calculate_next_run()
        
        # Start scheduler thread
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("✅ Lottery automation scheduler started successfully")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return False
        
        logger.info("Stopping lottery automation scheduler...")
        
        self.running = False
        schedule.clear()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("✅ Lottery automation scheduler stopped")
        return True
    
    def _run_scheduler(self):
        """Internal scheduler loop"""
        logger.info("Scheduler thread started")
        
        while self.running:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()
                
                # Sleep for 60 seconds before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
        
        logger.info("Scheduler thread stopped")
    
    def get_status(self):
        """Get current scheduler status"""
        return {
            'running': self.running,
            'schedule_time': self.schedule_time,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'current_time': datetime.now(SA_TIMEZONE).isoformat(),
            'timezone': 'South Africa (UTC+2)'
        }
    
    def run_now(self):
        """Manually trigger automation workflow immediately"""
        logger.info("Manual automation trigger requested")
        
        # Run in separate thread to avoid blocking
        manual_thread = threading.Thread(target=self.run_automation_workflow, daemon=True)
        manual_thread.start()
        
        return True

# Global scheduler instance
lottery_scheduler = LotteryScheduler()

def start_scheduler():
    """Start the lottery scheduler"""
    return lottery_scheduler.start()

def stop_scheduler():
    """Stop the lottery scheduler"""
    return lottery_scheduler.stop()

def get_scheduler_status():
    """Get scheduler status"""
    return lottery_scheduler.get_status()

def run_automation_now():
    """Run automation manually"""
    return lottery_scheduler.run_now()

if __name__ == "__main__":
    # Command line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            if start_scheduler():
                print("✅ Scheduler started successfully")
                # Keep the script running
                try:
                    while lottery_scheduler.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping scheduler...")
                    stop_scheduler()
            else:
                print("❌ Failed to start scheduler")
                
        elif command == 'stop':
            if stop_scheduler():
                print("✅ Scheduler stopped successfully")
            else:
                print("❌ Scheduler was not running")
                
        elif command == 'status':
            status = get_scheduler_status()
            print(f"Scheduler Status:")
            print(f"  Running: {status['running']}")
            print(f"  Schedule: {status['schedule_time']} {status['timezone']}")
            print(f"  Last Run: {status['last_run'] or 'Never'}")
            print(f"  Next Run: {status['next_run'] or 'Not scheduled'}")
            print(f"  Current Time: {status['current_time']}")
            
        elif command == 'run':
            print("🚀 Running automation now...")
            run_automation_now()
            
        else:
            print("Usage: python daily_scheduler.py [start|stop|status|run]")
    else:
        print("Lottery Automation Scheduler")
        print("Usage: python daily_scheduler.py [start|stop|status|run]")
        print("")
        print("Commands:")
        print("  start  - Start the daily scheduler (10:30 PM SA time)")
        print("  stop   - Stop the scheduler")
        print("  status - Show current status")
        print("  run    - Run automation immediately")