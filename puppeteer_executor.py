"""
Puppeteer Executor

A standalone module that executes Node.js puppeteer scripts to capture screenshots.
This avoids the issues with embedding JavaScript in Python multiline strings.
"""

import os
import subprocess
import logging
import tempfile
import json

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
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    # Create absolute paths
    script_path = os.path.join(os.getcwd(), 'puppeteer_script.js')
    
    # Run the Node.js script as a subprocess
    try:
        # Prepare the command
        cmd = ['node', script_path, url, output_path, html_path]
        
        # Execute the command with a timeout
        logger.info(f"Running puppeteer with command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if the process was successful
        if process.returncode == 0:
            logger.info(f"Successfully captured screenshot of {url}")
            return True
        else:
            logger.error(f"Failed to capture screenshot of {url}: {process.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while capturing screenshot of {url}")
        return False
    except Exception as e:
        logger.error(f"Error capturing screenshot of {url}: {str(e)}")
        return False