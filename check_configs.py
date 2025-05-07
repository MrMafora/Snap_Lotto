"""
Check all ScheduleConfig and Screenshot records to understand sync issues
"""
import sys
from main import app
from models import ScheduleConfig, Screenshot, db

def check_records():
    """Check all ScheduleConfig and Screenshot records"""
    try:
        with app.app_context():
            # Get all configs
            configs = ScheduleConfig.query.all()
            print(f"\nTotal ScheduleConfig records: {len(configs)}")
            
            for config in configs:
                print(f"ID: {config.id} | Type: {config.lottery_type} | URL: {config.url}")
            
            # Get all screenshots
            screenshots = Screenshot.query.all()
            print(f"\nTotal Screenshot records: {len(screenshots)}")
            
            for screenshot in screenshots:
                print(f"ID: {screenshot.id} | Type: {screenshot.lottery_type} | URL: {screenshot.url}")
                
            # Check for mismatches
            config_urls = {c.url for c in configs}
            screenshot_urls = {s.url for s in screenshots}
            
            print("\nURLs in ScheduleConfig but not in Screenshot:")
            for url in config_urls - screenshot_urls:
                config = ScheduleConfig.query.filter_by(url=url).first()
                print(f"  - {config.lottery_type}: {url}")
            
            print("\nURLs in Screenshot but not in ScheduleConfig:")
            for url in screenshot_urls - config_urls:
                screenshot = Screenshot.query.filter_by(url=url).first()
                print(f"  - {screenshot.lottery_type}: {url}")
            
    except Exception as e:
        print(f"Error checking records: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_records()