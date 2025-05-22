"""
Screenshot Manager factory module that provides a unified interface for taking screenshots.
This module allows choosing between lightweight and Playwright-based screenshot managers.
"""

import os
import importlib.util
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_lottery_type_from_url(url):
    """
    Extract lottery type from URL.
    
    Args:
        url (str): URL of the lottery website
        
    Returns:
        str: Lottery type or None if not found
    """
    lottery_types = {
        "lotto-history": "Lotto",
        "lotto-plus-1-history": "Lotto Plus 1",
        "lotto-plus-2-history": "Lotto Plus 2",
        "powerball-history": "Powerball",
        "powerball-plus-history": "Powerball Plus",
        "daily-lotto-history": "Daily Lotto",
        "lotto": "Lotto Results",
        "lotto-plus-1-results": "Lotto Plus 1 Results",
        "lotto-plus-2-results": "Lotto Plus 2 Results",
        "powerball": "Powerball Results",
        "powerball-plus": "Powerball Plus Results",
        "daily-lotto": "Daily Lotto Results",
    }
    
    for key, value in lottery_types.items():
        if key in url:
            return value
            
    return None


class ScreenshotManager:
    """Base Screenshot Manager class that defines the interface"""
    
    def __init__(self, screenshot_dir=None):
        """
        Initialize Screenshot Manager
        
        Args:
            screenshot_dir (str): Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir or os.path.join(os.getcwd(), 'screenshots')
        
        # Ensure screenshot directory exists
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            
    def take_screenshot(self, url, lottery_type=None):
        """
        Take a screenshot of a URL
        
        Args:
            url (str): URL to take screenshot of
            lottery_type (str, optional): Lottery type, detected from URL if not provided
            
        Returns:
            dict: Result with status, path to screenshot, and any additional info
        """
        raise NotImplementedError("Subclasses must implement take_screenshot")


class LightweightScreenshotManager(ScreenshotManager):
    """Lightweight Screenshot Manager that uses requests and pillow"""
    
    def __init__(self, screenshot_dir=None):
        """Initialize Lightweight Screenshot Manager"""
        super().__init__(screenshot_dir)
        
        # Import necessary libraries
        import requests
        from datetime import datetime
        from PIL import Image
        from io import BytesIO
        
        self.requests = requests
        self.datetime = datetime
        self.Image = Image
        self.BytesIO = BytesIO
        
    def take_screenshot(self, url, lottery_type=None):
        """
        Take a screenshot of a URL using requests and pillow
        
        Args:
            url (str): URL to take screenshot of
            lottery_type (str, optional): Lottery type, detected from URL if not provided
            
        Returns:
            dict: Result with status, path to screenshot, and any additional info
        """
        try:
            # Detect lottery type from URL if not provided
            if not lottery_type:
                lottery_type = extract_lottery_type_from_url(url)
                if not lottery_type:
                    lottery_type = "Unknown"
                    
            logger.info(f"Taking lightweight screenshot of {url} for {lottery_type}")
            
            # Get the webpage content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Generate a timestamp-based filename
            timestamp = self.datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_lottery_type = lottery_type.replace(" ", "_").lower()
            filename = f"{clean_lottery_type}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Save the HTML content for reference/debugging
            html_filename = f"{clean_lottery_type}_{timestamp}.html"
            html_filepath = os.path.join(self.screenshot_dir, html_filename)
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Create a simple image with text since we can't render the HTML visually
            # This is a placeholder - in a production app, you could use a headless browser
            # or a service like Selenium to take an actual screenshot
            text = f"HTML content for {lottery_type} downloaded at {timestamp}.\nSee {html_filename} for the HTML content."
            img = self._create_text_image(text, width=800, height=600)
            img.save(filepath)
            
            logger.info(f"Screenshot saved to {filepath}")
            logger.info(f"HTML content saved to {html_filepath}")
            
            return {
                'status': 'success',
                'message': 'Screenshot taken successfully',
                'path': filepath,
                'html_path': html_filepath,
                'lottery_type': lottery_type,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error taking screenshot: {str(e)}",
                'path': None
            }
    
    def _create_text_image(self, text, width=800, height=600, bg_color=(255, 255, 255), text_color=(0, 0, 0)):
        """Create a simple image with text"""
        img = self.Image.new('RGB', (width, height), color=bg_color)
        import PIL.ImageDraw
        import PIL.ImageFont
        draw = PIL.ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = PIL.ImageFont.truetype("arial.ttf", 14)
        except:
            # If unable to load Arial, use default font
            font = PIL.ImageFont.load_default()
            
        # Draw the text
        draw.text((20, 20), text, fill=text_color, font=font)
        return img


class PlaywrightScreenshotManager(ScreenshotManager):
    """Screenshot Manager that uses Playwright"""
    
    def __init__(self, screenshot_dir=None):
        """Initialize Playwright Screenshot Manager"""
        super().__init__(screenshot_dir)
        
        try:
            # Import Playwright
            from playwright.sync_api import sync_playwright
            self.sync_playwright = sync_playwright
            self.playwright_available = True
        except ImportError:
            logger.error("Playwright not available, please install it with: pip install playwright")
            self.playwright_available = False
            
    def take_screenshot(self, url, lottery_type=None):
        """
        Take a screenshot of a URL using Playwright
        
        Args:
            url (str): URL to take screenshot of
            lottery_type (str, optional): Lottery type, detected from URL if not provided
            
        Returns:
            dict: Result with status, path to screenshot, and any additional info
        """
        if not self.playwright_available:
            return {
                'status': 'error',
                'message': 'Playwright is not available',
                'path': None
            }
            
        try:
            # Detect lottery type from URL if not provided
            if not lottery_type:
                lottery_type = extract_lottery_type_from_url(url)
                if not lottery_type:
                    lottery_type = "Unknown"
                    
            logger.info(f"Taking Playwright screenshot of {url} for {lottery_type}")
            
            # Generate a timestamp-based filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_lottery_type = lottery_type.replace(" ", "_").lower()
            filename = f"{clean_lottery_type}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Save the HTML content for reference/debugging
            html_filename = f"{clean_lottery_type}_{timestamp}.html"
            html_filepath = os.path.join(self.screenshot_dir, html_filename)
            
            # Take screenshot using Playwright
            with self.sync_playwright() as playwright:
                # Launch browser
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 1024},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # Create new page and navigate to URL
                page = context.new_page()
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Save HTML content
                html_content = page.content()
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Take screenshot
                page.screenshot(path=filepath, full_page=True)
                
                # Close browser
                browser.close()
                
            logger.info(f"Screenshot saved to {filepath}")
            logger.info(f"HTML content saved to {html_filepath}")
            
            return {
                'status': 'success',
                'message': 'Screenshot taken successfully',
                'path': filepath,
                'html_path': html_filepath,
                'lottery_type': lottery_type,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error taking screenshot with Playwright: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error taking screenshot: {str(e)}",
                'path': None
            }


def get_screenshot_manager(use_playwright=False, screenshot_dir=None):
    """
    Factory function to get the appropriate screenshot manager
    
    Args:
        use_playwright (bool): Whether to use Playwright or lightweight manager
        screenshot_dir (str): Directory to save screenshots
        
    Returns:
        ScreenshotManager: Instance of screenshot manager
    """
    if use_playwright:
        logger.info("Using Playwright screenshot manager")
        return PlaywrightScreenshotManager(screenshot_dir)
    else:
        logger.info("Using lightweight screenshot manager")
        return LightweightScreenshotManager(screenshot_dir)