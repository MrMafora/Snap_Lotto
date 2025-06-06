#!/usr/bin/env python3
"""
Background processor for fresh screenshots with timeout protection
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime
from automated_data_extractor import LotteryDataExtractor
from main import app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def timeout_handler(signum, frame):
    raise TimeoutError("Processing timeout")

def process_screenshot_with_timeout(extractor, screenshot_path, timeout_seconds=120):
    """Process single screenshot with timeout protection"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        logging.info(f"Starting extraction: {screenshot_path}")
        result = extractor.process_single_image_safe(screenshot_path)
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError:
        logging.warning(f"Timeout processing {screenshot_path}")
        return False
    except Exception as e:
        logging.error(f"Error processing {screenshot_path}: {e}")
        return False
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    with app.app_context():
        extractor = LotteryDataExtractor()
        
        # Process today's screenshots
        screenshots = [
            'screenshots/20250606_172030_daily_lotto.png',
            'screenshots/20250606_171929_lotto.png',
            'screenshots/20250606_172007_powerball.png'
        ]
        
        processed_count = 0
        for screenshot in screenshots:
            if os.path.exists(screenshot):
                logging.info(f"Processing {screenshot}")
                result = process_screenshot_with_timeout(extractor, screenshot, 90)
                if result:
                    processed_count += 1
                    logging.info(f"Successfully processed {screenshot}")
                else:
                    logging.warning(f"Failed to process {screenshot}")
                time.sleep(5)  # Brief pause
        
        logging.info(f"Completed processing {processed_count}/{len(screenshots)} screenshots")