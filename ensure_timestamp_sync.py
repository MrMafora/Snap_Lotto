"""
Ensure timestamp synchronization between Screenshot and ScheduleConfig tables on application startup.

This script automatically verifies and fixes any timestamp synchronization issues when the application starts.
"""
import logging
from check_timestamp_sync import check_timestamp_sync, fix_timestamp_sync
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__, level=logging.INFO)

def ensure_sync_on_startup():
    """
    Run on application startup to ensure Screenshot and ScheduleConfig timestamps are in sync.
    
    Returns:
        bool: True if sync is OK (or fixed), False if errors occurred
    """
    try:
        logger.info("Verifying timestamp synchronization on startup")
        check_results = check_timestamp_sync()
        
        if check_results.get('error'):
            logger.error(f"Error checking timestamp sync: {check_results['error']}")
            return False
            
        mismatched = check_results.get('mismatched_pairs', 0)
        missing = check_results.get('missing_configs', 0)
        
        if mismatched > 0 or missing > 0:
            logger.warning(f"Found {mismatched} timestamp mismatches and {missing} missing configs")
            logger.info("Fixing timestamp synchronization issues")
            
            fixed_count = fix_timestamp_sync()
            logger.info(f"Fixed {fixed_count} synchronization issues")
            
            # Verify the fix worked
            new_check = check_timestamp_sync()
            if new_check.get('mismatched_pairs', 0) == 0 and new_check.get('missing_configs', 0) == 0:
                logger.info("All timestamps are now in sync!")
                return True
            else:
                remaining = new_check.get('mismatched_pairs', 0) + new_check.get('missing_configs', 0)
                logger.warning(f"Some issues remain: {remaining} problems")
                return False
        else:
            logger.info("All timestamps are already in sync!")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring timestamp sync: {str(e)}")
        return False