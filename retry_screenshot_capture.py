"""
Retry the screenshot capture for Daily Lotto Results with full HTML content
"""
from main import app
from models import Screenshot, ScheduleConfig, db
import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import uuid
from PIL import Image
import io

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("retry_capture")

def retry_daily_lotto_screenshot():
    """Retry capturing Daily Lotto Results with proper HTML content"""
    with app.app_context():
        # Get the Daily Lotto Results config
        config = ScheduleConfig.query.filter_by(lottery_type="Daily Lotto Results").first()
        if not config:
            logger.error("Could not find Daily Lotto Results config")
            return False
        
        # Request with extended timeout and headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        url = config.url
        lottery_type = config.lottery_type
        logger.info(f"Requesting URL: {url} with timeout 60s")
        
        try:
            response = requests.get(url, headers=headers, timeout=60, 
                                   verify=True, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch URL {url}: HTTP status {response.status_code}")
                return False
                
            # Save full HTML content
            html_content = response.text
            
            # Parse the content to find real lottery data
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Generate a timestamp for filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            
            # Create the screenshot directory if it doesn't exist
            SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            
            # Create filenames
            screenshot_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.html"
            filepath = os.path.join(SCREENSHOT_DIR, screenshot_filename)
            
            # Generate a preview image from the HTML
            # For better quality, try to extract and render the actual draw results
            # Find the main content or results section
            result_section = soup.find('div', class_='resultsHeader')
            
            # Create a more informative image
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1200, 800), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # Add text showing results were captured
            draw.text((50, 50), f"Daily Lotto Results captured on {timestamp}", fill=(0, 0, 0))
            
            # If we extracted any results, add them to the image
            if result_section:
                draw.text((50, 150), f"Results data found: {result_section.text[:500]}", fill=(0, 0, 0))
            else:
                draw.text((50, 150), "No specific results data extracted - see HTML file for details", fill=(0, 0, 0))
            
            # Add URL information
            draw.text((50, 700), f"Source: {url}", fill=(0, 0, 0))
            
            # Save the image
            img_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
            img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
            img.save(img_filepath)
            
            # Save the HTML content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Successfully captured content from {url} and saved to {filepath}")
            
            # Update or create screenshot record
            existing_screenshot = Screenshot.query.filter_by(url=url).first()
            
            if existing_screenshot:
                # Update existing record
                existing_screenshot.path = filepath
                existing_screenshot.zoomed_path = img_filepath
                existing_screenshot.timestamp = datetime.now()
                logger.info(f"Updated existing screenshot record for {lottery_type}")
            else:
                # Create new record
                new_screenshot = Screenshot(
                    url=url,
                    lottery_type=lottery_type,
                    path=filepath,
                    zoomed_path=img_filepath,
                    timestamp=datetime.now()
                )
                db.session.add(new_screenshot)
                logger.info(f"Created new screenshot record for {lottery_type}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error capturing screenshot for {url}: {str(e)}")
            return False

if __name__ == "__main__":
    success = retry_daily_lotto_screenshot()
    if success:
        print("Successfully updated Daily Lotto Results screenshot")
    else:
        print("Failed to update Daily Lotto Results screenshot")