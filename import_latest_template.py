#!/usr/bin/env python
"""
Direct import tool for the latest lottery template file.
This will import the most recent template file from attached_assets.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
import traceback
import re
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_latest_template():
    """Find the most recent lottery data template file in attached_assets"""
    template_pattern = "attached_assets/lottery_data_template_*.xlsx"
    template_files = glob.glob(template_pattern)
    
    # Also look for the specific file requested by the user
    user_template = "attached_assets/lottery_data_template_20250430_011720.xlsx"
    if os.path.exists(user_template):
        logger.info(f"Found specific user-requested template: {user_template}")
        return user_template
    
    if not template_files:
        logger.error("No template files found")
        return None
    
    # Sort by modification time (newest first)
    latest_file = max(template_files, key=os.path.getmtime)
    logger.info(f"Found latest template file: {latest_file}")
    return latest_file

def import_latest_template():
    """Import the latest lottery data template file"""
    # Import here to avoid circular imports
    from main import app
    import single_sheet_excel_import
    
    try:
        # Find the latest template file
        template_file = find_latest_template()
        if not template_file:
            return {"success": False, "error": "No template files found"}
        
        # Import the template file
        logger.info(f"Importing template file: {template_file}")
        with app.app_context():
            # Use the fixed import script
            import fixed_excel_import
            import_result = fixed_excel_import.import_excel_data(template_file, flask_app=app)
            
            if import_result.get('success', False):
                logger.info(f"Successfully imported template file.")
                logger.info(f"Added: {import_result.get('added', 0)}, "
                           f"Updated: {import_result.get('updated', 0)}, "
                           f"Total: {import_result.get('total', 0)}, "
                           f"Errors: {import_result.get('errors', 0)}")
            else:
                logger.error(f"Failed to import template file: {import_result.get('error', 'Unknown error')}")
            
            return import_result
    except Exception as e:
        logger.error(f"Error importing template file: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = import_latest_template()
    print(result)