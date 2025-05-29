"""
Fixed Screenshot Manager - Prevents System Hangs
Simple replacement for the problematic screenshot system
"""

import os
import logging

logger = logging.getLogger(__name__)

def capture_screenshot_safe(url, output_path):
    """
    Safe screenshot capture that won't hang the system
    Returns False immediately to prevent browser initialization issues
    """
    logger.info(f"Screenshot requested: {url} -> {output_path}")
    logger.warning("Browser-based screenshot capture disabled due to environment limitations")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    return False

def capture_multiple_screenshots_safe(url_list):
    """
    Safely process multiple screenshot requests without hanging
    """
    logger.info(f"Processing {len(url_list)} screenshot requests")
    results = []
    
    for url_info in url_list:
        url = url_info.get('url', '')
        output_path = f"screenshots/{url.split('/')[-1]}.png"
        result = capture_screenshot_safe(url, output_path)
        results.append(result)
    
    successful_count = sum(1 for r in results if r)
    logger.info(f"Screenshot batch completed: {successful_count}/{len(results)} successful")
    
    return successful_count > 0, successful_count