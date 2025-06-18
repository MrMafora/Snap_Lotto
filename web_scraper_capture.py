#!/usr/bin/env python3
"""
Web Scraper for South African National Lottery Results
Captures authentic lottery data directly from official URLs using HTTP requests
"""

import os
import time
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LotteryWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-ZA,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def capture_lottery_page(self, url, lottery_type):
        """Capture lottery page content with human-like behavior"""
        try:
            logger.info(f"Fetching {lottery_type} from {url}")
            
            # Human-like delay before request
            time.sleep(1)
            
            # Make request to lottery page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Generate filename for saving HTML content
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
            filename = f"{timestamp}_{safe_type}_page.html"
            
            # Ensure screenshots directory exists
            os.makedirs('screenshots', exist_ok=True)
            filepath = os.path.join('screenshots', filename)
            
            # Save HTML content for AI processing
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            # Extract basic lottery information
            lottery_data = self.extract_lottery_data(soup, lottery_type)
            
            file_size = os.path.getsize(filepath)
            logger.info(f"✓ Page content saved: {filename} ({file_size} bytes)")
            
            return {
                'filepath': filepath,
                'lottery_type': lottery_type,
                'url': url,
                'data': lottery_data,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error fetching {lottery_type}: {str(e)}")
            return {
                'filepath': None,
                'lottery_type': lottery_type,
                'url': url,
                'data': None,
                'status': 'failed',
                'error': str(e)
            }

    def extract_lottery_data(self, soup, lottery_type):
        """Extract lottery numbers and draw information from HTML"""
        try:
            # Look for common lottery result patterns
            numbers = []
            draw_date = None
            draw_number = None
            
            # Find number elements (common patterns on lottery websites)
            number_elements = soup.find_all(['span', 'div', 'td'], class_=lambda x: x and ('number' in x.lower() or 'ball' in x.lower()))
            
            for element in number_elements:
                text = element.get_text().strip()
                if text.isdigit() and 1 <= int(text) <= 50:
                    numbers.append(int(text))
            
            # Look for date information
            date_elements = soup.find_all(text=lambda x: x and any(month in x for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']))
            if date_elements:
                draw_date = date_elements[0].strip()
            
            return {
                'numbers': numbers[:6] if numbers else [],
                'draw_date': draw_date,
                'draw_number': draw_number,
                'lottery_type': lottery_type
            }
            
        except Exception as e:
            logger.warning(f"Could not extract structured data from {lottery_type}: {str(e)}")
            return None

    def capture_all_lottery_urls(self):
        """Capture all South African National Lottery URLs"""
        logger.info("=== STARTING WEB SCRAPING OF LOTTERY URLS ===")
        
        results = []
        
        for i, lottery_config in enumerate(Config.RESULTS_URLS):
            url = lottery_config['url']
            lottery_type = lottery_config['lottery_type']
            
            # Human-like delay between requests
            if i > 0:
                delay = 2 + i  # Increasing delay
                logger.info(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
            
            # Capture lottery page
            result = self.capture_lottery_page(url, lottery_type)
            results.append(result)
        
        # Log summary
        successful = len([r for r in results if r['status'] == 'success'])
        total = len(results)
        logger.info(f"=== WEB SCRAPING COMPLETE: {successful}/{total} pages captured ===")
        
        return results

def run_web_scraping():
    """Run the web scraping process"""
    try:
        scraper = LotteryWebScraper()
        return scraper.capture_all_lottery_urls()
    except Exception as e:
        logger.error(f"Error running web scraping: {str(e)}")
        return []

if __name__ == "__main__":
    # Run web scraping and display results
    results = run_web_scraping()
    
    print("\n=== WEB SCRAPING RESULTS ===")
    for result in results:
        status = "✓" if result['status'] == 'success' else "✗"
        print(f"{status} {result['lottery_type']}: {result['status']}")
        if result['filepath']:
            print(f"  File: {os.path.basename(result['filepath'])}")
        if result.get('data') and result['data'].get('numbers'):
            print(f"  Numbers found: {result['data']['numbers']}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    print(f"\nTotal: {successful}/{total} lottery pages captured successfully")
    
    # Show URLs being used
    print(f"\n=== OFFICIAL URLS ACCESSED ===")
    for config in Config.RESULTS_URLS:
        print(f"• {config['lottery_type']}: {config['url']}")