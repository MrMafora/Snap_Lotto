#!/usr/bin/env python3
"""
Simple test to find exactly where the automation gets stuck
"""
import os
import time
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cleanup_only():
    """Test just the cleanup step in isolation"""
    logger.info("=== TESTING CLEANUP ONLY ===")
    
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        logger.info(f"Screenshot directory: {screenshot_dir}")
        
        # Check if directory exists
        if not os.path.exists(screenshot_dir):
            logger.info("Directory doesn't exist, creating it")
            os.makedirs(screenshot_dir, exist_ok=True)
            return True, 0
        
        # List files
        files = os.listdir(screenshot_dir)
        logger.info(f"Found {len(files)} files: {files}")
        
        deleted_count = 0
        for filename in files:
            if filename.endswith('.png'):
                file_path = os.path.join(screenshot_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted: {filename}")
                except Exception as e:
                    logger.warning(f"Could not delete {filename}: {e}")
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} files")
        return True, deleted_count
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False, 0

if __name__ == "__main__":
    logger.info("Starting simple automation test...")
    start_time = time.time()
    
    success, count = test_cleanup_only()
    elapsed = time.time() - start_time
    
    logger.info(f"Test completed in {elapsed:.2f} seconds")
    logger.info(f"Result: success={success}, count={count}")
    
    if elapsed > 5:
        logger.warning("Test took too long - there may be a hanging issue")
    else:
        logger.info("Test completed quickly - cleanup function works fine")