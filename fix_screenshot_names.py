"""
Fix the names of duplicate lottery screenshots.

This script:
1. Fixes the specific case where Powerball_Results_20250503_021230.png is mislabeled
   (it actually contains PowerBall Plus data)
2. Updates the database to reflect the correct lottery type
"""
import os
import logging
import sys
import shutil
from main import app
from models import Screenshot, ScheduleConfig, db

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("fix_names")

def fix_powerball_filename():
    """Fix the mislabeled Powerball screenshot that contains PowerBall Plus data"""
    # Define the wrong and correct filenames
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    wrong_file = os.path.join(attached_assets_dir, 'Powerball_Results_20250503_021230.png')
    
    # Check if the file exists
    if not os.path.exists(wrong_file):
        logger.error(f"Wrong file not found: {wrong_file}")
        return False
    
    # No need to create a new copy since we already have Powerball_Plus_Results_20250503_020809.png
    # Delete the incorrectly named file
    try:
        os.remove(wrong_file)
        logger.info(f"Removed incorrectly named file: {wrong_file}")
        return True
    except Exception as e:
        logger.error(f"Error removing file: {str(e)}")
        return False

def update_database_records():
    """Update screenshot database records for the fixed files"""
    with app.app_context():
        try:
            # Find the PowerBall record that should be PowerBall Plus
            wrong_record = Screenshot.query.filter_by(lottery_type="PowerBall").first()
            
            if wrong_record:
                logger.info(f"Found PowerBall record with ID {wrong_record.id}")
                
                # Check if it's the specific wrong record we're looking for
                if "Powerball_Results_" in wrong_record.path:
                    # Instead of fixing, we'll delete this record as it's a duplicate
                    logger.info(f"Deleting duplicate PowerBall record with ID {wrong_record.id}")
                    db.session.delete(wrong_record)
                    db.session.commit()
                    return True
                else:
                    logger.info(f"This doesn't appear to be the record we're looking for: {wrong_record.path}")
            else:
                logger.info("No PowerBall record found to fix")
            
            return False
        except Exception as e:
            logger.error(f"Error updating database records: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    """Main execution function"""
    logger.info("Starting screenshot name fixer")
    
    # Fix PowerBall Plus filename
    file_fixed = fix_powerball_filename()
    
    # Update database records
    if file_fixed:
        db_updated = update_database_records()
        logger.info(f"Database records updated: {db_updated}")
    
    logger.info("Filename fixing complete")

if __name__ == "__main__":
    main()