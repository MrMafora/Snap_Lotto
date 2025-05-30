"""
Step 1: Clean Screenshot Folder
Simple, reliable cleanup system
"""
import os
import logging

logger = logging.getLogger(__name__)

def cleanup_screenshots():
    """Remove all PNG files from screenshots directory"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)
            logger.info("Created screenshots directory")
            return True, 0
        
        png_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
        count = 0
        
        for file in png_files:
            file_path = os.path.join(screenshot_dir, file)
            try:
                os.remove(file_path)
                count += 1
                logger.info(f"Removed: {file}")
            except Exception as e:
                logger.error(f"Failed to remove {file}: {e}")
        
        logger.info(f"Cleanup completed. Removed {count} PNG files")
        return True, count
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False, 0