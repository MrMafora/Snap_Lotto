#!/usr/bin/env python3
"""
Test single URL capture with Playwright
"""

import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def test_single_capture():
    """Test capturing one lottery URL"""
    url = "https://www.nationallottery.co.za/results/lotto"
    lottery_type = "Lotto"
    
    print(f"Testing capture of {lottery_type} from {url}")
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            # Create context with South African settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-ZA',
                timezone_id='Africa/Johannesburg'
            )
            
            page = await context.new_page()
            
            # Navigate to page
            print("Navigating to lottery page...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(3000)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_{timestamp}_{lottery_type.lower()}_screenshot.png"
            filepath = os.path.join("screenshots", filename)
            
            # Ensure directory exists
            os.makedirs("screenshots", exist_ok=True)
            
            # Take screenshot
            print("Taking screenshot...")
            await page.screenshot(path=filepath, full_page=True, quality=90)
            
            # Check file
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✓ Screenshot saved: {filename} ({file_size} bytes)")
                
                # Verify it's a valid PNG
                with open(filepath, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'\x89PNG'):
                        print("✓ Valid PNG format confirmed")
                    else:
                        print("✗ Invalid PNG format")
                        
                return True
            else:
                print("✗ Screenshot file was not created")
                return False
                
            await context.close()
            await browser.close()
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_single_capture())
    print(f"\nTest result: {'SUCCESS' if result else 'FAILED'}")