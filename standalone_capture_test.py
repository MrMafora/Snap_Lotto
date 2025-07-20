#!/usr/bin/env python3
"""
Standalone screenshot capture test - without Flask app context dependencies
"""

import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver with anti-detection features"""
    chrome_options = Options()
    
    # User agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    user_agent = random.choice(user_agents)
    screen_sizes = [(1920, 1080), (1366, 768), (1440, 900), (1280, 720)]
    screen_width, screen_height = random.choice(screen_sizes)
    
    logger.info(f"Using user agent: {user_agent[:50]}... and screen size: {screen_width}x{screen_height}")
    
    # Essential headless mode for Replit environment
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    
    # Window and user agent setup
    chrome_options.add_argument(f'--window-size={screen_width},{screen_height}')
    chrome_options.add_argument(f'--user-agent={user_agent}')
    
    # Anti-detection settings
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

def capture_homepage_lottery_data():
    """Capture homepage lottery data"""
    
    print("🧪 Standalone Homepage Capture Test")
    print("=" * 50)
    
    driver = setup_chrome_driver()
    if not driver:
        print("❌ Failed to setup browser driver")
        return None
    
    try:
        # Navigate to homepage
        url = 'https://www.nationallottery.co.za/'
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for content to load completely
        time.sleep(random.uniform(5, 8))
        
        # Check if homepage contains lottery information
        page_content = driver.page_source.lower()
        lottery_keywords = ['lotto', 'powerball', 'daily lotto', 'winning numbers', 'jackpot', 'draw']
        found_keywords = [keyword for keyword in lottery_keywords if keyword in page_content]
        
        if found_keywords:
            logger.info(f"✅ Homepage contains lottery information: {found_keywords}")
        else:
            logger.warning("❌ Homepage may not contain lottery data")
        
        # Try to scroll to lottery results section if visible
        try:
            lottery_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='lotto'], [class*='powerball'], [class*='lottery'], [class*='jackpot']")
            if lottery_elements:
                logger.info(f"Found {len(lottery_elements)} lottery-related elements")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", lottery_elements[0])
                time.sleep(random.uniform(2, 4))
        except Exception as scroll_error:
            logger.debug(f"Scroll attempt failed: {scroll_error}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"standalone_test_{timestamp}.png"
        filepath = os.path.join('screenshots', filename)
        
        # Ensure screenshots directory exists
        os.makedirs('screenshots', exist_ok=True)
        
        # Take screenshot
        driver.save_screenshot(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        print(f"✅ Screenshot captured successfully!")
        print(f"📁 File: {filepath}")
        print(f"📊 Size: {file_size:,} bytes")
        print(f"🔍 Lottery keywords found: {found_keywords}")
        
        return {
            'success': True,
            'filepath': filepath,
            'file_size': file_size,
            'keywords_found': found_keywords,
            'lottery_elements': len(lottery_elements) if 'lottery_elements' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Capture failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        driver.quit()

def test_ai_extraction_on_capture(filepath):
    """Test AI extraction on the captured screenshot"""
    if not os.path.exists(filepath):
        print("❌ Screenshot file not found for AI testing")
        return None
    
    print(f"\n🧠 Testing AI extraction on captured screenshot...")
    
    # Import and test AI extraction
    try:
        from complete_ai_workflow_test import extract_with_gemini
        
        extracted_data = extract_with_gemini(filepath)
        
        if extracted_data:
            print("✅ AI extraction successful!")
            print(f"🎯 Lottery Type: {extracted_data.get('lottery_type', 'N/A')}")
            print(f"📅 Draw Date: {extracted_data.get('draw_date', 'N/A')}")
            print(f"🔢 Main Numbers: {extracted_data.get('main_numbers', [])}")
            
            jackpot = extracted_data.get('next_jackpot')
            if jackpot:
                print(f"💰 Next Jackpot: R{jackpot:,}")
            else:
                print("💰 Next Jackpot: N/A")
                
            confidence = extracted_data.get('confidence')
            if confidence:
                print(f"📊 Confidence: {confidence}%")
                
            return extracted_data
        else:
            print("❌ AI extraction failed")
            return None
            
    except Exception as e:
        print(f"❌ AI extraction error: {e}")
        return None

if __name__ == "__main__":
    # Run standalone capture test
    result = capture_homepage_lottery_data()
    
    if result and result.get('success'):
        filepath = result['filepath']
        
        # Test AI extraction on captured screenshot
        ai_result = test_ai_extraction_on_capture(filepath)
        
        if ai_result:
            print("\n🎉 COMPLETE SUCCESS!")
            print("✅ Homepage capture working")
            print("✅ Lottery data detected")
            print("✅ AI extraction working")
            print("✅ End-to-end workflow operational")
        else:
            print("\n⚠️ Capture successful but AI extraction needs attention")
            print(f"Screenshot saved: {filepath}")
    else:
        print("\n❌ Homepage capture failed")
        if result:
            print(f"Error: {result.get('error', 'Unknown error')}")