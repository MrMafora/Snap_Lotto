import os
import urllib.request
import urllib.error
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def fetch_lottery_data(url):
    """
    Direct function to fetch lottery data from the website
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.html"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing content from {url}")
        
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read()
            
            # Save the HTML content to file
            with open(filepath, 'wb') as f:
                f.write(html_content)
            
            logger.info(f"HTML content saved to {filepath}")
            return filepath
            
    except urllib.error.URLError as e:
        logger.error(f"Error opening URL: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error capturing content: {str(e)}")
        return None

if __name__ == "__main__":
    # Test fetching data from all lottery URLs
    urls = [
        'https://www.nationallottery.co.za/lotto-history',
        'https://www.nationallottery.co.za/lotto-plus-1-history',
        'https://www.nationallottery.co.za/lotto-plus-2-history',
        'https://www.nationallottery.co.za/powerball-history',
        'https://www.nationallottery.co.za/powerball-plus-history',
        'https://www.nationallottery.co.za/daily-lotto-history'
    ]
    
    for url in urls:
        filepath = fetch_lottery_data(url)
        if filepath:
            print(f"Successfully fetched: {url} -> {filepath}")
        else:
            print(f"Failed to fetch: {url}")