#!/usr/bin/env python3
"""
Quick capture script to get current lottery results efficiently
"""

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_capture_all():
    """Quickly capture all lottery types"""
    logger.info("=== QUICK CAPTURE STARTED ===")
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        captured = 0
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for url_config in Config.RESULTS_URLS:
            try:
                url = url_config['url']
                lottery_type = url_config['lottery_type']
                
                logger.info(f"Capturing {lottery_type}")
                page.goto(url, wait_until='domcontentloaded', timeout=8000)
                page.wait_for_timeout(1500)
                
                safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
                filename = f"{timestamp}_{safe_type}_{captured+1750452587818}.png"
                filepath = os.path.join('screenshots', filename)
                
                os.makedirs('screenshots', exist_ok=True)
                page.screenshot(path=filepath, full_page=True)
                logger.info(f"Saved: {filename}")
                captured += 1
                
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to capture {lottery_type}: {str(e)}")
                continue
        
        browser.close()
        playwright.stop()
        
        logger.info(f"=== QUICK CAPTURE COMPLETED: {captured} screenshots ===")
        return captured > 0
        
    except Exception as e:
        logger.error(f"Quick capture failed: {str(e)}")
        return False

if __name__ == "__main__":
    quick_capture_all()