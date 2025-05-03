"""
Final cleanup to fix the Daily Lotto Results duplicate
"""
from main import app
from models import Screenshot, ScheduleConfig, db

with app.app_context():
    # Check for daily lotto results records
    daily_results = Screenshot.query.filter_by(lottery_type="Daily Lotto Results").all()
    
    if len(daily_results) > 1:
        print(f"Found {len(daily_results)} Daily Lotto Results records")
        
        google_url = None
        proper_url = None
        
        for record in daily_results:
            print(f"ID: {record.id}, URL: {record.url}, Timestamp: {record.timestamp}")
            
            if "google" in record.url:
                google_url = record
            else:
                proper_url = record
        
        if google_url and proper_url:
            print("\nFixing URLs...")
            # Delete the Google record
            print(f"Deleting record with Google URL (ID: {google_url.id})")
            db.session.delete(google_url)
            db.session.commit()
            
            # Update the config to match the proper URL
            config = ScheduleConfig.query.filter_by(lottery_type="Daily Lotto Results").first()
            if config:
                print(f"Updating config URL from {config.url} to {proper_url.url}")
                config.url = proper_url.url
                db.session.commit()
            
            print("\nFinal check:")
            final_records = Screenshot.query.filter_by(lottery_type="Daily Lotto Results").all()
            for record in final_records:
                print(f"ID: {record.id}, URL: {record.url}, Timestamp: {record.timestamp}")
    else:
        print("No duplicates found for Daily Lotto Results")