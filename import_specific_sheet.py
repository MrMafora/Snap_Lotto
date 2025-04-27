"""
Import a specific sheet from an Excel file using Flask app context
"""

import logging
import sys

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import_file = sys.argv[1] if len(sys.argv) > 1 else None
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not import_file or not sheet_name:
        logger.error("Usage: python import_specific_sheet.py <excel_file> <sheet_name>")
        sys.exit(1)
    
    # Import with Flask app context
    from import_snap_lotto_data import import_snap_lotto_data
    from main import app
    
    # Enter app context
    with app.app_context():
        logger.info(f"Starting import of {import_file} sheet {sheet_name} with Flask app context")
        result = import_snap_lotto_data(import_file, flask_app=app, sheet_name=sheet_name)
        
        if result and result.get('success'):
            logger.info(f"Import completed successfully!")
            logger.info(f"Added {result.get('added')} new records")
            logger.info(f"Updated {result.get('updated')} existing records")
            logger.info(f"Total processed: {result.get('total')}")
            sys.exit(0)
        else:
            logger.error("Import failed!")
            sys.exit(1)