#!/usr/bin/env python3
"""
Lottery Data Manager - Alternative data acquisition methods for SA National Lottery
Handles website blocking with multiple fallback strategies
"""

import os
import time
import random
import logging
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LotteryDataManager:
    """Manages lottery data acquisition with anti-blocking strategies"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Alternative approaches when direct access fails
        self.strategies = [
            'homepage_navigation',
            'api_endpoints', 
            'mobile_site',
            'archive_pages',
            'rss_feeds'
        ]

    def setup_stealth_driver(self):
        """Setup Chrome driver with maximum stealth capabilities"""
        chrome_options = Options()
        
        # Stealth configuration
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('--disable-javascript')  # Sometimes bypasses blocking
        
        # Random user agent and window size
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')
        chrome_options.add_argument('--window-size=1366,768')
        
        # Anti-detection measures
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

    def try_homepage_navigation(self):
        """Try accessing results through homepage navigation"""
        driver = self.setup_stealth_driver()
        if not driver:
            return None
            
        try:
            logger.info("Attempting homepage navigation strategy...")
            
            # Go to main homepage first
            driver.get('https://www.nationallottery.co.za/')
            
            # Wait longer for page load
            time.sleep(random.uniform(5, 10))
            
            # Look for Results section or navigation
            try:
                # Try multiple selectors for Results link
                selectors = [
                    "//a[contains(text(), 'Results')]",
                    "//a[@href*='results']",
                    "//nav//a[contains(text(), 'Results')]",
                    ".navigation a[href*='results']"
                ]
                
                results_element = None
                for selector in selectors:
                    try:
                        if selector.startswith('//'):
                            results_element = driver.find_element(By.XPATH, selector)
                        else:
                            results_element = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if results_element:
                    logger.info("Found Results navigation element")
                    results_element.click()
                    time.sleep(random.uniform(3, 7))
                    
                    # Check if we got actual results page (not 404)
                    page_content = driver.page_source.lower()
                    if '404' not in page_content and 'not be found' not in page_content:
                        logger.info("Successfully navigated to results page")
                        return driver
                    else:
                        logger.warning("Navigation led to 404 page")
                        
            except Exception as nav_error:
                logger.warning(f"Navigation failed: {nav_error}")
            
            # If navigation failed, try capturing homepage with results displayed
            page_content = driver.page_source.lower()
            if any(keyword in page_content for keyword in ['lotto', 'powerball', 'daily lotto', 'winning numbers']):
                logger.info("Homepage contains lottery information")
                return driver
            
        except Exception as e:
            logger.error(f"Homepage navigation strategy failed: {e}")
        finally:
            if driver:
                driver.quit()
        
        return None

    def try_mobile_site(self):
        """Try accessing mobile version of the site"""
        driver = self.setup_stealth_driver()
        if not driver:
            return None
            
        try:
            logger.info("Attempting mobile site strategy...")
            
            # Set mobile user agent
            mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": mobile_ua})
            
            # Set mobile viewport
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'mobile': True,
                'width': 375,
                'height': 667,
                'deviceScaleFactor': 2
            })
            
            # Try mobile URLs
            mobile_urls = [
                'https://m.nationallottery.co.za/',
                'https://mobile.nationallottery.co.za/',
                'https://www.nationallottery.co.za/mobile/',
                'https://www.nationallottery.co.za/?mobile=1'
            ]
            
            for url in mobile_urls:
                try:
                    driver.get(url)
                    time.sleep(random.uniform(3, 6))
                    
                    page_content = driver.page_source.lower()
                    if '404' not in page_content and 'not be found' not in page_content:
                        if any(keyword in page_content for keyword in ['lotto', 'powerball', 'results']):
                            logger.info(f"Mobile site accessible: {url}")
                            return driver
                            
                except Exception as url_error:
                    logger.debug(f"Mobile URL failed: {url} - {url_error}")
                    continue
            
        except Exception as e:
            logger.error(f"Mobile site strategy failed: {e}")
        finally:
            if driver:
                driver.quit()
        
        return None

    def try_api_endpoints(self):
        """Try accessing potential API endpoints"""
        logger.info("Attempting API endpoints strategy...")
        
        # Potential API endpoints that might exist
        api_endpoints = [
            'https://www.nationallottery.co.za/api/results',
            'https://www.nationallottery.co.za/api/latest-results',
            'https://api.nationallottery.co.za/results',
            'https://www.nationallottery.co.za/results.json',
            'https://www.nationallottery.co.za/feed/results',
            'https://www.nationallottery.co.za/rss/results'
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        for endpoint in api_endpoints:
            try:
                response = session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    if any(keyword in content for keyword in ['lotto', 'powerball', 'results', 'winning']):
                        logger.info(f"API endpoint accessible: {endpoint}")
                        return response.text
                        
            except Exception as e:
                logger.debug(f"API endpoint failed: {endpoint} - {e}")
                continue
        
        return None

    def capture_with_fallbacks(self, lottery_type):
        """Attempt capture using multiple fallback strategies"""
        logger.info(f"Starting multi-strategy capture for {lottery_type}")
        
        strategies = [
            self.try_homepage_navigation,
            self.try_mobile_site,
            self.try_api_endpoints
        ]
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"Trying strategy {i}/{len(strategies)}: {strategy.__name__}")
            
            try:
                result = strategy()
                if result:
                    logger.info(f"Strategy {strategy.__name__} succeeded!")
                    return result
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
            
            # Wait between strategies
            time.sleep(random.uniform(2, 5))
        
        logger.error(f"All capture strategies failed for {lottery_type}")
        return None

def test_capture_strategies():
    """Test all capture strategies"""
    print("🔍 Testing Lottery Data Capture Strategies")
    print("=" * 50)
    
    manager = LotteryDataManager()
    
    # Test each strategy
    strategies = [
        ("Homepage Navigation", manager.try_homepage_navigation),
        ("Mobile Site Access", manager.try_mobile_site), 
        ("API Endpoints", manager.try_api_endpoints)
    ]
    
    results = {}
    
    for name, strategy in strategies:
        print(f"\n🧪 Testing: {name}")
        try:
            result = strategy()
            if result:
                print(f"✅ {name}: SUCCESS")
                results[name] = "SUCCESS"
            else:
                print(f"❌ {name}: FAILED")
                results[name] = "FAILED"
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results[name] = f"ERROR - {str(e)[:50]}"
    
    print(f"\n📊 Results Summary:")
    for name, result in results.items():
        print(f"  {name}: {result}")
    
    return results

if __name__ == "__main__":
    test_capture_strategies()