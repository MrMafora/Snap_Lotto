"""
Fix Lottery Screenshots Synchronization Issues

This script diagnoses and fixes inconsistencies between Screenshot and ScheduleConfig records.
It ensures all lottery game types are properly synchronized.
"""
import os
import sys
import traceback
import logging
from datetime import datetime
from models import db, Screenshot, ScheduleConfig
import screenshot_diagnostics as diag
import selenium_screenshot_manager as ssm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_lottery_screenshots")

def inspect_database_records():
    """Inspect Screenshot and ScheduleConfig records for inconsistencies"""
    try:
        screenshots = Screenshot.query.all()
        configs = ScheduleConfig.query.all()
        
        print(f"Found {len(screenshots)} Screenshot records and {len(configs)} ScheduleConfig records")
        
        # Check for screenshots without configs
        screenshot_urls = {s.url for s in screenshots}
        config_urls = {c.url for c in configs}
        
        screenshots_without_configs = screenshot_urls - config_urls
        if screenshots_without_configs:
            print(f"Found {len(screenshots_without_configs)} Screenshot records with no matching ScheduleConfig:")
            for url in screenshots_without_configs:
                screenshot = Screenshot.query.filter_by(url=url).first()
                print(f"  - {screenshot.lottery_type}: {url}")
        
        # Check for configs without screenshots
        configs_without_screenshots = config_urls - screenshot_urls
        if configs_without_screenshots:
            print(f"Found {len(configs_without_screenshots)} ScheduleConfig records with no matching Screenshot:")
            for url in configs_without_screenshots:
                config = ScheduleConfig.query.filter_by(url=url).first()
                print(f"  - {config.lottery_type}: {url}")
        
        # Check for timestamp inconsistencies
        inconsistent_timestamps = []
        for url in screenshot_urls & config_urls:
            screenshot = Screenshot.query.filter_by(url=url).first()
            config = ScheduleConfig.query.filter_by(url=url).first()
            
            if not screenshot.timestamp or not config.last_run:
                inconsistent_timestamps.append((screenshot.lottery_type, url, "Missing timestamp"))
                continue
            
            time_diff = abs((screenshot.timestamp - config.last_run).total_seconds())
            if time_diff > 60:  # More than 1 minute difference
                inconsistent_timestamps.append((
                    screenshot.lottery_type, 
                    url, 
                    f"Timestamp difference: {time_diff:.1f} seconds",
                    f"Screenshot: {screenshot.timestamp}",
                    f"ScheduleConfig: {config.last_run}"
                ))
        
        if inconsistent_timestamps:
            print(f"Found {len(inconsistent_timestamps)} records with inconsistent timestamps:")
            for info in inconsistent_timestamps:
                print(f"  - {info[0]}: {info[1]}")
                for detail in info[2:]:
                    print(f"    {detail}")
        
        return {
            "total_screenshots": len(screenshots),
            "total_configs": len(configs),
            "screenshots_without_configs": len(screenshots_without_configs),
            "configs_without_screenshots": len(configs_without_screenshots),
            "inconsistent_timestamps": len(inconsistent_timestamps)
        }
    
    except Exception as e:
        print(f"Error inspecting database records: {str(e)}")
        traceback.print_exc()
        return None

