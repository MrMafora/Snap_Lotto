"""
Step 2 Fallback: Manual Screenshot Upload System
When automated capture is blocked, users can upload current lottery screenshots
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def capture_lottery_screenshots_fallback():
    """
    Fallback method when automated capture fails
    Checks for manually uploaded screenshots in uploads folder
    """
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Check if uploads folder has fresh lottery screenshots
        if not os.path.exists(uploads_dir):
            logger.warning("Step 2 Fallback: No uploads folder found")
            return False, 0
        
        # Look for recent lottery images in uploads
        lottery_keywords = ['lotto', 'powerball', 'daily']
        recent_files = []
        
        for file in os.listdir(uploads_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Check if it's a lottery-related file
                file_lower = file.lower()
                if any(keyword in file_lower for keyword in lottery_keywords):
                    file_path = os.path.join(uploads_dir, file)
                    # Check if file is recent (within last 24 hours)
                    file_time = os.path.getmtime(file_path)
                    current_time = datetime.now().timestamp()
                    if (current_time - file_time) < 86400:  # 24 hours
                        recent_files.append((file, file_path))
        
        if not recent_files:
            logger.warning("Step 2 Fallback: No recent lottery screenshots found in uploads")
            return False, 0
        
        # Copy recent lottery files to screenshots directory
        success_count = 0
        for filename, source_path in recent_files:
            try:
                import shutil
                timestamp = int(datetime.now().timestamp())
                new_filename = f"manual_{filename}_{timestamp}.png"
                dest_path = os.path.join(screenshot_dir, new_filename)
                shutil.copy2(source_path, dest_path)
                logger.info(f"Copied manual screenshot: {new_filename}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to copy {filename}: {e}")
        
        if success_count > 0:
            logger.info(f"Step 2 Fallback successful: {success_count} screenshots ready for AI processing")
            return True, success_count
        else:
            logger.error("Step 2 Fallback: No screenshots could be prepared")
            return False, 0
            
    except Exception as e:
        logger.error(f"Step 2 Fallback failed: {e}")
        return False, 0

def check_manual_upload_status():
    """Check if manual uploads are available for processing"""
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(uploads_dir):
            return False, "No uploads folder found"
        
        lottery_files = []
        for file in os.listdir(uploads_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_lower = file.lower()
                if any(keyword in file_lower for keyword in ['lotto', 'powerball', 'daily']):
                    lottery_files.append(file)
        
        if not lottery_files:
            return False, "No lottery screenshots found in uploads"
        
        return True, f"Found {len(lottery_files)} lottery screenshots ready for processing"
        
    except Exception as e:
        return False, f"Error checking uploads: {e}"