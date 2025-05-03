"""
Simple script to view current status of config and screenshots
"""
from main import app
from models import ScheduleConfig, Screenshot
from datetime import datetime, timedelta
import sys

def view_config_status():
    """View current status of all configs and screenshots"""
    print("\n=== SCREENSHOT CONFIGURATION STATUS ===")
    with app.app_context():
        configs = ScheduleConfig.query.filter_by(active=True).all()
        print(f"Found {len(configs)} active screenshot configurations")
        
        # Calculate the cutoff time for recent updates (last 5 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # Print status of each config
        for config in configs:
            screenshot = Screenshot.query.filter_by(url=config.url).first()
            
            if screenshot:
                # Check if recently updated
                is_recent = screenshot.timestamp and screenshot.timestamp > cutoff_time
                status = "RECENT" if is_recent else "OLD"
                time_str = screenshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                status = "MISSING"
                time_str = "N/A"
                
            url_domain = config.url.split("//")[1].split("/")[0] if "//" in config.url else config.url
                
            print(f"{status:7} | {config.lottery_type:20} | {time_str:19} | {url_domain}")
            
        # Count recent screenshots
        recent_screenshots = Screenshot.query.filter(
            Screenshot.timestamp > cutoff_time
        ).count()
        
        total_screenshots = Screenshot.query.count()
        
        print(f"\nSummary: {recent_screenshots} out of {total_screenshots} screenshots updated recently")
        print(f"         {len(configs)} total active configurations")
        
        # Success rate
        if total_screenshots > 0:
            print(f"         {recent_screenshots/len(configs):.0%} success rate")

if __name__ == "__main__":
    view_config_status()