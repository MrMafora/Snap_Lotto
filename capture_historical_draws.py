#!/usr/bin/env python3
"""
Capture screenshots of historical lottery draws
Uses za.national-lottery.com historical results pages
"""

import asyncio
import os
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def capture_historical_draws():
    """
    Capture screenshots of the last 10 draws for each lottery type
    from the historical results pages
    """
    
    # Historical results URLs for each lottery type
    lottery_urls = {
        'lotto': 'https://za.national-lottery.com/lotto/results/history',
        'lotto_plus_1': 'https://za.national-lottery.com/lotto-plus-1/results/history',
        'lotto_plus_2': 'https://za.national-lottery.com/lotto-plus-2/results/history',
        'powerball': 'https://za.national-lottery.com/powerball/results/history',
        'powerball_plus': 'https://za.national-lottery.com/powerball-plus/results/history',
        'daily_lotto': 'https://za.national-lottery.com/daily-lotto/results/history'
    }
    
    # Create directory for screenshots
    os.makedirs('screenshots/historical', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    total_captures = 0
    
    logger.info("Starting historical draw screenshot capture")
    logger.info("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        try:
            for lottery_type, url in lottery_urls.items():
                logger.info(f"\n📸 Processing {lottery_type.upper().replace('_', ' ')}")
                logger.info(f"URL: {url}")
                
                page = await browser.new_page()
                
                try:
                    # Navigate to historical results page
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Check if page loaded
                    title = await page.title()
                    logger.info(f"Page loaded: {title}")
                    
                    # Look for draw result links or table rows
                    # The page typically shows recent draws in a list/table
                    await page.wait_for_timeout(2000)
                    
                    # Try to find draw result links (typically the first 10 visible)
                    draw_links = await page.query_selector_all('a[href*="/results/"]')
                    
                    if draw_links:
                        logger.info(f"Found {len(draw_links)} draw links")
                        
                        # Capture first 10 draws
                        draws_to_capture = min(10, len(draw_links))
                        
                        for i in range(draws_to_capture):
                            try:
                                # Get the link
                                link = draw_links[i]
                                href = await link.get_attribute('href')
                                
                                if href and '/results/' in href:
                                    # Create new page for each draw
                                    draw_page = await browser.new_page()
                                    
                                    # Navigate to the specific draw result
                                    full_url = href if href.startswith('http') else f"https://za.national-lottery.com{href}"
                                    logger.info(f"  Draw {i+1}: {full_url}")
                                    
                                    await draw_page.goto(full_url, wait_until='domcontentloaded', timeout=20000)
                                    await draw_page.wait_for_timeout(2000)
                                    
                                    # Take screenshot
                                    screenshot_path = f"screenshots/historical/{timestamp}_{lottery_type}_draw_{i+1:02d}.png"
                                    await draw_page.screenshot(path=screenshot_path, full_page=True)
                                    
                                    file_size = os.path.getsize(screenshot_path)
                                    logger.info(f"  ✅ Captured: {screenshot_path} ({file_size:,} bytes)")
                                    total_captures += 1
                                    
                                    await draw_page.close()
                                    await asyncio.sleep(1)  # Be nice to the server
                                    
                            except Exception as e:
                                logger.error(f"  ❌ Error capturing draw {i+1}: {str(e)}")
                                continue
                    else:
                        # If no links found, just capture the history page showing recent draws
                        logger.info("No individual draw links found, capturing history page...")
                        screenshot_path = f"screenshots/historical/{timestamp}_{lottery_type}_history_page.png"
                        await page.screenshot(path=screenshot_path, full_page=True)
                        
                        file_size = os.path.getsize(screenshot_path)
                        logger.info(f"✅ Captured history page: {screenshot_path} ({file_size:,} bytes)")
                        total_captures += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {lottery_type}: {str(e)}")
                finally:
                    await page.close()
                    
        finally:
            await browser.close()
    
    logger.info("=" * 60)
    logger.info(f"✅ CAPTURE COMPLETE: {total_captures} screenshots saved")
    logger.info(f"Location: screenshots/historical/")
    
    return total_captures

if __name__ == '__main__':
    result = asyncio.run(capture_historical_draws())
    print(f"\n{'='*60}")
    print(f"Total screenshots captured: {result}")
    print(f"{'='*60}")
