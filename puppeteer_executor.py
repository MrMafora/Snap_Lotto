"""
Puppeteer Executor
A standalone module that executes Node.js puppeteer scripts to capture screenshots.
This avoids the issues with embedding JavaScript in Python multiline strings.
"""

import os
import subprocess
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_screenshot(url, output_path, html_path, timeout=120):
    """
    Capture a screenshot of a webpage using the external puppeteer script.
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        html_path (str): Path to save the HTML content
        timeout (int): Timeout in seconds
        
    Returns:
        bool: Success status
    """
    logger.info(f"Capturing screenshot of {url}")
    
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        
        # Run the Node.js script with arguments
        cmd = [
            'node', 'puppeteer_script.js',
            url, output_path, html_path
        ]
        
        # Run the command with a timeout
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            logger.info(f"Successfully captured screenshot: {output_path}")
            logger.info(f"Successfully saved HTML: {html_path}")
            return True
        else:
            logger.error(f"Failed to capture screenshot. Exit code: {result.returncode}")
            logger.error(f"Stdout: {result.stdout}")
            logger.error(f"Stderr: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout expired while capturing screenshot of {url}")
        return False
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return False

if __name__ == "__main__":
    # Test by capturing a single screenshot
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_dir = 'screenshots'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'html'), exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(output_dir, f"{timestamp}_test.png")
    html_path = os.path.join(output_dir, 'html', f"{timestamp}_test.html")
    
    success = capture_screenshot(test_url, screenshot_path, html_path)
    print(f"Test capture success: {success}")