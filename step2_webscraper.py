"""
Step 2: Web Scraper Alternative
Uses requests and BeautifulSoup to fetch lottery data when screenshots are blocked
"""
import os
import logging
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def scrape_lottery_data():
    """Scrape lottery data from National Lottery website using requests"""
    urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/lotto-plus-1-results', 
        'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'https://www.nationallottery.co.za/results/powerball',
        'https://www.nationallottery.co.za/results/powerball-plus',
        'https://www.nationallottery.co.za/results/daily-lotto'
    ]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    success_count = 0
    
    # Setup session with proper headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    for url in urls:
        try:
            logger.info(f"Scraping data from: {url}")
            
            # Make request with timeout
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Save HTML content as data file for AI processing
                lottery_type = url.split('/')[-1].replace('-', '_')
                timestamp = int(datetime.now().timestamp())
                filename = f"scraped_{lottery_type}_{timestamp}.html"
                output_path = os.path.join(screenshot_dir, filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    logger.info(f"Lottery data scraped successfully: {filename} ({size} bytes)")
                    success_count += 1
                else:
                    logger.error(f"Failed to save scraped data: {filename}")
                    
            else:
                logger.error(f"HTTP {response.status_code} for {url}")
                
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            continue
        
        # Polite delay between requests
        time.sleep(2)
    
    if success_count > 0:
        logger.info(f"Web scraping completed: {success_count}/{len(urls)} successful")
        return True, success_count
    else:
        logger.error("No lottery data could be scraped")
        return False, 0

def capture_lottery_screenshots():
    """Main function that tries scraping when browser automation fails"""
    logger.info("Attempting to capture current lottery data...")
    
    # Try web scraping approach
    try:
        return scrape_lottery_data()
    except Exception as e:
        logger.error(f"All capture methods failed: {e}")
        return False, 0