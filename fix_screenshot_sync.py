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
            
            # Step 4: Sync each lottery type individually to ensure independent success or failure
            # This prevents failures in one lottery type from affecting others
            logger.info("Step 4: Individually syncing each lottery type")
            
            lottery_types = [
                "Lotto", 
                "Lotto Plus 1", 
                "Lotto Plus 2", 
                "Powerball", 
                "Powerball Plus", 
                "Daily Lotto"
            ]
            
            sync_results = {}
            for lottery_type in lottery_types:
                logger.info(f"Syncing {lottery_type}...")
                success = fix.sync_specific_lottery_type(lottery_type)
                sync_results[lottery_type] = "Success" if success else "Failed"
                
                # Add small delay between syncs to prevent rate limiting
                import time
                time.sleep(2)
            
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
    Synchronize all lottery types using the correct method that works for Lotto Plus 2.
    This ensures consistent synchronization across all lottery types.
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
            
            results = {}
            for lottery_type in lottery_types:
                logger.info(f"Syncing {lottery_type}...")
                success = fix.sync_specific_lottery_type(lottery_type)
                results[lottery_type] = "Success" if success else "Failed"
                
                # Add small delay between syncs to prevent rate limiting
                import time
                time.sleep(2)
                
            return results
            
    except Exception as e:
        logger.error(f"Error syncing all types: {str(e)}")
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