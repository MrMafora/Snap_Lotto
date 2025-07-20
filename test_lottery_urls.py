#!/usr/bin/env python3
"""
Test and verify South African National Lottery URLs
"""

import requests
import time
from urllib.parse import urljoin

# Current URLs from screenshot_capture.py
CURRENT_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/lotto/results',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/lotto-plus/results', 
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/lotto-plus-2/results',
    'POWERBALL': 'https://www.nationallottery.co.za/powerball/results',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/powerball-plus/results',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/daily-lotto/results'
}

# Alternative URL patterns to test
ALTERNATIVE_PATTERNS = [
    'https://www.nationallottery.co.za/{}/latest-results',
    'https://www.nationallottery.co.za/games/{}/results',
    'https://www.nationallottery.co.za/results/{}',
    'https://www.nationallottery.co.za/{}-results'
]

def test_url(url, timeout=10):
    """Test if URL is accessible and returns valid content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.text.lower()
            if '404' in content or 'not be found' in content or 'error' in content:
                return False, f"404/Error page content detected"
            return True, f"Status: {response.status_code}, Length: {len(content)}"
        else:
            return False, f"Status: {response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def find_working_urls():
    """Test current URLs and find alternatives if needed"""
    
    print("🔍 Testing Current Lottery URLs")
    print("=" * 60)
    
    working_urls = {}
    failed_urls = {}
    
    # Test current URLs
    for lottery_type, url in CURRENT_URLS.items():
        print(f"Testing {lottery_type}...")
        success, message = test_url(url)
        
        if success:
            print(f"  ✅ {url} - {message}")
            working_urls[lottery_type] = url
        else:
            print(f"  ❌ {url} - {message}")
            failed_urls[lottery_type] = url
        
        time.sleep(1)  # Be respectful to the server
    
    # If we have failed URLs, try alternatives
    if failed_urls:
        print("\n🔧 Testing Alternative URL Patterns")
        print("=" * 60)
        
        for lottery_type in failed_urls:
            print(f"\nFinding alternatives for {lottery_type}...")
            
            # Try different URL patterns
            lottery_slug = lottery_type.lower().replace(' ', '-').replace('plus', 'plus')
            
            test_patterns = [
                f"https://www.nationallottery.co.za/{lottery_slug}/results",
                f"https://www.nationallottery.co.za/games/{lottery_slug}",
                f"https://www.nationallottery.co.za/results/{lottery_slug}",
                f"https://www.nationallottery.co.za/{lottery_slug}",
                f"https://www.nationallottery.co.za/{lottery_type.lower().replace(' ', '')}/results"
            ]
            
            found_working = False
            for test_url in test_patterns:
                success, message = test_url(test_url)
                if success:
                    print(f"  ✅ Found working URL: {test_url} - {message}")
                    working_urls[lottery_type] = test_url
                    found_working = True
                    break
                else:
                    print(f"  ❌ {test_url} - {message}")
                
                time.sleep(0.5)
            
            if not found_working:
                print(f"  ⚠️ No working URL found for {lottery_type}")
    
    return working_urls

def generate_updated_urls(working_urls):
    """Generate updated LOTTERY_URLS dictionary"""
    print("\n📝 Updated LOTTERY_URLS Configuration")
    print("=" * 60)
    print("LOTTERY_URLS = {")
    for lottery_type, url in working_urls.items():
        print(f"    '{lottery_type}': '{url}',")
    print("}")

if __name__ == "__main__":
    print("🌐 South African National Lottery URL Validator")
    print("=" * 60)
    
    working_urls = find_working_urls()
    
    print(f"\n📊 Results Summary:")
    print(f"✅ Working URLs: {len(working_urls)}")
    print(f"❌ Failed URLs: {len(CURRENT_URLS) - len(working_urls)}")
    
    if working_urls:
        generate_updated_urls(working_urls)
    else:
        print("\n⚠️ No working URLs found - website may be down or have major changes")