#!/usr/bin/env python
"""
Script to capture a single URL with timeout protection.
This script is designed to be called from other scripts or the scheduler.

Usage:
    python capture_single_url.py --url https://www.nationallottery.co.za/results/lotto --lottery-type "Lotto Results" [--timeout 300] [--method 0|1|2]

Methods:
    0 = undetected_chromedriver
    1 = playwright
    2 = requests (fastest but less reliable)
"""
import argparse
import logging
import sys
import time
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("capture_single_url")

def capture_url(url, lottery_type=None, timeout=300, method_index=None):
    """
    Capture a URL with the specialized National Lottery capture.
    
    Args:
        url (str): URL to capture
        lottery_type (str, optional): Type of lottery
        timeout (int): Timeout in seconds
        method_index (int, optional): Method to use (0=chrome, 1=playwright, 2=requests)
        
    Returns:
        bool: Success or failure
    """
    logger.info(f"Capturing URL: {url}")
    logger.info(f"Lottery type: {lottery_type}")
    logger.info(f"Timeout: {timeout}s")
    logger.info(f"Method index: {method_index}")
    
    # Set up timeout
    start_time = time.time()
    
    # Ensure we have a lottery type by using the normalize function from national_lottery_capture.py
    try:
        # Try to import the normalize function
        from national_lottery_capture import normalize_lottery_type
        if not lottery_type or lottery_type in ["National Lottery", "Lotto Results", "PowerBall Results", "Daily Lotto Results"]:
            normalized_lottery_type = normalize_lottery_type(url)
            logger.info(f"Normalized lottery type from URL: {normalized_lottery_type}")
            lottery_type = normalized_lottery_type
    except ImportError:
        # Fallback to simple determination if normalize_lottery_type isn't available
        logger.warning("Could not import normalize_lottery_type, using simple detection")
        if not lottery_type:
            if "lotto" in url.lower() and "plus" not in url.lower():
                lottery_type = "Lottery"
            elif "lotto-plus-1" in url.lower():
                lottery_type = "Lottery Plus 1"
            elif "lotto-plus-2" in url.lower():
                lottery_type = "Lottery Plus 2"
            elif "powerball" in url.lower() and "plus" not in url.lower():
                lottery_type = "Powerball"
            elif "powerball-plus" in url.lower():
                lottery_type = "Powerball Plus"
            elif "dailylotto" in url.lower() or "daily-lotto" in url.lower():
                lottery_type = "Daily Lottery"
            else:
                lottery_type = "National Lottery"
    
    # Import the specialized capture function
    try:
        # First try to get an application context
        try:
            # We may be running in a Flask app context
            from flask import current_app
            if not current_app:
                raise ImportError("No Flask app context")
        except (ImportError, RuntimeError):
            # If we're not in a Flask app context, try to get one
            try:
                from main import app
                with app.app_context():
                    # Import the specialized capture
                    from national_lottery_capture import capture_national_lottery_url
                    
                    # Capture with timeout
                    remaining_time = max(1, int(timeout - (time.time() - start_time)))
                    logger.info(f"Using Flask app context with {remaining_time}s remaining")
                    
                    # Execute the capture
                    success, html_path, img_path = capture_national_lottery_url(
                        url, lottery_type, save_to_db=True, method_index=method_index
                    )
                    
                    if success:
                        logger.info(f"Successfully captured {url}")
                        return True
                    else:
                        logger.error(f"Failed to capture {url}")
                        return False
            except ImportError:
                # If we can't get a Flask app context, try without it
                logger.warning("Could not import Flask app, proceeding without context")
                pass
        
        # If we get here, we're either in a Flask app context or we couldn't get one
        from national_lottery_capture import capture_national_lottery_url
        
        # Execute the capture
        success, html_path, img_path = capture_national_lottery_url(
            url, lottery_type, save_to_db=True, method_index=method_index
        )
        
        if success:
            logger.info(f"Successfully captured {url}")
            return True
        else:
            logger.error(f"Failed to capture {url}")
            return False
    except Exception as e:
        logger.error(f"Error importing or running capture function: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Capture a single URL with timeout protection.")
    parser.add_argument("--url", required=True, help="URL to capture")
    parser.add_argument("--lottery-type", help="Type of lottery (e.g., 'Lotto Results')")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")
    parser.add_argument("--method", type=int, choices=[0, 1, 2], help="Method to use (0=chrome, 1=playwright, 2=requests)")
    args = parser.parse_args()
    
    # Execute the capture with timeout
    success = capture_url(args.url, args.lottery_type, args.timeout, args.method)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()