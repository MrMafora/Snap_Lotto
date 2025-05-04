"""
Fix missing draw ID 2538 data for Lottery Plus 1 and Lottery Plus 2
This script uses the integrity_import.py module to import the missing data
and ensure consistent draw IDs between related lottery games.
"""
import logging
import sys
from datetime import datetime
from main import app
from integrity_import import import_latest_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_missing_draw_2538():
    """
    Fix the missing data for draw ID 2538 for Lottery Plus 1 and Lottery Plus 2
    
    Returns:
        dict: Import statistics
    """
    try:
        file_path = 'missing_lottery_plus_2538.txt'
        
        logger.info(f"Fixing missing draw ID 2538 data from {file_path}")
        
        with open(file_path, 'r') as f:
            text_data = f.read()
            
        with app.app_context():
            result = import_latest_results(text_data)
            
            logger.info(f"Import result: {result}")
            return result
    except Exception as e:
        logger.error(f"Error fixing missing draws: {e}")
        return {
            "success": False,
            "message": f"Import failed: {str(e)}",
            "total_processed": 0,
            "imported": 0,
            "updated": 0,
            "errors": 1
        }

if __name__ == "__main__":
    logger.info("Starting fix for missing draw ID 2538 data")
    result = fix_missing_draw_2538()
    
    # Print a formatted result
    print("\n=== MISSING DRAW ID 2538 FIX REPORT ===\n")
    print(f"Success: {'Yes' if result['success'] else 'No'}")
    print(f"Total processed: {result['total_processed']}")
    print(f"Records imported: {result['imported']}")
    print(f"Records updated: {result['updated']}")
    print(f"Errors: {result['errors']}")
    print(f"Fixed relationships: {result.get('fixed_relationships', 0)}")
    
    if 'by_lottery_type' in result:
        print("\nResults by lottery type:")
        for lottery_type, count in result['by_lottery_type'].items():
            print(f"  {lottery_type}: {count}")
    
    if 'message' in result:
        print(f"\nMessage: {result['message']}")
    
    print("\nFix completed.")