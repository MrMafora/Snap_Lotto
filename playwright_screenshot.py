#!/usr/bin/env python3
"""
Playwright-based screenshot capture for lottery automation
More reliable than Selenium for this use case
"""
import os
import asyncio
from playwright.async_api import async_playwright

async def capture_with_playwright(url, output_path):
    """Capture screenshot using Playwright - more reliable than Selenium"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Navigate to page
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(3000)  # Let content load
            
            # Take screenshot
            await page.screenshot(path=output_path, full_page=True)
            await browser.close()
            
            return os.path.exists(output_path)
            
    except Exception as e:
        print(f"Playwright error: {e}")
        return False

def sync_capture_screenshot(url, output_path):
    """Synchronous wrapper for the async Playwright function"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return asyncio.run(capture_with_playwright(url, output_path))

def test_playwright_capture():
    """Test Playwright screenshot capture"""
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_path = "screenshots/test_playwright.png"
    
    print(f"Testing Playwright capture for: {test_url}")
    success = sync_capture_screenshot(test_url, output_path)
    
    if success:
        size = os.path.getsize(output_path)
        print(f"✓ Playwright screenshot successful! ({size} bytes)")
        return True
    else:
        print("✗ Playwright screenshot failed")
        return False

if __name__ == "__main__":
    test_playwright_capture()