"""
Test screenshot capture functionality

This script tests the screenshot capture functionality directly, 
using the selenium_screenshot_manager module.
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_screenshot_capture():
    """
    Test the screenshot capture functionality
    
    Returns:
        dict: Result of the test
    """
    try:
        # Import the screenshot manager
        from selenium_screenshot_manager import SeleniumScreenshotManager
        
        # Create a screenshot manager instance
        manager = SeleniumScreenshotManager()
        
        # Set up test parameters
        url = "https://www.nationallottery.co.za/results/lotto"
        lottery_type = "Lotto Results"
        
        # Ensure the screenshots directory exists
        os.makedirs('screenshots', exist_ok=True)
        
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{lottery_type.lower().replace(' ', '-')}.png"
        filepath = os.path.join('screenshots', filename)
        
        logger.info(f"Capturing screenshot from {url}")
        logger.info(f"Saving to {filepath}")
        
        # Capture the screenshot
        result = manager.capture_screenshot(
            url=url,
            lottery_type=lottery_type,
            save_to_db=False,
            output_path=filepath
        )
        
        # Close the manager
        manager.close()
        
        # Check the result
        if result.get('success'):
            logger.info(f"Screenshot captured successfully: {result.get('path')}")
            logger.info(f"File size: {os.path.getsize(result.get('path'))} bytes")
            
            # Verify it's a PNG file
            with open(result.get('path'), 'rb') as f:
                header = f.read(8)
                is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
                logger.info(f"Is PNG file: {is_png}")
                
            return {
                'success': True,
                'path': result.get('path'),
                'size': os.path.getsize(result.get('path')),
                'is_png': is_png
            }
        else:
            logger.error(f"Screenshot capture failed: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error')
            }
    except Exception as e:
        logger.error(f"Error in test_screenshot_capture: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def test_direct_capture():
    """
    Test screenshot capture directly using Playwright
    """
    try:
        from playwright.sync_api import sync_playwright
        import time
        
        # Ensure the screenshots directory exists
        os.makedirs('screenshots', exist_ok=True)
        
        # Set up test parameters
        url = "https://www.nationallottery.co.za/results/lotto"
        
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_direct_playwright.png"
        filepath = os.path.join('screenshots', filename)
        
        logger.info(f"Capturing screenshot directly from {url}")
        logger.info(f"Saving to {filepath}")
        
        with sync_playwright() as p:
            # Launch a browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            
            try:
                # Navigate to the URL with a timeout of 30 seconds
                page.goto(url, timeout=30000)
                
                # Wait for page to load completely
                page.wait_for_load_state("networkidle", timeout=30000)
                
                # Additional wait for any JavaScript to complete
                time.sleep(3)
                
                # Take a screenshot
                page.screenshot(path=filepath)
                
                logger.info(f"Screenshot saved to {filepath}")
                logger.info(f"File size: {os.path.getsize(filepath)} bytes")
                
                # Verify it's a PNG file
                with open(filepath, 'rb') as f:
                    header = f.read(8)
                    is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
                    logger.info(f"Is PNG file: {is_png}")
                
                return {
                    'success': True,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'is_png': is_png
                }
            except Exception as e:
                logger.error(f"Error during screenshot capture: {str(e)}")
                return {
                    'success': False,
                    'error': str(e)
                }
            finally:
                # Close the browser
                browser.close()
    except Exception as e:
        logger.error(f"Error in test_direct_capture: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def create_placeholder_image(lottery_type, timestamp=None, width=800, height=600):
    """
    Create a placeholder image for testing
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp of the screenshot
        width (int): Width of the image
        height (int): Height of the image
        
    Returns:
        str: Path to the placeholder image
    """
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Ensure the screenshots directory exists
        os.makedirs('screenshots', exist_ok=True)
        
        # Create a timestamp for the filename
        ts = timestamp or datetime.now()
        ts_str = ts.strftime("%Y%m%d_%H%M%S")
        filename = f"{ts_str}_{lottery_type.lower().replace(' ', '-')}_placeholder.png"
        filepath = os.path.join('screenshots', filename)
        
        # Create a blank white image
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw a border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=(200, 200, 200))
        
        # Draw header background
        draw.rectangle([(0, 0), (width, 50)], fill=(227, 242, 253))
        
        # Draw title
        title = f"{lottery_type} Screenshot"
        draw.text((20, 15), title, fill=(0, 0, 0))
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 60), f"Date: {timestamp_str}", fill=(100, 100, 100))
        
        # Draw placeholder message
        draw.text((20, 100), "This is a placeholder image for testing.", fill=(0, 0, 0))
        
        # Save the image
        image.save(filepath)
        
        logger.info(f"Placeholder image saved to {filepath}")
        logger.info(f"File size: {os.path.getsize(filepath)} bytes")
        
        return filepath
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def create_test_database_entry(filepath, lottery_type, url):
    """
    Create a test database entry for a screenshot
    
    Args:
        filepath (str): Path to the screenshot file
        lottery_type (str): Type of lottery
        url (str): URL of the screenshot source
        
    Returns:
        int: ID of the created screenshot entry
    """
    try:
        from models import Screenshot, db
        from datetime import datetime
        
        # Create a new screenshot entry
        screenshot = Screenshot(
            lottery_type=lottery_type,
            url=url,
            path=filepath,
            timestamp=datetime.now()
        )
        
        # Add to database
        db.session.add(screenshot)
        db.session.commit()
        
        logger.info(f"Screenshot entry created with ID {screenshot.id}")
        
        return screenshot.id
    except Exception as e:
        logger.error(f"Error creating test database entry: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def run_tests():
    """Run all screenshot capture tests"""
    # First, test the screenshot capture using the manager
    manager_result = test_screenshot_capture()
    
    # Then, test direct capture using Playwright
    direct_result = test_direct_capture()
    
    # Finally, create a placeholder image
    placeholder_path = create_placeholder_image("Test Lottery")
    
    results = {
        'manager_test': manager_result,
        'direct_test': direct_result,
        'placeholder_test': {
            'success': placeholder_path is not None,
            'path': placeholder_path
        }
    }
    
    # Create database entries if any test succeeded
    from main import app
    with app.app_context():
        if manager_result.get('success'):
            create_test_database_entry(
                manager_result.get('path'),
                "Lotto Results",
                "https://www.nationallottery.co.za/results/lotto"
            )
        
        if direct_result.get('success'):
            create_test_database_entry(
                direct_result.get('path'),
                "Lotto Direct",
                "https://www.nationallottery.co.za/results/lotto"
            )
        
        if placeholder_path:
            create_test_database_entry(
                placeholder_path,
                "Test Lottery",
                "https://www.example.com/test"
            )
    
    return results

if __name__ == "__main__":
    logger.info("Starting screenshot capture tests...")
    
    results = run_tests()
    
    # Print a summary of results
    for test_name, result in results.items():
        success = result.get('success', False)
        logger.info(f"{test_name}: {'Success' if success else 'Failure'}")
        
        if success:
            logger.info(f"  Path: {result.get('path')}")
            if 'size' in result:
                logger.info(f"  Size: {result.get('size')} bytes")
            if 'is_png' in result:
                logger.info(f"  Is PNG: {result.get('is_png')}")
        else:
            logger.info(f"  Error: {result.get('error')}")
    
    logger.info("Tests completed!")
    
    # Print a simple summary to stdout
    print("\nScreenshot Capture Tests Results:")
    print("--------------------------------")
    for test_name, result in results.items():
        success = result.get('success', False)
        print(f"{test_name}: {'✓ Success' if success else '✗ Failure'}")
        
        if not success and 'error' in result:
            print(f"  Error: {result.get('error')}")
    
    print("\nIf tests succeeded, screenshot entries have been added to the database.")
    print("You can view them in the Export Screenshots page.")