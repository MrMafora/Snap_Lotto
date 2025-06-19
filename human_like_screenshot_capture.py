#!/usr/bin/env python3
"""
Human-like Screenshot Capture for SA National Lottery
Uses Playwright with human-like behavior to avoid anti-bot detection
"""

import os
import sys
import logging
import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumanLikeScreenshotCapture:
    def __init__(self):
        self.screenshot_dir = Config.SCREENSHOT_DIR
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Human-like timing patterns
        self.human_delays = {
            'page_load': (3, 7),  # 3-7 seconds for page load
            'scroll': (1, 3),     # 1-3 seconds between scrolls
            'click': (0.5, 2),    # 0.5-2 seconds before click
            'typing': (0.1, 0.3), # 0.1-0.3 seconds between keystrokes
        }
        
        # South African user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/111.0 Firefox/111.0'
        ]

    async def human_delay(self, delay_type='page_load'):
        """Add human-like delay"""
        min_delay, max_delay = self.human_delays.get(delay_type, (1, 3))
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def simulate_human_mouse_movement(self, page):
        """Simulate human-like mouse movements"""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass  # Ignore mouse movement errors

    async def simulate_human_scrolling(self, page):
        """Simulate human-like scrolling behavior"""
        try:
            # Scroll down in human-like chunks
            for _ in range(random.randint(3, 7)):
                scroll_amount = random.randint(200, 500)
                await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                await self.human_delay('scroll')
            
            # Scroll back up a bit (humans often do this)
            await page.evaluate('window.scrollBy(0, -200)')
            await self.human_delay('scroll')
            
        except Exception:
            pass  # Ignore scrolling errors

    async def capture_lottery_screenshot(self, url, lottery_type, retries=3):
        """
        Capture screenshot using human-like behavior
        
        Args:
            url: Lottery results URL
            lottery_type: Type of lottery (e.g., 'Lotto', 'Powerball')
            retries: Number of retry attempts
            
        Returns:
            Path to saved screenshot or None if failed
        """
        for attempt in range(retries):
            try:
                async with async_playwright() as p:
                    # Use random user agent
                    user_agent = random.choice(self.user_agents)
                    
                    # Launch browser with stealth settings
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-extensions',
                            '--no-first-run',
                            '--disable-default-apps',
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                            '--disable-features=TranslateUI',
                            '--disable-ipc-flooding-protection',
                            '--enable-features=NetworkService,NetworkServiceLogging',
                            '--disable-web-security',
                            '--allow-running-insecure-content'
                        ]
                    )
                    
                    try:
                        # Create context with South African location
                        context = await browser.new_context(
                            user_agent=user_agent,
                            viewport={'width': 1366, 'height': 768},
                            locale='en-ZA',
                            timezone_id='Africa/Johannesburg',
                            geolocation={'latitude': -26.2041, 'longitude': 28.0473},  # Johannesburg
                            permissions=['geolocation']
                        )
                        
                        # Add extra headers to look more human
                        await context.set_extra_http_headers({
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-ZA,en;q=0.9,af;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0'
                        })
                        
                        page = await context.new_page()
                        
                        # Navigate to page with human-like behavior
                        logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                        
                        # Navigate with timeout
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        
                        # Wait for initial load
                        await self.human_delay('page_load')
                        
                        # Simulate human behavior
                        await self.simulate_human_mouse_movement(page)
                        
                        # Wait for lottery results to load
                        try:
                            await page.wait_for_selector('.results, .winning-numbers, .draw-results', timeout=10000)
                        except:
                            # If specific selectors don't exist, wait for general content
                            await page.wait_for_load_state('networkidle', timeout=15000)
                        
                        # Scroll to see all content
                        await self.simulate_human_scrolling(page)
                        
                        # Generate filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
                        filename = f"{timestamp}_{safe_lottery_type}.png"
                        filepath = os.path.join(self.screenshot_dir, filename)
                        
                        # Take screenshot
                        await page.screenshot(
                            path=filepath,
                            full_page=True,
                            type='png'
                        )
                        
                        # Check if screenshot was actually created and has content
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:  # At least 1KB
                            logger.info(f"Successfully captured {lottery_type} screenshot: {filepath} ({os.path.getsize(filepath)} bytes)")
                            return filepath
                        else:
                            logger.warning(f"Screenshot file too small or empty: {filepath}")
                            
                    finally:
                        await browser.close()
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {lottery_type}: {str(e)}")
                if attempt < retries - 1:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(random.uniform(5, 15) * (attempt + 1))
                    
        logger.error(f"All attempts failed for {lottery_type}")
        return None

    async def capture_all_lottery_screenshots(self):
        """Capture screenshots from all lottery result pages"""
        results = []
        
        logger.info("=== STARTING HUMAN-LIKE LOTTERY SCREENSHOT CAPTURE ===")
        
        # Randomize order to look more human
        lottery_urls = Config.RESULTS_URLS.copy()
        random.shuffle(lottery_urls)
        
        for i, url_config in enumerate(lottery_urls):
            url = url_config['url']
            lottery_type = url_config['lottery_type']
            
            # Add random delay between captures
            if i > 0:
                delay = random.uniform(10, 30)  # 10-30 seconds between captures
                logger.info(f"Waiting {delay:.1f} seconds before next capture...")
                await asyncio.sleep(delay)
            
            # Capture screenshot
            filepath = await self.capture_lottery_screenshot(url, lottery_type)
            
            if filepath:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': None,
                    'status': 'failed'
                })
        
        # Log summary
        successful_captures = len([r for r in results if r['status'] == 'success'])
        total_captures = len(results)
        
        logger.info(f"=== SCREENSHOT CAPTURE COMPLETED ===")
        logger.info(f"Successfully captured {successful_captures}/{total_captures} screenshots")
        
        return results

async def run_human_like_capture():
    """Run the human-like screenshot capture process"""
    try:
        capture = HumanLikeScreenshotCapture()
        return await capture.capture_all_lottery_screenshots()
    except Exception as e:
        logger.error(f"Failed to run human-like capture: {str(e)}")
        return []

def run_capture():
    """Synchronous wrapper for the async capture function"""
    return asyncio.run(run_human_like_capture())

if __name__ == "__main__":
    results = run_capture()
    print(f"Captured {len([r for r in results if r['status'] == 'success'])} screenshots")