def fix_missing_configs():
    """Create missing ScheduleConfig records for existing Screenshots"""
    try:
        screenshots = Screenshot.query.all()
        created_count = 0
        
        for screenshot in screenshots:
            # Check if a config already exists
            existing_config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if not existing_config:
                # Create a new config
                new_config = ScheduleConfig(
                    url=screenshot.url,
                    lottery_type=screenshot.lottery_type,
                    last_run=screenshot.timestamp or datetime.now(),
                    active=True,
                    frequency='daily',
                    hour=1,
                    minute=0
                )
                db.session.add(new_config)
                created_count += 1
                print(f"Created ScheduleConfig for {screenshot.lottery_type}: {screenshot.url}")
        
        if created_count > 0:
            db.session.commit()
            print(f"Created {created_count} new ScheduleConfig records")
        else:
            print("No missing ScheduleConfig records found")
        
        return created_count
    
    except Exception as e:
        print(f"Error fixing missing configs: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return 0

def fix_missing_screenshots():
    """Create missing Screenshot records for existing ScheduleConfigs"""
    try:
        configs = ScheduleConfig.query.all()
        created_count = 0
        
        for config in configs:
            # Check if a screenshot already exists
            existing_screenshot = Screenshot.query.filter_by(url=config.url).first()
            if not existing_screenshot:
                # Create a new screenshot
                new_screenshot = Screenshot(
                    url=config.url,
                    lottery_type=config.lottery_type,
                    timestamp=config.last_run or datetime.now()
                )
                db.session.add(new_screenshot)
                created_count += 1
                print(f"Created Screenshot for {config.lottery_type}: {config.url}")
        
        if created_count > 0:
            db.session.commit()
            print(f"Created {created_count} new Screenshot records")
        else:
            print("No missing Screenshot records found")
        
        return created_count
    
    except Exception as e:
        print(f"Error fixing missing screenshots: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return 0

def fix_timestamp_inconsistencies():
    """Fix timestamp inconsistencies between Screenshot and ScheduleConfig records"""
    try:
        screenshots = Screenshot.query.all()
        fixed_count = 0
        
        for screenshot in screenshots:
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if not config:
                continue
            
            if not screenshot.timestamp or not config.last_run:
                # Fix missing timestamps
                now = datetime.now()
                if not screenshot.timestamp:
                    screenshot.timestamp = now
                if not config.last_run:
                    config.last_run = now
                fixed_count += 1
                print(f"Fixed missing timestamp for {screenshot.lottery_type}")
                continue
            
            # Check for significant timestamp differences
            time_diff = abs((screenshot.timestamp - config.last_run).total_seconds())
            if time_diff > 60:  # More than 1 minute difference
                # Use the more recent timestamp for both
                latest_time = max(screenshot.timestamp, config.last_run)
                screenshot.timestamp = latest_time
                config.last_run = latest_time
                fixed_count += 1
                print(f"Fixed timestamp inconsistency for {screenshot.lottery_type} (diff: {time_diff:.1f}s)")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"Fixed {fixed_count} timestamp inconsistencies")
        else:
            print("No timestamp inconsistencies found")
        
        return fixed_count
    
    except Exception as e:
        print(f"Error fixing timestamp inconsistencies: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return 0

def sync_specific_lottery_type(lottery_type):
    """Sync a specific lottery type by name"""
    try:
        screenshots = Screenshot.query.filter_by(lottery_type=lottery_type).all()
        if not screenshots:
            print(f"No screenshots found for lottery type: {lottery_type}")
            return False
        
        print(f"Found {len(screenshots)} screenshots for {lottery_type}")
        success_count = 0
        
        for screenshot in screenshots:
            print(f"Syncing {screenshot.lottery_type} from {screenshot.url}")
            # Use our enhanced synchronization function
            with ssm.screenshot_semaphore:
                filepath, _, _ = ssm.capture_screenshot(screenshot.url, lottery_type=lottery_type)
                
            if filepath:
                # Use the same timestamp for both updates
                now = datetime.now()
                
                # Update Screenshot
                screenshot.path = filepath
                screenshot.timestamp = now
                
                # Update or create ScheduleConfig
                config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
                if config:
                    config.last_run = now
                else:
                    # Create new config if it doesn't exist
                    config = ScheduleConfig(
                        url=screenshot.url,
                        lottery_type=screenshot.lottery_type,
                        last_run=now,
                        active=True,
                        frequency='daily',
                        hour=1,
                        minute=0
                    )
                    db.session.add(config)
                
                db.session.commit()
                success_count += 1
                print(f"Successfully synced {screenshot.lottery_type}")
            else:
                print(f"Failed to sync {screenshot.lottery_type}")
        
        print(f"Sync complete: {success_count}/{len(screenshots)} successful")
        return success_count > 0
    
    except Exception as e:
        print(f"Error syncing lottery type {lottery_type}: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return False

def resync_failed_games():
    """
    Identify and resync lottery game types that have failed or show inconsistent timestamps
    """
    try:
        # Get stats from diagnostic module
        stats = diag.sync_stats.get("by_lottery_type", {})
        
        # Identify games with failures
        failed_games = []
        for lottery_type, game_stats in stats.items():
            if game_stats.get("failed", 0) > 0:
                failed_games.append(lottery_type)
        
        # Also check for timestamp inconsistencies
        screenshots = Screenshot.query.all()
        for screenshot in screenshots:
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if not config:
                continue
            
            if not screenshot.timestamp or not config.last_run:
                if screenshot.lottery_type not in failed_games:
                    failed_games.append(screenshot.lottery_type)
                continue
            
            time_diff = abs((screenshot.timestamp - config.last_run).total_seconds())
            if time_diff > 60 and screenshot.lottery_type not in failed_games:
                failed_games.append(screenshot.lottery_type)
        
        if not failed_games:
            print("No failed games identified for resync")
            return True
        
        print(f"Attempting to resync {len(failed_games)} failed games:")
        for lottery_type in failed_games:
            print(f"Resyncing {lottery_type}")
            sync_specific_lottery_type(lottery_type)
        
        return True
    
    except Exception as e:
        print(f"Error resyncing failed games: {str(e)}")
        traceback.print_exc()
        return False

def complete_fix():
    """
    Perform a complete fix of all screenshot synchronization issues
    """
    try:
        print("\n=== Starting complete screenshot synchronization fix ===\n")
        
        # Step 1: Inspect current state
        print("\n[Step 1] Inspecting database records")
        inspect_database_records()
        
        # Step 2: Fix missing configs and screenshots
        print("\n[Step 2] Fixing missing ScheduleConfig records")
        fix_missing_configs()
        
        print("\n[Step 3] Fixing missing Screenshot records")
        fix_missing_screenshots()
        
        # Step 4: Fix timestamp inconsistencies
        print("\n[Step 4] Fixing timestamp inconsistencies")
        fix_timestamp_inconsistencies()
        
        # Step 5: Verify fix
        print("\n[Step 5] Verifying fixes")
        results = inspect_database_records()
        
        # Step 6: Resync still-failing games
        print("\n[Step 6] Resyncing any still-failing games")
        resync_failed_games()
        
        # Final verification
        print("\n[Final Verification]")
        final_results = inspect_database_records()
        
        print("\n=== Fix complete ===\n")
        return True
    
    except Exception as e:
        print(f"Error during complete fix: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        from main import app
        
        with app.app_context():
            if len(sys.argv) > 1:
                command = sys.argv[1]
                
                if command == "inspect":
                    inspect_database_records()
                
                elif command == "fix-configs":
                    fix_missing_configs()
                
                elif command == "fix-screenshots":
                    fix_missing_screenshots()
                
                elif command == "fix-timestamps":
                    fix_timestamp_inconsistencies()
                
                elif command == "sync":
                    if len(sys.argv) > 2:
                        lottery_type = sys.argv[2]
                        sync_specific_lottery_type(lottery_type)
                    else:
                        print("Please specify a lottery type to sync")
                
                elif command == "resync-failed":
                    resync_failed_games()
                
                elif command == "complete-fix":
                    complete_fix()
                
                else:
                    print("Unknown command. Available commands:")
                    print("  inspect - Inspect database records")
                    print("  fix-configs - Fix missing ScheduleConfig records")
                    print("  fix-screenshots - Fix missing Screenshot records")
                    print("  fix-timestamps - Fix timestamp inconsistencies")
                    print("  sync <lottery_type> - Sync a specific lottery type")
                    print("  resync-failed - Resync lottery types with failures")
                    print("  complete-fix - Perform a complete fix")
            
            else:
                print("Please specify a command. Run with 'complete-fix' for full repair.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()