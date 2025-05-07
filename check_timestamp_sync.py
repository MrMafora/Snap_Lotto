"""
Utility to check timestamp synchronization between Screenshot and ScheduleConfig tables.

This script identifies any discrepancies between timestamps to help diagnose synchronization issues.
"""
import os
import logging
from datetime import datetime, timedelta
from logger import setup_logger
from models import db, Screenshot, ScheduleConfig

# Set up module-specific logger
logger = setup_logger(__name__, level=logging.INFO)

def check_timestamp_sync():
    """
    Check if Screenshot.timestamp and ScheduleConfig.last_run are synchronized.
    
    Returns:
        dict: Summary of sync status and issues found
    """
    try:
        results = {
            'total_screenshots': 0,
            'total_configs': 0,
            'matching_pairs': 0,
            'mismatched_pairs': 0,
            'missing_configs': 0,
            'mismatched_details': []
        }
        
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        results['total_screenshots'] = len(screenshots)
        
        # Get all schedule config records
        configs = ScheduleConfig.query.all()
        results['total_configs'] = len(configs)
        
        logger.info(f"Found {len(screenshots)} screenshot records and {len(configs)} schedule config records")
        
        # Check each screenshot for corresponding config
        for screenshot in screenshots:
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            
            if not config:
                results['missing_configs'] += 1
                logger.warning(f"No ScheduleConfig record found for {screenshot.lottery_type} ({screenshot.url})")
                continue
                
            # Check if timestamps match exactly
            if screenshot.timestamp == config.last_run:
                results['matching_pairs'] += 1
                logger.debug(f"Timestamps match for {screenshot.lottery_type}: {screenshot.timestamp}")
            else:
                results['mismatched_pairs'] += 1
                
                # Calculate the difference in seconds
                if screenshot.timestamp and config.last_run:
                    diff_seconds = abs((screenshot.timestamp - config.last_run).total_seconds())
                    
                    mismatch_details = {
                        'lottery_type': screenshot.lottery_type,
                        'screenshot_timestamp': screenshot.timestamp.isoformat() if screenshot.timestamp else None,
                        'config_timestamp': config.last_run.isoformat() if config.last_run else None,
                        'difference_seconds': diff_seconds,
                        'url': screenshot.url
                    }
                    results['mismatched_details'].append(mismatch_details)
                    
                    logger.warning(
                        f"Timestamp mismatch for {screenshot.lottery_type}:\n"
                        f"  Screenshot: {screenshot.timestamp}\n"
                        f"  ScheduleConfig: {config.last_run}\n"
                        f"  Difference: {diff_seconds} seconds"
                    )
        
        # Calculate summary
        if results['total_screenshots'] > 0:
            sync_percentage = (results['matching_pairs'] / results['total_screenshots']) * 100
            results['sync_percentage'] = sync_percentage
            logger.info(f"Sync percentage: {sync_percentage:.1f}%")
            
            if results['mismatched_pairs'] > 0:
                logger.warning(f"Found {results['mismatched_pairs']} timestamp mismatches")
            else:
                logger.info("All timestamps are in sync!")
                
        return results
        
    except Exception as e:
        logger.error(f"Error checking timestamp sync: {str(e)}")
        return {'error': str(e)}

def fix_timestamp_sync():
    """
    Fix any timestamp synchronization issues by setting ScheduleConfig.last_run
    to match Screenshot.timestamp.
    
    Returns:
        int: Number of records fixed
    """
    try:
        fixed_count = 0
        
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        logger.info(f"Checking {len(screenshots)} screenshot records for sync issues")
        
        for screenshot in screenshots:
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            
            if not config:
                # Create a new config if it doesn't exist
                try:
                    now = datetime.now()
                    new_config = ScheduleConfig(
                        url=screenshot.url,
                        lottery_type=screenshot.lottery_type,
                        last_run=screenshot.timestamp or now,
                        active=True,
                        frequency='daily',
                        hour=1,
                        minute=0
                    )
                    db.session.add(new_config)
                    logger.info(f"Created new ScheduleConfig record for {screenshot.lottery_type}")
                    fixed_count += 1
                except Exception as e:
                    logger.error(f"Failed to create ScheduleConfig for {screenshot.lottery_type}: {str(e)}")
                continue
                
            # Check if timestamps match exactly
            if screenshot.timestamp and config.last_run and screenshot.timestamp != config.last_run:
                logger.info(f"Fixing timestamp for {screenshot.lottery_type}:")
                logger.info(f"  Old value: {config.last_run}")
                logger.info(f"  New value: {screenshot.timestamp}")
                
                # Update the config timestamp to match the screenshot timestamp
                config.last_run = screenshot.timestamp
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            logger.info(f"Fixed {fixed_count} timestamp synchronization issues")
        else:
            logger.info("No timestamp synchronization issues found")
            
        return fixed_count
        
    except Exception as e:
        logger.error(f"Error fixing timestamp sync: {str(e)}")
        db.session.rollback()
        return 0

if __name__ == "__main__":
    # Run both check and fix when executed directly
    print("Checking timestamp synchronization...")
    check_results = check_timestamp_sync()
    
    if check_results.get('mismatched_pairs', 0) > 0:
        print("\nFixing timestamp synchronization issues...")
        fixed_count = fix_timestamp_sync()
        print(f"Fixed {fixed_count} issues")
        
        # Verify the fix worked
        print("\nVerifying fix...")
        new_check = check_timestamp_sync()
        if new_check.get('mismatched_pairs', 0) == 0:
            print("All timestamps are now in sync!")
        else:
            print(f"Some issues remain: {new_check.get('mismatched_pairs')} mismatches")
    else:
        print("All timestamps are already in sync!")