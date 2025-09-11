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
        """Run the automation workflow - same proven working system with database locking"""
        logger.info("🚀 WORKER-SAFE: Starting scheduled automation...")
        
        # Try to acquire database lock first
        conn, worker_id = self._get_database_lock()
        if not conn or not worker_id:
            logger.info("🚫 WORKER-SAFE: Skipping automation - another worker is already running")
            return
        
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
                        # Step 3: Process with AI (EXACT SAME as manual button)
                        logger.info("Step 3: Processing screenshots with Google Gemini 2.5 Pro AI")
                        from ai_lottery_processor import CompleteLotteryProcessor
                        
                        # Initialize and run the comprehensive AI processor (EXACT SAME as manual button)
                        processor = CompleteLotteryProcessor()
                        workflow_result = processor.process_all_screenshots()
                        
                        # Check if processing was successful - comprehensive processor returns dict with results
                        success = workflow_result.get('total_success', 0) > 0 or len(workflow_result.get('database_records', [])) > 0
                        new_results = len(workflow_result.get('database_records', []))
                        logger.info(f"✅ WORKER-SAFE SUCCESS: {len(screenshots)} screenshots, {new_results} new results")
                        
                        # STEP 4: AUTO-VALIDATE EXISTING PREDICTIONS AND GENERATE NEW ONES
                        if new_results > 0:
                            logger.info("Step 4a: Auto-validating existing predictions against new lottery results...")
                            validation_results = 0
                            try:
                                from prediction_validation_system import PredictionValidationSystem
                                
                                validation_system = PredictionValidationSystem()
                                validation_result = validation_system.validate_all_pending_predictions()
                                validation_results = len(validation_result.get('validated_predictions', []))
                                logger.info(f"✅ WORKER-SAFE VALIDATION SUCCESS: Validated {validation_results} existing predictions")
                                
                            except Exception as validation_error:
                                logger.warning(f"⚠️ WORKER-SAFE VALIDATION WARNING: Prediction validation failed: {validation_error}")
                            
                            logger.info("Step 4b: FRESH prediction generation for next draws...")
                            try:
                                # Use ONLY the intelligent fresh prediction system to ensure unique numbers for each draw
                                from fresh_prediction_generator import generate_fresh_predictions_for_new_draws
                                fresh_predictions_success = generate_fresh_predictions_for_new_draws()
                                logger.info(f"✅ WORKER-SAFE FRESH PREDICTION SUCCESS: Generated fresh predictions using intelligent system only")
                                
                                predictions_generated = 1 if fresh_predictions_success else 0
                                
                                # Log success with predictions and validation
                                self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), True, 
                                                       f"Captured {len(screenshots)} screenshots, found {new_results} new results, validated {validation_results} predictions, generated {predictions_generated} AI predictions")
                            except Exception as prediction_error:
                                logger.warning(f"⚠️ WORKER-SAFE PREDICTION PARTIAL: Lottery results captured and predictions validated, but immediate prediction generation failed: {prediction_error}")
                                # Log success for results and validation but note prediction failure
                                self._log_automation_run(start_time, datetime.now(SA_TIMEZONE), True, 
                                                       f"Captured {len(screenshots)} screenshots, found {new_results} new results, validated {validation_results} predictions (generation failed: {prediction_error})")
                        else:
                            # Log success without predictions (no new results)
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
        finally:
            # Always release the database lock
            if conn and worker_id:
                self._release_database_lock(conn, worker_id)
    
    def _get_database_lock(self):
        """Try to acquire database lock for automation - prevents multiple workers running simultaneously"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            # Create automation lock table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS automation_lock (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    worker_id VARCHAR(100),
                    locked_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    CHECK (id = 1)
                );
                INSERT INTO automation_lock (id, worker_id, locked_at, expires_at) 
                VALUES (1, NULL, NULL, NULL) ON CONFLICT (id) DO NOTHING;
            """)
            
            # Try to acquire lock with 1 hour expiry (in case worker crashes)
            worker_id = f"worker_{os.getpid()}_{int(time.time())}"
            cur.execute("""
                UPDATE automation_lock 
                SET worker_id = %s, 
                    locked_at = NOW(), 
                    expires_at = NOW() + INTERVAL '1 hour'
                WHERE id = 1 AND (worker_id IS NULL OR expires_at < NOW())
                RETURNING worker_id
            """, (worker_id,))
            
            result = cur.fetchone()
            conn.commit()
            
            if result and result[0] == worker_id:
                logger.info(f"🔐 WORKER-SAFE: Acquired automation lock with worker_id={worker_id}")
                cur.close()
                return conn, worker_id
            else:
                cur.close()
                conn.close()
                logger.info("🔒 WORKER-SAFE: Another worker is already running automation")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ Failed to acquire database lock: {e}")
            return None, None
    
    def _release_database_lock(self, conn, worker_id):
        """Release database lock"""
        try:
            cur = conn.cursor()
            cur.execute("UPDATE automation_lock SET worker_id = NULL, locked_at = NULL, expires_at = NULL WHERE worker_id = %s", (worker_id,))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"🔓 WORKER-SAFE: Released automation lock for worker_id={worker_id}")
        except Exception as e:
            logger.error(f"❌ Failed to release database lock: {e}")

    def _generate_immediate_predictions(self):
        """Generate predictions immediately for the next draw after new results"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            game_types = ['DAILY LOTTO', 'LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS']
            predictions_generated = 0
            
            for game_type in game_types:
                try:
                    # Get the latest draw number for this game
                    cur.execute("""
                        SELECT MAX(draw_number) 
                        FROM lottery_results 
                        WHERE lottery_type = %s
                    """, (game_type,))
                    
                    result = cur.fetchone()
                    if not result or not result[0]:
                        logger.info(f"⚠️ No results found for {game_type}, skipping prediction generation")
                        continue
                    
                    latest_draw_number = result[0]
                    next_draw_number = latest_draw_number + 1
                    
                    # Check if prediction already exists for next draw
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM lottery_predictions 
                        WHERE game_type = %s 
                        AND (linked_draw_id = %s OR predicted_numbers IS NOT NULL)
                    """, (game_type, next_draw_number))
                    
                    existing_count = cur.fetchone()[0]
                    if existing_count > 0:
                        logger.info(f"✅ {game_type}: Prediction for draw {next_draw_number} already exists, skipping")
                        continue
                    
                    # Generate new prediction for next draw
                    logger.info(f"🎯 {game_type}: Generating prediction for next draw {next_draw_number}")
                    
                    from ai_lottery_predictor import AILotteryPredictor
                    predictor = AILotteryPredictor()
                    
                    # Get historical data for intelligent prediction
                    historical_data = predictor.get_historical_data_for_prediction(game_type, 80)
                    
                    if historical_data:
                        prediction = predictor.generate_intelligent_prediction(game_type, historical_data)
                        
                        if prediction:
                            # Calculate target draw date based on game schedule
                            from datetime import timedelta
                            
                            cur.execute("""
                                SELECT draw_date FROM lottery_results 
                                WHERE lottery_type = %s AND draw_number = %s
                            """, (game_type, latest_draw_number))
                            
                            latest_date_result = cur.fetchone()
                            if latest_date_result:
                                latest_draw_date = latest_date_result[0]
                                
                                # Calculate next draw date based on game type
                                if game_type == 'DAILY LOTTO':
                                    next_draw_date = latest_draw_date + timedelta(days=1)
                                elif game_type in ['POWERBALL', 'POWERBALL PLUS']:
                                    # PowerBall: Tuesday and Friday
                                    days_ahead = 2 if latest_draw_date.weekday() == 1 else 4 if latest_draw_date.weekday() == 4 else 3
                                    next_draw_date = latest_draw_date + timedelta(days=days_ahead)
                                else:  # LOTTO games
                                    # LOTTO: Wednesday and Saturday  
                                    days_ahead = 3 if latest_draw_date.weekday() == 2 else 4 if latest_draw_date.weekday() == 5 else 3
                                    next_draw_date = latest_draw_date + timedelta(days=days_ahead)
                                
                                # Store prediction
                                cur.execute("""
                                    INSERT INTO lottery_predictions (
                                        game_type, predicted_numbers, bonus_numbers, 
                                        confidence_score, prediction_method, reasoning, 
                                        target_draw_date, linked_draw_id, created_at,
                                        is_locked, lock_reason
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    prediction.game_type,
                                    prediction.predicted_numbers,
                                    prediction.bonus_numbers,
                                    prediction.confidence_score,
                                    prediction.prediction_method,
                                    f"IMMEDIATE: {prediction.reasoning}",
                                    next_draw_date,
                                    next_draw_number,
                                    prediction.created_at,
                                    True,
                                    f"Auto-generated immediately after draw {latest_draw_number} results"
                                ))
                                
                                conn.commit()
                                predictions_generated += 1
                                logger.info(f"✅ {game_type}: Generated prediction for draw {next_draw_number} targeting {next_draw_date}")
                            else:
                                logger.warning(f"⚠️ {game_type}: Could not determine latest draw date")
                        else:
                            logger.warning(f"⚠️ {game_type}: AI prediction generation failed")
                    else:
                        logger.warning(f"⚠️ {game_type}: No historical data available for prediction")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating prediction for {game_type}: {e}")
                    continue
            
            cur.close()
            conn.close()
            return predictions_generated
            
        except Exception as e:
            logger.error(f"❌ Error in immediate prediction generation: {e}")
            return 0
    
    def _fill_prediction_gaps(self):
        """Detect and fill any gaps in predictions where draws exist but predictions don't"""
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            game_types = ['DAILY LOTTO', 'LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS']
            gaps_filled = 0
            
            for game_type in game_types:
                try:
                    # Find draws that exist but don't have predictions
                    cur.execute("""
                        SELECT lr.draw_number, lr.draw_date
                        FROM lottery_results lr
                        LEFT JOIN lottery_predictions lp ON (
                            lp.game_type = lr.lottery_type 
                            AND lp.linked_draw_id = lr.draw_number
                        )
                        WHERE lr.lottery_type = %s 
                        AND lp.id IS NULL
                        AND lr.draw_date >= CURRENT_DATE - INTERVAL '30 days'
                        ORDER BY lr.draw_number DESC
                        LIMIT 10
                    """, (game_type,))
                    
                    missing_predictions = cur.fetchall()
                    
                    if missing_predictions:
                        logger.info(f"🔍 {game_type}: Found {len(missing_predictions)} draws without predictions")
                        
                        for draw_number, draw_date in missing_predictions:
                            try:
                                logger.info(f"🔧 {game_type}: Filling gap for draw {draw_number} ({draw_date})")
                                
                                from ai_lottery_predictor import AILotteryPredictor
                                predictor = AILotteryPredictor()
                                
                                # Get historical data for intelligent prediction
                                historical_data = predictor.get_historical_data_for_prediction(game_type, 80)
                                
                                if historical_data:
                                    prediction = predictor.generate_intelligent_prediction(game_type, historical_data)
                                    
                                    if prediction:
                                        # Store gap-filling prediction
                                        cur.execute("""
                                            INSERT INTO lottery_predictions (
                                                game_type, predicted_numbers, bonus_numbers, 
                                                confidence_score, prediction_method, reasoning, 
                                                target_draw_date, linked_draw_id, created_at,
                                                is_locked, lock_reason, validation_status
                                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """, (
                                            prediction.game_type,
                                            prediction.predicted_numbers,
                                            prediction.bonus_numbers,
                                            prediction.confidence_score,
                                            prediction.prediction_method,
                                            f"GAP-FILL: {prediction.reasoning}",
                                            draw_date,
                                            draw_number,
                                            prediction.created_at,
                                            True,
                                            f"Gap-filling prediction for historical draw {draw_number}",
                                            'pending'  # Will be validated if results exist
                                        ))
                                        
                                        conn.commit()
                                        gaps_filled += 1
                                        logger.info(f"✅ {game_type}: Filled prediction gap for draw {draw_number}")
                                    else:
                                        logger.warning(f"⚠️ {game_type}: Failed to generate gap-filling prediction for draw {draw_number}")
                                else:
                                    logger.warning(f"⚠️ {game_type}: No historical data for gap-filling draw {draw_number}")
                                    
                            except Exception as e:
                                logger.error(f"❌ Error filling gap for {game_type} draw {draw_number}: {e}")
                                continue
                    else:
                        logger.info(f"✅ {game_type}: No prediction gaps found")
                        
                except Exception as e:
                    logger.error(f"❌ Error checking gaps for {game_type}: {e}")
                    continue
            
            cur.close()
            conn.close()
            return gaps_filled
            
        except Exception as e:
            logger.error(f"❌ Error in gap detection and filling: {e}")
            return 0
    
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