"""
Step 2: Live Data Capture
Fetches current lottery results from National Lottery website
"""
import os
import json
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def capture_lottery_screenshots():
    """Fetch current lottery data from South African National Lottery website"""
    urls = [
        ('https://www.nationallottery.co.za/results/lotto', 'Lotto'),
        ('https://www.nationallottery.co.za/results/lotto-plus-1-results', 'Lotto Plus 1'),
        ('https://www.nationallottery.co.za/results/lotto-plus-2-results', 'Lotto Plus 2'),
        ('https://www.nationallottery.co.za/results/powerball', 'Powerball'),
        ('https://www.nationallottery.co.za/results/powerball-plus', 'Powerball Plus'),
        ('https://www.nationallottery.co.za/results/daily-lotto', 'Daily Lotto')
    ]
    
    data_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(data_dir, exist_ok=True)
    
    success_count = 0
    
    # Enhanced headers to handle compressed responses
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Create session for better handling
    session = requests.Session()
    session.headers.update(headers)
    
    for url, lottery_type in urls:
        try:
            logger.info(f"Fetching current data from: {url}")
            
            # Fetch page content with session
            response = session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Get raw content and decode properly
            content = response.content
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract key lottery information
            lottery_data = {
                'lottery_type': lottery_type,
                'url': url,
                'fetch_time': datetime.now().isoformat(),
                'page_title': soup.title.string if soup.title else '',
                'status_code': response.status_code,
                'content_length': len(content),
                'html_snippet': str(soup)[:3000]  # Store snippet for AI processing
            }
            
            # Save as JSON file for AI processing
            timestamp = int(datetime.now().timestamp())
            filename = f"live_{lottery_type.lower().replace(' ', '_')}_{timestamp}.json"
            output_path = os.path.join(data_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(lottery_data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 200:
                logger.info(f"Live lottery data captured: {filename}")
                success_count += 1
            else:
                logger.warning(f"Data file too small: {filename}")
                
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            
    session.close()
    
    if success_count > 0:
        logger.info(f"Live data capture completed: {success_count}/{len(urls)} successful")
        return True, success_count
    else:
        logger.error("Could not capture current lottery data - the website may be blocking requests")
        logger.info("Note: This happens when the lottery website has security measures preventing automated access")
        return False, 0