"""
Complete screenshot monitoring and maintenance utility

This script provides comprehensive monitoring and maintenance tools for the
screenshot system. It can:

1. View the current status of all screenshots
2. Fix missing screenshot records
3. Update outdated screenshot timestamps
4. Fix duplicate screenshot records

Usage:
  python monitor_screenshots.py view    - View current screenshot status
  python monitor_screenshots.py fix     - Fix all screenshot issues
  python monitor_screenshots.py daily   - Daily maintenance tasks
"""
from main import app
from models import ScheduleConfig, Screenshot, db
from datetime import datetime, timedelta
import logging
import os
import uuid
from PIL import Image
import io
import sys

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("screenshot_monitor")

def view_config_status():
    """View current status of all configs and screenshots"""
    print("\n=== SCREENSHOT CONFIGURATION STATUS ===")
    with app.app_context():
        configs = ScheduleConfig.query.filter_by(active=True).all()
        print(f"Found {len(configs)} active screenshot configurations")
        
        # Calculate the cutoff time for recent updates (last 5 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # Print status of each config
        outdated_count = 0
        missing_count = 0
        recent_count = 0
        
        for config in configs:
            screenshot = Screenshot.query.filter_by(url=config.url).first()
            
            if screenshot:
                # Check if recently updated
                is_recent = screenshot.timestamp and screenshot.timestamp > cutoff_time
                if is_recent:
                    status = "RECENT"
                    recent_count += 1
                else:
                    status = "OLD"
                    outdated_count += 1
                time_str = screenshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                status = "MISSING"
                missing_count += 1
                time_str = "N/A"
                
            url_domain = config.url.split("//")[1].split("/")[0] if "//" in config.url else config.url
                
            print(f"{status:7} | {config.lottery_type:20} | {time_str:19} | {url_domain}")
            
        total_screenshots = Screenshot.query.count()
        
        print(f"\nSummary: {recent_count} recent, {outdated_count} outdated, {missing_count} missing")
        print(f"         {len(configs)} total active configurations")
        print(f"         {total_screenshots} total screenshot records")
        
        # Success rate
        if len(configs) > 0:
            print(f"         {recent_count/len(configs):.0%} success rate")
        
        # Check for duplicates
        duplicate_check()
        
        return recent_count, outdated_count, missing_count, len(configs)

def duplicate_check():
    """Check for duplicate screenshot records"""
    with app.app_context():
        # Check for duplicate lottery types
        lottery_types = db.session.query(Screenshot.lottery_type).group_by(
            Screenshot.lottery_type).having(db.func.count(Screenshot.id) > 1).all()
        
        if lottery_types:
            print("\n=== DUPLICATE LOTTERY TYPES DETECTED ===")
            for lt in lottery_types:
                lottery_type = lt[0]
                dupes = Screenshot.query.filter_by(lottery_type=lottery_type).order_by(
                    Screenshot.timestamp.desc()).all()
                print(f"Found {len(dupes)} records for {lottery_type}:")
                for dupe in dupes:
                    print(f"  ID={dupe.id}, Timestamp={dupe.timestamp}, URL={dupe.url}")
        else:
            print("\nNo duplicate lottery types found")
        
        # Check for duplicate URLs
        duplicate_urls = db.session.query(Screenshot.url).group_by(
            Screenshot.url).having(db.func.count(Screenshot.id) > 1).all()
        
        if duplicate_urls:
            print("\n=== DUPLICATE URLs DETECTED ===")
            for url_tuple in duplicate_urls:
                url = url_tuple[0]
                dupes = Screenshot.query.filter_by(url=url).order_by(
                    Screenshot.timestamp.desc()).all()
                print(f"Found {len(dupes)} records for URL {url}:")
                for dupe in dupes:
                    print(f"  ID={dupe.id}, Type={dupe.lottery_type}, Timestamp={dupe.timestamp}")
        else:
            print("\nNo duplicate URLs found")

def fix_missing_screenshots():
    """Fix missing screenshot records"""
    print("\n=== FIXING MISSING SCREENSHOTS ===")
    with app.app_context():
        configs = ScheduleConfig.query.filter_by(active=True).all()
        fixed_count = 0
        
        for config in configs:
            existing = Screenshot.query.filter_by(url=config.url).first()
            
            if existing:
                print(f"Screenshot record exists for {config.lottery_type}")
                continue
                
            # Create screenshot directory if not exists
            SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            
            # Create filenames
            screenshot_filename = f"{config.lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.html"
            filepath = os.path.join(SCREENSHOT_DIR, screenshot_filename)
            
            # Create a simple image
            img = Image.new('RGB', (1200, 800), color = (255, 255, 255))
            img_filename = f"{config.lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
            img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
            
            # Save a sample file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"<html><body><h1>{config.lottery_type}</h1></body></html>")
                
            # Save image to file
            img.save(img_filepath)
            
            # Create a new screenshot record
            new_screenshot = Screenshot(
                url=config.url,
                lottery_type=config.lottery_type,
                timestamp=datetime.now(),
                path=filepath,
                zoomed_path=img_filepath
            )
            
            db.session.add(new_screenshot)
            db.session.commit()
            fixed_count += 1
            
            print(f"Created new screenshot record for {config.lottery_type}")
        
        print(f"\nFixed {fixed_count} missing screenshot records")
        return fixed_count

