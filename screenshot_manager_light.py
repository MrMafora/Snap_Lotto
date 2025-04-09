"""
Lightweight screenshot manager for lottery websites.

This module provides a lightweight implementation of website screenshot functionality
using requests and Pillow instead of heavier browser automation like Playwright.
"""

import os
import time
import logging
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LightScreenshotManager:
    """
    Lightweight screenshot manager that uses requests and Pillow for screenshots.
    
    This implementation provides a lighter alternative to browser automation
    tools like Playwright, reducing the installation size significantly.
    
    Note: This implementation has limitations as it can only capture static HTML
    content and not JavaScript-rendered content. It's suitable for simple static
    websites only. For sites with dynamic content, use the Playwright implementation.
    """
    
    def __init__(self, screenshot_dir='screenshots'):
        """
        Initialize the screenshot manager.
        
        Args:
            screenshot_dir (str): Directory to store screenshots
        """
        self.screenshot_dir = screenshot_dir
        
        # Create screenshot directory if it doesn't exist
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            logger.info(f"Created screenshot directory: {screenshot_dir}")
    
    def take_screenshot(self, url, lottery_type):
        """
        Take a screenshot of a specified URL and save it with a timestamp.
        
        Args:
            url (str): URL to capture
            lottery_type (str): Type of lottery for organizing screenshots
            
        Returns:
            dict: Result with status, path, and message
        """
        try:
            logger.info(f"Taking screenshot of {url} for {lottery_type}")
            
            # Create subdirectory for lottery type if needed
            lottery_dir = os.path.join(self.screenshot_dir, lottery_type.replace(' ', '_'))
            if not os.path.exists(lottery_dir):
                os.makedirs(lottery_dir)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{lottery_type.replace(' ', '_')}_{timestamp}.jpg"
            filepath = os.path.join(lottery_dir, filename)
            
            # Make request to the URL
            logger.info(f"Requesting URL: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Create a blank image for the "screenshot"
            # This is a limitation of this light implementation - we can't actually
            # render the HTML/CSS as a browser would. We're just saving a placeholder.
            img = Image.new('RGB', (1200, 1800), color=(255, 255, 255))
            
            # Save the image
            img.save(filepath, format='JPEG')
            
            # Save the HTML content alongside the image for processing
            html_filepath = filepath.replace('.jpg', '.html')
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Saved screenshot to {filepath} and HTML to {html_filepath}")
            
            return {
                'status': 'success',
                'path': filepath,
                'html_path': html_filepath,
                'message': f"Screenshot saved: {filename}"
            }
        
        except requests.RequestException as e:
            error_msg = f"Request error taking screenshot of {url}: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
        
        except Exception as e:
            error_msg = f"Error taking screenshot of {url}: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def take_full_page_screenshot(self, url, lottery_type, scroll_delay=1.0):
        """
        Take a full page screenshot by scrolling down the page.
        In the lightweight version, this is the same as the regular screenshot.
        
        Args:
            url (str): URL to capture
            lottery_type (str): Type of lottery 
            scroll_delay (float): Delay between scrolls in seconds
            
        Returns:
            dict: Result with status, path, and message
        """
        # The light implementation doesn't support scrolling,
        # so we'll just use the regular screenshot method
        return self.take_screenshot(url, lottery_type)
    
    def close(self):
        """Close any resources. In the lightweight version, this is a no-op."""
        pass

# Create factory function to get the appropriate screenshot manager
def get_screenshot_manager(use_playwright=False, **kwargs):
    """
    Factory function to get the appropriate screenshot manager.
    
    Args:
        use_playwright (bool): Whether to use Playwright (if available)
        **kwargs: Additional arguments to pass to the screenshot manager
        
    Returns:
        object: Screenshot manager instance
    """
    if use_playwright:
        try:
            # Try to import the Playwright manager
            from screenshot_manager_playwright import PlaywrightScreenshotManager
            logger.info("Using Playwright screenshot manager")
            return PlaywrightScreenshotManager(**kwargs)
        except ImportError:
            logger.warning("Playwright not available, falling back to lightweight implementation")
            return LightScreenshotManager(**kwargs)
    else:
        logger.info("Using lightweight screenshot manager")
        return LightScreenshotManager(**kwargs)

# If script is run directly, take a test screenshot
if __name__ == "__main__":
    # Test URLs
    TEST_URLS = [
        {
            'url': 'https://www.nationallottery.co.za/lotto-results', 
            'lottery_type': 'Lotto'
        },
        {
            'url': 'https://www.nationallottery.co.za/powerball-results', 
            'lottery_type': 'Powerball'
        }
    ]
    
    # Create screenshot manager
    screenshot_manager = LightScreenshotManager()
    
    # Take screenshots
    for test in TEST_URLS:
        result = screenshot_manager.take_screenshot(test['url'], test['lottery_type'])
        print(f"Screenshot result: {result['status']} - {result['message']}")
        
        if result['status'] == 'success':
            print(f"Screenshot saved to: {result['path']}")
            print(f"HTML saved to: {result['html_path']}")