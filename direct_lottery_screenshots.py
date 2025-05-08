"""
Direct Lottery Screenshots

This script directly captures screenshots from lottery websites using requests
and saves them with proper timestamps. It doesn't create any placeholder or
synthetic data - it only saves what it gets from the source.
"""

import os
import sys
import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# South African Lottery URLs
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'type': 'lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'type': 'lotto_plus_1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'type': 'lotto_plus_2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'type': 'powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'type': 'powerball_plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'type': 'daily_lotto'}
]

def download_lottery_page(url, lottery_type):
    """
    Download a lottery page directly and save it as HTML
    
    Args:
        url (str): URL to download
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{lottery_type}.html"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        logger.info(f"Downloading {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Successfully saved {lottery_type} to {filepath}")
            return True, filepath
        else:
            logger.error(f"Failed to download {url}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False, None

def download_all_lottery_pages():
    """
    Download all lottery pages
    
    Returns:
        dict: Results for each lottery type
    """
    results = {}
    
    for lottery in LOTTERY_URLS:
        url = lottery['url']
        lottery_type = lottery['type']
        
        logger.info(f"Processing {lottery_type}")
        success, filepath = download_lottery_page(url, lottery_type)
        
        if success:
            results[lottery_type] = {
                'status': 'success',
                'path': filepath
            }
        else:
            results[lottery_type] = {
                'status': 'failed',
                'message': f"Failed to download {url}"
            }
            
        # Be nice to the server
        time.sleep(1)
    
    return results

def update_database_records():
    """
    Update database records with new screenshot paths
    Only call this if you want to update the app's database
    """
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            screenshots = Screenshot.query.all()
            for screenshot in screenshots:
                # Find the matching type
                for lottery in LOTTERY_URLS:
                    if lottery['type'].replace('_', ' ').title() == screenshot.lottery_type:
                        lottery_type = lottery['type']
                        # Find the latest file for this type
                        files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(f"{lottery_type}.html")]
                        if files:
                            # Sort by name (which has timestamp prefix)
                            latest_file = sorted(files)[-1]
                            filepath = os.path.join(SCREENSHOTS_DIR, latest_file)
                            
                            # Update the database
                            screenshot.path = filepath
                            screenshot.timestamp = datetime.now()
                            db.session.commit()
                            logger.info(f"Updated database record for {screenshot.lottery_type}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting direct lottery screenshot download")
    results = download_all_lottery_pages()
    
    success_count = sum(1 for result in results.values() if result['status'] == 'success')
    total_count = len(results)
    
    print(f"\nCompleted: {success_count}/{total_count} successful downloads")
    
    # Summarize results
    for lottery_type, result in results.items():
        status = "✅" if result['status'] == 'success' else "❌"
        message = result.get('path', result.get('message', 'Unknown'))
        print(f"{status} {lottery_type}: {message}")
    
    # Don't update database by default when run directly
    print("\nTo update the database, call the update_database_records() function")