#!/usr/bin/env python3
"""
Test PNG screenshot capture from results pages only
"""

import logging
from step2_capture import get_urls_from_database, capture_url_screenshot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_results_capture():
    """Test capturing PNG screenshots from results pages"""
    logger.info("=== TESTING RESULTS PAGE PNG CAPTURE ===")
    
    # Get results page URLs
    urls = get_urls_from_database()
    
    print(f"Testing PNG capture for {len(urls)} results pages:")
    for url_config in urls:
        print(f"- {url_config['lottery_type']}: {url_config['url']}")
    
    # Test capture of first URL only
    if urls:
        test_url = urls[0]
        logger.info(f"Testing PNG capture for: {test_url['lottery_type']}")
        
        result = capture_url_screenshot(test_url['url'], test_url['lottery_type'])
        
        if result['status'] == 'success':
            print(f"\n✓ SUCCESS: {result['filename']} ({result.get('file_size', 'Unknown')} bytes)")
        else:
            print(f"\n✗ FAILED: {result['status']}")
            if 'error' in result:
                print(f"Error: {result['error']}")
    
    return True

if __name__ == "__main__":
    test_results_capture()