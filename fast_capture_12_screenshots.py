"""
Fast Capture of 12 Screenshots from lottery websites

This optimized script uses requests with specific headers to capture
the 12 requested lottery screenshots, with shorter timeouts and wait periods.
"""

import os
import sys
import time
import requests
from datetime import datetime
import concurrent.futures

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Specific URLs requested for screenshots
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

def capture_screenshot(lottery_info):
    """Capture a screenshot from the URL"""
    url = lottery_info['url']
    lottery_type = lottery_info['type']
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{lottery_type}.html"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    
    # Use a custom session to manage connection
    session = requests.Session()
    
    # Disable content encoding to avoid gzip issues
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'identity',  # Force no encoding
        'Connection': 'close',  # Close connection after request
        'Cache-Control': 'no-cache'  # Disable caching
    })
    
    # Use GET request with streaming to avoid processing the whole response at once
    try:
        print(f"Capturing {lottery_type} from {url}")
        
        # Use streaming to get response in chunks with a shorter timeout
        response = session.get(url, stream=True, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                # Write response in chunks to avoid memory issues
                for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                    f.write(chunk)
            
            print(f"✅ Successfully saved {lottery_type} to {filepath}")
            return True, filepath, None, lottery_type
        else:
            error_message = f"Error: Status code {response.status_code}"
            print(f"❌ {lottery_type}: {error_message}")
            return False, None, error_message, lottery_type
    except requests.exceptions.RequestException as e:
        error_message = f"Request error: {str(e)}"
        print(f"❌ {lottery_type}: {error_message}")
        return False, None, error_message, lottery_type
    except Exception as e:
        error_message = f"General error: {str(e)}"
        print(f"❌ {lottery_type}: {error_message}")
        return False, None, error_message, lottery_type
    finally:
        # Close the session to ensure connections are freed
        session.close()

def capture_all_screenshots_parallel():
    """Capture all screenshots in parallel from the specified URLs"""
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all URL capture jobs
        future_to_lottery = {
            executor.submit(capture_screenshot, lottery): lottery 
            for lottery in LOTTERY_URLS
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_lottery):
            success, filepath, error_message, lottery_type = future.result()
            
            # Record the result
            if success:
                results[lottery_type] = {
                    'status': 'success',
                    'path': filepath
                }
            else:
                results[lottery_type] = {
                    'status': 'failed',
                    'message': error_message
                }
    
    # Print out results
    success_count = sum(1 for result in results.values() if result['status'] == 'success')
    print(f"\nCapture complete: {success_count} out of {len(LOTTERY_URLS)} screenshots captured successfully.")
    
    # Print details of each capture
    for lottery_type, result in results.items():
        status = "✅" if result['status'] == 'success' else "❌"
        if result['status'] == 'success':
            message = result['path']
        else:
            message = result.get('message', 'Unknown error')
        print(f"{status} {lottery_type}: {message}")
    
    return results

def update_database():
    """Update database with screenshot paths"""
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Map of lottery types to common database names
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
            
            for lottery_type, db_name in lottery_type_map.items():
                # Find the newest file for this lottery type
                html_files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(f"{lottery_type}.html")]
                
                if html_files:
                    # Sort by name (which contains timestamp) to get the newest
                    newest_file = sorted(html_files, reverse=True)[0]
                    html_path = os.path.join(SCREENSHOTS_DIR, newest_file)
                    
                    # Look for exact or partial match in database
                    screenshot = Screenshot.query.filter_by(lottery_type=db_name).first()
                    if not screenshot:
                        for s in Screenshot.query.all():
                            if db_name.lower() in s.lottery_type.lower():
                                screenshot = s
                                break
                    
                    if screenshot:
                        # Update existing record
                        screenshot.path = html_path
                        screenshot.timestamp = datetime.now()
                        print(f"Updated {db_name} record with {html_path}")
                    else:
                        # Create new record
                        screenshot = Screenshot(
                            lottery_type=db_name,
                            url=next((lot['url'] for lot in LOTTERY_URLS if lot['type'] == lottery_type), ''),
                            path=html_path,
                            timestamp=datetime.now()
                        )
                        db.session.add(screenshot)
                        print(f"Created new record for {db_name} with {html_path}")
            
            # Commit all changes
            db.session.commit()
            print("Database updated successfully.")
            return True
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting fast capture of 12 lottery screenshots...")
    results = capture_all_screenshots_parallel()
    
    # Update database if requested
    if any(arg in sys.argv for arg in ['--update-db', '-u']):
        print("\nUpdating database...")
        update_database()