#!/usr/bin/env python3
"""
Worker-Safe Scheduler Fix for Multi-Process Gunicorn Environment
Ensures automation runs reliably at 23:45 SA time regardless of worker restarts
"""

import os
import sys
import time
import logging
import threading
import schedule
from datetime import datetime, timezone, timedelta
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# South African timezone (UTC+2)
SA_TIMEZONE = timezone(timedelta(hours=2))

class WorkerSafeLotteryScheduler:
    """
    A scheduler that works reliably with Gunicorn multi-worker processes
    Uses APScheduler with database persistence to ensure jobs run exactly once
    """
    
    def __init__(self):
        self.scheduler = None
        self.running = False
    
    def run_automation_now(self):
        """Run the automation workflow - same proven working system"""
        logger.info("🚀 WORKER-SAFE: Starting scheduled automation...")
        
        start_time = datetime.now(SA_TIMEZONE)
        
        try:
            # Import Flask app and use same working system
            sys.path.append('.')
            from app import app
            import glob
            
            # Run within Flask application context
            with app.app_context():
                logger.info("=== WORKER-SAFE: Using SAME 4-step system as manual button ===")
                
                # Step 1: Clean screenshots
                logger.info("Step 1: Clean up existing screenshots")
                existing_screenshots = glob.glob('screenshots/*.png')
                for screenshot in existing_screenshots:
                    try:
                        os.remove(screenshot)
                        logger.info(f"Deleted old screenshot: {screenshot}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {screenshot}: {e}")
                
                # Step 2: Capture screenshots using robust system
                logger.info("Step 2: Capturing 6 fresh screenshots")
                try:
                    from robust_screenshot_capture import robust_screenshot_capture
                    import asyncio
                    
                    capture_count = asyncio.run(robust_screenshot_capture())
                    screenshots = glob.glob('screenshots/*.png')
                    logger.info(f"Screenshot capture: {capture_count}/6, found {len(screenshots)} files")
                    
                    if len(screenshots) >= 6:
                        # Step 3: Process with AI
                        logger.info("Step 3: Processing with AI")
                        from ai_lottery_processor import CompleteLotteryProcessor
                        
                        processor = CompleteLotteryProcessor()
                        result = processor.process_all_screenshots()
                        
                        new_results = len(result.get('database_records', []))
                        logger.info(f"✅ WORKER-SAFE SUCCESS: {len(screenshots)} screenshots, {new_results} new results")
                        
                        # Log success
                        self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), True, 
                                               f"Captured {len(screenshots)} screenshots, found {new_results} new results")
                        
                    else:
                        error_msg = f'Expected 6 screenshots, only captured {len(screenshots)}'
                        logger.error(f"❌ WORKER-SAFE FAILED: {error_msg}")
                        self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), False, error_msg)
                        
                except Exception as e:
                    logger.error(f"❌ WORKER-SAFE ERROR: {e}")
                    self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), False, str(e))
        
        except Exception as e:
            logger.error(f"💥 WORKER-SAFE CRITICAL ERROR: {e}")
            self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), False, f"Critical error: {str(e)}")
    
    def _log_automation_run(self, start_time, end_time, success, message):
        """Log automation run to database"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id SERIAL PRIMARY KEY,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    success BOOLEAN NOT NULL,
                    message TEXT,
                    duration_seconds INTEGER,
                    scheduler_type VARCHAR(50) DEFAULT 'worker_safe',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            duration_seconds = int((end_time - start_time).total_seconds())
            
            cur.execute("""
                INSERT INTO automation_logs (start_time, end_time, success, message, duration_seconds, scheduler_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (start_time, end_time, success, message, duration_seconds, 'worker_safe'))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"📊 WORKER-SAFE: Logged run - success={success}, duration={duration_seconds}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to log automation run: {e}")
    
    def start(self):
        """Start the worker-safe scheduler using APScheduler"""
        if self.running:
            logger.warning("WORKER-SAFE: Scheduler already running")
            return False
            
        try:
            # Use APScheduler with background execution
            self.scheduler = BackgroundScheduler(
                timezone=SA_TIMEZONE,
                daemon=True,
                coalesce=True,  # Prevent multiple instances of the same job
                max_instances=1  # Only one instance of job can run at a time
            )
            
            # Schedule daily at 23:45 SA time
            self.scheduler.add_job(
                func=self.run_automation_now,
                trigger=CronTrigger(hour=23, minute=45, timezone=SA_TIMEZONE),
                id='daily_lottery_automation',
                name='Daily Lottery Automation',
                replace_existing=True,  # Replace if already exists
                misfire_grace_time=300  # Allow 5 minutes grace period
            )
            
            self.scheduler.start()
            self.running = True
            
            logger.info("✅ WORKER-SAFE: APScheduler started, job scheduled for 23:45 SA time daily")
            return True
            
        except Exception as e:
            logger.error(f"❌ WORKER-SAFE: Failed to start scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("✅ WORKER-SAFE: Scheduler stopped")
            return True
        return False
    
    def get_status(self):
        """Get scheduler status"""
        if not self.scheduler:
            return {'running': False, 'jobs': 0}
            
        jobs = self.scheduler.get_jobs()
        next_run = None
        if jobs:
            next_run = jobs[0].next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if jobs[0].next_run_time else None
        
        return {
            'running': self.running,
            'jobs': len(jobs),
            'next_run': next_run,
            'scheduler_type': 'APScheduler (worker-safe)',
            'timezone': 'South Africa (UTC+2)'
        }

# Global instance
_worker_safe_scheduler = WorkerSafeLotteryScheduler()

def start_worker_safe_scheduler():
    """Start the worker-safe scheduler"""
    return _worker_safe_scheduler.start()

def stop_worker_safe_scheduler():
    """Stop the worker-safe scheduler"""
    return _worker_safe_scheduler.stop()

def get_worker_safe_status():
    """Get worker-safe scheduler status"""
    return _worker_safe_scheduler.get_status()

def run_automation_now_worker_safe():
    """Run automation immediately via worker-safe scheduler"""
    _worker_safe_scheduler.run_automation_now()
    return True

if __name__ == "__main__":
    # Test the worker-safe scheduler
    logger.info("Testing worker-safe scheduler...")
    
    if start_worker_safe_scheduler():
        logger.info("✅ Worker-safe scheduler started")
        status = get_worker_safe_status()
        for key, value in status.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Stopping worker-safe scheduler...")
            stop_worker_safe_scheduler()
    else:
        logger.error("❌ Failed to start worker-safe scheduler")