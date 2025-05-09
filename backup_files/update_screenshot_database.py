"""
Update Screenshot Database

This script only updates the database with paths to screenshots that already exist.
It doesn't attempt to download new screenshots.
"""

import os
import sys
from datetime import datetime

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'

# South African Lottery URLs and types
LOTTERY_URLS = [
    # History URLs
    {'url': 'https://www.nationallottery.co.za/lotto-history', 'type': 'lotto_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'type': 'lotto_plus_1_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'type': 'lotto_plus_2_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-history', 'type': 'powerball_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'type': 'powerball_plus_history'},
    {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'type': 'daily_lotto_history'},
    
    # Results URLs
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'type': 'lotto_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'type': 'lotto_plus_1_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'type': 'lotto_plus_2_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'type': 'powerball_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'type': 'powerball_plus_results'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'type': 'daily_lotto_results'},
]

def update_database():
    """
    Update database with screenshot paths for existing screenshot files
    """
    try:
        from models import db, Screenshot
        from main import app
        
        print("Updating database with screenshot paths...")
        
        # Map of lottery types to database names
        lottery_type_map = {
            'lotto_history': 'Lotto',
            'lotto_plus_1_history': 'Lotto Plus 1',
            'lotto_plus_2_history': 'Lotto Plus 2',
            'powerball_history': 'Powerball',
            'powerball_plus_history': 'Powerball Plus',
            'daily_lotto_history': 'Daily Lotto',
            'lotto_results': 'Lotto Results',
            'lotto_plus_1_results': 'Lotto Plus 1 Results',
            'lotto_plus_2_results': 'Lotto Plus 2 Results',
            'powerball_results': 'Powerball Results',
            'powerball_plus_results': 'Powerball Plus Results',
            'daily_lotto_results': 'Daily Lotto Results',
        }
        
        results = {}
        
        with app.app_context():
            # First, get all existing screenshots in the database
            existing_screenshots = Screenshot.query.all()
            for screenshot in existing_screenshots:
                print(f"Found existing record: {screenshot.lottery_type}, URL: {screenshot.url}")
            
            # Update each lottery type
            for lottery_type, db_name in lottery_type_map.items():
                # Find html files for this lottery type
                html_files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(f"{lottery_type}.html")]
                
                if html_files:
                    # Sort by name (which contains timestamp) to get the newest
                    newest_file = sorted(html_files, reverse=True)[0]
                    html_path = os.path.join(SCREENSHOTS_DIR, newest_file)
                    
                    # Look for exact match first
                    screenshot = Screenshot.query.filter_by(lottery_type=db_name).first()
                    
                    if not screenshot:
                        # Try partial match
                        for s in existing_screenshots:
                            if db_name.lower() in s.lottery_type.lower():
                                screenshot = s
                                break
                    
                    if screenshot:
                        # Update existing record
                        old_path = screenshot.path
                        screenshot.path = html_path
                        screenshot.timestamp = datetime.now()
                        print(f"Updated {db_name} record: {old_path} -> {html_path}")
                        results[lottery_type] = {'status': 'updated', 'path': html_path}
                    else:
                        # Create new record
                        url = next((lot['url'] for lot in LOTTERY_URLS if lot['type'] == lottery_type), '')
                        screenshot = Screenshot(
                            lottery_type=db_name,
                            url=url,
                            path=html_path,
                            timestamp=datetime.now()
                        )
                        db.session.add(screenshot)
                        print(f"Created new record for {db_name} with {html_path}")
                        results[lottery_type] = {'status': 'created', 'path': html_path}
                else:
                    print(f"No HTML files found for {lottery_type}")
                    results[lottery_type] = {'status': 'error', 'message': 'No HTML files found'}
            
            # Commit all changes
            db.session.commit()
            print("Database updated successfully.")
            
            # Print summary
            updated_count = sum(1 for r in results.values() if r['status'] == 'updated')
            created_count = sum(1 for r in results.values() if r['status'] == 'created')
            print(f"\nSummary: {updated_count} records updated, {created_count} records created")
            
            return True, results
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        return False, {"error": str(e)}

if __name__ == "__main__":
    if not os.path.exists(SCREENSHOTS_DIR):
        print(f"Error: Screenshots directory {SCREENSHOTS_DIR} does not exist!")
        sys.exit(1)
        
    screenshot_files = os.listdir(SCREENSHOTS_DIR)
    html_files = [f for f in screenshot_files if f.endswith('.html')]
    
    if not html_files:
        print("Error: No HTML files found in screenshots directory!")
        sys.exit(1)
        
    print(f"Found {len(html_files)} HTML files in screenshots directory.")
    update_database()