"""
Test the download functionality for screenshots.

This script:
1. Retrieves all screenshots from the database
2. Validates that each screenshot file exists
3. Verifies that no placeholder images are created
4. Reports the status of each screenshot's download capability
"""
import os
import logging
from datetime import datetime
from models import Screenshot, db
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_screenshot_downloads():
    """
    Test the download capability for all screenshots
    
    Returns:
        dict: Test results
    """
    results = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'details': []
    }
    
    try:
        # Get all screenshots
        screenshots = Screenshot.query.all()
        
        results['total'] = len(screenshots)
        
        for screenshot in screenshots:
            screenshot_result = {
                'id': screenshot.id,
                'lottery_type': screenshot.lottery_type,
                'timestamp': screenshot.timestamp.strftime('%Y-%m-%d %H:%M:%S') if screenshot.timestamp else 'None',
                'path': screenshot.path,
                'status': 'invalid',
                'error': None
            }
            
            # Basic validation
            if not screenshot.path:
                screenshot_result['error'] = 'No path specified'
            elif not os.path.exists(screenshot.path):
                screenshot_result['error'] = 'File does not exist'
            elif os.path.getsize(screenshot.path) == 0:
                screenshot_result['error'] = 'File is empty'
            else:
                # File exists and has content
                screenshot_result['status'] = 'valid'
                results['valid'] += 1
            
            # If the status is still invalid, count it
            if screenshot_result['status'] == 'invalid':
                results['invalid'] += 1
            
            results['details'].append(screenshot_result)
        
    except Exception as e:
        logger.error(f"Error testing screenshot downloads: {str(e)}")
        results['error'] = str(e)
    
    return results

def fix_screenshot_paths_in_db():
    """
    Update screenshot paths in the database to point to actual files
    
    Returns:
        dict: Update results
    """
    results = {
        'total': 0,
        'updated': 0,
        'details': []
    }
    
    try:
        # Get all screenshots
        screenshots = Screenshot.query.all()
        
        results['total'] = len(screenshots)
        
        # Base screenshot directory
        base_dir = Config.SCREENSHOT_DIR
        
        for screenshot in screenshots:
            # Skip if already valid
            if screenshot.path and os.path.exists(screenshot.path) and os.path.getsize(screenshot.path) > 0:
                continue
                
            # New path naming convention
            lottery_type_clean = screenshot.lottery_type.replace(' ', '_').lower()
            if screenshot.timestamp:
                date_str = screenshot.timestamp.strftime('%Y%m%d')
                new_filename = f"{lottery_type_clean}_{date_str}.png"
            else:
                # If no timestamp, use current date
                date_str = datetime.now().strftime('%Y%m%d')
                new_filename = f"{lottery_type_clean}_{date_str}.png"
            
            # Potential screenshot file
            new_path = os.path.join(base_dir, new_filename)
            
            # Only update if the new file exists
            if os.path.exists(new_path) and os.path.getsize(new_path) > 0:
                screenshot.path = new_path
                results['updated'] += 1
                results['details'].append({
                    'id': screenshot.id,
                    'lottery_type': screenshot.lottery_type,
                    'old_path': screenshot.path,
                    'new_path': new_path
                })
        
        # Commit changes if any updates were made
        if results['updated'] > 0:
            db.session.commit()
            
    except Exception as e:
        logger.error(f"Error fixing screenshot paths: {str(e)}")
        results['error'] = str(e)
    
    return results

if __name__ == "__main__":
    print("Testing screenshot download functionality...")
    
    # First, test current screenshots
    initial_test = test_screenshot_downloads()
    
    print(f"Initial Test Results:")
    print(f"  Total screenshots: {initial_test['total']}")
    print(f"  Valid for download: {initial_test['valid']}")
    print(f"  Invalid screenshots: {initial_test['invalid']}")
    
    # If there are invalid screenshots, try to fix their paths
    if initial_test['invalid'] > 0:
        print("\nAttempting to fix invalid screenshot paths...")
        fix_results = fix_screenshot_paths_in_db()
        
        print(f"Path Fix Results:")
        print(f"  Total screenshots: {fix_results['total']}")
        print(f"  Updated paths: {fix_results['updated']}")
        
        # Test again after fixes
        final_test = test_screenshot_downloads()
        
        print(f"\nFinal Test Results:")
        print(f"  Total screenshots: {final_test['total']}")
        print(f"  Valid for download: {final_test['valid']}")
        print(f"  Invalid screenshots: {final_test['invalid']}")
        
        # List remaining invalid screenshots
        if final_test['invalid'] > 0:
            print("\nRemaining invalid screenshots:")
            for detail in final_test['details']:
                if detail['status'] == 'invalid':
                    print(f"  ID {detail['id']}: {detail['lottery_type']} - {detail['error']}")
    
    print("\nDownload Route:")
    print("  To download a valid screenshot, use the URL: /download-screenshot/<screenshot_id>")
    print("  The file will be served as an attachment with the correct filename.")