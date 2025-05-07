"""
Fix Screenshot Synchronization Issues
This script addresses the inconsistent screenshot synchronization where only Lotto Plus 2 Results
appears to be properly updated while other lottery types show outdated data or errors.
"""
import os
import sys
import traceback
import logging
from datetime import datetime
from flask import Flask
from models import db, Screenshot, ScheduleConfig
import selenium_screenshot_manager as ssm
import fix_lottery_screenshots as fix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_lottery_sync_issues(app=None):
    """
    Comprehensive fix for lottery screenshot synchronization issues.
    Addresses the specific issue where only Lotto Plus 2 Results are displaying correctly.
    
    Args:
        app: Flask application instance (optional)
        
    Returns:
        dict: Results of the synchronization fix
    """
    try:
        if app is None:
            from main import app
        
        with app.app_context():
            logger.info("Starting comprehensive fix for lottery screenshot synchronization issues")
            
            # Step 1: Run diagnostic inspection to identify issues
            logger.info("Step 1: Inspecting screenshot synchronization issues")
            issues = fix.inspect_database_records()
            
            # Step 2: Fix structural record issues
            logger.info("Step 2: Fixing missing database records")
            configs_fixed = fix.fix_missing_configs()
            screenshots_fixed = fix.fix_missing_screenshots()
            
            # Step 3: Fix timestamp inconsistencies
            logger.info("Step 3: Fixing timestamp inconsistencies")
            timestamps_fixed = fix.fix_timestamp_inconsistencies()
            
            # Step 4: Sync all lottery types with improved concurrency
            # This uses our new queue-based approach for better performance
            logger.info("Step 4: Syncing all lottery types with improved concurrency")
            
            lottery_types = [
                "Lotto", 
                "Lotto Plus 1", 
                "Lotto Plus 2", 
                "Powerball", 
                "Powerball Plus", 
                "Daily Lotto"
            ]
            
            # Use the enhanced sync_all_types function for better concurrency
            sync_results = sync_all_types()
            
            # Step 5: Final verification
            logger.info("Step 5: Performing final verification")
            final_status = fix.inspect_database_records()
            
            # Return results
            return {
                "initial_issues": issues,
                "configs_fixed": configs_fixed,
                "screenshots_fixed": screenshots_fixed,
                "timestamps_fixed": timestamps_fixed,
                "sync_results": sync_results,
                "final_status": final_status
            }
    
    except Exception as e:
        logger.error(f"Error fixing lottery sync issues: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

def sync_all_types():
    """
    Synchronize all lottery types using the improved queue-based approach.
    This ensures consistent synchronization across all lottery types with better concurrency handling.
    """
    try:
        from main import app
        
        with app.app_context():
            lottery_types = [
                "Lotto", 
                "Lotto Plus 1", 
                "Lotto Plus 2", 
                "Powerball", 
                "Powerball Plus", 
                "Daily Lotto"
            ]
            
            # Get all related screenshots from the database
            screenshots = Screenshot.query.filter(Screenshot.lottery_type.in_(lottery_types)).all()
            
            # Log what we found
            found_types = {ss.lottery_type for ss in screenshots}
            missing_types = set(lottery_types) - found_types
            
            if missing_types:
                logger.warning(f"Missing screenshots for: {', '.join(missing_types)}")
                # Try to fix missing screenshots
                for lottery_type in missing_types:
                    config = ScheduleConfig.query.filter_by(lottery_type=lottery_type).first()
                    if config and config.url:
                        logger.info(f"Creating missing screenshot record for {lottery_type}")
                        new_screenshot = Screenshot(
                            lottery_type=lottery_type,
                            url=config.url,
                            timestamp=datetime.now()
                        )
                        db.session.add(new_screenshot)
                        try:
                            db.session.commit()
                            logger.info(f"Created screenshot record for {lottery_type}")
                        except Exception as e:
                            logger.error(f"Failed to create screenshot for {lottery_type}: {str(e)}")
                            db.session.rollback()
            
            # Get screenshots again in case we added any
            screenshots = Screenshot.query.filter(Screenshot.lottery_type.in_(lottery_types)).all()
            
            # Use the improved queue-based screenshot capture
            logger.info(f"Starting enhanced screenshot synchronization for {len(screenshots)} lottery types")
            
            # Use our selenium screenshot manager for reliable capture
            import selenium_screenshot_manager as ssm
            
            # Clear the screenshot queue
            while not ssm.screenshot_queue.empty():
                try:
                    ssm.screenshot_queue.get_nowait()
                except:
                    break
            
            # Add all screenshots to the queue
            for screenshot in screenshots:
                ssm.screenshot_queue.put(screenshot)
            
            # Create worker threads to process the queue
            import threading
            import queue
            import time
            import random
            
            # Track results
            results = {}
            success_count = 0
            failed_types = []
            
            # Create thread-safe containers for results
            results_lock = threading.Lock()
            
            def worker():
                """Worker thread to process screenshots from the queue"""
                while True:
                    try:
                        # Get the next screenshot from the queue with a timeout
                        try:
                            screenshot = ssm.screenshot_queue.get(timeout=5)
                        except queue.Empty:
                            # Queue is empty, exit this worker
                            break
                        
                        lottery_type = screenshot.lottery_type
                        url = screenshot.url
                        
                        logger.info(f"Processing {lottery_type} from {url}")
                        
                        # Add a small random delay to avoid rate limiting
                        time.sleep(random.uniform(0.5, 2.0))
                        
                        # Process the screenshot using our task function
                        success, _, _ = ssm.process_screenshot_task(screenshot)
                        
                        # Update the results with thread safety
                        with results_lock:
                            nonlocal success_count, failed_types
                            results[lottery_type] = "Success" if success else "Failed"
                            if success:
                                success_count += 1
                            else:
                                failed_types.append(lottery_type)
                        
                        # Mark task as done
                        ssm.screenshot_queue.task_done()
                    
                    except Exception as e:
                        logger.error(f"Worker thread error: {str(e)}")
                        traceback.print_exc()
                        
                        # Ensure we mark the task as done even on error
                        try:
                            ssm.screenshot_queue.task_done()
                        except:
                            pass
            
            # Start worker threads - up to 6 concurrent threads
            worker_threads = []
            max_workers = min(6, len(screenshots))  # Don't create more threads than we have work
            
            logger.info(f"Starting {max_workers} worker threads")
            for i in range(max_workers):
                thread = threading.Thread(target=worker)
                thread.daemon = True
                thread.start()
                worker_threads.append(thread)
            
            # Wait for all screenshots to be processed
            try:
                # Join with a generous timeout
                ssm.screenshot_queue.join()
                logger.info("All tasks completed successfully")
            except Exception as e:
                logger.warning(f"Exception waiting for queue completion: {str(e)}")
            
            # Wait for worker threads to exit
            for thread in worker_threads:
                thread.join(timeout=5)
            
            # Final verification
            logger.info(f"Sync complete: {success_count}/{len(screenshots)} successful")
            if failed_types:
                logger.warning(f"Failed types: {', '.join(failed_types)}")
            
            # Run a database integrity check
            from check_timestamp_sync import check_timestamp_sync
            sync_status = check_timestamp_sync()
            logger.info(f"Timestamp sync check: {sync_status['in_sync']} synced, {sync_status['out_of_sync']} not synced")
            
            # Fix any remaining timestamp issues
            if sync_status['out_of_sync'] > 0:
                from check_timestamp_sync import fix_timestamp_sync
                fixed = fix_timestamp_sync()
                logger.info(f"Fixed {fixed} timestamp synchronization issues")
            
            return results
                
    except Exception as e:
        logger.error(f"Error in sync_all_types: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    try:
        from main import app
        
        with app.app_context():
            if len(sys.argv) > 1:
                command = sys.argv[1]
                
                if command == "fix-all":
                    logger.info("Executing comprehensive fix for all lottery types")
                    results = fix_lottery_sync_issues(app)
                    print(f"Fix results: {results}")
                
                elif command == "sync-all":
                    logger.info("Syncing all lottery types")
                    results = sync_all_types()
                    print(f"Sync results: {results}")
                
                elif command == "sync":
                    if len(sys.argv) > 2:
                        lottery_type = sys.argv[2]
                        logger.info(f"Syncing specific lottery type: {lottery_type}")
                        success = fix.sync_specific_lottery_type(lottery_type)
                        print(f"Sync result: {'Success' if success else 'Failed'}")
                    else:
                        print("Please specify a lottery type to sync")
                
                else:
                    print("Unknown command. Available commands:")
                    print("  fix-all - Run comprehensive fix for all lottery types")
                    print("  sync-all - Sync all lottery types")
                    print("  sync <lottery_type> - Sync a specific lottery type")
            
            else:
                print("Please specify a command. Run with 'fix-all' for comprehensive fix.")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        traceback.print_exc()