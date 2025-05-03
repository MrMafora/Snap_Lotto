"""
Final status check for screenshots
"""
from main import app
from models import ScheduleConfig, Screenshot
from datetime import datetime
import sys

with app.app_context():
    configs = ScheduleConfig.query.filter_by(active=True).all()
    screenshots = Screenshot.query.all()
    
    print("\n=== FINAL SCREENSHOT STATUS ===")
    print(f"Found {len(configs)} active configs and {len(screenshots)} screenshot records")
    
    # Check if Daily Lotto Results exists
    daily_results = Screenshot.query.filter_by(lottery_type="Daily Lotto Results").first()
    if daily_results:
        print(f"Daily Lotto Results: Found (timestamp: {daily_results.timestamp})")
    else:
        print("Daily Lotto Results: MISSING")
        
    # Check if Daily Lotto is recent
    daily_lotto = Screenshot.query.filter_by(lottery_type="Daily Lotto").first()
    if daily_lotto:
        print(f"Daily Lotto: Found (timestamp: {daily_lotto.timestamp})")
    else:
        print("Daily Lotto: MISSING")
    
    # Print all screenshot records
    print("\nAll screenshot records:")
    for screenshot in screenshots:
        print(f"  {screenshot.lottery_type} - {screenshot.timestamp} - {screenshot.url}")