#!/usr/bin/env python3
"""
Emergency fix to get screenshot capture working immediately
This will replace the hanging browser setup with a working solution
"""
import os
import subprocess
import time
from urllib.parse import urlparse

def emergency_screenshot_capture(url, output_path):
    """Emergency screenshot using system Chrome directly"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use system chrome directly with minimal options
        chrome_cmd = [
            '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--window-size=1920,1080',
            '--screenshot=' + output_path,
            url
        ]
        
        print(f"Emergency capture: {url}")
        
        # Run with timeout to prevent hanging
        result = subprocess.run(chrome_cmd, timeout=30, capture_output=True, text=True)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"✓ Emergency screenshot success: {output_path}")
            return True
        else:
            print(f"✗ Emergency screenshot failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Emergency screenshot timed out")
        return False
    except Exception as e:
        print(f"✗ Emergency screenshot error: {e}")
        return False

def fix_screenshot_manager():
    """Replace the broken screenshot function with working version"""
    
    working_function = '''
def capture_screenshot_from_url(url, output_path):
    """Working screenshot capture - emergency fix"""
    import subprocess
    import os
    
    if not _screenshot_lock.acquire(blocking=False):
        logger.warning("Screenshot capture already in progress, skipping")
        return False
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Emergency capture: {url}")
        
        # Use wkhtmltopdf for reliable screenshots
        cmd = [
            'wkhtmltoimage',
            '--width', '1920',
            '--height', '1080',
            '--quality', '94',
            url,
            output_path
        ]
        
        result = subprocess.run(cmd, timeout=25, capture_output=True)
        
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Screenshot captured successfully: {output_path}")
            
            # Apply smart cropping
            try:
                crop_white_space(output_path, output_path)
                logger.info("Smart cropping applied")
            except Exception as e:
                logger.warning(f"Smart cropping failed: {e}")
            
            return True
        else:
            logger.error("Screenshot capture failed")
            return False
            
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return False
    finally:
        _screenshot_lock.release()
'''
    
    return working_function

def test_emergency_fix():
    """Test the emergency screenshot fix"""
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_path = "screenshots/emergency_test.png"
    
    success = emergency_screenshot_capture(test_url, output_path)
    
    if success:
        print(f"✓ Emergency fix works! Screenshot size: {os.path.getsize(output_path)} bytes")
        return True
    else:
        print("✗ Emergency fix still not working")
        return False

if __name__ == "__main__":
    test_emergency_fix()