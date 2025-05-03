"""
Check screenshot paths in database
"""
from main import app
from models import Screenshot, ScheduleConfig
import os

with app.app_context():
    # Get Daily Lotto and Daily Lotto Results screenshots
    daily_screenshots = Screenshot.query.filter(
        Screenshot.lottery_type.in_(["Daily Lotto", "Daily Lotto Results"])
    ).all()
    
    print(f"Found {len(daily_screenshots)} Daily Lotto-related screenshots")
    
    for screenshot in daily_screenshots:
        print(f"\nLottery Type: {screenshot.lottery_type}")
        print(f"Timestamp: {screenshot.timestamp}")
        print(f"URL: {screenshot.url}")
        print(f"Path: {screenshot.path}")
        print(f"Zoomed Path: {screenshot.zoomed_path}")
        
        # Check if files exist
        path_exists = os.path.exists(screenshot.path) if screenshot.path else False
        zoomed_exists = os.path.exists(screenshot.zoomed_path) if screenshot.zoomed_path else False
        
        print(f"Path exists: {path_exists}")
        print(f"Zoomed path exists: {zoomed_exists}")
        
        # Check file type (extension)
        if screenshot.path:
            _, ext = os.path.splitext(screenshot.path)
            print(f"Path file type: {ext}")
        
        if screenshot.zoomed_path:
            _, ext = os.path.splitext(screenshot.zoomed_path)
            print(f"Zoomed path file type: {ext}")