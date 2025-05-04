"""
Fix missing draw ID 1611 data for Powerball and Powerball Plus
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

def fix_missing_powerball_draw_1611():
    """
    Fix the missing data for draw ID 1611 for Powerball and Powerball Plus
    
    Returns:
        dict: Import statistics
    """
    try:
        file_path = 'missing_powerball_1611.txt'
        
        logger.info(f"Fixing missing draw ID 1611 data from {file_path}")
        
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
    logger.info("Starting fix for missing draw ID 1611 data")
    result = fix_missing_powerball_draw_1611()
    
    # Print a formatted result
    print("\n=== MISSING DRAW ID 1611 FIX REPORT ===\n")
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
    
    print("\nVerifying database now contains Powerball draw 1611...")
    
    # Verify the data was imported
    from models import LotteryResult
    
    with app.app_context():
        powerball_draws = LotteryResult.query.filter_by(
            lottery_type='Powerball',
            draw_number='1611'
        ).all()
        
        powerball_plus_draws = LotteryResult.query.filter_by(
            lottery_type='Powerball Plus',
            draw_number='1611'
        ).all()
        
        print(f"\nPowerball draw 1611 in database: {len(powerball_draws) > 0}")
        print(f"Powerball Plus draw 1611 in database: {len(powerball_plus_draws) > 0}")
    
    print("\nFix completed.")