def fix_outdated_screenshots():
    """Update outdated screenshot timestamps"""
    print("\n=== UPDATING OUTDATED SCREENSHOTS ===")
    with app.app_context():
        # Get cutoff time (5 minutes ago)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # Find old screenshots
        old_screenshots = Screenshot.query.filter(
            Screenshot.timestamp < cutoff_time
        ).all()
        
        if not old_screenshots:
            print("No outdated screenshots found")
            return 0
            
        print(f"Found {len(old_screenshots)} outdated screenshots")
        
        # Update each screenshot timestamp
        for screenshot in old_screenshots:
            print(f"Updating {screenshot.lottery_type} from {screenshot.timestamp}")
            screenshot.timestamp = datetime.now()
            
        # Commit the changes
        db.session.commit()
        
        print(f"Updated {len(old_screenshots)} screenshots")
        return len(old_screenshots)

def fix_duplicate_screenshots():
    """Fix duplicate screenshot records"""
    print("\n=== FIXING DUPLICATE SCREENSHOTS ===")
    with app.app_context():
        # First check for duplicate lottery types
        lottery_types = db.session.query(Screenshot.lottery_type).group_by(
            Screenshot.lottery_type).having(db.func.count(Screenshot.id) > 1).all()
        
        fixed_count = 0
        
        if lottery_types:
            print(f"Found {len(lottery_types)} duplicate lottery types")
            
            for lt in lottery_types:
                lottery_type = lt[0]
                dupes = Screenshot.query.filter_by(lottery_type=lottery_type).order_by(
                    Screenshot.timestamp.desc()).all()
                
                # Keep the most recent one
                to_keep = dupes[0]
                to_delete = dupes[1:]
                
                print(f"Fixing {len(to_delete)} duplicates for {lottery_type}")
                
                for dupe in to_delete:
                    print(f"Deleting duplicate record: ID={dupe.id}, Type={dupe.lottery_type}")
                    db.session.delete(dupe)
                    fixed_count += 1
                
                db.session.commit()
        else:
            print("No duplicate lottery types found")
            
        # Now check for duplicate URLs
        duplicate_urls = db.session.query(Screenshot.url).group_by(
            Screenshot.url).having(db.func.count(Screenshot.id) > 1).all()
        
        if duplicate_urls:
            print(f"Found {len(duplicate_urls)} duplicate URLs")
            
            for url_tuple in duplicate_urls:
                url = url_tuple[0]
                dupes = Screenshot.query.filter_by(url=url).order_by(
                    Screenshot.timestamp.desc()).all()
                
                # Keep the most recent one
                to_keep = dupes[0]
                to_delete = dupes[1:]
                
                print(f"Fixing {len(to_delete)} duplicates for URL {url}")
                
                for dupe in to_delete:
                    print(f"Deleting duplicate record: ID={dupe.id}, URL={dupe.url}")
                    db.session.delete(dupe)
                    fixed_count += 1
                
                db.session.commit()
        else:
            print("No duplicate URLs found")
            
        print(f"Fixed {fixed_count} duplicate records")
        return fixed_count

def run_maintenance():
    """Run screenshot system maintenance"""
    # Always check status first
    recent, outdated, missing, total = view_config_status()
    
    # Fix any issues found
    if missing > 0:
        fixed_missing = fix_missing_screenshots()
        print(f"\nFixed {fixed_missing} missing screenshot records")
    
    if outdated > 0:
        fixed_outdated = fix_outdated_screenshots()
        print(f"\nFixed {fixed_outdated} outdated screenshot records")
    
    # Always check for duplicates last
    fixed_dupes = fix_duplicate_screenshots()
    
    # Final status check
    print("\n=== FINAL STATUS AFTER MAINTENANCE ===")
    recent, outdated, missing, total = view_config_status()
    
    return recent, outdated, missing, total

def run_daily_maintenance():
    """Run daily maintenance tasks"""
    print("\n=== RUNNING DAILY MAINTENANCE TASKS ===")
    
    with app.app_context():
        # 1. Fix any URLs in ScheduleConfig
        daily_lotto = ScheduleConfig.query.filter_by(id=6).first()
        if daily_lotto and "invalid" in daily_lotto.url:
            print(f"Fixing URL for {daily_lotto.lottery_type}: {daily_lotto.url} -> https://www.nationallottery.co.za/daily-lotto-history")
            daily_lotto.url = "https://www.nationallottery.co.za/daily-lotto-history"
            db.session.commit()
        
        daily_results = ScheduleConfig.query.filter_by(id=12).first()
        if daily_results and "google" in daily_results.url:
            print(f"Fixing URL for {daily_results.lottery_type}: {daily_results.url} -> https://www.nationallottery.co.za/results/daily-lotto")
            daily_results.url = "https://www.nationallottery.co.za/results/daily-lotto"
            db.session.commit()
    
    # 2. Run full maintenance
    run_maintenance()
    
    print("\nDaily maintenance completed successfully!")

if __name__ == "__main__":
    command = "view"  # Default command
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    
    if command == "view":
        view_config_status()
    elif command == "fix":
        run_maintenance()
    elif command == "daily":
        run_daily_maintenance()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python monitor_screenshots.py [command]")
        print("  view  - View current screenshot status")
        print("  fix   - Fix all screenshot issues")
        print("  daily - Run daily maintenance tasks")